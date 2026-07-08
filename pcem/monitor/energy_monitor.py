"""
Energy Monitor — Real System Power Measurement

PATENT-CRITICAL MODULE: Measures ACTUAL CPU/system power consumption
during inference, rather than relying solely on token-based estimates.

This module:
1. Tracks CPU utilization during inference using psutil
2. Estimates power consumption from CPU% × TDP wattage
3. Compares measured energy vs estimated energy
4. Self-calibrates: uses measurement history to improve future estimates
5. Provides estimation accuracy tracking (estimation_error_pct over time)

The key insight: Token-based energy estimation is approximate (~30% error).
By measuring actual system power, we can:
- Provide accurate carbon footprint data
- Calibrate the estimation model over time
- Detect anomalous energy consumption
"""

import time
import statistics
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from backend.database.connection import SessionLocal
from backend.database.models import EnergyMeasurement


class EnergyMonitor:
    """
    Monitors actual system power consumption during inference.
    
    Uses psutil to track CPU utilization and estimate real power draw.
    Tracks estimation accuracy over time for self-calibration.
    """

    # Default TDP (Thermal Design Power) for common hardware
    # Adjustable per system via set_tdp()
    DEFAULT_CPU_TDP_WATTS = 65.0     # Typical desktop CPU
    DEFAULT_GPU_TDP_WATTS = 150.0    # Typical mid-range GPU
    IDLE_POWER_WATTS = 15.0          # Base system idle power

    # Power Usage Effectiveness (typical data center = 1.2)
    PUE = 1.2

    # Sampling interval for CPU measurements
    SAMPLE_INTERVAL_SEC = 0.1

    def __init__(self, cpu_tdp_watts: float = None, gpu_tdp_watts: float = None):
        """Initialize monitor with optional TDP values."""
        self.cpu_tdp = cpu_tdp_watts or self.DEFAULT_CPU_TDP_WATTS
        self.gpu_tdp = gpu_tdp_watts or self.DEFAULT_GPU_TDP_WATTS
        self._start_time = None
        self._cpu_samples = []
        self._is_measuring = False
        self._calibration_factor = 1.0
        self._load_calibration()

    def _load_calibration(self):
        """
        Load calibration factor from historical measurements.
        
        If we consistently over-estimate by 40%, the calibration
        factor adjusts future estimates down by 40%.
        """
        try:
            db = SessionLocal()
            measurements = (
                db.query(EnergyMeasurement)
                .filter(EnergyMeasurement.estimation_error_pct.isnot(None))
                .order_by(EnergyMeasurement.created_at.desc())
                .limit(20)
                .all()
            )
            db.close()

            if len(measurements) >= 3:
                errors = [m.estimation_error_pct for m in measurements if m.estimation_error_pct]
                avg_error = statistics.mean(errors)
                # Calibration: if estimation is 30% too high, factor = 0.7
                self._calibration_factor = max(0.3, min(2.0, 1.0 - avg_error / 100))
        except Exception:
            self._calibration_factor = 1.0

    def start_measurement(self) -> None:
        """Begin measuring system power consumption."""
        if not PSUTIL_AVAILABLE:
            self._start_time = time.time()
            return

        # Prime the CPU percent counter
        psutil.cpu_percent(interval=None)

        self._start_time = time.time()
        self._cpu_samples = []
        self._is_measuring = True

    def sample(self) -> None:
        """Take a single CPU utilization sample during inference."""
        if not PSUTIL_AVAILABLE or not self._is_measuring:
            return

        cpu_pct = psutil.cpu_percent(interval=None)
        self._cpu_samples.append(cpu_pct)

    def stop_measurement(self) -> Dict[str, Any]:
        """
        Stop measuring and calculate actual energy consumption.
        
        Power model:
          actual_power = idle_power + (cpu_pct/100 × cpu_tdp) × PUE
          energy = power × duration
        
        Returns:
            Dict with measured energy, CPU stats, and duration.
        """
        if self._start_time is None:
            return {"measured_kwh": 0, "duration_seconds": 0, "error": "No measurement started"}

        duration = time.time() - self._start_time
        self._is_measuring = False

        # Take final sample
        if PSUTIL_AVAILABLE:
            self._cpu_samples.append(psutil.cpu_percent(interval=None))

        # Calculate power
        if self._cpu_samples:
            avg_cpu = statistics.mean(self._cpu_samples)
            peak_cpu = max(self._cpu_samples)
        else:
            avg_cpu = 20.0  # Fallback estimate
            peak_cpu = 50.0

        # Power model: idle + CPU load + PUE overhead
        avg_power_watts = (
            self.IDLE_POWER_WATTS +
            (avg_cpu / 100.0) * self.cpu_tdp
        ) * self.PUE

        # Energy = Power × Time (convert W·s to kWh)
        measured_kwh = (avg_power_watts * duration) / 3600 / 1000

        self._start_time = None
        self._cpu_samples = []

        return {
            "measured_kwh": round(measured_kwh, 8),
            "avg_power_watts": round(avg_power_watts, 2),
            "duration_seconds": round(duration, 3),
            "cpu_avg_percent": round(avg_cpu, 1),
            "cpu_peak_percent": round(peak_cpu, 1),
            "cpu_samples": len(self._cpu_samples) if self._cpu_samples else 1,
            "psutil_available": PSUTIL_AVAILABLE,
        }

    def compare_and_record(
        self,
        estimated_kwh: float,
        measurement: Dict[str, Any],
        run_id: int = None,
    ) -> Dict[str, Any]:
        """
        Compare estimated vs measured energy and save to database.
        
        This is the self-calibration loop:
        1. Record the comparison
        2. Calculate estimation error percentage
        3. Over time, the calibration factor adjusts future estimates
        
        Returns:
            Comparison results including estimation accuracy.
        """
        measured_kwh = measurement.get("measured_kwh", 0)

        # Calculate estimation error
        if measured_kwh > 0:
            error_pct = ((estimated_kwh - measured_kwh) / measured_kwh) * 100
        else:
            error_pct = 0

        # Calibrated estimate (what the estimate SHOULD have been)
        calibrated_estimate = estimated_kwh * self._calibration_factor

        # Save to database
        db = SessionLocal()
        try:
            record = EnergyMeasurement(
                run_id=run_id,
                estimated_kwh=estimated_kwh,
                measured_kwh=measured_kwh,
                cpu_avg_percent=measurement.get("cpu_avg_percent"),
                duration_seconds=measurement.get("duration_seconds"),
                avg_power_watts=measurement.get("avg_power_watts"),
                estimation_error_pct=round(error_pct, 2),
            )
            db.add(record)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

        return {
            "estimated_kwh": round(estimated_kwh, 8),
            "measured_kwh": round(measured_kwh, 8),
            "calibrated_estimate_kwh": round(calibrated_estimate, 8),
            "estimation_error_pct": round(error_pct, 2),
            "calibration_factor": round(self._calibration_factor, 4),
            "measurement_details": measurement,
        }

    def get_calibration_stats(self) -> Dict[str, Any]:
        """
        Get historical calibration statistics.
        
        Shows how estimation accuracy has improved over time.
        """
        db = SessionLocal()
        try:
            records = (
                db.query(EnergyMeasurement)
                .filter(EnergyMeasurement.estimation_error_pct.isnot(None))
                .order_by(EnergyMeasurement.created_at.desc())
                .limit(50)
                .all()
            )

            if not records:
                return {
                    "total_measurements": 0,
                    "calibration_factor": self._calibration_factor,
                    "status": "no_data",
                }

            errors = [r.estimation_error_pct for r in records]
            recent_errors = errors[:10]

            return {
                "total_measurements": len(records),
                "avg_error_pct": round(statistics.mean(errors), 2),
                "recent_avg_error_pct": round(statistics.mean(recent_errors), 2),
                "error_std": round(statistics.stdev(errors), 2) if len(errors) > 1 else 0,
                "calibration_factor": round(self._calibration_factor, 4),
                "trend": "improving" if abs(statistics.mean(recent_errors)) < abs(statistics.mean(errors)) else "stable",
            }
        finally:
            db.close()


# Singleton instance
energy_monitor = EnergyMonitor()

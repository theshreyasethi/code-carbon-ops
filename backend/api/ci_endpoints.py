"""
CI/CD Carbon Enforcement Endpoints — with Anomaly Detection

PATENT-CRITICAL MODULE: Combines static carbon budgets with
statistical anomaly detection per repository.

This module:
1. Maintains per-repo carbon footprint baselines (mean, std)
2. Uses z-score anomaly detection to flag unusual carbon spikes
3. Detects carbon trends per repository (improving/worsening)
4. Provides optimization suggestions based on code metrics
5. Dual enforcement: static budget + anomaly detection

Enforcement logic:
  - z_score > 3.0  → BLOCK  (extreme anomaly, 99.7th percentile)
  - z_score > 2.0  → WARN   (unusual spike, 97.7th percentile)  
  - over_budget     → WARN/BLOCK (existing budget logic)
  - else            → ALLOW
"""

from fastapi import APIRouter
from datetime import datetime, timedelta
import math
import statistics as stats_lib
from typing import Dict, Any, List, Optional

from pcem.analyzer.task_analyzer import analyze_task
from pcem.monitor.carbon_monitor import get_current_carbon_data
from pcem.router.smart_router import select_best_server
from offsets.calculator import get_offset_recommendation
from backend.database.connection import SessionLocal
from backend.database.models import CIRun

router = APIRouter(prefix="/api/v1/ci", tags=["CI/CD"])


# Default carbon budgets per job type (grams CO2)
CI_CARBON_BUDGETS = {
    "build_and_test": 50.0,
    "build": 30.0,
    "test": 20.0,
    "deploy": 40.0,
    "lint": 10.0,
    "integration_test": 100.0,
    "full_deploy": 200.0,
    "default": 50.0,
}

# Energy estimation per line of code change (kWh)
ENERGY_PER_LINE = 0.000005
ENERGY_BASE_BUILD = 0.01
ENERGY_PER_FILE = 0.0005


class CIAnomalyDetector:
    """
    Statistical anomaly detector for CI/CD carbon footprints.
    
    Maintains per-repo baselines and detects when a new PR's
    predicted carbon is statistically unusual compared to history.
    
    Uses z-score analysis: z = (x - μ) / σ
    - z > 2.0: Unusual (WARN)
    - z > 3.0: Extreme anomaly (BLOCK)
    """

    # Minimum historical runs before anomaly detection activates
    MIN_HISTORY_FOR_DETECTION = 5

    # Z-score thresholds
    WARN_THRESHOLD = 2.0   # ~97.7th percentile
    BLOCK_THRESHOLD = 3.0  # ~99.7th percentile

    def get_repo_baseline(self, repo: str) -> Dict[str, Any]:
        """
        Calculate carbon footprint baseline for a repository.
        
        Returns mean, std, min, max, and sample count from
        the last 90 days of CI runs for this repo.
        """
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(days=90)
            runs = (
                db.query(CIRun)
                .filter(
                    CIRun.repo == repo,
                    CIRun.created_at >= cutoff,
                    CIRun.predicted_carbon_g.isnot(None),
                )
                .all()
            )

            if len(runs) < self.MIN_HISTORY_FOR_DETECTION:
                return {
                    "status": "insufficient_data",
                    "sample_count": len(runs),
                    "mean": None,
                    "std": None,
                    "min": None,
                    "max": None,
                }

            carbons = [r.predicted_carbon_g for r in runs]

            return {
                "status": "ready",
                "sample_count": len(carbons),
                "mean": round(stats_lib.mean(carbons), 4),
                "std": round(stats_lib.stdev(carbons), 4) if len(carbons) > 1 else 0,
                "min": round(min(carbons), 4),
                "max": round(max(carbons), 4),
                "median": round(stats_lib.median(carbons), 4),
            }

        finally:
            db.close()

    def detect_anomaly(
        self, repo: str, predicted_carbon: float
    ) -> Dict[str, Any]:
        """
        Check if a new CI run's carbon footprint is anomalous.
        
        Uses z-score: z = (predicted - mean) / std
        
        Returns:
            anomaly result with z_score, is_anomaly flag, and severity.
        """
        baseline = self.get_repo_baseline(repo)

        if baseline["status"] != "ready":
            return {
                "is_anomaly": False,
                "z_score": 0,
                "severity": "none",
                "reason": "Insufficient history for anomaly detection",
                "baseline": baseline,
            }

        mean = baseline["mean"]
        std = baseline["std"]

        # Avoid division by zero
        if std == 0 or std is None:
            z_score = 0 if predicted_carbon <= mean else 1.0
        else:
            z_score = (predicted_carbon - mean) / std

        # Determine severity
        if z_score > self.BLOCK_THRESHOLD:
            severity = "critical"
            is_anomaly = True
        elif z_score > self.WARN_THRESHOLD:
            severity = "warning"
            is_anomaly = True
        elif z_score > 1.5:
            severity = "elevated"
            is_anomaly = False
        else:
            severity = "normal"
            is_anomaly = False

        pct_above_mean = ((predicted_carbon - mean) / mean * 100) if mean > 0 else 0

        return {
            "is_anomaly": is_anomaly,
            "z_score": round(z_score, 3),
            "severity": severity,
            "pct_above_mean": round(pct_above_mean, 1),
            "reason": self._anomaly_reason(z_score, severity, pct_above_mean),
            "baseline": baseline,
        }

    def get_trend(self, repo: str) -> Dict[str, Any]:
        """
        Analyze carbon footprint trend for a repository.
        
        Uses linear regression on recent CI runs to detect
        if the repo's carbon footprint is increasing or decreasing.
        """
        db = SessionLocal()
        try:
            runs = (
                db.query(CIRun)
                .filter(CIRun.repo == repo, CIRun.predicted_carbon_g.isnot(None))
                .order_by(CIRun.created_at.desc())
                .limit(20)
                .all()
            )

            if len(runs) < 3:
                return {"direction": "insufficient_data", "slope": 0}

            # Simple linear regression (most recent first → reverse for time order)
            carbons = [r.predicted_carbon_g for r in reversed(runs)]
            n = len(carbons)
            x_mean = (n - 1) / 2
            y_mean = sum(carbons) / n
            numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(carbons))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            slope = numerator / denominator if denominator > 0 else 0

            if slope < -0.5:
                direction = "improving"
            elif slope > 0.5:
                direction = "worsening"
            else:
                direction = "stable"

            return {
                "direction": direction,
                "slope": round(slope, 4),
                "recent_runs": n,
                "latest_carbon": round(carbons[-1], 4) if carbons else 0,
                "oldest_carbon": round(carbons[0], 4) if carbons else 0,
            }

        finally:
            db.close()

    def suggest_optimizations(
        self, code_metrics: Dict, predicted_carbon: float, budget: float
    ) -> List[Dict[str, str]]:
        """
        Generate specific optimization suggestions based on code metrics.
        
        Analyzes what's causing high carbon and suggests actionable fixes.
        """
        suggestions = []
        files_changed = code_metrics.get("files_changed", 0)
        lines_added = code_metrics.get("lines_added", 0)
        lines_removed = code_metrics.get("lines_removed", 0)
        total_lines = lines_added + lines_removed

        if total_lines > 500:
            suggestions.append({
                "type": "split_pr",
                "priority": "high",
                "description": (
                    f"This PR changes {total_lines} lines. Split into smaller PRs "
                    f"(<200 lines each) to reduce per-run carbon by ~{int(total_lines / 200 * 30)}%."
                ),
            })

        if files_changed > 20:
            suggestions.append({
                "type": "reduce_scope",
                "priority": "high",
                "description": (
                    f"{files_changed} files changed. Consider splitting by component "
                    f"to run targeted tests instead of full test suite."
                ),
            })

        if lines_added > lines_removed * 3 and lines_added > 100:
            suggestions.append({
                "type": "code_review",
                "priority": "medium",
                "description": (
                    f"Heavy code addition ({lines_added} added vs {lines_removed} removed). "
                    f"Review for dead code or duplicated logic that increases build time."
                ),
            })

        if predicted_carbon > budget * 0.8:
            suggestions.append({
                "type": "schedule",
                "priority": "medium",
                "description": (
                    "Schedule this CI run during off-peak carbon hours "
                    "(typically early morning or late night when renewable energy is higher)."
                ),
            })

        if predicted_carbon > budget:
            suggestions.append({
                "type": "cache",
                "priority": "high",
                "description": (
                    "Enable aggressive build caching (Docker layer cache, npm cache, "
                    "dependency caching) to reduce redundant computation."
                ),
            })

        return suggestions

    def _anomaly_reason(
        self, z_score: float, severity: str, pct_above: float
    ) -> str:
        """Generate human-readable anomaly explanation."""
        if severity == "critical":
            return (
                f"⚠️ EXTREME ANOMALY: This PR's carbon footprint is {pct_above:.0f}% above "
                f"your repo's average (z-score: {z_score:.1f}, >99.7th percentile). "
                f"This is highly unusual and may indicate a significant code change."
            )
        elif severity == "warning":
            return (
                f"⚡ UNUSUAL SPIKE: This PR's carbon is {pct_above:.0f}% above average "
                f"(z-score: {z_score:.1f}, >97.7th percentile). Review code changes."
            )
        elif severity == "elevated":
            return (
                f"📈 Slightly elevated carbon ({pct_above:.0f}% above average), "
                f"but within normal variation."
            )
        else:
            return "✅ Carbon footprint is within normal range for this repository."


# Singleton
anomaly_detector = CIAnomalyDetector()


@router.post("/predict")
async def predict_ci_carbon(request: dict):
    """
    Predict the carbon impact of a CI/CD pipeline run.
    Enhanced with anomaly detection and optimization suggestions.
    """
    repo = request.get("repo", "unknown")
    pr_number = request.get("pr_number")
    branch = request.get("branch", "main")
    job_type = request.get("job_type", "build_and_test")
    code_metrics = request.get("code_metrics", {})

    files_changed = code_metrics.get("files_changed", 1)
    lines_added = code_metrics.get("lines_added", 0)
    lines_removed = code_metrics.get("lines_removed", 0)
    total_lines = lines_added + lines_removed

    # Step 1: Estimate energy
    energy_kwh = (
        ENERGY_BASE_BUILD +
        ENERGY_PER_FILE * files_changed +
        ENERGY_PER_LINE * total_lines
    )

    # Step 2: Create task analysis
    task_analysis = {
        "model": "ci-pipeline",
        "total_tokens": total_lines * 10,
        "estimated_energy_kwh": round(energy_kwh, 6),
        "estimated_gpu_seconds": files_changed * 30,
        "complexity": "moderate" if total_lines < 500 else "complex",
    }

    # Step 3: Route to best server
    carbon_data = get_current_carbon_data()
    routing = select_best_server(
        task_analysis, carbon_data,
        carbon_budget_g=CI_CARBON_BUDGETS.get(job_type, 50.0),
    )

    predicted_carbon = routing["predicted_carbon_g"]
    budget = CI_CARBON_BUDGETS.get(job_type, 50.0)

    # Step 4: Anomaly detection (NEW — P4)
    anomaly_result = anomaly_detector.detect_anomaly(repo, predicted_carbon)

    # Step 5: Make enforcement decision (enhanced with anomaly detection)
    if anomaly_result.get("z_score", 0) > anomaly_detector.BLOCK_THRESHOLD:
        action = "BLOCK"
        block_reason = "anomaly"
    elif predicted_carbon > budget:
        action = "BLOCK"
        block_reason = "over_budget"
    elif anomaly_result.get("z_score", 0) > anomaly_detector.WARN_THRESHOLD:
        action = "WARN"
        block_reason = "anomaly"
    elif predicted_carbon > budget * 0.8:
        action = "WARN"
        block_reason = "near_budget"
    else:
        action = "ALLOW"
        block_reason = None

    # Step 6: Get trend and optimization suggestions (NEW — P4)
    trend = anomaly_detector.get_trend(repo)
    optimization_suggestions = anomaly_detector.suggest_optimizations(
        code_metrics, predicted_carbon, budget
    )

    # Step 7: Offset recommendation
    offset = get_offset_recommendation(predicted_carbon, budget)

    # Step 8: Build mitigation options
    mitigation_options = []
    if action != "ALLOW":
        mitigation_options.append({
            "type": "optimize",
            "description": f"Reduce code changes to lower estimated energy ({energy_kwh:.4f} kWh)",
        })
        if routing.get("alternatives"):
            alt = routing["alternatives"][0]
            mitigation_options.append({
                "type": "reroute",
                "description": f"Route to {alt['name']} ({alt['predicted_carbon_g']}g CO₂)",
            })
        mitigation_options.append({
            "type": "schedule",
            "description": "Wait for a green window when carbon intensity is lower",
        })
        if offset.get("offset_cost_usd", 0) > 0:
            mitigation_options.append({
                "type": "offset",
                "description": f"Purchase carbon offset: ${offset['offset_cost_usd']:.6f}",
            })

    # Step 9: Save to database
    db = SessionLocal()
    try:
        ci_run = CIRun(
            repo=repo,
            branch=branch,
            pr_number=pr_number,
            job_type=job_type,
            files_changed=files_changed,
            lines_added=lines_added,
            lines_removed=lines_removed,
            predicted_energy_kwh=energy_kwh,
            predicted_carbon_g=predicted_carbon,
            recommended_server=routing["selected_server"]["name"],
            carbon_budget_g=budget,
            enforcement_action=action,
        )
        db.add(ci_run)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    # Step 10: Return enhanced response
    return {
        "prediction": {
            "energy_kwh": round(energy_kwh, 6),
            "carbon_g": round(predicted_carbon, 4),
            "water_liters": round(energy_kwh * 1.8, 4),
        },
        "budget": {
            "carbon_limit_g": budget,
            "job_type": job_type,
            "utilization_pct": round(predicted_carbon / budget * 100, 1),
        },
        "server_recommendation": {
            "name": routing["selected_server"]["name"],
            "region": routing["selected_server"]["region"],
            "carbon_intensity": routing["selected_server"]["carbon_intensity"],
            "renewable_pct": routing["selected_server"]["renewable_pct"],
        },
        "enforcement_action": action,
        "enforcement_reason": block_reason,
        "carbon_saved_g": round(routing["carbon_saved_vs_default"], 4),
        # NEW — P4: Anomaly detection results
        "anomaly_detection": {
            "is_anomaly": anomaly_result.get("is_anomaly", False),
            "z_score": anomaly_result.get("z_score", 0),
            "severity": anomaly_result.get("severity", "normal"),
            "explanation": anomaly_result.get("reason", ""),
            "baseline": anomaly_result.get("baseline", {}),
        },
        # NEW — P4: Trend analysis
        "repo_trend": trend,
        # NEW — P4: Optimization suggestions
        "optimization_suggestions": optimization_suggestions,
        "offset_status": offset.get("status", "WITHIN_BUDGET"),
        "mitigation_options": mitigation_options,
        "code_metrics": {
            "files_changed": files_changed,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
        },
    }


@router.get("/history")
async def ci_history(limit: int = 20):
    """Get recent CI/CD carbon check history."""
    db = SessionLocal()
    try:
        runs = db.query(CIRun).order_by(CIRun.created_at.desc()).limit(limit).all()
        return {"runs": [r.to_dict() for r in runs]}
    finally:
        db.close()


@router.get("/anomaly/{repo:path}")
async def repo_anomaly_stats(repo: str):
    """Get anomaly detection stats for a specific repository."""
    baseline = anomaly_detector.get_repo_baseline(repo)
    trend = anomaly_detector.get_trend(repo)
    return {
        "repo": repo,
        "baseline": baseline,
        "trend": trend,
    }

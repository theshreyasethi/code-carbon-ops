"""
Database Models - SQLAlchemy ORM

Three tables:
1. inference_runs    - Every AI inference request
2. offset_purchases  - Carbon credit purchases
3. carbon_cache      - Cached carbon API responses
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database.connection import Base


class InferenceRun(Base):
    """Stores every AI inference request and its carbon impact."""
    __tablename__ = "inference_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_hash = Column(String(64), nullable=True)       # SHA256 hash for privacy
    model = Column(String(100), nullable=False)            # e.g., "gpt-4"
    total_tokens = Column(Integer, nullable=True)
    estimated_energy_kwh = Column(Float, nullable=True)
    server_region = Column(String(50), nullable=True)
    server_name = Column(String(100), nullable=True)
    carbon_used_g = Column(Float, nullable=True)
    carbon_saved_g = Column(Float, nullable=True)
    renewable_pct = Column(Float, nullable=True)
    latency_ms = Column(Float, nullable=True)
    offset_purchased_g = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to offset purchases
    offsets = relationship("OffsetPurchase", back_populates="inference_run")

    def to_dict(self):
        return {
            "id": self.id,
            "model": self.model,
            "total_tokens": self.total_tokens,
            "estimated_energy_kwh": self.estimated_energy_kwh,
            "server_region": self.server_region,
            "server_name": self.server_name,
            "carbon_used_g": self.carbon_used_g,
            "carbon_saved_g": self.carbon_saved_g,
            "renewable_pct": self.renewable_pct,
            "offset_purchased_g": self.offset_purchased_g,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class OffsetPurchase(Base):
    """Stores carbon credit purchases."""
    __tablename__ = "offset_purchases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("inference_runs.id"), nullable=True)
    amount_g = Column(Float, nullable=False)
    cost_usd = Column(Float, nullable=False)
    provider = Column(String(100), default="simulation")
    status = Column(String(50), default="completed")       # pending/completed/failed
    transaction_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to inference run
    inference_run = relationship("InferenceRun", back_populates="offsets")

    def to_dict(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "amount_g": self.amount_g,
            "cost_usd": self.cost_usd,
            "provider": self.provider,
            "status": self.status,
            "transaction_id": self.transaction_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class CarbonCache(Base):
    """Caches carbon API responses to reduce API calls."""
    __tablename__ = "carbon_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    region = Column(String(50), unique=True, nullable=False)
    carbon_intensity = Column(Float, nullable=True)
    energy_mix = Column(Text, nullable=True)               # JSON string
    fetched_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        return {
            "region": self.region,
            "carbon_intensity": self.carbon_intensity,
            "energy_mix": json.loads(self.energy_mix) if self.energy_mix else {},
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None
        }


class HistoricalCarbon(Base):
    """Stores historical carbon data for predictive forecasting."""
    __tablename__ = "historical_carbon"

    id = Column(Integer, primary_key=True, autoincrement=True)
    region = Column(String(50), nullable=False, index=True)
    carbon_intensity = Column(Float, nullable=False)
    renewable_pct = Column(Float, nullable=True)
    hour_of_day = Column(Integer, nullable=True)        # 0-23
    day_of_week = Column(Integer, nullable=True)         # 0=Mon, 6=Sun
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "region": self.region,
            "carbon_intensity": self.carbon_intensity,
            "renewable_pct": self.renewable_pct,
            "hour_of_day": self.hour_of_day,
            "day_of_week": self.day_of_week,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None
        }


class CIRun(Base):
    """Stores CI/CD pipeline carbon check results."""
    __tablename__ = "ci_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo = Column(String(200), nullable=True)
    branch = Column(String(200), nullable=True)
    pr_number = Column(Integer, nullable=True)
    job_type = Column(String(100), nullable=True)
    files_changed = Column(Integer, nullable=True)
    lines_added = Column(Integer, nullable=True)
    lines_removed = Column(Integer, nullable=True)
    predicted_energy_kwh = Column(Float, nullable=True)
    predicted_carbon_g = Column(Float, nullable=True)
    recommended_server = Column(String(100), nullable=True)
    carbon_budget_g = Column(Float, default=50.0)
    enforcement_action = Column(String(20), nullable=True)  # ALLOW / WARN / BLOCK
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "repo": self.repo,
            "branch": self.branch,
            "pr_number": self.pr_number,
            "files_changed": self.files_changed,
            "predicted_energy_kwh": self.predicted_energy_kwh,
            "predicted_carbon_g": self.predicted_carbon_g,
            "recommended_server": self.recommended_server,
            "enforcement_action": self.enforcement_action,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class RoutingFeedback(Base):
    """
    P1: Stores routing decision outcomes for adaptive learning.
    
    Each row records what was PREDICTED vs what ACTUALLY happened,
    enabling the Thompson Sampling algorithm to learn which servers
    perform best under different urgency levels.
    """
    __tablename__ = "routing_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    server_region = Column(String(50), nullable=False, index=True)
    urgency_level = Column(Integer, nullable=True)            # 1-5
    predicted_carbon = Column(Float, nullable=True)           # What we estimated
    actual_carbon = Column(Float, nullable=True)              # What actually happened
    predicted_latency = Column(Float, nullable=True)          # Estimated ms
    actual_latency = Column(Float, nullable=True)             # Measured ms
    satisfaction_score = Column(Float, nullable=True)          # 0.0 to 1.0
    model_used = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "server_region": self.server_region,
            "urgency_level": self.urgency_level,
            "predicted_carbon": self.predicted_carbon,
            "actual_carbon": self.actual_carbon,
            "predicted_latency": self.predicted_latency,
            "actual_latency": self.actual_latency,
            "satisfaction_score": self.satisfaction_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EnergyMeasurement(Base):
    """
    P3: Stores actual energy measurements vs estimates.
    
    Tracks CPU utilization during inference to compute REAL energy
    consumption, then compares against the token-based estimation.
    Over time, the estimation model self-calibrates.
    """
    __tablename__ = "energy_measurements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("inference_runs.id"), nullable=True)
    estimated_kwh = Column(Float, nullable=True)
    measured_kwh = Column(Float, nullable=True)
    cpu_avg_percent = Column(Float, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    avg_power_watts = Column(Float, nullable=True)
    estimation_error_pct = Column(Float, nullable=True)       # (est-meas)/meas * 100
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "estimated_kwh": self.estimated_kwh,
            "measured_kwh": self.measured_kwh,
            "cpu_avg_percent": self.cpu_avg_percent,
            "duration_seconds": self.duration_seconds,
            "avg_power_watts": self.avg_power_watts,
            "estimation_error_pct": self.estimation_error_pct,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


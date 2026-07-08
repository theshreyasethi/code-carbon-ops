"""
CRUD Operations - Database Read/Write Functions

Functions for saving and retrieving:
- Inference runs
- Offset purchases
- Carbon cache data
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.database.models import InferenceRun, OffsetPurchase, CarbonCache


# ============== Inference Runs ==============

def save_inference_run(db: Session, data: Dict[str, Any]) -> InferenceRun:
    """
    Save an inference run to the database.
    
    Args:
        db: Database session
        data: Dict with inference results from the /infer endpoint
    
    Returns:
        Created InferenceRun record
    """
    # Hash the prompt for privacy
    prompt = data.get("prompt", "")
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest() if prompt else None

    run = InferenceRun(
        prompt_hash=prompt_hash,
        model=data.get("model", "unknown"),
        total_tokens=data.get("total_tokens"),
        estimated_energy_kwh=data.get("energy_kwh"),
        server_region=data.get("server_region"),
        server_name=data.get("server_name"),
        carbon_used_g=data.get("carbon_used_g"),
        carbon_saved_g=data.get("carbon_saved_g"),
        renewable_pct=data.get("renewable_pct"),
        latency_ms=data.get("latency_ms"),
        offset_purchased_g=data.get("offset_purchased_g", 0),
    )
    
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_inference_history(db: Session, limit: int = 50) -> List[Dict]:
    """Get recent inference runs, newest first."""
    runs = (
        db.query(InferenceRun)
        .order_by(InferenceRun.created_at.desc())
        .limit(limit)
        .all()
    )
    return [run.to_dict() for run in runs]


def get_inference_stats(db: Session) -> Dict[str, Any]:
    """Get aggregate stats for all inference runs."""
    from sqlalchemy import func
    
    stats = db.query(
        func.count(InferenceRun.id).label("total_runs"),
        func.coalesce(func.sum(InferenceRun.carbon_used_g), 0).label("total_carbon_g"),
        func.coalesce(func.sum(InferenceRun.carbon_saved_g), 0).label("total_saved_g"),
        func.coalesce(func.avg(InferenceRun.renewable_pct), 0).label("avg_renewable_pct"),
    ).first()
    
    return {
        "total_runs": stats.total_runs or 0,
        "total_carbon_used_g": round(float(stats.total_carbon_g), 2),
        "total_carbon_saved_g": round(float(stats.total_saved_g), 2),
        "avg_renewable_pct": round(float(stats.avg_renewable_pct), 4),
    }


# ============== Offset Purchases ==============

def save_offset_purchase(db: Session, data: Dict[str, Any]) -> OffsetPurchase:
    """
    Save a carbon offset purchase to the database.
    
    Args:
        db: Database session
        data: Dict with offset purchase details
    
    Returns:
        Created OffsetPurchase record
    """
    purchase = OffsetPurchase(
        run_id=data.get("run_id"),
        amount_g=data.get("amount_g", 0),
        cost_usd=data.get("cost_usd", 0),
        provider=data.get("provider", "simulation"),
        status=data.get("status", "completed"),
        transaction_id=data.get("transaction_id"),
    )
    
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


def get_offset_history(db: Session) -> Dict[str, Any]:
    """Get offset purchase history with totals."""
    purchases = (
        db.query(OffsetPurchase)
        .order_by(OffsetPurchase.created_at.desc())
        .all()
    )
    
    total_offset_g = sum(p.amount_g for p in purchases)
    total_cost_usd = sum(p.cost_usd for p in purchases)
    
    return {
        "total_offset_g": round(total_offset_g, 2),
        "total_cost_usd": round(total_cost_usd, 4),
        "transaction_count": len(purchases),
        "transactions": [p.to_dict() for p in purchases]
    }


# ============== Carbon Cache ==============

def cache_carbon_data(db: Session, region: str, carbon_intensity: float, energy_mix: Dict) -> CarbonCache:
    """Save or update cached carbon data for a region."""
    existing = db.query(CarbonCache).filter(CarbonCache.region == region).first()
    
    if existing:
        existing.carbon_intensity = carbon_intensity
        existing.energy_mix = json.dumps(energy_mix)
        existing.fetched_at = datetime.utcnow()
    else:
        existing = CarbonCache(
            region=region,
            carbon_intensity=carbon_intensity,
            energy_mix=json.dumps(energy_mix),
        )
        db.add(existing)
    
    db.commit()
    db.refresh(existing)
    return existing


def get_cached_carbon(db: Session, region: str) -> Optional[Dict]:
    """Get cached carbon data for a region."""
    cached = db.query(CarbonCache).filter(CarbonCache.region == region).first()
    return cached.to_dict() if cached else None

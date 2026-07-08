"""
Prediction API Endpoints

Provides carbon forecasting endpoints:
- GET /api/v1/predict/best-time     — Best time to run across all regions
- GET /api/v1/predict/forecast/{region} — 24-hour forecast for a region
- GET /api/v1/predict/compare       — Compare all regions at a given hour
"""

from fastapi import APIRouter
from typing import Optional
from pcem.predictor.predictor import predict_best_time, get_hourly_forecast, get_region_comparison

router = APIRouter(prefix="/api/v1/predict", tags=["Predictions"])


@router.get("/best-time")
async def best_time(hours: int = 24):
    """Predict the best time and region to run an AI task."""
    result = predict_best_time(hours_window=hours)
    return result


@router.get("/forecast/{region}")
async def forecast(region: str, hours: int = 24):
    """Get 24-hour carbon intensity forecast for a specific region."""
    data = get_hourly_forecast(region, hours_ahead=hours)
    if not data:
        return {"error": f"No historical data for region: {region}", "forecast": []}
    return {
        "region": region,
        "forecast": data,
        "hours": hours
    }


@router.get("/compare")
async def compare_regions(hour: Optional[int] = None):
    """Compare all regions at a specific hour (default: current hour)."""
    data = get_region_comparison(hour_utc=hour)
    return {
        "hour_utc": hour,
        "regions": data
    }

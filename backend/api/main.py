"""
CodeCarbonOps - Carbon-Aware AI Inference Router
Main FastAPI Application
"""

from dotenv import load_dotenv
load_dotenv()  # Load .env file (for ELECTRICITY_MAPS_API_KEY)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="CodeCarbonOps API",
    description="Carbon-Aware AI Inference Router - Routes LLM tasks to the greenest servers worldwide",
    version="0.4.0",
)

# CORS middleware for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== Register Sub-Routers ==============

from backend.api.predict_endpoints import router as predict_router
from backend.api.ci_endpoints import router as ci_router
app.include_router(predict_router)
app.include_router(ci_router)


# ============== Database Initialization ==============

@app.on_event("startup")
async def startup_event():
    """Initialize database and seed historical data on server startup."""
    from backend.database.connection import init_db
    init_db()

    # Seed historical data for demo (only if DB is empty)
    from pcem.predictor.carbon_collector import seed_historical_data
    seed_historical_data(days=7)


# ============== Health Endpoints ==============

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CodeCarbonOps - Carbon-Aware AI Router",
        "version": "0.3.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": "0.3.0",
        "services": {
            "api": "up",
            "task_analyzer": "up",
            "carbon_monitor": "up",
            "smart_router": "up",
            "offset_service": "up",
            "database": "up"
        }
    }


# ============== Inference Endpoint ==============

@app.post("/api/v1/infer")
async def infer(request: dict):
    """
    Carbon-aware LLM inference endpoint (v2.0).
    
    Enhanced with:
    - P1: Self-adaptive routing with Thompson Sampling feedback
    - P3: Real energy measurement vs estimation comparison
    - P5: Carbon-aware model auto-selection (downgrade when dirty grid)
    """
    import time
    from pcem.analyzer.task_analyzer import analyze_task
    from pcem.monitor.carbon_monitor import get_current_carbon_data
    from pcem.router.smart_router import select_best_server
    from pcem.router.adaptive_learner import adaptive_learner
    from pcem.monitor.energy_monitor import energy_monitor
    from pcem.analyzer.model_selector import model_selector
    from backend.database.connection import SessionLocal
    from backend.database import crud
    
    # Extract request parameters
    prompt = request.get("prompt", "")
    model = request.get("model", "gpt-4")
    carbon_budget_g = request.get("carbon_budget_g", 100.0)
    preferences = request.get("preferences", {})
    urgency = preferences.get("urgency", 3)
    urgency = max(1, min(5, int(urgency)))
    
    # Step 1: Get current carbon data
    carbon_data = get_current_carbon_data()
    
    # Step 2: P5 — Carbon-Aware Model Selection
    # Get average carbon intensity across regions for model decision
    regions = carbon_data.get("regions", {})
    avg_carbon = 400
    if regions:
        intensities = [r.get("carbon_intensity_g_kwh", 400) for r in regions.values()]
        avg_carbon = sum(intensities) / len(intensities)
    
    model_adjustment = model_selector.get_carbon_aware_model(
        requested_model=model,
        carbon_intensity=avg_carbon,
        urgency=urgency,
    )
    
    # Use recommended model if auto-selected, otherwise keep original
    effective_model = model
    if model_adjustment["action"] == "auto_selected":
        effective_model = model_adjustment["recommended_model"]
    
    # Step 3: Analyze task complexity (with effective model)
    task_analysis = analyze_task(prompt, effective_model)
    
    # Step 4: P3 — Start energy measurement
    energy_monitor.start_measurement()
    inference_start = time.time()
    
    # Step 5: Select best server (uses P1 adaptive scoring internally)
    routing_decision = select_best_server(
        task_analysis=task_analysis,
        carbon_data=carbon_data,
        carbon_budget_g=carbon_budget_g,
        preferences=preferences,
    )
    
    # Simulate inference work (CPU activity for measurement)
    _simulate_inference_work(task_analysis.get("estimated_gpu_seconds", 1.0))
    
    # Step 6: P3 — Stop energy measurement
    inference_duration = time.time() - inference_start
    energy_measurement = energy_monitor.stop_measurement()
    energy_comparison = energy_monitor.compare_and_record(
        estimated_kwh=task_analysis["estimated_energy_kwh"],
        measurement=energy_measurement,
    )
    
    # Step 7: Check if offset is needed
    offset_needed = 0
    if routing_decision["predicted_carbon_g"] > carbon_budget_g:
        offset_needed = routing_decision["predicted_carbon_g"] - carbon_budget_g
    
    # Step 8: Save to database
    db = SessionLocal()
    run_id = None
    try:
        run = crud.save_inference_run(db, {
            "prompt": prompt,
            "model": effective_model,
            "total_tokens": task_analysis.get("total_tokens"),
            "energy_kwh": task_analysis.get("estimated_energy_kwh"),
            "server_region": routing_decision["selected_server"]["region"],
            "server_name": routing_decision["selected_server"]["name"],
            "carbon_used_g": round(routing_decision["predicted_carbon_g"], 4),
            "carbon_saved_g": round(routing_decision["carbon_saved_vs_default"], 4),
            "renewable_pct": routing_decision["selected_server"]["renewable_pct"],
            "latency_ms": routing_decision["selected_server"]["latency_ms"],
            "offset_purchased_g": round(offset_needed, 4),
        })
        run_id = run.id
    except Exception:
        pass
    finally:
        db.close()
    
    # Step 9: P1 — Record routing outcome for adaptive learning
    selected_server = routing_decision["selected_server"]
    actual_latency = inference_duration * 1000  # Convert to ms
    actual_carbon = routing_decision["predicted_carbon_g"]  # Approx
    if energy_comparison.get("measured_kwh", 0) > 0:
        actual_carbon = energy_comparison["measured_kwh"] * selected_server["carbon_intensity"]
    
    satisfaction = adaptive_learner.record_outcome(
        server_region=selected_server["region"],
        urgency=urgency,
        predicted_carbon=routing_decision["predicted_carbon_g"],
        actual_carbon=actual_carbon,
        predicted_latency=selected_server.get("latency_ms", 100),
        actual_latency=actual_latency,
        model_used=effective_model,
    )
    
    # Step 10: Get adaptive weights for response transparency
    adapted_weights = adaptive_learner.get_adaptive_weights(urgency)
    weights_pct = {k: int(v * 100) for k, v in adapted_weights.items()}
    
    return {
        "result": f"[Simulated LLM response for: {prompt[:50]}...]",
        "run_id": run_id,
        "metadata": {
            "server_region": selected_server["region"],
            "server_name": selected_server["name"],
            "carbon_used_g": round(routing_decision["predicted_carbon_g"], 4),
            "energy_kwh": round(task_analysis["estimated_energy_kwh"], 6),
            "carbon_intensity_g_kwh": selected_server["carbon_intensity"],
            "renewable_pct": selected_server["renewable_pct"],
            "energy_mix": selected_server["energy_mix"],
            "offset_purchased_g": round(offset_needed, 4),
            "carbon_saved_g": round(routing_decision["carbon_saved_vs_default"], 4),
            "latency_ms": selected_server["latency_ms"],
            "cost_per_hour": selected_server.get("cost_per_hour", 0),
            "urgency": urgency,
            "weights_used": weights_pct,
        },
        # P1: Adaptive learning feedback
        "adaptive_routing": {
            "satisfaction_score": round(satisfaction, 3) if satisfaction is not None else None,
            "adapted_weights": weights_pct,
            "exploration_active": True,
        },
        # P3: Energy measurement comparison
        "energy_measurement": {
            "estimated_kwh": energy_comparison.get("estimated_kwh", 0),
            "measured_kwh": energy_comparison.get("measured_kwh", 0),
            "estimation_error_pct": energy_comparison.get("estimation_error_pct", 0),
            "calibration_factor": energy_comparison.get("calibration_factor", 1.0),
            "duration_seconds": energy_measurement.get("duration_seconds", 0),
            "cpu_avg_percent": energy_measurement.get("cpu_avg_percent", 0),
        },
        # P5: Model selection decision
        "model_selection": {
            "requested_model": model,
            "effective_model": effective_model,
            "action": model_adjustment["action"],
            "reason": model_adjustment["reason"],
            "quality_tradeoff": model_adjustment.get("quality_tradeoff"),
            "energy_savings": model_adjustment.get("energy_savings"),
        },
        "alternatives": routing_decision.get("alternatives", []),
        "budget_status": "OK" if offset_needed == 0 else "OFFSET_REQUIRED",
    }


def _simulate_inference_work(gpu_seconds: float):
    """
    Simulate CPU work to generate real energy measurements.
    Caps at 2 seconds to keep responses fast.
    """
    import time
    work_duration = min(gpu_seconds * 0.01, 2.0)  # Scale down, max 2s
    end_time = time.time() + work_duration
    total = 0
    while time.time() < end_time:
        for i in range(10000):
            total += i * i  # CPU-intensive work
    return total


# ============== Carbon Data Endpoints ==============

@app.get("/api/v1/carbon/realtime")
async def get_realtime_carbon():
    """Get real-time carbon intensity for all tracked regions"""
    from pcem.monitor.carbon_monitor import get_current_carbon_data
    return get_current_carbon_data()


@app.get("/api/v1/carbon/regions")
async def get_regions():
    """Get list of all available regions with current carbon data"""
    from pcem.monitor.carbon_monitor import get_all_regions
    return get_all_regions()


@app.get("/api/v1/carbon/servers")
async def get_servers():
    """Get list of available GPU servers"""
    from pcem.router.smart_router import get_available_servers
    return get_available_servers()


# ============== Offset Endpoints ==============

@app.post("/api/v1/offsets/purchase")
async def purchase_offset(request: dict):
    """Purchase carbon offset for a given amount"""
    from backend.database.connection import SessionLocal
    from backend.database import crud
    
    amount_g = request.get("amount_g", 0)
    
    # Calculate cost
    cost_per_g = 0.0002  # $0.0002 per gram CO2
    cost_usd = amount_g * cost_per_g
    
    transaction_id = f"SIM-{abs(hash(str(amount_g)))}"
    
    # Save to database
    db = SessionLocal()
    try:
        purchase = crud.save_offset_purchase(db, {
            "run_id": request.get("run_id"),
            "amount_g": amount_g,
            "cost_usd": round(cost_usd, 4),
            "provider": "simulation",
            "status": "completed",
            "transaction_id": transaction_id,
        })
    except Exception:
        pass
    finally:
        db.close()
    
    return {
        "status": "completed",
        "amount_g": amount_g,
        "cost_usd": round(cost_usd, 4),
        "provider": "simulation",
        "transaction_id": transaction_id
    }


@app.get("/api/v1/offsets/history")
async def get_offset_history():
    """Get history of offset purchases from database"""
    from backend.database.connection import SessionLocal
    from backend.database import crud
    
    db = SessionLocal()
    try:
        return crud.get_offset_history(db)
    finally:
        db.close()


# ============== History & Stats Endpoints ==============

@app.get("/api/v1/history")
async def get_history():
    """Get recent inference run history"""
    from backend.database.connection import SessionLocal
    from backend.database import crud
    
    db = SessionLocal()
    try:
        runs = crud.get_inference_history(db, limit=50)
        return {"runs": runs, "count": len(runs)}
    finally:
        db.close()


@app.get("/api/v1/stats")
async def get_stats():
    """Get aggregate statistics for all inference runs"""
    from backend.database.connection import SessionLocal
    from backend.database import crud
    
    db = SessionLocal()
    try:
        return crud.get_inference_stats(db)
    finally:
        db.close()

# CodeCarbonOps - Complete Code Walkthrough

> A file-by-file explanation of the Carbon-Aware AI Inference Router

---

## 🏗️ Project Overview

We built a **Carbon-Aware AI Inference Router** that:
1. Receives an LLM/AI task request
2. Estimates how much energy it will consume
3. Checks carbon intensity of servers worldwide
4. Routes to the **greenest server**
5. Purchases carbon offsets if budget exceeded

---

## 📁 Project Structure

```
CodeCarbonOps/
├── backend/           ← FastAPI Backend (API Server)
├── pcem/              ← Prediction & Carbon Engine (Core Logic)
├── offsets/           ← Carbon Offset Module
├── ci-integration/    ← GitHub Actions (Optional)
├── docs/              ← Documentation
├── README.md
└── .gitignore
```

---

# 🔷 BACKEND - FastAPI Server

## 📄 `backend/api/main.py`
**Purpose:** Main API server that receives requests and coordinates all modules.

### Key Endpoints:

```python
# Health check - Just returns "healthy"
@app.get("/")
async def root():
    return {"status": "healthy", "service": "CodeCarbonOps"}

# Main inference endpoint - The heart of the system
@app.post("/api/v1/infer")
async def infer(request: dict):
    # Step 1: Analyze how complex the task is
    task_analysis = analyze_task(prompt, model)
    
    # Step 2: Get current carbon data worldwide
    carbon_data = get_current_carbon_data()
    
    # Step 3: Pick the best (greenest) server
    routing_decision = select_best_server(...)
    
    # Step 4: Check if we need to buy offsets
    if over_budget:
        offset_needed = predicted_carbon - budget
    
    # Return result with carbon report
    return {"result": "...", "metadata": {...}}
```

### API Endpoints Summary:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check |
| `/api/v1/infer` | POST | Send AI task, get carbon-optimized execution |
| `/api/v1/carbon/realtime` | GET | Get current carbon data for all regions |
| `/api/v1/carbon/servers` | GET | List available GPU servers |
| `/api/v1/offsets/purchase` | POST | Buy carbon offsets |

---

## 📄 `backend/requirements.txt`
**Purpose:** Python dependencies list.

| Package | Purpose |
|---------|---------|
| fastapi | Web framework (like Flask but faster) |
| uvicorn | Server to run FastAPI |
| pydantic | Data validation |
| sqlalchemy | Database ORM (for future use) |
| httpx | HTTP client for API calls |

---

# 🔷 PCEM - Prediction & Carbon Engine

This is the **brain** of the system with 4 sub-modules.

---

## 📂 ANALYZER - Task Analysis

### 📄 `pcem/analyzer/task_analyzer.py`
**Purpose:** Estimates energy consumption for LLM tasks.

**Key Concept:** Different AI models use different amounts of energy.

```python
# Energy factors per 1000 tokens (in kWh)
MODEL_ENERGY_FACTORS = {
    "gpt-4": 0.00021,           # Large model = more energy
    "gpt-3.5-turbo": 0.00004,   # Small model = less energy
    "claude-3-opus": 0.00025,
    "llama-3-70b": 0.00014,
}
```

### Main Function:

```python
def analyze_task(prompt: str, model: str) -> dict:
    """
    Example:
    Input: prompt="Summarize climate change", model="gpt-4"
    Output: {
        "model": "gpt-4",
        "total_tokens": 1006,
        "estimated_energy_kwh": 0.000211,
        "estimated_gpu_seconds": 40.24,
        "complexity": "moderate"
    }
    """
```

---

## 📂 MONITOR - Carbon Tracking

### 📄 `pcem/monitor/carbon_monitor.py`
**Purpose:** Tracks real-time carbon intensity worldwide.

**Key Concept:** Electricity grids have different carbon intensities:
- Sweden (hydro) → 45 g CO2/kWh (very clean!)
- India (coal) → 708 g CO2/kWh (high carbon)

```python
def get_current_carbon_data():
    """
    Returns data like:
    {
        "eu-north-1": {
            "carbon_intensity_g_kwh": 45,
            "renewable_pct": 0.90,
            "energy_mix": {
                "hydro": 0.65,
                "wind": 0.20,
                "nuclear": 0.10,
                "solar": 0.03
            }
        }
    }
    """
```

### Time-of-Day Simulation:
```python
# Solar is higher at noon, lower at night
solar_factor = max(0, min(1, 1 - abs(hour - 12) / 12))
# At midnight: solar_factor = 0 (no sun)
# At noon: solar_factor = 1 (max sun)
```

---

## 📂 ROUTER - Server Selection

### 📄 `pcem/router/smart_router.py`
**Purpose:** Picks the best server based on multiple factors.

**Key Concept:** Score each server, pick lowest score (best):

```python
def calculate_server_score(server, preferences):
    """
    Score = (weight × carbon) + (weight × latency) + (weight × cost)
    Lower score = Better server
    """
    weights = {
        "carbon": 0.5,      # 50% weight on carbon
        "renewable": 0.2,   # 20% weight on renewable %
        "latency": 0.2,     # 20% weight on speed
        "cost": 0.1         # 10% weight on price
    }
```

---

## 📂 CALCULATOR - CWF Calculations

### 📄 `pcem/calculator/cwf_calculator.py`
**Purpose:** Calculates Carbon and Water Footprint.

```python
def calculate_carbon_footprint(energy_kwh, region):
    """
    Formula: CO2 (grams) = Energy (kWh) × Carbon Intensity (g/kWh)
    
    Example:
    - Energy: 0.02 kWh
    - Region: Sweden (45 g/kWh)
    - Result: 0.02 × 45 = 0.9g CO2
    """
```

---

## 📂 DATA - Static Data Files

### 📄 `pcem/data/fallback_factors.json`
Offline carbon intensity data for 15+ regions worldwide.

### 📄 `pcem/data/servers.json`
List of 10 GPU servers across USA, Europe, Asia.

---

# 🔷 OFFSETS - Carbon Credit System

## 📄 `offsets/calculator.py`
**Purpose:** Calculates offset amount and cost.

```python
def get_offset_recommendation(predicted_carbon_g, budget_g):
    """
    Example:
    - Predicted: 15g CO2, Budget: 10g CO2
    - Offset needed: 5g
    - Cost: $0.00005
    """
```

## 📄 `offsets/providers/simulation.py`
**Purpose:** Simulates purchasing carbon credits.

---

# 🔄 Complete System Flow

```
1. USER REQUEST
   {"prompt": "Summarize AI", "model": "gpt-4", "budget": 10g}
   
2. TASK ANALYZER → Estimates: 1000 tokens, 0.00021 kWh
   
3. CARBON MONITOR → Fetches: Sweden=45, Mumbai=708 g/kWh
   
4. SMART ROUTER → Selected: Sweden (score=0.12)
   
5. BUDGET CHECK → 0.9g < 10g budget → OK!
   
6. RESPONSE
   {
     "server_region": "eu-north-1",
     "carbon_used_g": 0.9,
     "renewable_pct": 90%,
     "carbon_saved_g": 13.3
   }
```

---

# 📊 Key Files Summary

| File | Purpose |
|------|---------|
| `backend/api/main.py` | API server with endpoints |
| `pcem/analyzer/task_analyzer.py` | LLM energy estimation |
| `pcem/monitor/carbon_monitor.py` | Real-time carbon tracking |
| `pcem/router/smart_router.py` | Server selection algorithm |
| `pcem/calculator/cwf_calculator.py` | Carbon/water calculations |
| `pcem/data/fallback_factors.json` | Regional carbon data |
| `pcem/data/servers.json` | GPU server list |
| `offsets/calculator.py` | Offset calculations |
| `offsets/providers/simulation.py` | Simulated purchases |

---

*Document created for code reference and team onboarding*

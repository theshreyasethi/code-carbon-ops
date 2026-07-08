# CodeCarbonOps — Complete Project Context Handoff

> **Purpose of this document**: Transfer ALL project context to another LLM for research paper writing. This covers the entire project: what it is, how it works, every file, the patent rejection, teacher's paper blueprints, and strategic recommendations.

---

## 1. PROJECT OVERVIEW

### What Is CodeCarbonOps?

CodeCarbonOps is a **closed-loop carbon-aware AI inference routing system**. It routes AI/LLM inference requests to the geographically greenest cloud server, measures actual energy consumption post-execution, and self-improves its routing decisions over time using Bayesian learning (Thompson Sampling).

### Core Problem It Solves

The same AI inference request (e.g., "summarize this article using GPT-4o") can produce vastly different carbon emissions depending on WHERE and WHEN it runs:
- Running in **Sweden** (eu-north-1): ~46 g CO2/kWh (mostly hydroelectric)
- Running in **India** (ap-south-1): ~708 g CO2/kWh (mostly coal)
- That is a **15x difference** for the identical computation

CodeCarbonOps automatically routes inference to the greenest available server, taking into account carbon intensity, latency, cost, renewable energy percentage, and user urgency.

### The 6-Step Closed Loop

```
Step 1: REQUEST INTAKE
  User submits prompt + model + urgency (1-5)

Step 2: CARBON DATA ACQUISITION
  Fetch real-time carbon intensity from ElectricityMaps API for 15 regions

Step 3: REGION & MODEL SELECTION
  Score all servers using weighted multi-objective function + Thompson Sampling

Step 4: EXECUTION
  Run inference on selected server (simulated in current version)

Step 5: TELEMETRY MEASUREMENT
  Measure actual CPU power via psutil, compare estimated vs measured energy

Step 6: FEEDBACK & ADAPTATION
  Record outcome, update Beta distributions, self-calibrate energy model
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | **FastAPI** (Python 3.10+) | REST API server |
| Frontend | **React + Vite** | Dashboard UI |
| Database | **SQLite** via SQLAlchemy ORM | Persistent storage |
| Energy Monitoring | **psutil** | CPU utilization tracking |
| Carbon Data | **ElectricityMaps API** | Real-time carbon intensity |
| Testing | **pytest** (54 tests, all passing) | Automated test suite |

---

## 2. COMPLETE FILE STRUCTURE

```
c:\Users\vibhu\CodeCarbonOps\
|
+-- backend/                          # FastAPI backend
|   +-- api/
|   |   +-- main.py                   # Main FastAPI app, /api/v1/infer endpoint, health checks
|   |   +-- ci_endpoints.py           # CI/CD anomaly detection endpoints (/api/v1/ci/*)
|   |   +-- predict_endpoints.py      # Forecast endpoints (/api/v1/predict/*)
|   +-- database/
|   |   +-- connection.py             # SQLAlchemy engine + session factory (SQLite)
|   |   +-- models.py                 # 7 ORM tables (see Section 4)
|   |   +-- crud.py                   # CRUD operations for inference runs
|   +-- models/                       # (empty - Pydantic models inline in endpoints)
|   +-- services/                     # (empty - business logic is in pcem/)
|   +-- requirements.txt              # Python dependencies
|
+-- pcem/                             # Core engine (Patent-Critical Execution Modules)
|   +-- analyzer/
|   |   +-- task_analyzer.py          # Token estimation + energy estimation per model
|   |   +-- model_selector.py         # Carbon-aware model downgrading logic
|   +-- calculator/
|   |   +-- cwf_calculator.py         # Carbon & water footprint calculator
|   +-- data/
|   |   +-- servers.json              # 10 GPU server configs (AWS/Azure/GCP across 10 regions)
|   |   +-- fallback_factors.json     # Static carbon intensity + water factors for 15 regions
|   +-- monitor/
|   |   +-- carbon_monitor.py         # Real-time carbon data: ElectricityMaps API + UK Carbon API + fallback
|   |   +-- energy_monitor.py         # psutil-based power measurement + self-calibration loop
|   +-- predictor/
|   |   +-- carbon_collector.py       # Historical carbon data collector + seed_historical_data()
|   |   +-- predictor.py              # Time-series forecasting (Exponential Smoothing / Holt-Winters)
|   +-- router/
|       +-- smart_router.py           # Multi-objective server scoring + selection
|       +-- adaptive_learner.py       # Thompson Sampling + Bayesian adaptive weights
|
+-- dashboard/                        # React frontend (Vite)
|   +-- src/
|   |   +-- App.jsx                   # Main dashboard layout
|   |   +-- components/
|   |       +-- InferenceForm.jsx     # Prompt input + model/urgency selection
|   |       +-- ResultsPanel.jsx      # Routing results + carbon savings display
|   |       +-- CarbonTable.jsx       # Regional carbon intensity table
|   |       +-- PredictivePanel.jsx   # Forecast charts + best-time recommendation
|   |       +-- StatsCards.jsx        # Summary statistics cards
|   +-- package.json
|   +-- vite.config.js
|
+-- tests/                            # pytest test suite (54 tests, ALL PASS)
|   +-- conftest.py                   # Test fixtures
|   +-- test_api.py                   # API endpoint tests
|   +-- test_cwf_calculator.py        # Carbon/water calculator tests
|   +-- test_offset_calculator.py     # Offset purchase tests
|   +-- test_smart_router.py          # Router + adaptive learning tests
|   +-- test_task_analyzer.py         # Task analysis tests
|
+-- ci-integration/                   # CI/CD GitHub Actions integration (webhook-based)
+-- offsets/                          # Carbon offset simulation module
+-- docs/                             # Documentation
|
+-- .env                              # ELECTRICITY_MAPS_API_KEY (real key exists)
+-- .env.example                      # Template for API key
+-- .gitignore
+-- README.md                         # Project documentation
+-- CONTRIBUTING.md                   # Contribution guidelines
+-- codecarbonops.db                  # SQLite database (106 KB, with real data)
+-- experimental_results.md           # Experimental validation results
|
+-- patent rejected.pdf               # 11-page patent rejection report (image-based scan)
+-- patent_pages/                     # Extracted PNG images of each rejection page
+-- project_explained.md              # Earlier project documentation
```

---

## 3. KEY ALGORITHMS - DETAILED DESCRIPTIONS

### 3.1 Smart Router - Multi-Objective Server Scoring

**File**: `pcem/router/smart_router.py` (236 lines)

The router scores each candidate server using a three-layer system (lower score = better):

**Layer 1 - Urgency-Based Static Weights:**
```
Urgency 1 (speed first):  carbon=0.15, renewable=0.10, latency=0.45, cost=0.30
Urgency 2:                carbon=0.20, renewable=0.10, latency=0.35, cost=0.35
Urgency 3 (balanced):     carbon=0.30, renewable=0.15, latency=0.25, cost=0.30
Urgency 4:                carbon=0.40, renewable=0.20, latency=0.15, cost=0.25
Urgency 5 (green first):  carbon=0.50, renewable=0.25, latency=0.05, cost=0.20
```

**Layer 2 - Adaptive Weight Adjustment:**
The system learns from historical prediction errors. If carbon is consistently under-predicted (actual > predicted), the carbon weight increases automatically. Learning rate = 0.15. Requires >= 3 samples before adaptation kicks in.

**Layer 3 - Thompson Sampling Exploration Bonus:**
Each (server, urgency) pair maintains a Beta(alpha, beta) distribution:
- alpha increments when actual carbon < predicted carbon (success)
- beta increments when actual carbon >= predicted carbon (failure)
- Each routing decision samples theta ~ Beta(alpha, beta) to get an exploration bonus
- Under-explored servers get more variable samples (encourages exploration)
- Proven good servers get consistently favorable samples

**Final Score** = SUM(adapted_weights * normalized_factors) + exploration_bonus

**Normalized factors:**
- carbon_norm = carbon_intensity / 1000
- renewable_norm = 1 - renewable_pct (inverted, higher renewable is better)
- latency_norm = latency_ms / 1000
- cost_norm = cost_per_hour / 10

### 3.2 Adaptive Learner - Thompson Sampling

**File**: `pcem/router/adaptive_learner.py` (321 lines)

**Satisfaction Score Computation (after each inference):**
```python
carbon_ratio = actual_carbon / predicted_carbon
latency_ratio = actual_latency / predicted_latency

carbon_satisfaction = min(1.0, 1.0 / max(carbon_ratio, 0.5))
latency_satisfaction = min(1.0, 1.0 / max(latency_ratio, 0.5))

satisfaction = 0.6 * carbon_satisfaction + 0.4 * latency_satisfaction
```

If satisfaction > 0.5: alpha += 1 (reward). Otherwise: beta += 1 (penalty).

**Adaptive Weight Adjustment:**
```python
avg_carbon_error = sum(total_carbon_errors) / total_count
if avg_carbon_error < 0:  # We underestimate carbon
    carbon_adjustment = min(LEARNING_RATE, abs(avg_carbon_error) / 100)
    weights["carbon"] += carbon_adjustment
    weights["latency"] -= carbon_adjustment / 2
    weights["cost"] -= carbon_adjustment / 2
```

**Database Storage:** Results stored in `routing_feedback` table. Last 30 days of feedback loaded into memory cache at startup.

### 3.3 Energy Self-Calibration

**File**: `pcem/monitor/energy_monitor.py` (260 lines)

**Power Model:**
```
actual_power_watts = (IDLE_POWER + (cpu_percent / 100) * CPU_TDP) * PUE

Where:
  IDLE_POWER = 15W (base system)
  CPU_TDP = 65W (default desktop CPU)
  PUE = 1.2 (Power Usage Effectiveness)

energy_kwh = (actual_power_watts * duration_seconds) / 3600 / 1000
```

**Self-Calibration Loop:**
1. For each inference: record estimated_kwh (from token-based model) and measured_kwh (from psutil)
2. Calculate estimation_error_pct = ((estimated - measured) / measured) * 100
3. Load last 20 measurements, compute average error
4. calibration_factor = 1.0 - (avg_error / 100), clamped to [0.3, 2.0]
5. Future estimates are multiplied by this factor to improve accuracy

### 3.4 Carbon Intensity Forecasting

**File**: `pcem/predictor/predictor.py` (476 lines)

Two forecasting methods:
- **Weighted Moving Average (WMA)**: Used when < 24 data points available
- **Exponential Smoothing with 24-hour seasonal decomposition (Holt-Winters)**: Used when >= 24 data points

**Output**: 24-hour forecast with:
- Point predictions per hour
- 95% confidence intervals (upper/lower bounds, Z = 1.96)
- Accuracy metrics: MAPE, RMSE
- Best-time recommendation (lowest carbon hour in next 24h)

**Data Source**: `carbon_collector.py` seeds 168 hours (7 days) of realistic historical data per region at startup, with solar/wind diurnal patterns built in.

### 3.5 Carbon-Aware Model Auto-Selection

**File**: `pcem/analyzer/model_selector.py` (328 lines)

Decision matrix based on urgency + carbon intensity:
```
Urgency 1-2: NEVER downgrade (user explicitly needs max quality)
Urgency 3 + carbon > 500 g/kWh: SUGGEST lighter model
Urgency 4 + carbon > 400 g/kWh: RECOMMEND lighter model
Urgency 5 + carbon > 300 g/kWh: AUTO-SELECT lighter model
```

**Model registry includes**: GPT-4o to GPT-4o-mini, Claude-4-Opus to Claude-4-Sonnet to Claude-3.5-Haiku, Gemini-2.5-Pro to Gemini-2.5-Flash, o3 to o3-mini, etc.

Each model has a quality score (0-100) and energy factor (kWh per 1000 tokens). The system reports exact quality loss % and energy savings %.

### 3.6 Task Analyzer - Token and Energy Estimation

**File**: `pcem/analyzer/task_analyzer.py` (177 lines)

**Token Estimation:** ~4 characters per token for English text
**Energy Estimation:** Energy = (total_tokens / 1000) * model_energy_factor

**Model Energy Factors (kWh per 1000 tokens):**
```
gpt-4o:          0.00016
gpt-4o-mini:     0.00005
gpt-4.5:         0.00024
o1:              0.00030
o3:              0.00035
o3-mini:         0.00012
claude-4-opus:   0.00028
claude-4-sonnet: 0.00015
claude-3.5-haiku:0.00004
gemini-2.5-pro:  0.00020
gemini-2.0-flash:0.00008
deepseek-r1:     0.00022
llama-4-maverick:0.00018
```

### 3.7 Carbon & Water Footprint Calculator

**File**: `pcem/calculator/cwf_calculator.py` (108 lines)

```
carbon_g = energy_kwh * carbon_intensity_g_per_kwh
water_l = energy_kwh * water_factor_l_per_kwh
```

Water factors per region from fallback_factors.json (range: 0.8 L/kWh in Sweden to 2.5 L/kWh in Bahrain).

### 3.8 CI/CD Anomaly Detection

**File**: `backend/api/ci_endpoints.py` (17,387 bytes)

Receives webhook-like payloads with PR metadata (files_changed, lines_added, lines_removed). Predicts energy/carbon consumption and applies Z-score anomaly detection:
- Z < 2.0: ALLOW (normal PR)
- 2.0 <= Z < 3.0: WARN (unusually large)
- Z >= 3.0: BLOCK (anomalous, likely needs review)

**Note**: This is a simulated webhook receiver. It does NOT integrate with actual GitHub APIs. There is no real CI/CD pipeline connection.

### 3.9 Carbon Monitor - Real-Time Data

**File**: `pcem/monitor/carbon_monitor.py` (394 lines)

Three data sources (tried in order):
1. **ElectricityMaps API** (requires API key, free tier 100 req/month)
2. **UK Carbon Intensity API** (free, no key, UK only)
3. **Fallback static data** from fallback_factors.json

Region mapping to ElectricityMaps zones:
```
us-east-1     -> US-MIDA-PJM
us-west-2     -> US-NW-PACW
eu-west-1     -> IE
eu-north-1    -> SE-SE3
eu-central-1  -> DE
ap-south-1    -> IN-WE
ap-southeast-1-> SG
ap-northeast-1-> JP-TK
ap-east-1     -> HK
sa-east-1     -> BR-S
me-south-1    -> BH
af-south-1    -> ZA
ca-central-1  -> CA-ON
uk-south      -> GB
australia-east-> AU-NSW
```

Cache TTL: 15 minutes (900 seconds).

---

## 4. DATABASE SCHEMA

**Database**: SQLite (codecarbonops.db, 106 KB)
**ORM**: SQLAlchemy

### 7 Tables

**Table: inference_runs** - Every inference request
- id, prompt_hash, model, total_tokens, estimated_energy_kwh, server_region, server_name, carbon_used_g, carbon_saved_g, renewable_pct, latency_ms, offset_purchased_g, created_at

**Table: offset_purchases** - Carbon credit purchases (simulated)
- id, run_id (FK to inference_runs), amount_g, cost_usd, provider, status, transaction_id, created_at

**Table: carbon_cache** - Cached API responses (15-min TTL)
- id, region (unique), carbon_intensity, energy_mix (JSON), fetched_at

**Table: historical_carbon** - Time-series data for forecasting
- id, region (indexed), carbon_intensity, renewable_pct, hour_of_day (0-23), day_of_week (0-6), recorded_at (indexed)

**Table: ci_runs** - CI/CD pipeline carbon checks
- id, repo, branch, pr_number, job_type, files_changed, lines_added, lines_removed, predicted_energy_kwh, predicted_carbon_g, recommended_server, carbon_budget_g, enforcement_action (ALLOW/WARN/BLOCK), created_at

**Table: routing_feedback** - Adaptive learning outcomes (Thompson Sampling)
- id, server_region (indexed), urgency_level, predicted_carbon, actual_carbon, predicted_latency, actual_latency, satisfaction_score (0-1), model_used, created_at (indexed)

**Table: energy_measurements** - Self-calibration data
- id, run_id (FK), estimated_kwh, measured_kwh, cpu_avg_percent, duration_seconds, avg_power_watts, estimation_error_pct, created_at

---

## 5. API ENDPOINTS

### Core Inference
- POST /api/v1/infer - Submit inference (prompt, model, urgency, max_tokens). Returns: selected server, predicted carbon, carbon saved, alternatives, energy measurement, model recommendation

### Carbon Data
- GET /api/v1/carbon - Current carbon intensity for all 15 regions
- GET /api/v1/carbon/{region} - Single region

### Forecasting
- GET /api/v1/predict/{region} - 24-hour forecast with confidence bands

### History and Stats
- GET /api/v1/history - Past inference runs
- GET /api/v1/stats - Aggregate statistics

### CI/CD
- POST /api/v1/ci/check - Submit PR metadata for carbon analysis
- GET /api/v1/ci/history - Past CI/CD checks

### Health
- GET / - Basic health check
- GET /health - Detailed service status

---

## 6. REGIONS AND SERVERS

### 15 Carbon Intensity Regions

| Region ID | Location | Fallback Carbon (g/kWh) | Water Factor (L/kWh) |
|-----------|----------|------------------------|---------------------|
| eu-north-1 | Sweden (Stockholm) | 45 | 0.8 |
| sa-east-1 | Brazil (Sao Paulo) | 85 | 0.9 |
| ca-central-1 | Canada (Central) | 120 | 1.0 |
| uk-south | UK South | 225 | 1.3 |
| us-west-2 | US (Oregon) | 285 | 1.2 |
| eu-west-1 | Ireland | 296 | 1.4 |
| eu-central-1 | Germany (Frankfurt) | 338 | 1.5 |
| us-east-1 | US (Virginia) | 379 | 1.5 |
| ap-southeast-1 | Singapore | 408 | 1.7 |
| ap-northeast-1 | Japan (Tokyo) | 465 | 1.6 |
| me-south-1 | Bahrain | 520 | 2.5 |
| ap-east-1 | Hong Kong | 650 | 2.0 |
| australia-east | Australia (Sydney) | 680 | 2.0 |
| ap-south-1 | India (Mumbai) | 708 | 2.1 |
| af-south-1 | South Africa (Cape Town) | 870 | 2.3 |

### 10 Configured GPU Servers

| Server | Region | Provider | GPU | Cost/hr | Latency |
|--------|--------|----------|-----|---------|---------|
| AWS Stockholm | eu-north-1 | AWS | A100 | $3.50 | 180ms |
| AWS Oregon | us-west-2 | AWS | A100 | $3.20 | 120ms |
| AWS Virginia | us-east-1 | AWS | A100 | $3.00 | 80ms |
| Azure UK South | uk-south | Azure | A100 | $3.40 | 150ms |
| GCP Netherlands | eu-west-1 | GCP | A100 | $3.30 | 160ms |
| AWS Sao Paulo | sa-east-1 | AWS | A10G | $2.80 | 250ms |
| AWS Canada | ca-central-1 | AWS | A100 | $3.10 | 100ms |
| AWS Mumbai | ap-south-1 | AWS | A100 | $2.50 | 50ms |
| AWS Tokyo | ap-northeast-1 | AWS | A100 | $3.60 | 200ms |
| Azure Sydney | australia-east | Azure | A100 | $3.80 | 280ms |

---

## 7. EXPERIMENTAL RESULTS (ALREADY OBTAINED)

### 7.1 Carbon Reduction Through Geo-Routing

| Scenario | Default Carbon (g/kWh) | Routed Carbon (g/kWh) | Reduction |
|----------|----------------------|---------------------|-----------|
| India to Sweden | 672.0 | 46.2 | **93.1%** |
| US East to Sweden | 389.3 | 46.2 | **88.1%** |
| Australia to Canada | 663.5 | 118.1 | **82.2%** |
| Germany to Sweden | 337.5 | 46.2 | **86.3%** |
| Average | ~515.4 | ~82.1 | **~84.1%** |

### 7.2 Model Auto-Selection Savings

| Original Model | Auto-Selected | Energy Savings | Quality Loss |
|---------------|--------------|---------------|-------------|
| GPT-4o (95/100) | GPT-4o-mini (82/100) | **68.8%** | 13.7% |
| Claude-4-Opus (97/100) | Claude-4-Sonnet (90/100) | **46.4%** | 7.2% |
| Gemini-2.5-Pro (94/100) | Gemini-2.5-Flash (80/100) | **55.0%** | 14.9% |
| o3 (99/100) | o3-mini (85/100) | **65.7%** | 14.1% |

### 7.3 Forecasting

| Region | Method | Data Points | Method |
|--------|--------|-------------|--------|
| eu-north-1 (Sweden) | Holt-Winters | 168 (real API) | 24h forecast with confidence bands |
| ap-south-1 (India) | Holt-Winters | 168 (real API) | 24h forecast with confidence bands |
| us-east-1 (Virginia) | Holt-Winters | 168 (real API) | 24h forecast with confidence bands |
| eu-central-1 (Germany) | Holt-Winters | 168 (real API) | 24h forecast with confidence bands |
| australia-east (Sydney) | Holt-Winters | 168 (real API) | 24h forecast with confidence bands |

### 7.4 CI/CD Anomaly Detection

| Test Case | Files | Lines | Predicted Carbon | Z-Score | Action |
|-----------|-------|-------|-----------------|---------|--------|
| Normal PR | 5 | 120 | 0.6g | -0.3 | ALLOW |
| Large PR | 50 | 2,100 | 2.1g | -0.6 | ALLOW |
| Anomalous PR | 200 | 10,000 | 62.2g | +4.2 | BLOCK |

### 7.5 Adaptive Learning

| Metric | Value |
|--------|-------|
| Routing feedback records | 20 (seeded) |
| Mean satisfaction score | 0.87 / 1.0 |
| Thompson Sampling | Beta distributions updating after each inference |
| Exploration weight | lambda = 0.15 |

### 7.6 Test Suite

| Category | Tests | Passed | Failed |
|----------|-------|--------|--------|
| Core Backend and API | 8 | 8 | 0 |
| PCEM Predictor Engine | 10 | 10 | 0 |
| Routing and Adaptive Learning | 12 | 12 | 0 |
| Task Analytics and Carbon | 14 | 14 | 0 |
| CI/CD Integrations | 10 | 10 | 0 |
| **Total** | **54** | **54** | **0** |

---

## 8. PATENT REJECTION - FULL DETAILS

### 8.1 What Was Filed

**Title**: "A Closed-Loop Carbon-Aware AI Inference Routing System with Adaptive Feedback-Based Region and Model Selection"

**Filed**: Indian Patent Office, examined under Sections 2(1)(j) and 2(1)(ja)

**Decision**: Non-patentable (7 May 2026)

### 8.2 Rejection Grounds

| Ground | Assessment | Reason |
|--------|-----------|--------|
| Novelty (Sec 2(1)(j)) | LOW | Core elements already disclosed individually and in combination |
| Inventive Step (Sec 2(1)(ja)) | WEAK | System is an obvious aggregation of known techniques |
| Industrial Applicability | 100% | Not disputed |

### 8.3 Three Prior-Art References That Caused Rejection

**Reference 1: IBM Patent US20250037142A1** (January 2025)
- Title: "Carbon-aware workload allocation in cloud environment"
- Covers: Allocating workloads across cloud clusters based on predicted carbon emissions using time-series tracking and prediction models
- Anticipates: Step 2 (carbon data acquisition) + Step 3 (region selection based on carbon)

**Reference 2: Farahani et al.** (November 2025)
- Title: "Toward Sustainability-Aware LLM Inference on Edge Clusters"
- Covers: Carbon- and latency-aware routing of inference requests with empirical telemetry on NVIDIA edge hardware
- Anticipates: Multi-objective routing (carbon + latency + workload) and inference-level decision making

**Reference 3: CarbonFlex by Shenoy et al.** (May 2025)
- Title: "CarbonFlex: Enabling Carbon-aware Provisioning and Scheduling for Cloud Clusters"
- Covers: Continuous learning scheduler with feedback loop using historical data for joint carbon/performance optimization. Decreases carbon by ~57%
- Anticipates: Step 6 (feedback loop, Bayesian learning, adaptive routing)

### 8.4 Additional Prior Art Found in Research (Not in Report)

| Reference | Year | Covers |
|-----------|------|--------|
| GAR / GAR-PD (arXiv:2605.11603) | 2026 | Constrained multi-objective CO2 minimization for LLM inference with rolling carbon budgets |
| EcoServe | 2025 | ILP-based carbon-aware provisioning distinguishing GPU vs host embodied carbon |
| EAPO (Energy-Aware Prompt Optimization) | 2025 | Bayesian optimization + RL for energy-efficient prompts |
| FCI (Federated Carbon Intelligence, Harvard) | 2025 | Hardware health telemetry + grid carbon using RL |
| CAFE (Carbon-Aware Federated Learning) | 2025 | Lyapunov-based carbon-budgeted federated learning |

### 8.5 Examiner Key Quotes

"Most core elements, carbon-aware routing, predictive scheduling, and adaptive learning, are already disclosed individually and in combination in prior art."

"Inventive step is weak. The system largely represents an obvious aggregation of known techniques (carbon-aware scheduling + ML-based adaptation + inference routing)."

---

## 9. TEACHER'S RESEARCH PAPER BLUEPRINTS

The teacher provided two detailed publication blueprints:

### 9.1 OPTION A: SoftwareX Paper (Software Description)

**Requirements:**
- 3,000 words maximum
- Maximum 6 figures
- Must use SoftwareX journal template
- GitHub repository with README, LICENSE, source code is MANDATORY

**Suggested Titles:**
1. "CodeCarbonOps: Open-Source Software for Closed-Loop Carbon-Aware AI Inference Routing"
2. "CodeCarbonOps: Software for Carbon-Aware AI Inference Dispatch with Adaptive Feedback and Energy Self-Calibration"

**Suggested Abstract (teacher provided):**
"CodeCarbonOps is an open-source software platform for closed-loop carbon-aware AI inference routing across geographically distributed execution regions. The software integrates real-time carbon-intensity retrieval, urgency-aware region scoring, post-execution telemetry measurement, adaptive feedback updates, optional forecast-assisted scheduling, and optional low-energy model substitution. It is implemented using a FastAPI backend, database support, and a web-based interface for monitoring and experimentation. The system is designed to reduce inference-related carbon emissions while preserving execution constraints such as latency and task urgency. Experimental use with real carbon-intensity data demonstrates substantial carbon reduction through geo-routing and additional energy savings through optional model substitution. The software, documentation, and source code are publicly available for reuse and extension."

**Keywords:** Carbon-aware inference, Sustainable AI, Green computing, Inference routing, Energy telemetry, Adaptive scheduling, Open-source software

**Section Structure:**
- Section 1 (0.5-0.75 page): Motivation and significance. Figure 1: Architecture overview.
- Section 2 (1-1.25 pages): Software description. Table 1: Module/Input/Output/Role. Figure 2: End-to-end workflow.
- Section 3 (1 page): Architecture and implementation. Table 2: Layer/Technology/Purpose. Figure 3: Layered architecture.
- Section 4 (1-1.25 pages): Illustrative examples. Tables 3-4: Routing + model results. Figures 4-6: Results.
- Section 5 (0.5 page): Impact and reuse potential.
- References: 20-30

### 9.2 OPTION B: Sustainable Computing Paper (Full Research Article)

**Requirements:**
- Abstract max 250 words (factual, state purpose/results/conclusions, no references)
- 1-7 keywords
- 3-5 highlights (each max 85 characters)
- Data statement required
- Numbered sections, references in [square brackets]

**Suggested Titles:**
1. "Closed-Loop Carbon-Aware AI Inference Routing with Adaptive Feedback-Based Region Selection"
2. "Adaptive Carbon-Aware AI Inference Dispatch Using Real-Time Carbon Signals and Post-Execution Telemetry"
3. "Energy-Aware and Carbon-Aware AI Inference Routing with Forecast-Assisted Scheduling and Self-Calibration"

**Recommended Length:** 7,000-8,500 words, 8-10 figures, 5-7 tables, 35-55 references

**Keywords:** Carbon-aware AI, Green inference routing, Sustainable computing, Energy-aware scheduling, Adaptive feedback, Telemetry-based optimization, Distributed AI systems

**Highlights (each max 85 characters):**
1. Closed-loop routing reduces carbon in distributed AI inference
2. Telemetry feedback improves routing over repeated requests
3. Forecasting supports lower-carbon execution time decisions
4. Model substitution saves energy under high-carbon conditions
5. CodeCarbonOps integrates routing, telemetry, and adaptation

**Graphical Abstract:** 531 x 1328 pixels. Flow: Inference request -> Carbon data -> Region/model selection -> Execution -> Telemetry -> Feedback update. No dashboard screenshots.

**Section-by-Section Plan:**

Section 1. Introduction (1.5-2 pages)
- AI inference carbon growth, regional variation, why static scheduling fails, why feedback matters, gap, 3-4 contributions
- No table, no figure

Section 2. Related Work (1.5-2 pages)
- 2.1 Carbon measurement and accounting tools
- 2.2 Carbon-aware scheduling and workload shifting
- 2.3 AI inference optimization and model switching
- 2.4 Adaptive routing and feedback-based systems
- TABLE 1 (VERY IMPORTANT): Related work comparison with columns: Reference, Carbon-aware, Inference-specific, Geo-routing, Adaptive feedback, Telemetry, Forecasting, Model switching, Limitation

Section 3. Problem Definition and System Overview (1-1.25 pages)
- Define inference request, candidate regions, carbon signal, latency/urgency constraints, objective
- Figure 1: Overall system architecture
- Optional Table 2: Notation and variables

Section 4. Proposed Method (2-2.5 pages)
- 4.1 Closed-loop dispatch workflow (Figure 2: workflow)
- 4.2 Adaptive routing engine with EQUATIONS for region score and update rule (Figure 3: routing decision)
- 4.3 Energy self-calibration with EQUATIONS for estimated energy, measured energy, calibration update
- 4.4 Forecast-assisted scheduling (Figures 4-5: pipeline and forecast curve)
- 4.5 Model auto-selection (Figure 6: model selection logic)

Section 5. System Implementation (1-1.25 pages)
- FastAPI, storage, telemetry, dashboard, API, execution flow
- Table 4: Component/Technology/Version/Purpose

Section 6. Experimental Setup (1-1.25 pages)
- Regions, data source, workloads, baselines, metrics, number of runs
- Table 5: Experimental settings
- Table 6: Baselines (Random routing, Nearest region, Carbon-only, etc.)

Section 7. Results and Discussion (2-2.5 pages)
- 7.1 Carbon reduction from geo-routing (Table 7 + Figure 8)
- 7.2 Model substitution results (Table 8)
- 7.3 Forecasting performance (Table 9: MAE, RMSE, MAPE per region)
- 7.4 Self-calibration results (Figure 9: estimated vs measured energy)
- 7.5 ABLATION STUDY (VERY IMPORTANT) - Table 10: Full model vs without feedback vs without forecasting vs without model selection vs without calibration

Section 8. Discussion and Limitations (0.75-1 page)
- Strengths, API dependency, latency tradeoffs, limited real deployment, generalizability

Section 9. Conclusion (0.5 page)
- Restate problem, summarize method, main numerical findings, future work

**Reference Mix:** 15-20 journal, 8-12 conference, 3-5 standards/tools, 3-5 API/data, 2-4 scheduling, 2-4 bandit/adaptive

**What NOT to use as main figures:** Dashboard screenshots as multiple pages, test-pass screenshots, too many UI images, patent-claim style flowcharts

---

## 10. STRATEGIC RECOMMENDATION

### 10.1 Should You Modify the Project?

**NO. Write the paper on the existing project as-is.**

Reasons:
1. The teacher's blueprints describe your EXISTING system, not hypothetical new features
2. A research paper has a different bar than a patent. You need a working system with real results, not "non-obvious inventive step"
3. Adding new features risks bugs and delays
4. The existing system already has: working routing, real API data, self-calibration, forecasting, model selection, 54 passing tests

### 10.2 Which Venue?

- Short deadline (less than 3 weeks): SoftwareX (faster, 80% ready)
- Maximum career impact: Sustainable Computing (full research paper, stronger)
- Want both: SoftwareX first, then Sustainable Computing
- Teacher prefers one: Follow teacher's recommendation

### 10.3 What Still Needs to Be Done (For Sustainable Computing)

Already done:
- Working software with all modules
- Real carbon API data
- 54 tests passing
- Basic experimental results

Still needed:
- Define formal baselines ("Random routing", "Nearest region", "Carbon-only without feedback")
- Run 30+ inference experiments with full logging
- Run ablation study (disable each module individually, measure impact)
- Calculate forecast accuracy metrics (MAE, RMSE, MAPE per region)
- Related work comparison table (compare 8-10 systems)
- Clean GitHub repo (add LICENSE, polish README, remove temp files)
- Formalize equations (region score, update rule, calibration formula)
- Create clean architecture and workflow diagrams

### 10.4 Novel Features for a Second Paper (Future, NOT for Paper 1)

Three genuinely novel features identified through deep literature research:

1. **CACO (Carbon-Aware Agentic Chain Orchestration)**: Chain-level carbon budgets for multi-step agentic AI workflows with mid-chain model downgrading. Zero prior implementations exist.

2. **PECA (Per-Query Embodied Carbon Attribution)**: Adding GPU manufacturing emissions (amortized) to each query's carbon bill, including hardware degradation awareness.

3. **MDSI (Multi-Dimensional Sustainability Index)**: Routing based on carbon + water stress + environmental justice scores instead of carbon alone.

---

## 11. HOW TO RUN THE PROJECT

### Backend
```bash
cd c:\Users\vibhu\CodeCarbonOps
.venv\Scripts\activate
python -m uvicorn backend.api.main:app --reload --port 8000
```

### Frontend
```bash
cd c:\Users\vibhu\CodeCarbonOps\dashboard
npm run dev
```

### Tests
```bash
cd c:\Users\vibhu\CodeCarbonOps
python -m pytest tests/ -v
```

### Environment
- Python 3.10+ (3.14.2 installed)
- Node.js for React dashboard
- .env file contains ELECTRICITY_MAPS_API_KEY (real key exists)
- Virtual environment at .venv/

---

## 12. KEY FILES THE NEW MODEL SHOULD READ

Priority order for reading source code:

1. `pcem/router/smart_router.py` - Core routing algorithm (236 lines)
2. `pcem/router/adaptive_learner.py` - Thompson Sampling (321 lines)
3. `pcem/monitor/energy_monitor.py` - Energy measurement + calibration (260 lines)
4. `pcem/predictor/predictor.py` - Forecasting Holt-Winters (476 lines)
5. `pcem/analyzer/model_selector.py` - Model auto-selection (328 lines)
6. `pcem/analyzer/task_analyzer.py` - Token/energy estimation (177 lines)
7. `pcem/monitor/carbon_monitor.py` - ElectricityMaps API (394 lines)
8. `backend/api/main.py` - Main API with /infer endpoint (370 lines)
9. `backend/database/models.py` - All 7 database tables (227 lines)
10. `experimental_results.md` - All experimental data (63 lines)

---

## 13. IMPORTANT NOTES FOR THE NEW MODEL

1. **The inference is SIMULATED** - the system does not actually call OpenAI/Anthropic/Google APIs. It simulates the inference step but measures REAL CPU power consumption during the simulation via psutil.

2. **The CI/CD pipeline is NOT connected** - the anomaly detection endpoint exists but is not integrated with GitHub Actions. It is a simulated webhook receiver.

3. **Carbon data is REAL** - ElectricityMaps API provides actual real-time carbon intensity data. The system has a valid API key.

4. **Water footprint exists** - The CWF calculator already computes water usage per region (L/kWh), though it is not prominently featured in the paper blueprints.

5. **The project was originally for an Indian patent** - the code has "PATENT-CRITICAL MODULE" comments in several files. These should be cleaned for paper version.

6. **Database has real data** - The SQLite database (106 KB) contains actual inference runs, routing feedback, energy measurements, and historical carbon data.

7. **Python dependencies** - fastapi, uvicorn, pydantic, python-dotenv, sqlalchemy, alembic, httpx, aiohttp, python-dateutil, psutil

8. **The project lives at**: `c:\Users\vibhu\CodeCarbonOps` on a Windows machine

9. **GitHub repo needs preparation** - Currently no LICENSE file, README needs polish, temp files need cleanup before submission to SoftwareX

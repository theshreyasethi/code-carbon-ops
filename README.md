# CodeCarbonOps: Open-Source Software for Closed-Loop Carbon-Aware AI Inference Routing

CodeCarbonOps is an open-source platform for closed-loop, carbon-aware artificial intelligence (AI) and large language model (LLM) inference routing across geographically distributed execution regions. The system integrates real-time power grid carbon-intensity telemetry, urgency-aware multi-objective server scoring, post-execution energy measurement, adaptive Bayesian feedback updates (Thompson Sampling), forecast-assisted scheduling, and dynamic low-energy model substitution.

This repository provides the complete reference implementation, including the backend API server, core prediction and execution modules, persistent telemetry database, automated test suite, and an interactive monitoring dashboard.

---

## 1. System Architecture & Core Workflow

Standard cloud routing policies typically optimize for latency or compute cost while ignoring regional power grid emission factors. Because electrical grid carbon intensity varies by up to 15x across geographic regions (e.g., hydroelectric-dominant regions around 45 g CO2/kWh versus fossil-dominant regions exceeding 700 g CO2/kWh), location and timing decisions significantly impact the carbon footprint of AI workloads.

CodeCarbonOps implements a six-stage closed-loop architecture:

```
[Request Intake] -> [Grid Telemetry Acquisition] -> [Multi-Objective Scoring & Model Selection]
                                                                  |
[Adaptive Learning] <- [Post-Execution Telemetry] <- [Distributed Execution]
```

1. **Request Intake**: Accepts prompt text, target AI model architecture, user urgency level (1-5), and maximum latency constraints.
2. **Grid Telemetry Acquisition**: Retrieves real-time regional carbon intensity (g CO2/kWh) and renewable generation percentages across 15 global cloud regions via ElectricityMaps and regional grid APIs.
3. **Multi-Objective Scoring & Model Selection**: Evaluates candidate execution servers using a three-layer scoring model balancing latency, cost, renewable mix, and carbon intensity. When grid intensity exceeds acceptable thresholds under flexible urgency constraints, the system automatically suggests or selects energy-efficient fallback models (e.g., substituting GPT-4o with GPT-4o-mini).
4. **Distributed Execution**: Dispatches the inference workload to the selected optimal server region.
5. **Post-Execution Telemetry**: Monitors local CPU utilization and execution duration via `psutil` to estimate actual power draw and energy consumption, comparing predicted versus measured metrics.
6. **Adaptive Bayesian Feedback (Thompson Sampling)**: Updates Beta(alpha, beta) reward distributions based on routing satisfaction scores. These distributions govern exploration-exploitation trade-offs in subsequent routing cycles and continuously self-calibrate the energy prediction model.

---

## 2. Repository Structure

```
CodeCarbonOps/
├── backend/                       # FastAPI REST API Backend
│   ├── api/
│   │   ├── main.py                # Core application entry point and /api/v1/infer endpoint
│   │   ├── ci_endpoints.py        # CI/CD pipeline anomaly detection endpoints
│   │   └── predict_endpoints.py   # 24-hour carbon intensity forecasting endpoints
│   ├── database/
│   │   ├── connection.py          # SQLAlchemy engine and session management
│   │   ├── models.py              # ORM schemas for all 7 database tables
│   │   └── crud.py                # Database query and persistence operations
│   └── requirements.txt           # Python backend dependencies
│
├── pcem/                          # Core Prediction & Execution Modules
│   ├── analyzer/
│   │   ├── task_analyzer.py       # Token count estimation and per-model energy profiling
│   │   └── model_selector.py      # Carbon-aware model downgrading and substitution logic
│   ├── calculator/
│   │   └── cwf_calculator.py      # Combined carbon and water footprint computation
│   ├── data/
│   │   ├── servers.json           # Candidate GPU server catalog across 10 cloud regions
│   │   └── fallback_factors.json  # Baseline emission and water consumption factors
│   ├── monitor/
│   │   ├── carbon_monitor.py      # Real-time API integration (ElectricityMaps / UK Grid)
│   │   └── energy_monitor.py      # Hardware power measurement and self-calibration loop
│   ├── predictor/
│   │   ├── carbon_collector.py    # Time-series carbon data collection and seeding
│   │   └── predictor.py           # Holt-Winters exponential smoothing forecasting engine
│   └── router/
│       ├── smart_router.py        # Urgency-weighted multi-objective server scoring
│       └── adaptive_learner.py    # Thompson Sampling and Bayesian weight adaptation
│
├── dashboard/                     # React + Vite Interactive Frontend
│   ├── src/
│   │   ├── App.jsx                # Dashboard layout and navigation
│   │   └── components/
│   │       ├── InferenceForm.jsx  # Workload submission and urgency selection interface
│   │       ├── ResultsPanel.jsx   # Routing decisions, savings analysis, and alternative comparisons
│   │       ├── CarbonTable.jsx    # Real-time regional grid emission monitoring table
│   │       ├── PredictivePanel.jsx# 24-hour forecasting charts and scheduling recommendations
│   │       └── StatsCards.jsx     # High-level system telemetry and cumulative savings metrics
│   ├── package.json
│   └── vite.config.js
│
├── tests/                         # Comprehensive Automated Test Suite (54 Tests)
│   ├── conftest.py                # Test fixtures and in-memory database configuration
│   ├── test_api.py                # REST API endpoint verification
│   ├── test_cwf_calculator.py     # Carbon and water calculation unit tests
│   ├── test_offset_calculator.py  # Carbon credit and offset calculation tests
│   ├── test_smart_router.py       # Router scoring and Bayesian adaptation verification
│   └── test_task_analyzer.py      # Token estimation and complexity analysis tests
│
├── scripts/                       # Utility and Database Analysis Scripts
├── dataset/                       # Curated CSV Data Exports for Research Validation
├── ci-integration/                # Continuous Integration Webhook Examples
├── offsets/                       # Carbon Credit Simulation Module
├── docs/                          # Detailed Technical Reports and Architecture Guides
├── LICENSE                        # MIT License
└── README.md                      # Project Documentation
```

---

## 3. Key Algorithms & Implementation Details

### 3.1 Multi-Objective Server Scoring
Candidate servers are evaluated using a normalized weighted cost function:

`Score = w_c * C_norm + w_r * (1 - R_norm) + w_l * L_norm + w_k * K_norm + ExplorationBonus`

Where `C_norm`, `R_norm`, `L_norm`, and `K_norm` represent normalized values for carbon intensity, renewable percentage, network latency, and compute cost, respectively. The weights `(w_c, w_r, w_l, w_k)` adjust dynamically based on the user-specified urgency level (1 to 5).

### 3.2 Thompson Sampling Exploration-Exploitation
To prevent premature convergence on locally optimal servers and adapt to changing grid conditions, each server-urgency pair maintains a Beta distribution `Beta(alpha, beta)`. Successes (actual emissions lower than predicted baseline) increment `alpha`, while overshoots increment `beta`. During routing, samples drawn from these distributions provide an exploration bonus, ensuring balanced discovery across global infrastructure.

### 3.3 Holt-Winters Exponential Smoothing Forecasting
When historical time-series data exceeds 24 observations, the predictor engine applies Holt-Winters triple exponential smoothing with a 24-hour seasonal period. This generates hourly carbon intensity forecasts with 95% confidence intervals over a 24-hour horizon, allowing deferred workloads to execute during projected renewable energy peaks.

### 3.4 Self-Calibrating Power Model
The energy monitor calculates runtime CPU power consumption via:

`P_watts = (P_idle + (CPU_util / 100) * TDP_cpu) * PUE`

Post-execution percentage errors between estimated task energy and measured runtime power are tracked over a rolling window. The system computes a calibration adjustment factor `k_cal` that scales future preliminary model estimates to systematically eliminate estimation bias.

---

## 4. Getting Started

### 4.1 Prerequisites
* Python 3.10 or higher
* Node.js 18.x or higher
* npm or yarn

### 4.2 Backend Setup & Execution

1. Navigate to the project root and create a Python virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:
   * **Windows (PowerShell)**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   * **Linux / macOS**:
     ```bash
     source .venv/bin/activate
     ```

3. Install required backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. Configure environment variables by creating a `.env` file (or copying `.env.example`):
   ```bash
   ELECTRICITY_MAPS_API_KEY=your_optional_api_key_here
   ```
   *Note: If no API key is provided, the system seamlessly falls back to free grid APIs and static regional baselines.*

5. Start the FastAPI server:
   ```bash
   python -m uvicorn backend.api.main:app --reload --port 8000
   ```
   The REST API will be available at `http://localhost:8000`. Interactive API documentation (Swagger UI) can be accessed at `http://localhost:8000/docs`.

### 4.3 Frontend Dashboard Setup & Execution

1. Open a separate terminal and navigate to the dashboard directory:
   ```bash
   cd dashboard
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Launch the development server:
   ```bash
   npm run dev
   ```
   The interactive dashboard will be accessible at `http://localhost:5173`.

---

## 5. Running the Test Suite

The repository includes a comprehensive suite of 54 automated unit and integration tests using `pytest` and FastAPI's `TestClient`.

To execute the test suite:
```bash
# Ensure your virtual environment is activated
python -m pytest tests/ -v
```

### Test Coverage Summary
* **API Integration (`test_api.py`)**: Verifies endpoint responsiveness, JSON payload schemas, health checks, and database persistence.
* **Smart Router (`test_smart_router.py`)**: Validates urgency weight scaling, fallback routing, and Thompson Sampling Beta distribution updates.
* **Task Analyzer (`test_task_analyzer.py`)**: Verifies token approximation rules, complexity classification, and model energy coefficients.
* **Carbon & Water Calculator (`test_cwf_calculator.py`)**: Verifies emission and water consumption calculations across distinct geographic zones.
* **Offset Calculator (`test_offset_calculator.py`)**: Tests budget enforcement thresholds and multi-provider carbon offset estimations.

All 54 tests execute against an isolated, session-scoped in-memory database to ensure complete reproducibility without mutating production telemetry.

---

## 6. REST API Reference

| HTTP Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/infer` | Submit an inference request; returns optimal server routing, estimated carbon, and savings. |
| `GET` | `/api/v1/carbon/realtime` | Retrieve real-time carbon intensity and renewable energy percentages across all 15 monitored regions. |
| `GET` | `/api/v1/carbon/regions` | List detailed grid emission metadata for all configured regions. |
| `GET` | `/api/v1/carbon/servers` | Retrieve the catalog of active candidate GPU execution servers. |
| `GET` | `/api/v1/predict/{region}`| Generate a 24-hour carbon intensity forecast with 95% confidence bands for a target region. |
| `GET` | `/api/v1/history` | Retrieve historical inference execution logs and routing decisions. |
| `GET` | `/api/v1/stats` | Access cumulative system metrics, total requests routed, and total greenhouse gas emissions avoided. |
| `POST` | `/api/v1/ci/check` | Analyze pull request changes to predict CI/CD pipeline carbon footprint and enforce budget rules. |
| `GET` | `/health` | Perform system health check across database and live grid telemetry connections. |

---

## 7. Database Schema

The persistent telemetry engine utilizes SQLite (`codecarbonops.db`) managed via SQLAlchemy ORM, organized into 7 relational tables:

1. **`inference_runs`**: Stores individual inference request logs, selected servers, latency metrics, energy consumption, and carbon avoided.
2. **`routing_feedback`**: Records predicted versus actual performance metrics and calculated satisfaction scores to drive Bayesian adaptation.
3. **`energy_measurements`**: Logs estimated versus hardware-measured energy consumption and runtime estimation error percentages for self-calibration.
4. **`historical_carbon`**: Houses hourly time-series carbon intensity and renewable percentage records utilized by the forecasting engine.
5. **`carbon_cache`**: Maintains temporary caches of live grid API responses to optimize network traffic and enforce rate limits.
6. **`ci_runs`**: Logs CI/CD anomaly detection evaluations, predicted pipeline energy draw, and automated enforcement actions (`ALLOW`, `WARN`, `BLOCK`).
7. **`offset_purchases`**: Tracks simulated or executed carbon credit transactions required to offset budget exceedances.

Curated CSV exports of these tables are provided in the `dataset/` directory for independent academic review and experimental reproduction.

---

## 8. License & Citation

This software is released under the **MIT License**. 

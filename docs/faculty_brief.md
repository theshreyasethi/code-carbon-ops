# CodeCarbonOps — Faculty Presentation Brief

---

## Abstract

**CodeCarbonOps** is a self-learning, carbon-aware AI inference routing system that minimizes the environmental footprint of Large Language Model (LLM) workloads. The system dynamically routes AI tasks across 15 globally distributed cloud servers by considering real-time electricity grid carbon intensity data (sourced from ElectricityMaps API), forecasted future carbon patterns, and user-defined urgency constraints.

The core contribution is a **closed-loop, multi-objective optimization engine** comprising five novel subsystems: (1) a **Thompson Sampling-based adaptive routing learner** that uses Bayesian Bandits to learn optimal server assignments from historical outcomes; (2) a **Holt-Winters Exponential Smoothing forecaster** that predicts carbon intensity 24 hours ahead with confidence intervals; (3) a **real-time energy measurement module** using CPU telemetry (psutil) that self-calibrates token-based energy estimates against measured power consumption; (4) a **z-score anomaly detection system** for CI/CD pipelines that maintains per-repository carbon baselines and flags statistically unusual carbon spikes; and (5) a **carbon-aware model auto-selection engine** that dynamically trades model quality for energy efficiency when grid carbon exceeds defined thresholds.

The system is implemented as a full-stack application (FastAPI backend, React dashboard, SQLite database) and operates on **real-time carbon intensity data** from 15 global regions. Experimental results demonstrate that intelligent routing alone reduces carbon emissions by up to **97%** (e.g., routing from India at 854 g/kWh to Sweden at 15 g/kWh), and combined with model auto-selection, achieves up to **99% reduction** with quantified quality tradeoffs.

---

## 1. Project Overview — In Brief

### What It Does
Every AI inference (e.g., a ChatGPT query) consumes electricity. The carbon footprint of that electricity depends **entirely on where and when** the computation runs:

- **Sweden**: 15 g CO₂/kWh (98% hydro + wind) → **very clean**
- **India**: 854 g CO₂/kWh (58% coal) → **very dirty**

The **same query** running in Sweden produces **~57 times less carbon** than in India.

CodeCarbonOps exploits this fact: it routes every AI task to the server with the **lowest carbon intensity at that moment**, while balancing latency, cost, and quality constraints.

### Why It's Novel
Existing carbon-aware tools (like Google Carbon Footprint, CodeCarbon) only **measure** emissions. Our system **actively reduces** them using five ML/statistical techniques working in a closed feedback loop. No existing system combines all five.

---

## 2. System Architecture

```
User Request (prompt, model, urgency)
        │
        ▼
┌─── P5: Model Auto-Selection ───┐
│  Downgrades model if grid dirty │
└──────────────┬──────────────────┘
               │
        ▼
┌─── Task Analyzer ──────────────┐
│  Token estimation, energy calc  │
└──────────────┬──────────────────┘
               │
        ▼
┌─── Carbon Monitor ─────────────┐
│  Real-time data: 15 regions     │
│  (ElectricityMaps + UK API)     │
└──────────────┬──────────────────┘
               │
        ▼
┌─── P3: Energy Measurement ─────┐
│  Start CPU monitoring (psutil)  │
└──────────────┬──────────────────┘
               │
        ▼
┌─── P1: Adaptive Smart Router ──┐
│  Layer 1: Urgency weights       │
│  Layer 2: Learned adjustments   │
│  Layer 3: Thompson Sampling     │
│  → Select best server           │
└──────────────┬──────────────────┘
               │
        ▼
┌─── Inference Execution ────────┐
│  Run AI task on selected server │
└──────────────┬──────────────────┘
               │
        ▼
┌─── P3: Stop Measurement ───────┐
│  Compare estimated vs measured  │
│  Update calibration factor      │
└──────────────┬──────────────────┘
               │
        ▼
┌─── P1: Record Feedback ────────┐
│  Update Beta(α,β) distributions │
│  System learns for next time    │
└─────────────────────────────────┘
```

---

## 3. Feature-by-Feature Explanation with ML Formulas

---

### Feature 1 (P1): Self-Adaptive Routing — Thompson Sampling

> **File:** `pcem/router/adaptive_learner.py` (320 lines)
> **ML Technique:** Multi-Armed Bandit → Thompson Sampling with Beta-Bernoulli model

#### What It Does
The system must choose **which of 15 servers** to route each AI task to. This is a classic **Exploration vs Exploitation** problem:
- **Exploit:** Always pick the server that worked best historically
- **Explore:** Try less-used servers that _might_ be better

Thompson Sampling solves this optimally by maintaining a probabilistic belief about each server's "goodness."

#### Mathematical Foundation

**Beta Distribution** — Each server-urgency pair maintains a Beta distribution:

$$\text{Beta}(\alpha, \beta)$$

Where:
- **α (alpha)** = number of "successes" + 1 (prior)
- **β (beta)** = number of "failures" + 1 (prior)

A "success" means: the server's actual carbon and latency were ≤ what was predicted.
A "failure" means: the actual performance was worse than predicted.

**Initialization:** Every server starts with $\text{Beta}(1, 1)$ — a uniform distribution (no preference).

**Sampling:** For each routing decision, we sample from each server's Beta distribution:

$$\theta_s \sim \text{Beta}(\alpha_s, \beta_s) \quad \text{for each server } s$$

The server with the **highest sample** gets selected. This naturally balances:
- Servers with many successes → Beta(50, 5) → samples cluster near 0.9 → **exploit**
- Servers with few observations → Beta(2, 2) → samples are high-variance → **explore**

**Update Rule:** After each routing decision:

```
IF actual_carbon ≤ predicted_carbon AND actual_latency ≤ predicted_latency:
    α_s ← α_s + 1    (success)
ELSE:
    β_s ← β_s + 1    (failure)
```

**Exploration Bonus Calculation:**
```python
exploration_bonus = sample_from_Beta(α, β)  × exploration_weight
# exploration_weight = 0.15 (tunable hyperparameter)
```

**Adaptive Weight Adjustment:** The system also adjusts the importance of each scoring factor based on historical prediction errors:

$$w'_{\text{carbon}} = w_{\text{carbon}} \times \left(1 + \frac{\bar{e}_{\text{carbon}}}{E_{\text{max}}} \times \eta\right)$$

Where:
- $w_{\text{carbon}}$ = base urgency weight for carbon
- $\bar{e}_{\text{carbon}}$ = mean historical error for carbon predictions
- $E_{\text{max}}$ = maximum allowed error (capped at 50%)
- $\eta$ = learning rate (0.1)

**Satisfaction Score (composite metric):**

$$S = 0.6 \times S_{\text{carbon}} + 0.4 \times S_{\text{latency}}$$

Where:

$$S_{\text{carbon}} = \min\left(1.0, \frac{\text{predicted\_carbon}}{\text{actual\_carbon}}\right)$$

$$S_{\text{latency}} = \min\left(1.0, \frac{\text{predicted\_latency}}{\text{actual\_latency}}\right)$$

#### Final Server Score (3-Layer Architecture)

$$\text{Score}(s) = \underbrace{\sum_{f} w'_f \cdot x_{f}(s)}_{\text{Layer 1+2: Adaptive Weighted Sum}} + \underbrace{\theta_s \cdot \lambda}_{\text{Layer 3: Thompson Sampling}}$$

Where:
- $f \in \{\text{carbon, renewable, latency, cost}\}$ — the four factors
- $w'_f$ — urgency-based weight, adaptively adjusted from historical errors
- $x_f(s)$ — normalized score of server $s$ on factor $f$ (0 to 1)
- $\theta_s$ — sample from Beta distribution for server $s$
- $\lambda$ = 0.15 — exploration weight

---

### Feature 2 (P2): Carbon Intensity Forecasting — Holt-Winters Exponential Smoothing

> **File:** `pcem/predictor/predictor.py` (461 lines)
> **ML Technique:** Triple Exponential Smoothing (Holt-Winters method) with additive seasonality

#### What It Does
Predicts carbon intensity for each region **24 hours into the future** with confidence intervals. This allows the system to recommend **"wait 3 hours for 40% less carbon"** instead of just picking the best server right now.

#### Mathematical Foundation

**Holt-Winters Triple Exponential Smoothing** decomposes a time series into three components:

$$\hat{y}_{t+h} = L_t + h \cdot T_t + S_{t+h-m}$$

Where:
- $\hat{y}_{t+h}$ = forecast at time $t+h$ (h hours ahead)
- $L_t$ = **Level** (smoothed value at time $t$)
- $T_t$ = **Trend** (direction the series is moving)
- $S_t$ = **Seasonal component** (repeating 24-hour daily pattern)
- $m$ = **seasonal period** = 24 (hours in a day)

**Update Equations (Additive Model):**

Level update:
$$L_t = \alpha (y_t - S_{t-m}) + (1 - \alpha)(L_{t-1} + T_{t-1})$$

Trend update:
$$T_t = \beta (L_t - L_{t-1}) + (1 - \beta) T_{t-1}$$

Seasonal update:
$$S_t = \gamma (y_t - L_t) + (1 - \gamma) S_{t-m}$$

Where:
- $\alpha$ = level smoothing parameter (0 to 1)
- $\beta$ = trend smoothing parameter (0 to 1)
- $\gamma$ = seasonal smoothing parameter (0 to 1)
- These are **auto-optimized** by `statsmodels` using maximum likelihood estimation

**Why Additive Seasonality?**
Carbon intensity follows a **daily solar cycle** — it drops during sunny hours (10 AM – 3 PM) when solar power peaks, and rises at night. This pattern **adds/subtracts** from the baseline rather than scaling it, making additive seasonality appropriate.

**Confidence Intervals (95%):**

$$\text{CI}_{t+h} = \hat{y}_{t+h} \pm z_{0.975} \times \sigma_r \times \left(1 + \frac{h}{H} \times 0.5\right)$$

Where:
- $z_{0.975} = 1.96$ (95% confidence z-score)
- $\sigma_r$ = standard deviation of residuals from the fitted model
- $h$ = forecast horizon (hours ahead)
- $H$ = total forecast window (24 hours)
- The factor $(1 + h/H \times 0.5)$ **widens** the bands for further-out predictions

**Fallback: Weighted Moving Average** (when data < 48 points):

$$\hat{y}_{h} = \frac{\sum_{i=1}^{n} w_i \cdot y_i \cdot \mathbb{1}[\text{hour}(y_i) = h]}{\sum_{i=1}^{n} w_i \cdot \mathbb{1}[\text{hour}(y_i) = h]}$$

Where $w_i = e^{-0.1 \times (n-1-i)}$ — exponential decay weighting that gives **recent observations more influence**.

**Accuracy Metrics:**

MAPE (Mean Absolute Percentage Error):
$$\text{MAPE} = \frac{100\%}{n} \sum_{i=1}^{n} \left|\frac{y_i - \hat{y}_i}{y_i}\right|$$

RMSE (Root Mean Square Error):
$$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2}$$

**Trend Detection** (via simple linear regression):

$$\text{slope} = \frac{\sum_{i=1}^{n} (i - \bar{i})(y_i - \bar{y})}{\sum_{i=1}^{n} (i - \bar{i})^2}$$

- slope < −1 → "improving" (grid getting cleaner)
- slope > +1 → "worsening" (more fossil fuel)
- else → "stable"

---

### Feature 3 (P3): Real Energy Measurement — CPU Power Model

> **File:** `pcem/monitor/energy_monitor.py` (230 lines)
> **Technique:** System-level CPU telemetry + physics-based power model + self-calibration

#### What It Does
Instead of only **estimating** energy from token counts ($E = \text{tokens} \times \text{factor}$), the system **measures actual CPU power consumption** during inference using `psutil` and compares it against the estimate.

#### Mathematical Foundation

**Power Model:**

$$P_{\text{actual}} = \left(P_{\text{idle}} + \frac{\text{CPU\%}}{100} \times P_{\text{TDP}}\right) \times \text{PUE}$$

Where:
- $P_{\text{idle}}$ = 15W (base system idle power)
- $\text{CPU\%}$ = average CPU utilization measured by psutil
- $P_{\text{TDP}}$ = 65W (Thermal Design Power of CPU)
- $\text{PUE}$ = 1.2 (Power Usage Effectiveness — accounts for cooling, networking, etc.)

**Energy Calculation:**

$$E_{\text{measured}} = \frac{P_{\text{actual}} \times t}{3600 \times 1000} \quad \text{(kWh)}$$

Where $t$ = duration in seconds.

**Estimation Error:**

$$\text{Error\%} = \frac{E_{\text{estimated}} - E_{\text{measured}}}{E_{\text{measured}}} \times 100$$

**Self-Calibration Factor:**
After accumulating enough measurements (≥3), the system calculates:

$$\text{CF} = \max\left(0.3, \min\left(2.0, 1 - \frac{\bar{\text{Error\%}}}{100}\right)\right)$$

Future estimates are adjusted: $E'_{\text{estimated}} = E_{\text{estimated}} \times \text{CF}$

If the system consistently over-estimates by 40%, the calibration factor becomes 0.6, automatically correcting future estimates.

---

### Feature 4 (P4): Anomaly Detection in CI/CD — Z-Score Analysis

> **File:** `backend/api/ci_endpoints.py` (340 lines)
> **Technique:** Z-Score Statistical Anomaly Detection with per-repository baselines

#### What It Does
When a CI/CD pipeline (GitHub Actions) evaluates a Pull Request, the system checks if the predicted carbon footprint is **statistically unusual** compared to the repository's historical baseline.

#### Mathematical Foundation

**Per-Repository Baseline** (from last 90 days of CI runs):

$$\mu_r = \frac{1}{n} \sum_{i=1}^{n} c_i \quad, \quad \sigma_r = \sqrt{\frac{1}{n-1} \sum_{i=1}^{n} (c_i - \mu_r)^2}$$

Where $c_i$ = predicted carbon (grams) for the $i$-th CI run of repository $r$.

**Z-Score Calculation:**

$$z = \frac{c_{\text{new}} - \mu_r}{\sigma_r}$$

**Decision Thresholds (based on standard normal distribution):**

| Z-Score | Percentile | Interpretation | Action |
|---------|-----------|----------------|--------|
| z ≤ 2.0 | ≤ 97.7% | Normal variation | **ALLOW** |
| 2.0 < z ≤ 3.0 | 97.7% – 99.7% | Unusual spike | **WARN** |
| z > 3.0 | > 99.7% | Extreme anomaly | **BLOCK** |

**Why This Works:**
By the **empirical rule** (68-95-99.7), 99.7% of normally distributed data falls within 3 standard deviations of the mean. If a PR's carbon exceeds this, it's nearly certainly an anomaly (e.g., massive code change, dependency explosion, or misconfigured build).

**Trend Detection** (same linear regression as P2):

$$\text{slope} = \frac{\sum (i - \bar{i})(c_i - \bar{c})}{\sum (i - \bar{i})^2}$$

A positive slope means the repo's carbon is **increasing** over time (e.g., growing codebase, less efficient tests).

---

### Feature 5 (P5): Carbon-Aware Model Auto-Selection — Decision Matrix

> **File:** `pcem/analyzer/model_selector.py` (290 lines)
> **Technique:** Multi-criteria decision matrix with urgency-gated thresholds

#### What It Does
Instead of just choosing WHERE to run, this module chooses WHAT to run. When the grid is carbon-heavy, it recommends a lighter model variant (e.g., GPT-4o → GPT-4o-mini) that uses less energy.

#### Mathematical Foundation

**Quality-Energy Tradeoff:**

$$\text{Energy Savings\%} = \left(1 - \frac{E_{\text{alt}}}{E_{\text{orig}}}\right) \times 100$$

$$\text{Quality Loss\%} = \frac{Q_{\text{orig}} - Q_{\text{alt}}}{Q_{\text{orig}}} \times 100$$

**Example:**
```
GPT-4o:      Quality=95, Energy=0.00016 kWh/1K tokens
GPT-4o-mini: Quality=82, Energy=0.00005 kWh/1K tokens

Energy Savings = (1 - 0.00005/0.00016) × 100 = 68.8%
Quality Loss   = (95 - 82) / 95 × 100         = 13.7%
```

**Decision Logic (gated by urgency):**

| Urgency | Carbon Threshold | Max Quality Loss | Action |
|---------|-----------------|-------------------|--------|
| 1–2 (Critical) | — | 0% | **Never downgrade** |
| 3 (Balanced) | > 500 g/kWh | 15% | **Suggest** lighter model |
| 4 (Flexible) | > 400 g/kWh | 25% | **Recommend** lighter model |
| 5 (Minimal) | > 300 g/kWh | 40% | **Auto-select** lighter model |

**Alternative Selection Algorithm:**
When multiple alternatives exist (e.g., GPT-4o can go to GPT-4o-mini OR GPT-4-turbo):

```
IF carbon_intensity > 600 g/kWh:
    select = argmin(energy_factor)     # Prefer maximum energy savings
ELSE:
    select = argmax(quality)           # Prefer best quality among viable
```

Where "viable" = alternatives with quality_loss ≤ max_allowed for that urgency.

---

### Multi-Factor Server Scoring (Smart Router Core)

> **File:** `pcem/router/smart_router.py` (236 lines)

The router uses a **weighted multi-objective optimization** to score each server:

**Normalization** (Min-Max to [0, 1]):

$$x_{\text{norm}} = \frac{x_{\text{max}} - x_i}{x_{\text{max}} - x_{\text{min}}}$$

(Inverted for "lower is better" metrics like carbon and latency)

**Four scoring dimensions:**

| Factor | What It Measures | Lower = Better? |
|--------|-----------------|-----------------|
| Carbon Intensity | g CO₂ per kWh of grid electricity | Yes ✓ |
| Renewable % | % of grid power from clean sources | No (higher = better) |
| Latency | Milliseconds to reach server | Yes ✓ |
| Cost | $/hour for GPU compute | Yes ✓ |

**Urgency-Based Weight Table:**

| Urgency | Carbon | Renewable | Latency | Cost | Meaning |
|---------|--------|-----------|---------|------|---------|
| 1 (Critical) | 15% | 10% | 45% | 30% | Speed first |
| 2 | 20% | 10% | 35% | 35% | Speed + cost |
| 3 (Balanced) | 30% | 15% | 25% | 30% | Equal balance |
| 4 | 40% | 20% | 15% | 25% | Green-leaning |
| 5 (Minimal) | 50% | 25% | 5% | 20% | Maximum green |

---

## 4. Data Sources Summary

| Data | Source | Type |
|------|--------|------|
| Real-time carbon intensity (15 regions) | ElectricityMaps API | ✅ Real-time live |
| UK carbon intensity | UK Carbon Intensity API (free) | ✅ Real-time live |
| Historical carbon (360 records) | ElectricityMaps `/history` endpoint | ✅ Real historical |
| Server specifications | `servers.json` (real AWS/GCP/Azure specs) | ✅ Real specs |
| Model energy factors | Published research on LLM power consumption | ✅ Research-based |
| CPU energy measurement | psutil system monitoring | ✅ Real hardware |

---

## 5. Key ML/Statistical Techniques Summary Table

| # | Technique | Where Used | Formula | Purpose |
|---|-----------|-----------|---------|---------|
| 1 | **Thompson Sampling** (Bayesian Bandit) | P1: Server selection | $\theta \sim \text{Beta}(\alpha, \beta)$ | Balance explore vs exploit across 15 servers |
| 2 | **Beta Distribution** | P1: Uncertainty modeling | $f(x; \alpha, \beta) = \frac{x^{\alpha-1}(1-x)^{\beta-1}}{B(\alpha,\beta)}$ | Model success/failure probability per server |
| 3 | **Holt-Winters Exponential Smoothing** | P2: 24h carbon forecast | $\hat{y}_{t+h} = L_t + hT_t + S_{t+h-m}$ | Seasonal decomposition for daily carbon patterns |
| 4 | **Confidence Intervals** | P2: Prediction uncertainty | $\hat{y} \pm z_{0.975} \cdot \sigma_r \cdot f(h)$ | Quantify forecast reliability |
| 5 | **Exponential Decay Weighting** | P2: Fallback forecaster | $w_i = e^{-0.1(n-1-i)}$ | Give recent observations more weight |
| 6 | **Linear Regression** (slope) | P2+P4: Trend detection | $b = \frac{\sum(x_i-\bar{x})(y_i-\bar{y})}{\sum(x_i-\bar{x})^2}$ | Detect improving/worsening carbon trends |
| 7 | **Physics Power Model** | P3: Energy measurement | $P = (P_{idle} + \frac{CPU\%}{100} \cdot TDP) \times PUE$ | Convert CPU utilization to watts |
| 8 | **Self-Calibration** | P3: Error correction | $CF = 1 - \bar{e}/100$ | Auto-correct systematic estimation bias |
| 9 | **Z-Score Anomaly Detection** | P4: CI/CD enforcement | $z = \frac{x - \mu}{\sigma}$ | Detect statistically unusual carbon spikes |
| 10 | **Multi-Objective Optimization** | Router: Server scoring | $S = \sum_f w_f \cdot x_f + \theta \cdot \lambda$ | Weighted scoring across 4 dimensions |
| 11 | **MAPE / RMSE** | P2: Forecast accuracy | $\text{MAPE} = \frac{100}{n}\sum|\frac{y-\hat{y}}{y}|$ | Quantify prediction quality |
| 12 | **Min-Max Normalization** | Router: Factor scaling | $x' = \frac{x_{max} - x}{x_{max} - x_{min}}$ | Scale different metrics to [0,1] |

---

## 6. One-Paragraph Explanation (For Faculty)

> *"CodeCarbonOps is a carbon-aware AI inference router that uses real-time electricity grid data from the ElectricityMaps API to route AI workloads to the greenest of 15 global servers. It employs Thompson Sampling (a Bayesian multi-armed bandit algorithm) to adaptively learn which servers perform best under different urgency constraints, Holt-Winters Exponential Smoothing to forecast carbon intensity 24 hours ahead with confidence intervals, psutil-based CPU telemetry to measure and self-calibrate energy estimates, z-score anomaly detection, and a decision-matrix-based model auto-selector that trades model quality for energy efficiency when the grid is carbon-heavy. All five techniques operate in a closed feedback loop — the system learns from every routing decision and improves over time. The platform is built with FastAPI (backend), React (dashboard), SQLite (persistence), and statsmodels/scipy (ML), and operates entirely on real-time data from global electricity grid APIs."*

# CodeCarbonOps
## Carbon-Aware AI Inference Routing System

> **"A Closed-Loop System and Method for Real-Time Carbon-Aware Routing of AI Inference Workloads with Post-Execution Feedback and Self-Calibration"**

### A Project Report for Faculty Review


## Table of Contents

1. Introduction & Problem Statement
2. Project Objectives
3. How It Works - Simple Explanation
4. System Architecture
5. Key Features
6. Technology Stack
7. Implementation Phases
8. Real-World Impact
9. Future Enhancements
10. Conclusion

---

## 1. Introduction & Problem Statement

### The Problem: AI's Hidden Environmental Cost

Artificial Intelligence, especially Large Language Models (LLMs) like ChatGPT, consumes enormous amounts of electricity. Every time you ask an AI a question, servers in data centers use energy to process your request.

**Key Statistics:**
- Training GPT-3 produced ~552 tonnes of CO2 (equivalent to 120 cars driving for a year)
- A single ChatGPT query uses 10x more energy than a Google search
- Global data centers consume about 1-2% of world's electricity

**The Hidden Problem:**
Not all electricity is equal! The same AI task produces DIFFERENT carbon emissions depending on WHERE it runs:

| Server Location | Carbon Intensity | Energy Source |
|-----------------|------------------|---------------|
| Sweden | 45 g CO2/kWh | 90% Hydropower |
| Oregon, USA | 120 g CO2/kWh | 70% Wind |
| Mumbai, India | 708 g CO2/kWh | 70% Coal |

**The same AI task in India produces 15x more carbon than in Sweden!**

### Current Situation
Today, when you use AI:
- Your request goes to the NEAREST or CHEAPEST server
- NO consideration of carbon footprint
- NO option to choose greener alternatives
- Users have NO visibility into environmental impact

---

## 2. Project Objectives

### Main Goal
Build a system that automatically routes AI tasks to the **greenest server in the world** at any given moment.

### Specific Objectives

1. **Predict Before Execute**
   - Estimate how much energy an AI task will consume BEFORE running it
   - Calculate expected carbon and water footprint

2. **Real-Time Global Monitoring**
   - Track carbon intensity of electricity grids worldwide
   - Monitor energy mix: solar, wind, hydro, coal, gas percentages
   - Consider time of day (solar availability varies)

3. **Smart Routing**
   - Automatically select the greenest available server
   - Balance carbon footprint with latency and cost
   - Suggest waiting for "green windows" if possible

4. **Carbon Offset Integration**
   - When green servers aren't available, automatically purchase carbon credits
   - Ensure every AI task is carbon-neutral

5. **Transparency**
   - Show users exactly how much carbon their AI task produced
   - Display which energy sources powered their request

---

## 3. How It Works - Simple Explanation

### Step-by-Step Flow

```
STEP 1: USER SENDS A REQUEST
┌─────────────────────────────────────────┐
│  "Summarize this 50-page document"      │
│  Carbon Budget: 10g CO2                 │
└─────────────────────────────────────────┘
                    │
                    ▼
STEP 2: TASK ANALYZER
┌─────────────────────────────────────────┐
│  Analyzes the request:                  │
│  • Token count: 15,000 (input+output)   │
│  • Model needed: GPT-4                  │
│  • Estimated energy: 0.02 kWh           │
└─────────────────────────────────────────┘
                    │
                    ▼
STEP 3: CARBON MONITOR (Checks World Map)
┌─────────────────────────────────────────┐
│  RIGHT NOW across the world:            │
│                                         │
│  🇸🇪 Sweden:  45 g/kWh (Sunny + Hydro)  │
│  🇺🇸 Oregon: 120 g/kWh (Windy today)    │
│  🇮🇳 Mumbai: 708 g/kWh (Peak coal use)  │
│  🇩🇪 Germany: 400 g/kWh (Night, no sun) │
└─────────────────────────────────────────┘
                    │
                    ▼
STEP 4: SMART ROUTER (Picks Best Server)
┌─────────────────────────────────────────┐
│  Scoring each server:                   │
│                                         │
│  Sweden:  Carbon=0.9g  Latency=200ms ⭐ │
│  Oregon:  Carbon=2.4g  Latency=100ms    │
│  Mumbai:  Carbon=14.2g Latency=50ms  ❌ │
│                                         │
│  DECISION: Run in Sweden (0.9g CO2)     │
└─────────────────────────────────────────┘
                    │
                    ▼
STEP 5: EXECUTE & FEEDBACK (The Core Loop)
┌─────────────────────────────────────────┐
│  1. Result: "The document discusses..." │
│                                         │
│  2. Measure Actuals (Post-Execution):   │
│  • Actual Carbon Used: 0.95g CO2        │
│  • Actual Latency: 215ms                │
│                                         │
│  3. 🔄 Feedback Loop:                   │
│  Uses actual post-execution measurements│
│  to update routing models and calibrate │
│  future routing decisions.              │
└─────────────────────────────────────────┘
```

### If Carbon Budget Cannot Be Met

```
SCENARIO: User wants max 5g CO2, but minimum available is 8g

STEP 6: CARBON OFFSET SYSTEM
┌─────────────────────────────────────────┐
│  Budget exceeded by 3g CO2              │
│                                         │
│  Action: Purchase carbon offset         │
│  • Amount: 3g CO2                       │
│  • Cost: $0.0006 (very small!)          │
│  • Provider: Certified offset program   │
│                                         │
│  Result: Task is now CARBON NEUTRAL ✅  │
└─────────────────────────────────────────┘
```

---

## 4. System Architecture

### High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│                    (Web Dashboard / API)                         │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      BACKEND API (FastAPI)                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │  /api/infer    │  │ /api/carbon    │  │ /api/offsets   │     │
│  │  LLM Proxy     │  │ Carbon Data    │  │ Buy Credits    │     │
│  └────────────────┘  └────────────────┘  └────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  TASK ANALYZER  │  │ CARBON MONITOR  │  │  SMART ROUTER   │
│                 │  │                 │  │                 │
│ • Token count   │  │ • API polling   │  │ • Score servers │
│ • Model size    │  │ • Energy mix    │  │ • Pick greenest │
│ • Energy est.   │  │ • Forecasting   │  │ • Latency/cost  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    EXTERNAL DATA SOURCES                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Electricity  │  │ UK Carbon    │  │ Ember        │           │
│  │ Maps API     │  │ Intensity    │  │ Climate      │           │
│  │ (Real-time)  │  │ (Forecast)   │  │ (Historical) │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    GPU SERVERS WORLDWIDE                         │
│                                                                  │
│   🇸🇪 Sweden     🇺🇸 Oregon     🇮🇳 Mumbai     🇩🇪 Germany        │
│   (AWS)        (Azure)       (GCP)         (AWS)              │
└──────────────────────────────────────────────────────────────────┘
```

### Component Description

| Component | Purpose |
|-----------|---------|
| **Backend API** | Receives user requests, coordinates all modules |
| **Task Analyzer** | Estimates energy needed for AI tasks |
| **Carbon Monitor** | Fetches real-time carbon data from APIs |
| **Smart Router** | Picks the optimal server based on multiple factors |
| **Offset Module** | Purchases carbon credits when needed |
| **Dashboard** | Visual interface for monitoring and analytics |

---

## 5. Core Invention & Patent Claims

Based on our IPR strategy, the technical components are structured into a primary main claim and several supporting dependent claims to maximize patent strength and survival.

### Core Invention (Main Claim)
**A Closed-Loop Carbon-Aware AI Inference Routing System**
The strongest technical heart of the work is the closed-loop feedback mechanism. The system:
1. **Receives** an inference request.
2. **Selects** a region/server based on a combined score of carbon intensity, network latency, and urgency.
3. **Executes** the request on the selected optimal server.
4. **Measures** the actual post-execution energy consumption and latency.
5. **Uses Feedback** to update and calibrate future routing decisions, creating a self-improving loop.

### Supporting Features (Dependent Claims)

While the closed-loop system is the core, the following advanced mechanisms support and enhance the system:

1. **Thompson Sampling Update Mechanism**: Balances the exploration of new, potentially green servers with the exploitation of known green servers.
2. **Holt-Winters Forecasting**: Applies statistical forecasting to historical grid data to predict near-future carbon intensity variations.
3. **Model Auto-Selection Thresholds**: Dynamically selects algorithms or AI models of different sizes based on available carbon budgets and current grid constraints.
4. **Self-Calibration Factor**: Automatically adjusts prediction models based on the variance between predicted metrics and actual post-execution metrics detected in the core loop.
5. **CI/CD Anomaly Detection**: Actively monitors deployed agents to detect unexpected performance drops or sudden, unanticipated spikes in carbon emissions.

---

## 6. Technology Stack

### Backend Technologies

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **Python 3.14** | Primary language | Best AI/ML ecosystem |
| **FastAPI** | Web framework | Fast, modern, async support |
| **Uvicorn** | ASGI server | High performance |
| **SQLAlchemy** | Database ORM | Easy database operations |
| **PostgreSQL** | Database | Reliable, scalable |
| **Pydantic** | Data validation | Type safety |

### Frontend Technologies

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **React** | UI framework | Component-based, popular |
| **Vite** | Build tool | Fast development |
| **Chart.js** | Visualizations | Carbon charts |
| **Leaflet** | Maps | World carbon map |

### External APIs

| API | Purpose | Data Provided |
|-----|---------|---------------|
| **ElectricityMaps** | Real-time carbon | 50+ countries, energy mix |
| **UK Carbon Intensity** | UK forecasts | Regional breakdown |
| **Ember Climate** | Historical data | 200+ regions |
| **Patch.io** | Carbon offsets | Credit purchases |

### Infrastructure

| Component | Technology |
|-----------|------------|
| Hosting | AWS / Azure / GCP |
| Containers | Docker |
| CI/CD | GitHub Actions (optional) |
| Monitoring | Prometheus + Grafana |

---

## 7. Implementation Phases

### Phase 1: Foundation (Week 1) ✅ COMPLETED
- Project structure setup
- Basic FastAPI server
- Carbon calculation module
- Fallback carbon data for 15+ regions

### Phase 2: Core Intelligence (Week 2)
- Task analyzer for LLM energy estimation
- Real-time carbon monitor with API integration
- Smart router algorithm
- Server database with global GPU options

### Phase 3: Integration (Week 3)
- Connect all modules
- Implement inference proxy endpoint
- Add database persistence
- API documentation

### Phase 4: Offset System (Week 4)
- Offset calculator
- Simulated offset purchases
- (Optional) Real offset API integration
- Transaction logging

### Phase 5: Dashboard (Week 5)
- React frontend setup
- Real-time carbon map
- Analytics charts
- User settings

### Phase 6: Testing & Polish (Week 6)
- Unit and integration tests
- Performance optimization
- Documentation
- Demo preparation

---

## 8. Real-World Impact

### Environmental Benefits

**Example Calculation:**
- Average AI company processes 1 million requests/day
- Default routing: 500g CO2 average per request
- With CodeCarbonOps: 100g CO2 average per request

**Annual Savings:**
```
Old Way:    1,000,000 × 500g × 365 = 182,500 tonnes CO2/year
New Way:    1,000,000 × 100g × 365 =  36,500 tonnes CO2/year
                                    ────────────────────────
Saved:                               146,000 tonnes CO2/year
```

**That's equivalent to:**
- 🚗 Taking 31,700 cars off the road
- 🌳 Planting 6.7 million trees
- 🏠 Powering 17,600 homes for a year

### Business Benefits

1. **Cost Savings** - Often green servers are also cheaper (hydro power)
2. **Compliance** - Meet ESG (Environmental, Social, Governance) requirements
3. **Marketing** - "Carbon-Neutral AI" is a competitive advantage
4. **Transparency** - Show customers their environmental impact

---

## 9. Future Enhancements

### Short Term (3-6 months)
- Mobile app for monitoring
- Slack/Teams integration for alerts
- Multi-cloud support (AWS + Azure + GCP)

### Medium Term (6-12 months)
- Machine learning for better predictions
- Predictive scheduling based on weather forecasts
- Blockchain-verified carbon credits

### Long Term (1-2 years)
- Edge computing for reduced latency
- Hardware-level power monitoring
- Industry-standard Carbon API

---

## 10. Conclusion

### Summary

CodeCarbonOps addresses a critical but often ignored problem: **the environmental impact of AI computation**. By intelligently routing AI tasks to the greenest servers worldwide and automatically offsetting unavoidable emissions, we can:

1. **Reduce AI's carbon footprint by up to 80%**
2. **Provide complete transparency** on environmental impact
3. **Ensure carbon neutrality** through automated offsets
4. **Maintain performance** while being sustainable

### Innovation

This project is innovative because:
- **Proactive, not reactive** - Predicts carbon BEFORE execution
- **Global optimization** - Considers entire world, not just one region
- **Real-time** - Uses live data, not static averages
- **Automatic** - No manual intervention needed
- **Transparent** - Users see exactly where their AI runs

### Alignment with UN Sustainable Development Goals

This project directly supports:
- **SDG 7**: Affordable and Clean Energy
- **SDG 12**: Responsible Consumption and Production
- **SDG 13**: Climate Action

---

## Project Team

| Role | Responsibility |
|------|----------------|
| **Member 1** | CI/CD Integration Lead |
| **Member 2** | PCEM Core Engineer (Prediction Engine) |
| **Member 3** | Backend & Data Lead (API Development) |
| **Member 4** | Dashboard & Offset Lead (UI + Offsets) |

---

## References

1. ElectricityMaps - https://electricitymaps.com
2. Ember Climate - https://ember-climate.org
3. UK Carbon Intensity API - https://carbonintensity.org.uk
4. "Energy and Policy Considerations for Deep Learning in NLP" - Strubell et al., 2019
5. IEA Emissions Factors Database - https://iea.org

---

*Document prepared for faculty review*
*Project: CodeCarbonOps*
*Date: January 2026*

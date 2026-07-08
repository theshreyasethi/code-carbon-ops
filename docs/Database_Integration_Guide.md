# Database Task Specification

## For: Member 3 (Backend & Data Lead)

---

## 🎯 Your Task

Build a PostgreSQL database layer for the project using SQLAlchemy.

---

## 📊 Tables You Need to Create

### 1. inference_runs
Store every AI inference request.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Auto-increment ID |
| prompt_hash | VARCHAR(64) | SHA256 hash of prompt (privacy) |
| model | VARCHAR(100) | Model used (gpt-4, etc.) |
| total_tokens | INTEGER | Token count |
| estimated_energy_kwh | FLOAT | Energy consumed |
| server_region | VARCHAR(50) | Where it ran |
| carbon_used_g | FLOAT | CO2 in grams |
| renewable_pct | FLOAT | % renewable energy |
| created_at | TIMESTAMP | When it ran |

### 2. offset_purchases
Store carbon credit purchases.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | |
| run_id | FOREIGN KEY → inference_runs | Link to the run |
| amount_g | FLOAT | Offset amount |
| cost_usd | FLOAT | Cost |
| provider | VARCHAR(100) | Who sold it |
| status | VARCHAR(50) | pending/completed/failed |

### 3. carbon_cache
Cache API responses.

| Column | Type | Description |
|--------|------|-------------|
| region | VARCHAR(50) | Region ID |
| carbon_intensity | FLOAT | g CO2/kWh |
| energy_mix | JSONB | Solar/wind/hydro breakdown |
| fetched_at | TIMESTAMP | When fetched |

---

## 📁 Files to Create

```
backend/database/
├── __init__.py
├── connection.py    ← Database connection
├── models.py        ← SQLAlchemy model classes
└── crud.py          ← CRUD operations
```

---

## 🔗 Integration Points

Your code needs to work with existing `backend/api/main.py`:
- After inference runs, save to `inference_runs` table
- After offset purchase, save to `offset_purchases` table

---

## 📚 Resources to Learn

- SQLAlchemy ORM: https://docs.sqlalchemy.org/en/20/orm/
- FastAPI with SQL: https://fastapi.tiangolo.com/tutorial/sql-databases/
- PostgreSQL + Docker: https://hub.docker.com/_/postgres

---

## ✅ Deliverables

1. Database models for all 3 tables
2. CRUD functions for basic operations
3. Integration with existing API endpoints
4. Test that data persists after server restart

---

## 🧪 How to Test

1. Run an inference via API
2. Check database - row should exist
3. Restart server
4. Query database - data should still be there

---

**Build it yourself. Ask questions if stuck. Create a PR when done.**

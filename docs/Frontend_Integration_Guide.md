# Frontend Task Specification

## For: Member 4 (Dashboard & Offset Lead)

---

## 🎯 Your Task

Build a React dashboard that visualizes the carbon routing system.

---

## 🔌 API Endpoints Available

The backend already provides these endpoints (running on `localhost:8000`):

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/api/v1/carbon/realtime` | GET | Carbon data for all regions |
| `/api/v1/carbon/servers` | GET | List of GPU servers |
| `/api/v1/infer` | POST | Run inference, get carbon report |
| `/api/v1/offsets/history` | GET | Offset purchase history |

Test them with Postman or browser before coding!

---

## 🎨 Features to Build

### Must Have (Priority 1)
- [ ] Display real-time carbon data table (region, intensity, renewable %)
- [ ] Inference test form (prompt, model selector, budget input)
- [ ] Show results: server selected, carbon used, carbon saved

### Should Have (Priority 2)
- [ ] Stats cards: total runs, total carbon saved, greenest region
- [ ] Color-code regions: green (low carbon) → red (high carbon)
- [ ] Refresh button to reload carbon data

### Nice to Have (Priority 3)
- [ ] World map showing server locations
- [ ] Charts showing carbon by region
- [ ] Dark mode

---

## 📁 Folder Structure

```
dashboard/
├── src/
│   ├── App.jsx           ← Main component
│   ├── components/       ← Your components
│   └── services/
│       └── api.js        ← Functions to call backend
├── package.json
└── index.html
```

---

## 🔨 Tech to Use

- **React** (with Vite) - UI framework
- **Axios** or **fetch** - API calls
- Up to you for styling (CSS, Tailwind, etc.)

---

## 📚 Resources to Learn

- Vite + React: https://vitejs.dev/guide/
- Axios: https://axios-http.com/docs/intro
- React Tutorial: https://react.dev/learn

---

## 🔗 How to Connect to Backend

```javascript
// Example concept - implement yourself
const API_URL = 'http://localhost:8000';

// Fetch carbon data
fetch(`${API_URL}/api/v1/carbon/realtime`)
  .then(response => response.json())
  .then(data => console.log(data));
```

---

## ✅ Deliverables

1. Working React app showing carbon data
2. Form to test inference endpoint
3. Results display with carbon metrics
4. Clean, readable code

---

## 🧪 How to Test

1. Start backend: `python -m uvicorn backend.api.main:app --reload`
2. Start frontend: `npm run dev`
3. Data should load from API
4. Inference form should work

---

**Design it. Build it. Make it look good. Create a PR when done.**

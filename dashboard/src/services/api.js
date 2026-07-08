import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = axios.create({
    baseURL: API_URL,
    timeout: 15000,
    headers: { 'Content-Type': 'application/json' }
});

// Carbon Data
export const getCarbonRealtime = () => api.get('/api/v1/carbon/realtime');
export const getCarbonRegions = () => api.get('/api/v1/carbon/regions');
export const getCarbonServers = () => api.get('/api/v1/carbon/servers');

// Inference
export const runInference = (data) => api.post('/api/v1/infer', data);

// History & Stats
export const getHistory = () => api.get('/api/v1/history');
export const getStats = () => api.get('/api/v1/stats');

// Offsets
export const purchaseOffset = (data) => api.post('/api/v1/offsets/purchase', data);
export const getOffsetHistory = () => api.get('/api/v1/offsets/history');

// Predictions
export const getPredictBestTime = () => api.get('/api/v1/predict/best-time', { timeout: 30000 });
export const getForecast = (region) => api.get(`/api/v1/predict/forecast/${region}`, { timeout: 30000 });
export const getRegionComparison = (hour) => api.get('/api/v1/predict/compare', { params: { hour }, timeout: 30000 });

// CI/CD
export const predictCICarbon = (data) => api.post('/api/v1/ci/predict', data, { timeout: 30000 });
export const getCIHistory = () => api.get('/api/v1/ci/history');

// Health
export const getHealth = () => api.get('/health');

export default api;

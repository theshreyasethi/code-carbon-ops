import { useState, useEffect } from 'react';
import { getPredictBestTime, getForecast } from '../services/api';
import {
    Chart as ChartJS,
    CategoryScale, LinearScale, PointElement, LineElement,
    Filler, Title, Tooltip, Legend
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Title, Tooltip, Legend);

const TOP_REGIONS = [
    { id: 'eu-north-1', label: 'Sweden', color: '#10b981' },
    { id: 'ap-south-1', label: 'India', color: '#f59e0b' },
    { id: 'us-west-2', label: 'US Oregon', color: '#3b82f6' },
    { id: 'eu-central-1', label: 'Germany', color: '#8b5cf6' },
    { id: 'australia-east', label: 'Australia', color: '#ef4444' },
];

export default function PredictivePanel() {
    const [bestTime, setBestTime] = useState(null);
    const [forecasts, setForecasts] = useState({});
    const [selectedRegion, setSelectedRegion] = useState('eu-north-1');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        setError('');
        try {
            // Load best time prediction
            const btRes = await getPredictBestTime();
            setBestTime(btRes.data);

            // Load forecasts for key regions
            const forecastData = {};
            for (const region of TOP_REGIONS) {
                try {
                    const fRes = await getForecast(region.id);
                    forecastData[region.id] = fRes.data.forecast || [];
                } catch { forecastData[region.id] = []; }
            }
            setForecasts(forecastData);
        } catch (err) {
            setError('Failed to load predictions. Is historical data seeded?');
        } finally {
            setLoading(false);
        }
    };

    // Build Chart.js data
    const buildChartData = () => {
        const datasets = TOP_REGIONS.map((region) => {
            const data = forecasts[region.id] || [];
            return {
                label: region.label,
                data: data.map(d => d.predicted_carbon),
                borderColor: region.color,
                backgroundColor: region.id === selectedRegion
                    ? region.color + '20'
                    : 'transparent',
                fill: region.id === selectedRegion,
                tension: 0.4,
                pointRadius: region.id === selectedRegion ? 4 : 2,
                borderWidth: region.id === selectedRegion ? 3 : 1.5,
            };
        });

        const labels = (forecasts[TOP_REGIONS[0].id] || []).map(d => d.time_label);

        return { labels, datasets };
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                labels: { color: '#94a3b8', font: { size: 12 } }
            },
            title: {
                display: true,
                text: '24-Hour Carbon Intensity Forecast (g/kWh)',
                color: '#e2e8f0',
                font: { size: 16, weight: 'bold' }
            },
            tooltip: {
                callbacks: {
                    label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y} g/kWh`
                }
            }
        },
        scales: {
            x: {
                ticks: { color: '#64748b', maxTicksLimit: 12 },
                grid: { color: '#1e293b' }
            },
            y: {
                ticks: { color: '#64748b' },
                grid: { color: '#1e293b' },
                title: { display: true, text: 'g CO₂/kWh', color: '#64748b' }
            }
        },
        interaction: { intersect: false, mode: 'index' }
    };

    if (loading) {
        return (
            <div className="card">
                <div className="card-header"><h2>Predictive Carbon Forecasting</h2></div>
                <div className="card-body" style={{ textAlign: 'center', padding: '3rem' }}>
                    Loading predictions...
                </div>
            </div>
        );
    }

    return (
        <div className="predictive-section">
            <div className="card">
                <div className="card-header">
                    <h2>Predictive Carbon Forecasting</h2>
                    <button className="btn-refresh" onClick={loadData}>Refresh</button>
                </div>
                <div className="card-body">
                    {error && <div className="error-msg">{error}</div>}

                    {/* Best Time Recommendation */}
                    {bestTime && bestTime.best_overall && (
                        <div className="prediction-banner">
                            <div className="prediction-text">
                                {bestTime.recommendation}
                            </div>
                            <div className="prediction-meta">
                                <span>Forecast window: {bestTime.forecast_window_hours}h</span>
                                <span>Regions analyzed: {bestTime.by_region?.length || 0}</span>
                            </div>
                        </div>
                    )}

                    {/* Region Selector */}
                    <div className="region-tabs">
                        {TOP_REGIONS.map(r => (
                            <button
                                key={r.id}
                                className={`region-tab ${selectedRegion === r.id ? 'active' : ''}`}
                                style={{ borderColor: selectedRegion === r.id ? r.color : 'transparent' }}
                                onClick={() => setSelectedRegion(r.id)}
                            >
                                {r.label}
                            </button>
                        ))}
                    </div>

                    {/* Chart */}
                    <div style={{ height: '350px', marginTop: '1rem' }}>
                        <Line data={buildChartData()} options={chartOptions} />
                    </div>

                    {/* Region Best Times Table */}
                    {bestTime?.by_region && (
                        <div style={{ marginTop: '1.5rem' }}>
                            <h3 style={{ color: '#e2e8f0', marginBottom: '0.8rem' }}>Best Time Per Region</h3>
                            <table className="carbon-table">
                                <thead>
                                    <tr>
                                        <th>Region</th>
                                        <th>Current (g/kWh)</th>
                                        <th>Best Time</th>
                                        <th>Best (g/kWh)</th>
                                        <th>Savings</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {bestTime.by_region.slice(0, 8).map((r, i) => (
                                        <tr key={i}>
                                            <td><strong>{r.region}</strong></td>
                                            <td>{r.current_carbon}</td>
                                            <td>
                                                {r.hours_from_now === 0
                                                    ? 'Now'
                                                    : `${r.best_time_label} (in ${r.hours_from_now}h)`
                                                }
                                            </td>
                                            <td>
                                                <span className={`carbon-badge ${r.best_carbon < 100 ? 'very-low' : r.best_carbon < 300 ? 'low' : 'moderate'}`}>
                                                    {r.best_carbon}
                                                </span>
                                            </td>
                                            <td style={{ color: r.potential_savings_pct > 0 ? '#10b981' : '#64748b' }}>
                                                {r.potential_savings_pct > 0 ? `↓ ${r.potential_savings_pct}%` : '—'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

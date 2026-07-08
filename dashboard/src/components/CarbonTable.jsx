import { useState, useEffect } from 'react';
import { getCarbonRegions } from '../services/api';

export default function CarbonTable() {
    const [regions, setRegions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchRegions();
    }, []);

    const fetchRegions = async () => {
        try {
            setLoading(true);
            const res = await getCarbonRegions();
            setRegions(res.data);
        } catch (err) {
            console.error('Error fetching regions:', err);
        } finally {
            setLoading(false);
        }
    };

    const getIntensityColor = (intensity) => {
        if (intensity < 100) return '#22c55e';      // Green - very clean
        if (intensity < 250) return '#84cc16';       // Light green
        if (intensity < 400) return '#f59e0b';       // Yellow/amber
        if (intensity < 600) return '#f97316';       // Orange
        return '#ef4444';                             // Red - dirty
    };

    const getIntensityLabel = (intensity) => {
        if (intensity < 100) return 'Very Low';
        if (intensity < 250) return 'Low';
        if (intensity < 400) return 'Moderate';
        if (intensity < 600) return 'High';
        return 'Very High';
    };

    if (loading) {
        return <div className="card"><div className="card-body">Loading carbon data...</div></div>;
    }

    return (
        <div className="card">
            <div className="card-header">
                <h2>Real-Time Carbon Intensity</h2>
                <button className="btn btn-sm" onClick={fetchRegions}>Refresh</button>
            </div>
            <div className="card-body">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Region</th>
                            <th>Country</th>
                            <th>Carbon (g/kWh)</th>
                            <th>Level</th>
                            <th>Renewable %</th>
                            <th>Top Sources</th>
                        </tr>
                    </thead>
                    <tbody>
                        {regions.map((region) => {
                            const mix = region.energy_mix || {};
                            const topSources = Object.entries(mix)
                                .filter(([, v]) => v > 0.01)
                                .sort(([, a], [, b]) => b - a)
                                .slice(0, 3)
                                .map(([k, v]) => `${k} ${(v * 100).toFixed(0)}%`)
                                .join(', ');

                            return (
                                <tr key={region.id}>
                                    <td><strong>{region.name}</strong></td>
                                    <td>{region.country}</td>
                                    <td>
                                        <span
                                            className="intensity-badge"
                                            style={{ backgroundColor: getIntensityColor(region.carbon_intensity) }}
                                        >
                                            {region.carbon_intensity?.toFixed(1)}
                                        </span>
                                    </td>
                                    <td>
                                        <span style={{ color: getIntensityColor(region.carbon_intensity) }}>
                                            {getIntensityLabel(region.carbon_intensity)}
                                        </span>
                                    </td>
                                    <td>
                                        <div className="renewable-bar">
                                            <div
                                                className="renewable-fill"
                                                style={{ width: `${(region.renewable_pct || 0) * 100}%` }}
                                            />
                                            <span>{((region.renewable_pct || 0) * 100).toFixed(0)}%</span>
                                        </div>
                                    </td>
                                    <td className="sources-cell">{topSources}</td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

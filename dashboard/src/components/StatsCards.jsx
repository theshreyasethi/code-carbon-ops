import { useState, useEffect } from 'react';
import { getStats, getHistory } from '../services/api';

export default function StatsCards() {
    const [stats, setStats] = useState(null);
    const [recentRuns, setRecentRuns] = useState(0);

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            const [statsRes, historyRes] = await Promise.all([getStats(), getHistory()]);
            setStats(statsRes.data);
            setRecentRuns(historyRes.data.count || 0);
        } catch (err) {
            console.error('Stats fetch error:', err);
        }
    };

    if (!stats) {
        return <div className="stats-cards"><div className="stat-card">Loading stats...</div></div>;
    }

    const cards = [
        {
            label: 'Total Inferences',
            value: stats.total_runs,
            color: '#6366f1'
        },
        {
            label: 'Carbon Used',
            value: `${stats.total_carbon_used_g.toFixed(2)}g`,
            color: '#10b981'
        },
        {
            label: 'Carbon Saved',
            value: `${stats.total_carbon_saved_g.toFixed(2)}g`,
            color: '#22c55e'
        },
        {
            label: 'Avg Renewable',
            value: `${(stats.avg_renewable_pct * 100).toFixed(1)}%`,
            color: '#f59e0b'
        }
    ];

    return (
        <div className="stats-cards">
            {cards.map((card, i) => (
                <div key={i} className="stat-card" style={{ borderTop: `3px solid ${card.color}` }}>
                    <div className="stat-value" style={{ marginTop: '0.5rem' }}>{card.value}</div>
                    <div className="stat-label">{card.label}</div>
                </div>
            ))}
        </div>
    );
}

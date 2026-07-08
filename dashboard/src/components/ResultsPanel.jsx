export default function ResultsPanel({ result }) {
    if (!result) return null;

    const meta = result.metadata || {};
    const mix = meta.energy_mix || {};
    const isOffset = result.budget_status === 'OFFSET_REQUIRED';

    const topSources = Object.entries(mix)
        .filter(([, v]) => v > 0.01)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 4);

    return (
        <div className="card results-card">
            <div className="card-header">
                <h2>Routing Result</h2>
                <span className={`status-badge ${isOffset ? 'status-warning' : 'status-ok'}`}>
                    {isOffset ? 'Offset Required' : 'Within Budget'}
                </span>
            </div>
            <div className="card-body">
                <div className="result-grid">
                    {/* Server Info */}
                    <div className="result-item">
                        <div className="result-label">Server Selected</div>
                        <div className="result-value">{meta.server_name}</div>
                        <div className="result-sub">{meta.server_region}</div>
                    </div>

                    {/* Carbon Used */}
                    <div className="result-item highlight-green">
                        <div className="result-label">Carbon Used</div>
                        <div className="result-value">{meta.carbon_used_g}g CO₂</div>
                        <div className="result-sub">{meta.energy_kwh} kWh</div>
                    </div>

                    {/* Carbon Saved */}
                    <div className="result-item highlight-blue">
                        <div className="result-label">Carbon Saved</div>
                        <div className="result-value">{meta.carbon_saved_g}g CO₂</div>
                        <div className="result-sub">vs worst option</div>
                    </div>

                    {/* Renewable % */}
                    <div className="result-item">
                        <div className="result-label">Renewable Energy</div>
                        <div className="result-value">{((meta.renewable_pct || 0) * 100).toFixed(1)}%</div>
                        <div className="result-sub">{meta.carbon_intensity_g_kwh} g/kWh</div>
                    </div>

                    {/* Latency */}
                    <div className="result-item">
                        <div className="result-label">Latency</div>
                        <div className="result-value">{meta.latency_ms}ms</div>
                    </div>

                    {/* Offset if needed */}
                    {isOffset && (
                        <div className="result-item highlight-yellow">
                            <div className="result-label">Offset Purchased</div>
                            <div className="result-value">{meta.offset_purchased_g}g CO₂</div>
                        </div>
                    )}
                </div>

                {/* Model Auto-Selection & Savings */}
                {result.model_selection && result.model_selection.action !== 'keep_original' && (
                    <div className="model-selection-section" style={{ marginTop: '20px', padding: '15px', backgroundColor: 'var(--bg-secondary)', borderRadius: '8px', borderLeft: '4px solid var(--accent-green)' }}>
                        <h3 style={{ marginTop: 0, marginBottom: '10px', fontSize: '1.1rem' }}>Model Auto-Selection</h3>
                        <p style={{ margin: '0 0 10px 0', fontSize: '0.95rem' }}>
                            {result.model_selection.reason}
                        </p>
                        <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
                            <span className="badge" style={{ padding: '4px 8px', borderRadius: '4px', background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>
                                <b>Original:</b> {result.model_selection.requested_model}
                            </span>
                            <span className="badge" style={{ padding: '4px 8px', borderRadius: '4px', background: 'var(--accent-green)22', color: 'var(--accent-green)', border: '1px solid var(--accent-green)55' }}>
                                <b>Selected:</b> {result.model_selection.effective_model}
                            </span>
                            {result.model_selection.energy_savings && (
                                <span className="badge highlight-green" style={{ padding: '4px 8px', borderRadius: '4px' }}>
                                    <b>Savings:</b> {result.model_selection.energy_savings.carbon_savings_pct}%
                                </span>
                            )}
                            {result.model_selection.quality_tradeoff && (
                                <span className="badge highlight-yellow" style={{ padding: '4px 8px', borderRadius: '4px' }}>
                                    <b>Quality Tradeoff:</b> -{result.model_selection.quality_tradeoff.quality_loss_pct}%
                                </span>
                            )}
                        </div>
                    </div>
                )}

                {/* Energy Mix Bar */}
                {topSources.length > 0 && (
                    <div className="energy-mix-section">
                        <h3>Energy Mix</h3>
                        <div className="energy-bar">
                            {topSources.map(([source, pct]) => (
                                <div
                                    key={source}
                                    className={`energy-segment energy-${source}`}
                                    style={{ width: `${pct * 100}%` }}
                                    title={`${source}: ${(pct * 100).toFixed(1)}%`}
                                >
                                    {pct > 0.08 && `${source} ${(pct * 100).toFixed(0)}%`}
                                </div>
                            ))}
                        </div>
                        <div className="energy-legend">
                            {topSources.map(([source, pct]) => (
                                <span key={source} className={`legend-item energy-${source}`}>
                                    {source}: {(pct * 100).toFixed(1)}%
                                </span>
                            ))}
                        </div>
                    </div>
                )}

                {/* Alternatives */}
                {result.alternatives && result.alternatives.length > 0 && (
                    <div className="alternatives-section">
                        <h3>Alternative Servers</h3>
                        <div className="alt-list">
                            {result.alternatives.map((alt, i) => (
                                <div key={i} className="alt-item">
                                    <span className="alt-name">{alt.name}</span>
                                    <span className="alt-carbon">{alt.predicted_carbon_g}g CO₂</span>
                                    <span className="alt-renewable">{((alt.renewable_pct || 0) * 100).toFixed(0)}% renewable</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

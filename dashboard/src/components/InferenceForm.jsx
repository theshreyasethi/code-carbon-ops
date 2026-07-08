import { useState } from 'react';
import { runInference } from '../services/api';
import ResultsPanel from './ResultsPanel';

const MODELS = [
    // OpenAI (2025-2026)
    { value: 'o3', label: 'OpenAI o3 (Reasoning)' },
    { value: 'o4-mini', label: 'OpenAI o4-mini (Reasoning)' },
    { value: 'gpt-4.5', label: 'GPT-4.5' },
    { value: 'gpt-4o', label: 'GPT-4o' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
    // Anthropic (2025-2026)
    { value: 'claude-4-opus', label: 'Claude 4 Opus' },
    { value: 'claude-4-sonnet', label: 'Claude 4 Sonnet' },
    { value: 'claude-3.5-sonnet', label: 'Claude 3.5 Sonnet' },
    { value: 'claude-3.5-haiku', label: 'Claude 3.5 Haiku' },
    // Google (2025-2026)
    { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro' },
    { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
    { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash' },
    // Meta (open-source)
    { value: 'llama-4-maverick', label: 'Llama 4 Maverick (400B)' },
    { value: 'llama-4-scout', label: 'Llama 4 Scout (109B)' },
    // Other
    { value: 'deepseek-r1', label: 'DeepSeek R1' },
    { value: 'mistral-large', label: 'Mistral Large' },
];

export default function InferenceForm({ onInferenceComplete }) {
    const [prompt, setPrompt] = useState('');
    const [model, setModel] = useState('gpt-4o');
    const [budget, setBudget] = useState(10);
    const [urgency, setUrgency] = useState(3);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');

    const URGENCY_LABELS = {
        1: { label: 'Critical', desc: 'Fastest server, ignore carbon' },
        2: { label: 'High', desc: 'Speed first, some carbon awareness' },
        3: { label: 'Balanced', desc: 'Balance speed, cost & carbon equally' },
        4: { label: 'Low', desc: 'Carbon matters more, can wait' },
        5: { label: 'Minimal', desc: 'Optimal carbon efficiency, no rush' },
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!prompt.trim()) {
            setError('Please enter a prompt');
            return;
        }

        setLoading(true);
        setError('');
        setResult(null);

        try {
            const res = await runInference({
                prompt: prompt.trim(),
                model,
                carbon_budget_g: parseFloat(budget),
                preferences: { urgency: parseInt(urgency) },
            });
            setResult(res.data);
            if (onInferenceComplete) onInferenceComplete();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to run inference. Is the backend running?');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="inference-section">
            <div className="card">
                <div className="card-header">
                    <h2>Test Carbon-Aware Inference</h2>
                </div>
                <div className="card-body">
                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label htmlFor="prompt">Prompt</label>
                            <textarea
                                id="prompt"
                                value={prompt}
                                onChange={(e) => setPrompt(e.target.value)}
                                placeholder="Enter your AI prompt here... e.g., 'Summarize climate change impacts on agriculture'"
                                rows={3}
                            />
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label htmlFor="model">Model</label>
                                <select id="model" value={model} onChange={(e) => setModel(e.target.value)}>
                                    {MODELS.map((m) => (
                                        <option key={m.value} value={m.value}>{m.label}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="form-group">
                                <label htmlFor="budget">Carbon Budget: {budget}g CO₂</label>
                                <input
                                    id="budget"
                                    type="range"
                                    min="1"
                                    max="100"
                                    value={budget}
                                    onChange={(e) => setBudget(e.target.value)}
                                />
                                <div className="range-labels">
                                    <span>1g</span>
                                    <span>50g</span>
                                    <span>100g</span>
                                </div>
                            </div>
                        </div>

                        <div className="form-group">
                            <label htmlFor="urgency">
                                Urgency: {URGENCY_LABELS[urgency].label}
                                <span className="urgency-desc"> — {URGENCY_LABELS[urgency].desc}</span>
                            </label>
                            <div className="urgency-slider-container">
                                <input
                                    id="urgency"
                                    type="range"
                                    min="1"
                                    max="5"
                                    step="1"
                                    value={urgency}
                                    onChange={(e) => setUrgency(e.target.value)}
                                    className="urgency-slider"
                                />
                                <div className="urgency-labels">
                                    <span>1 (Critical)</span>
                                    <span>2</span>
                                    <span>3 (Balanced)</span>
                                    <span>4</span>
                                    <span>5 (Minimal)</span>
                                </div>
                                <div className="urgency-weight-bar">
                                    <div className="weight-segment" style={{flex: urgency === '1' || urgency === 1 ? 45 : urgency === '2' || urgency === 2 ? 35 : urgency === '3' || urgency === 3 ? 25 : urgency === '4' || urgency === 4 ? 15 : 5, background: 'var(--accent-blue)'}}>
                                        <span>Latency {urgency == 1 ? 45 : urgency == 2 ? 35 : urgency == 3 ? 25 : urgency == 4 ? 15 : 5}%</span>
                                    </div>
                                    <div className="weight-segment" style={{flex: urgency == 1 ? 15 : urgency == 2 ? 20 : urgency == 3 ? 30 : urgency == 4 ? 40 : 50, background: 'var(--accent-green)'}}>
                                        <span>Carbon {urgency == 1 ? 15 : urgency == 2 ? 20 : urgency == 3 ? 30 : urgency == 4 ? 40 : 50}%</span>
                                    </div>
                                    <div className="weight-segment" style={{flex: urgency == 1 ? 10 : urgency == 2 ? 10 : urgency == 3 ? 15 : urgency == 4 ? 20 : 25, background: 'var(--accent-cyan)'}}>
                                        <span>Renewable {urgency == 1 ? 10 : urgency == 2 ? 10 : urgency == 3 ? 15 : urgency == 4 ? 20 : 25}%</span>
                                    </div>
                                    <div className="weight-segment" style={{flex: urgency == 1 ? 30 : urgency == 2 ? 35 : urgency == 3 ? 30 : urgency == 4 ? 25 : 20, background: 'var(--accent-amber)'}}>
                                        <span>Cost {urgency == 1 ? 30 : urgency == 2 ? 35 : urgency == 3 ? 30 : urgency == 4 ? 25 : 20}%</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {error && <div className="error-msg">{error}</div>}

                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            {loading ? 'Routing to optimal server...' : 'Execute Routing Policy'}
                        </button>
                    </form>
                </div>
            </div>

            {result && <ResultsPanel result={result} />}
        </div>
    );
}

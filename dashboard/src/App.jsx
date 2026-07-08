import { useState } from 'react';
import StatsCards from './components/StatsCards';
import CarbonTable from './components/CarbonTable';
import InferenceForm from './components/InferenceForm';
import PredictivePanel from './components/PredictivePanel';
import './App.css';

function App() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleInferenceComplete = () => {
    setRefreshKey((k) => k + 1);
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="header-title">
            <h1>CodeCarbonOps</h1>
            <span className="header-subtitle">Carbon-Aware Inference Router</span>
          </div>
          <div className="header-badge">
            <span className="pulse-dot"></span>
            Live Monitoring
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="app-main">
        {/* Stats Overview */}
        <section className="section">
          <StatsCards key={`stats-${refreshKey}`} />
        </section>

        {/* Inference Test */}
        <section className="section">
          <InferenceForm onInferenceComplete={handleInferenceComplete} />
        </section>

        {/* Predictive Forecasting */}
        <section className="section">
          <PredictivePanel key={`predict-${refreshKey}`} />
        </section>

        {/* Carbon Data Table */}
        <section className="section">
          <CarbonTable key={`carbon-${refreshKey}`} />
        </section>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>CodeCarbonOps — Routing computation to the most carbon-efficient servers worldwide</p>
      </footer>
    </div>
  );
}

export default App;

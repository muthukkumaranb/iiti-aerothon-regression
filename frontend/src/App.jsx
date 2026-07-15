import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine,
  BarChart, Bar
} from 'recharts';
import {
  Activity, Gauge, Cpu, BarChart3, Settings, Play, RefreshCw, AlertTriangle, ShieldCheck, Box
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [activeTab, setActiveTab] = useState('cockpit');
  const [engines, setEngines] = useState([]);
  const [selectedEngineId, setSelectedEngineId] = useState(1);
  const [selectedCycle, setSelectedCycle] = useState(1);
  const [historyData, setHistoryData] = useState([]);
  const [latestData, setLatestData] = useState(null);
  const [modelMetrics, setModelMetrics] = useState(null);
  const [selectedMetricModel, setSelectedMetricModel] = useState('compressor_health');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // What-If Form Inputs
  const [whatIfInputs, setWhatIfInputs] = useState({
    altitude_m: 5000,
    mach: 0.4,
    tamb_k: 250,
    pamb_pa: 50000,
    rpm_rev_min: 60000,
    fuel_flow_kg_s: 0.5,
    p2_pa: 100000,
    t2_k: 300,
    p3_pa: 100000,
    t3_k: 1100,
    p4_pa: 80000,
    t4_k: 950,
    cycle: 1
  });
  const [whatIfResults, setWhatIfResults] = useState(null);
  const [whatIfLoading, setWhatIfLoading] = useState(false);

  // Fetch initial engines list and model metrics
  useEffect(() => {
    async function initData() {
      try {
        const resEngines = await fetch(`${API_BASE}/engines/`);
        const enginesData = await resEngines.json();
        setEngines(enginesData);
        if (enginesData.length > 0) {
          setSelectedEngineId(enginesData[0].engine_id);
        }

        const resMetrics = await fetch(`${API_BASE}/model-metrics/`);
        const metricsData = await resMetrics.json();
        setModelMetrics(metricsData);
      } catch (err) {
        console.error("Failed to load initial data", err);
        setError("Failed to connect to HoloTwin Backend. Ensure the Django server is running.");
      }
    }
    initData();
  }, []);

  // Fetch engine history and latest data when selected engine changes
  useEffect(() => {
    if (!selectedEngineId) return;

    async function fetchEngineData() {
      setLoading(true);
      try {
        const resLatest = await fetch(`${API_BASE}/engines/${selectedEngineId}/latest/`);
        const latestJson = await resLatest.json();
        setLatestData(latestJson);
        setSelectedCycle(latestJson.cycle);

        const resHist = await fetch(`${API_BASE}/engines/${selectedEngineId}/history/`);
        const histJson = await resHist.json();
        setHistoryData(histJson);
      } catch (err) {
        console.error("Failed to fetch engine history", err);
      } finally {
        setLoading(false);
      }
    }
    fetchEngineData();
  }, [selectedEngineId]);

  // Handle engine change
  const handleEngineChange = (e) => {
    setSelectedEngineId(parseInt(e.target.value));
  };

  // Find record for currently scrubbed cycle
  const currentCycleRecord = historyData.find(d => d.cycle === selectedCycle) || latestData;

  // Run What-If simulation
  const handleWhatIfSubmit = async (e) => {
    e.preventDefault();
    setWhatIfLoading(true);
    try {
      const res = await fetch(`${API_BASE}/predict/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(whatIfInputs)
      });
      const data = await res.json();
      setWhatIfResults(data);
    } catch (err) {
      console.error("What-If simulation failed", err);
    } finally {
      setWhatIfLoading(false);
    }
  };

  // Helper to color-code health indicators
  const getHealthColor = (val) => {
    if (val >= 0.95) return 'var(--status-green)';
    if (val >= 0.85) return 'var(--status-amber)';
    return 'var(--status-red)';
  };

  if (error) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', gap: '1rem', padding: '2rem', textAlign: 'center' }}>
        <AlertTriangle size={48} color="var(--status-red)" />
        <h2 style={{ fontFamily: 'Orbitron', color: '#fff' }}>HoloTwin Server Offline</h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '500px' }}>{error}</p>
        <button className="submit-btn" onClick={() => window.location.reload()}>Retry Connection</button>
      </div>
    );
  }

  // Prep degradation chart data with extrapolations
  const chartData = historyData.map(d => ({
    cycle: d.cycle,
    OverallHealth: d.true_health.overall,
    PredictedOverallHealth: d.predicted_health.overall,
    CompressorHealth: d.true_health.compressor,
    CombustorHealth: d.true_health.combustor,
    TurbineHealth: d.true_health.turbine,
  }));

  // Append extrapolation trend lines if available
  if (latestData && latestData.extrapolations) {
    latestData.extrapolations.forEach(ext => {
      chartData.push({
        cycle: ext.cycle,
        ProjectedOverallHealth: ext.projected_health
      });
    });
  }

  return (
    <div className="hud-container">
      {/* Top HUD Header */}
      <header className="hud-header">
        <div className="hud-title-group">
          <Activity size={28} color="var(--color-compressor)" />
          <div>
            <h1 className="hud-title">HoloTwin</h1>
            <div className="hud-subtitle">Physics-Informed Digital Twin</div>
          </div>
        </div>

        <nav className="hud-nav">
          <button
            className={`hud-nav-btn ${activeTab === 'cockpit' ? 'active' : ''}`}
            onClick={() => setActiveTab('cockpit')}
          >
            Cockpit HUD
          </button>
          <button
            className={`hud-nav-btn ${activeTab === 'whatif' ? 'active' : ''}`}
            onClick={() => setActiveTab('whatif')}
          >
            What-If Simulator
          </button>
          <button
            className={`hud-nav-btn ${activeTab === 'metrics' ? 'active' : ''}`}
            onClick={() => setActiveTab('metrics')}
          >
            Twin Diagnostics
          </button>
        </nav>
      </header>

      {/* Control Bar (Engine Selector & Scrubber) */}
      {activeTab === 'cockpit' && latestData && (
        <div className="control-bar">
          <div className="control-group">
            <span className="control-label">Virtual Engine ID:</span>
            <select className="control-select" value={selectedEngineId} onChange={handleEngineChange}>
              {engines.map(eng => (
                <option key={eng.engine_id} value={eng.engine_id}>
                  Engine {eng.engine_id} (Latest Cycle: {eng.latest_cycle})
                </option>
              ))}
            </select>
          </div>

          <div className="scrubber-container">
            <span className="control-label">Timeline Scrubber:</span>
            <input
              type="range"
              min={1}
              max={latestData.cycle}
              value={selectedCycle}
              onChange={(e) => setSelectedCycle(parseInt(e.target.value))}
              className="scrubber-slider"
              style={{
                background: `linear-gradient(to right, var(--color-compressor) 0%, var(--color-compressor) ${((selectedCycle - 1) / (latestData.cycle - 1)) * 100}%, var(--bg-tertiary) ${((selectedCycle - 1) / (latestData.cycle - 1)) * 100}%, var(--bg-tertiary) 100%)`
              }}
            />
            <span className="control-label" style={{ minWidth: '80px', textAlign: 'right' }}>
              Cycle {selectedCycle} / {latestData.cycle}
            </span>
          </div>
        </div>
      )}

      {/* Tab Switcher Content */}
      <main className="tab-content">
        {activeTab === 'cockpit' && (
          loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh', gap: '1rem', flexDirection: 'column' }}>
              <RefreshCw className="animate-spin" size={32} color="var(--color-compressor)" style={{ animation: 'spin 1s linear infinite' }} />
              <div style={{ fontFamily: 'Orbitron', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Synchronizing Digital Twin State...</div>
            </div>
          ) : (
            currentCycleRecord && (
              <div className="dashboard-grid">

                {/* 1. Overall Health Index Gauge */}
                <section className="hud-panel" style={{ gridColumn: 'span 4', height: '270px' }}>
                  <h3 className="hud-panel-title">
                    <span>Overall Health Index</span>
                    <Gauge size={16} />
                  </h3>
                  <div className="overall-gauge-container">
                    <svg className="overall-gauge-svg">
                      <circle className="overall-gauge-bg" cx="75" cy="75" r="60" />
                      <circle
                        className="overall-gauge-value"
                        cx="75"
                        cy="75"
                        r="60"
                        stroke={getHealthColor(currentCycleRecord.predicted_health.overall)}
                        strokeDasharray={`${2 * Math.PI * 60}`}
                        strokeDashoffset={`${2 * Math.PI * 60 * (1 - currentCycleRecord.predicted_health.overall)}`}
                      />
                      <text className="overall-gauge-text" x="75" y="75">
                        {(currentCycleRecord.predicted_health.overall * 100).toFixed(1)}%
                      </text>
                    </svg>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.5rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                      Status: {currentCycleRecord.predicted_health.overall >= 0.95 ? 'Normal' : currentCycleRecord.predicted_health.overall >= 0.85 ? 'Degraded' : 'Critical'}
                    </div>
                  </div>
                </section>

                {/* 2. Subsystem Health Panel */}
                <section className="hud-panel" style={{ gridColumn: 'span 4', height: '270px' }}>
                  <h3 className="hud-panel-title">
                    <span>Subsystem Health Status</span>
                    <Cpu size={16} />
                  </h3>
                  <div className="subsystem-list">
                    {/* Compressor */}
                    <div className="subsystem-item">
                      <div className="subsystem-header">
                        <span className="subsystem-name" style={{ color: 'var(--color-compressor)' }}>
                          <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-compressor)' }}></span>
                          Compressor Stage
                        </span>
                        <span>{(currentCycleRecord.predicted_health.compressor * 100).toFixed(1)}%</span>
                      </div>
                      <div className="subsystem-bar-bg">
                        <div
                          className="subsystem-bar-fill"
                          style={{
                            width: `${currentCycleRecord.predicted_health.compressor * 100}%`,
                            backgroundColor: getHealthColor(currentCycleRecord.predicted_health.compressor)
                          }}
                        ></div>
                      </div>
                    </div>
                    {/* Combustor */}
                    <div className="subsystem-item">
                      <div className="subsystem-header">
                        <span className="subsystem-name" style={{ color: 'var(--color-combustor)' }}>
                          <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-combustor)' }}></span>
                          Combustor Chamber
                        </span>
                        <span>{(currentCycleRecord.predicted_health.combustor * 100).toFixed(1)}%</span>
                      </div>
                      <div className="subsystem-bar-bg">
                        <div
                          className="subsystem-bar-fill"
                          style={{
                            width: `${currentCycleRecord.predicted_health.combustor * 100}%`,
                            backgroundColor: getHealthColor(currentCycleRecord.predicted_health.combustor)
                          }}
                        ></div>
                      </div>
                    </div>
                    {/* Turbine */}
                    <div className="subsystem-item">
                      <div className="subsystem-header">
                        <span className="subsystem-name" style={{ color: 'var(--color-turbine)' }}>
                          <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-turbine)' }}></span>
                          Turbine Expander
                        </span>
                        <span>{(currentCycleRecord.predicted_health.turbine * 100).toFixed(1)}%</span>
                      </div>
                      <div className="subsystem-bar-bg">
                        <div
                          className="subsystem-bar-fill"
                          style={{
                            width: `${currentCycleRecord.predicted_health.turbine * 100}%`,
                            backgroundColor: getHealthColor(currentCycleRecord.predicted_health.turbine)
                          }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </section>

                {/* 3. Performance Prediction Card */}
                <section className="hud-panel" style={{ gridColumn: 'span 4', height: '270px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <h3 className="hud-panel-title">
                      <span>Performance Predictions</span>
                      <Activity size={16} />
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                      <div className="performance-stat">
                        <span className="sensor-label">Predicted Thrust</span>
                        <div className="performance-value">{currentCycleRecord.predicted_performance.value.toFixed(1)} N</div>
                        <div className="performance-range">
                          <ShieldCheck size={12} color="var(--color-compressor)" />
                          80% CI: [{currentCycleRecord.predicted_performance.low_ci.toFixed(0)} - {currentCycleRecord.predicted_performance.high_ci.toFixed(0)}] N
                        </div>
                      </div>
                      <div className="performance-stat">
                        <span className="sensor-label">Predicted TSFC</span>
                        <div className="performance-value" style={{ color: 'var(--color-combustor)' }}>{currentCycleRecord.predicted_tsfc.value.toFixed(5)} g/N/s</div>
                        <div className="performance-range">
                          <ShieldCheck size={12} color="var(--color-combustor)" />
                          80% CI: [{currentCycleRecord.predicted_tsfc.low_ci.toFixed(5)} - {currentCycleRecord.predicted_tsfc.high_ci.toFixed(5)}]
                        </div>
                      </div>
                    </div>
                  </div>
                </section>

                {/* 3D Digital Twin Model Panel */}
                <section className="hud-panel" style={{ gridColumn: 'span 7', height: '380px', display: 'flex', flexDirection: 'column' }}>
                  <h3 className="hud-panel-title">
                    <span>Interactive 3D Engine Model</span>
                    <Box size={16} />
                  </h3>
                  <div style={{ flexGrow: 1, width: '100%', position: 'relative', borderRadius: '6px', overflow: 'hidden', border: '1px solid var(--border-color)' }}>
                    <iframe
                      title="Turbojet Engine Demonstration"
                      frameBorder="0"
                      allowFullScreen
                      mozallowfullscreen="true"
                      webkitallowfullscreen="true"
                      allow="autoplay; fullscreen; xr-spatial-tracking"
                      xr-spatial-tracking="true"
                      execution-while-out-of-viewport="true"
                      execution-while-not-rendered="true"
                      web-share="true"
                      src="https://sketchfab.com/models/dc1621a57fc744fba9f5506225dbfe90/embed?autostart=1&preload=1&ui_theme=dark&ui_hint=0&ui_infos=0"
                      style={{ width: '100%', height: '100%', border: 'none' }}
                    />
                  </div>
                </section>

                {/* 4. Operating Conditions Panel */}
                <section className="hud-panel" style={{ gridColumn: 'span 5', height: '380px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <h3 className="hud-panel-title">
                    <span>Operating Conditions & Raw Sensors</span>
                    <Settings size={16} />
                  </h3>
                  <div className="sensor-grid" style={{ flexGrow: 1, alignContent: 'center' }}>
                    <div className="sensor-card">
                      <div className="sensor-label">Altitude</div>
                      <div className="sensor-value">
                        {(currentCycleRecord.operating_conditions.altitude_m / 1000).toFixed(2)}
                        <span className="sensor-unit">km</span>
                      </div>
                    </div>
                    <div className="sensor-card">
                      <div className="sensor-label">Mach Speed</div>
                      <div className="sensor-value">
                        {currentCycleRecord.operating_conditions.mach.toFixed(3)}
                        <span className="sensor-unit">M</span>
                      </div>
                    </div>
                    <div className="sensor-card">
                      <div className="sensor-label">Ambient Temp</div>
                      <div className="sensor-value">
                        {currentCycleRecord.operating_conditions.tamb_k.toFixed(1)}
                        <span className="sensor-unit">K</span>
                      </div>
                    </div>
                    <div className="sensor-card">
                      <div className="sensor-label">Ambient Press</div>
                      <div className="sensor-value">
                        {(currentCycleRecord.operating_conditions.pamb_pa / 1000).toFixed(1)}
                        <span className="sensor-unit">kPa</span>
                      </div>
                    </div>
                    <div className="sensor-card">
                      <div className="sensor-label">Shaft Speed</div>
                      <div className="sensor-value">
                        {currentCycleRecord.operating_conditions.rpm_rev_min.toFixed(0)}
                        <span className="sensor-unit">RPM</span>
                      </div>
                    </div>
                    <div className="sensor-card">
                      <div className="sensor-label">Fuel Flow</div>
                      <div className="sensor-value">
                        {currentCycleRecord.operating_conditions.fuel_flow_kg_s.toFixed(3)}
                        <span className="sensor-unit">kg/s</span>
                      </div>
                    </div>
                  </div>
                </section>

                {/* 5. Historical & Extrapolation Chart */}
                <section className="hud-panel" style={{ gridColumn: 'span 12' }}>
                  <h3 className="hud-panel-title">
                    <span>Engine Health Degradation & Projected Trend</span>
                    <BarChart3 size={16} />
                  </h3>
                  <div style={{ width: '100%', height: '260px' }}>
                    <ResponsiveContainer>
                      <LineChart data={chartData} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                        <XAxis dataKey="cycle" stroke="var(--text-secondary)" label={{ value: 'Cycle', position: 'insideBottomRight', offset: -5 }} />
                        <YAxis domain={[0.6, 1.05]} stroke="var(--text-secondary)" />
                        <Tooltip contentStyle={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-color)' }} />
                        <Legend verticalAlign="top" height={36} />

                        <Line type="monotone" dataKey="OverallHealth" name="True Overall Health" stroke="var(--status-green)" strokeWidth={2} dot={false} activeDot={{ r: 6 }} />
                        <Line type="monotone" dataKey="PredictedOverallHealth" name="Predicted Health" stroke="var(--color-compressor)" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="ProjectedOverallHealth" name="Projected Health (Extrapolated)" stroke="var(--status-red)" strokeWidth={2} strokeDasharray="5 5" dot={false} />

                        <ReferenceLine x={selectedCycle} stroke="var(--text-muted)" label={`Cycle ${selectedCycle}`} strokeDasharray="3 3" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </section>

              </div>
            )
          )
        )}

        {/* Tab: What-If Simulation */}
        {activeTab === 'whatif' && (
          <div className="whatif-container">
            <section className="hud-panel">
              <h3 className="hud-panel-title">
                <span>Ad-Hoc Physics Simulator</span>
                <Play size={16} />
              </h3>
              <form onSubmit={handleWhatIfSubmit}>
                <div className="whatif-grid">
                  {Object.keys(whatIfInputs).map((key) => (
                    <div className="form-group" key={key}>
                      <label className="form-label">{key.replace('_', ' ').toUpperCase()}</label>
                      <input
                        type="number"
                        step="any"
                        value={whatIfInputs[key]}
                        onChange={(e) => setWhatIfInputs({ ...whatIfInputs, [key]: parseFloat(e.target.value) })}
                        className="form-input"
                        required
                      />
                    </div>
                  ))}
                </div>
                <button type="submit" className="submit-btn" disabled={whatIfLoading}>
                  {whatIfLoading ? 'Running Simulator...' : 'Run Simulation'}
                </button>
              </form>

              {whatIfResults && (
                <div style={{ marginTop: '2.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '2rem' }}>
                  <h4 style={{ fontFamily: 'Orbitron', fontSize: '1rem', marginBottom: '1.5rem', color: 'var(--color-compressor)' }}>
                    Simulation Outputs (Digital Twin Cascade Results)
                  </h4>

                  <div className="whatif-results-grid">
                    <div className="sensor-card">
                      <div className="sensor-label">Compressor Health</div>
                      <div className="sensor-value" style={{ color: getHealthColor(whatIfResults.predicted_compressor_health) }}>
                        {(whatIfResults.predicted_compressor_health * 100).toFixed(2)}%
                      </div>
                    </div>
                    <div className="sensor-card">
                      <div className="sensor-label">Combustor Health</div>
                      <div className="sensor-value" style={{ color: getHealthColor(whatIfResults.predicted_combustor_health) }}>
                        {(whatIfResults.predicted_combustor_health * 100).toFixed(2)}%
                      </div>
                    </div>
                    <div className="sensor-card">
                      <div className="sensor-label">Turbine Health</div>
                      <div className="sensor-value" style={{ color: getHealthColor(whatIfResults.predicted_turbine_health) }}>
                        {(whatIfResults.predicted_turbine_health * 100).toFixed(2)}%
                      </div>
                    </div>
                    <div className="sensor-card">
                      <div className="sensor-label">Overall Health</div>
                      <div className="sensor-value" style={{ color: getHealthColor(whatIfResults.predicted_overall_health) }}>
                        {(whatIfResults.predicted_overall_health * 100).toFixed(2)}%
                      </div>
                    </div>
                    <div className="sensor-card">
                      <div className="sensor-label">Predicted Thrust</div>
                      <div className="sensor-value">
                        {whatIfResults.predicted_thrust.value.toFixed(1)} N
                      </div>
                      <div className="performance-range">
                        80% CI: [{whatIfResults.predicted_thrust.low_ci.toFixed(0)} - {whatIfResults.predicted_thrust.high_ci.toFixed(0)}] N
                      </div>
                    </div>
                    <div className="sensor-card">
                      <div className="sensor-label">Predicted TSFC</div>
                      <div className="sensor-value">
                        {whatIfResults.predicted_tsfc.value.toFixed(5)}
                      </div>
                      <div className="performance-range">
                        80% CI: [{whatIfResults.predicted_tsfc.low_ci.toFixed(5)} - {whatIfResults.predicted_tsfc.high_ci.toFixed(5)}]
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </section>
          </div>
        )}

        {/* Tab: Twin Diagnostics (Model Metrics) */}
        {activeTab === 'metrics' && modelMetrics && (
          <div className="whatif-container" style={{ maxWidth: '1100px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '1.5rem' }}>

              {/* Models Summary Table */}
              <section className="hud-panel" style={{ gridColumn: 'span 12' }}>
                <h3 className="hud-panel-title">Model Generalization & Validation Metrics (Held-Out Engine 10)</h3>
                <table className="metrics-table">
                  <thead>
                    <tr>
                      <th>Target Model</th>
                      <th>RMSE</th>
                      <th>MAE</th>
                      <th>MAPE</th>
                      <th>R² Score</th>
                      <th>Inference Latency</th>
                      <th>Model Size</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.keys(modelMetrics).map((modelKey) => {
                      const model = modelMetrics[modelKey];
                      return (
                        <tr
                          key={modelKey}
                          style={{ cursor: 'pointer', backgroundColor: selectedMetricModel === modelKey ? 'rgba(56, 189, 248, 0.05)' : '' }}
                          onClick={() => setSelectedMetricModel(modelKey)}
                        >
                          <td style={{ fontWeight: '600', textTransform: 'capitalize', color: 'var(--color-compressor)' }}>
                            {modelKey.replace('_', ' ')}
                          </td>
                          <td>{model.rmse ? model.rmse.toFixed(5) : 'N/A'}</td>
                          <td>{model.mae ? model.mae.toFixed(5) : 'N/A'}</td>
                          <td>{model.mape ? `${model.mape.toFixed(3)}%` : 'N/A'}</td>
                          <td style={{ color: model.r2 >= 0.85 ? 'var(--status-green)' : model.r2 >= 0 ? 'var(--status-amber)' : 'var(--status-red)' }}>
                            {model.r2 ? model.r2.toFixed(4) : 'N/A'}
                          </td>
                          <td>{model.latency_ms ? `${model.latency_ms.toFixed(2)} ms` : 'N/A'}</td>
                          <td>{model.model_size_kb ? `${model.model_size_kb.toFixed(1)} KB` : 'N/A'}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </section>

              {/* Feature Importance Panel */}
              {modelMetrics[selectedMetricModel] && modelMetrics[selectedMetricModel].feature_importances && (
                <section className="hud-panel" style={{ gridColumn: 'span 12' }}>
                  <h3 className="hud-panel-title">
                    <span>Feature Importances: {selectedMetricModel.replace('_', ' ').toUpperCase()}</span>
                    <BarChart3 size={16} />
                  </h3>
                  <div style={{ width: '100%', height: '300px' }}>
                    <ResponsiveContainer>
                      <BarChart
                        layout="vertical"
                        data={
                          Object.entries(modelMetrics[selectedMetricModel].feature_importances)
                            .map(([name, val]) => ({ name, value: val }))
                            .sort((a, b) => b.value - a.value)
                        }
                        margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                        <XAxis type="number" stroke="var(--text-secondary)" />
                        <YAxis type="category" dataKey="name" stroke="var(--text-secondary)" width={120} />
                        <Tooltip contentStyle={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-color)' }} />
                        <Bar dataKey="value" fill="var(--color-compressor)" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </section>
              )}

            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;

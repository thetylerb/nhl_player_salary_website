import React, { useState, useCallback } from 'react';
import './App.css';
import PlayerSearch from './components/PlayerSearch';
import PlayerCard from './components/PlayerCard';
import SalaryEstimate from './components/SalaryEstimate';
import ComparablesTable from './components/ComparablesTable';
import StatSliders from './components/StatSliders';
import { estimateSalary } from './services/api';

const SKATER_WEIGHTS = {
  goals_per_60: 1.0,
  assists_per_60: 0.8,
  points_per_60: 1.0,
  toi_per_game: 0.7,
  corsi_for_pct: 0.5,
  xgf_pct: 0.6,
  penalty_diff_per_60: 0.3,
};

const GOALIE_WEIGHTS = {
  save_pct: 1.0,
  gaa: 0.9,
  quality_start_pct: 0.7,
  games_started: 0.4,
};

export default function App() {
  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [weights, setWeights] = useState(SKATER_WEIGHTS);
  const [faStatus, setFaStatus] = useState('auto');
  const [positionFilter, setPositionFilter] = useState(true);
  const [selectedPlayer, setSelectedPlayer] = useState(null);

  const runEstimate = useCallback(async (playerId, w, fa, posFilter) => {
    setLoading(true);
    setError(null);
    try {
      const result = await estimateSalary({
        player_id: playerId,
        weights: w,
        fa_status: fa,
        position_filter: posFilter,
        n_comparables: 10,
      });
      setEstimate(result);
    } catch (err) {
      const msg = err?.response?.data?.error || err.message || 'Failed to estimate salary';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  const handlePlayerSelect = useCallback((player) => {
    setSelectedPlayer(player);
    const isGoalie = player.position === 'G';
    const defaultWeights = isGoalie ? GOALIE_WEIGHTS : SKATER_WEIGHTS;
    setWeights(defaultWeights);
    runEstimate(player.nhl_id, defaultWeights, faStatus, positionFilter);
  }, [faStatus, positionFilter, runEstimate]);

  const handleWeightsChange = useCallback((newWeights) => {
    setWeights(newWeights);
    if (selectedPlayer) {
      runEstimate(selectedPlayer.nhl_id, newWeights, faStatus, positionFilter);
    }
  }, [selectedPlayer, faStatus, positionFilter, runEstimate]);

  const handleFaChange = useCallback((val) => {
    setFaStatus(val);
    if (selectedPlayer) {
      runEstimate(selectedPlayer.nhl_id, weights, val, positionFilter);
    }
  }, [selectedPlayer, weights, positionFilter, runEstimate]);

  const handlePosFilterChange = useCallback((val) => {
    setPositionFilter(val);
    if (selectedPlayer) {
      runEstimate(selectedPlayer.nhl_id, weights, faStatus, val);
    }
  }, [selectedPlayer, weights, faStatus, runEstimate]);

  const playerPosition = estimate?.player?.position || selectedPlayer?.position || 'C';
  const isGoalie = playerPosition === 'G';

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-icon">🏒</span>
            <h1>NHL Salary Estimator</h1>
          </div>
          <p className="subtitle">AI-powered contract valuation — comparables engine + regression model</p>
        </div>
      </header>

      <main className="App-main">
        <div className="search-section">
          <PlayerSearch onPlayerSelect={handlePlayerSelect} />
        </div>

        {loading && (
          <div className="loading-overlay">
            <div className="loading-spinner" />
            <p>Analyzing player data...</p>
          </div>
        )}

        {error && !loading && (
          <div className="error-banner">⚠️ {error}</div>
        )}

        {estimate && !loading && (
          <div className="results-grid">
            <div className="results-top">
              <PlayerCard player={estimate.player} salary={estimate.current_salary} verdict={estimate.verdict} />
            </div>

            <div className="results-body">
              <div className="estimates-column">
                <SalaryEstimate
                  comparablesEstimate={estimate.comparables_estimate}
                  regressionEstimate={estimate.regression_estimate}
                  currentSalary={estimate.current_salary}
                  verdict={estimate.verdict}
                />
              </div>
              <div className="controls-column">
                <StatSliders
                  weights={weights}
                  isGoalie={isGoalie}
                  onWeightsChange={handleWeightsChange}
                  faStatus={faStatus}
                  onFaStatusChange={handleFaChange}
                  positionFilter={positionFilter}
                  onPositionFilterChange={handlePosFilterChange}
                />
              </div>
            </div>

            <div className="comparables-section">
              <ComparablesTable comparables={estimate.comparables} isGoalie={isGoalie} />
            </div>
          </div>
        )}

        {!estimate && !loading && !error && (
          <div className="hero-placeholder">
            <div className="hero-icon">🏒</div>
            <h2>Search any NHL player to get started</h2>
            <p>Get AI-powered salary estimates based on comparable players and statistical modeling</p>
            <div className="hero-features">
              <div className="feature"><span className="feature-icon">📊</span><span>Statistical comparables</span></div>
              <div className="feature"><span className="feature-icon">🤖</span><span>Regression model</span></div>
              <div className="feature"><span className="feature-icon">⚖️</span><span>Fair value verdict</span></div>
              <div className="feature"><span className="feature-icon">🎚️</span><span>Adjustable weights</span></div>
            </div>
          </div>
        )}
      </main>

      <footer className="App-footer">
        <p>Data: NHL Stats API · MoneyPuck · PuckPedia · Estimates are not official contract valuations.</p>
      </footer>
    </div>
  );
}

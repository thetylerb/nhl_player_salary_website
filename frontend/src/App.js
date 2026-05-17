import React, { useState, useCallback } from 'react';
import './App.css';
import PlayerSearch from './components/PlayerSearch';
import PlayerCard from './components/PlayerCard';
import SalaryEstimate from './components/SalaryEstimate';
import ComparablesTable from './components/ComparablesTable';
import StatSliders from './components/StatSliders';
import AdminPage from './components/AdminPage';
import { estimateSalary } from './services/api';

if (window.location.hash === '#admin') {
  document.title = 'Admin — NHL Salary Estimator';
}

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

function Topbar() {
  return (
    <header className="topbar">
      <div className="topbar-inner">
        <div className="brand">
          <div className="brand-mark">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M2 11.5 L11 2.5 M2 9 L4.5 11.5 M9.5 2.5 L12 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
              <circle cx="3" cy="11" r="1.2" fill="currentColor"/>
            </svg>
          </div>
          <div className="brand-text">
            <span className="brand-name">Capwire Analytics</span>
            <span className="brand-sub">NHL · Salary Engine · v2.4</span>
          </div>
        </div>

        <nav className="nav">
          <a href="#" className="active">Estimator</a>
          <a href="#">League View</a>
          <a href="#">Free Agents</a>
          <a href="#">Contracts</a>
          <a href="#">Model</a>
        </nav>

        <div className="ticker">
          <div className="ticker-item">
            <span className="live-dot" />
            <span className="ticker-k">Live</span>
          </div>
          <div className="ticker-item">
            <span className="ticker-k">Cap</span>
            <span className="ticker-v">$92.4M</span>
          </div>
          <div className="ticker-item">
            <span className="ticker-k">Avg AAV</span>
            <span className="ticker-v">$3.81M</span>
          </div>
          <div className="ticker-item">
            <span className="ticker-k">Model RMSE</span>
            <span className="ticker-v">±$1.2M</span>
          </div>
          <div className="ticker-item">
            <span className="ticker-k">Build</span>
            <span className="ticker-v">2026.05.17</span>
          </div>
        </div>
      </div>
    </header>
  );
}

function HeroSection() {
  return (
    <section className="hero">
      <div>
        <h1 className="hero-title">Salary Estimator <em>/ Contract Valuation</em></h1>
        <p className="hero-sub">
          A comparables engine and a regression model trained on 12 seasons of NHL contracts.
          Search any player to project fair-market value.
        </p>
      </div>
      <div className="hero-meta">
        <div><span>Players indexed</span><b>1,284</b></div>
        <div><span>Contracts (active)</span><b>728</b></div>
        <div><span>Sample window</span><b>2013 – 2026</b></div>
      </div>
    </section>
  );
}

function HeroPlaceholder() {
  return (
    <div className="hero-placeholder">
      <p className="hero-placeholder-title">Search any NHL player to get started</p>
      <p className="hero-placeholder-sub">
        Get AI-powered salary estimates based on comparable players and statistical modeling
      </p>
      <div className="hero-features">
        <span className="feature">Statistical comparables</span>
        <span className="feature">Regression model</span>
        <span className="feature">Fair value verdict</span>
        <span className="feature">Adjustable weights</span>
      </div>
    </div>
  );
}

function PageFooter() {
  return (
    <footer className="footer">
      <div>Data · MoneyPuck · PuckPedia · NHL Stats API</div>
      <div>
        Estimates are not official contract valuations ·{' '}
        <a href="#admin">Admin</a>
      </div>
    </footer>
  );
}

function MainApp() {
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
    <>
      <Topbar />
      <main className="page">
        <HeroSection />

        <PlayerSearch onPlayerSelect={handlePlayerSelect} />

        {loading && (
          <div className="loading-overlay">
            <div className="loading-spinner" />
            <span>Analyzing player data…</span>
          </div>
        )}

        {error && !loading && (
          <div className="error-banner">⚠ {error}</div>
        )}

        {estimate && !loading && (
          <>
            {/* Top grid: player card + comparables estimate */}
            <section className="grid-top">
              <PlayerCard
                player={estimate.player}
                salary={estimate.current_salary}
                verdict={estimate.verdict}
              />
              <SalaryEstimate
                type="comparables"
                result={estimate.comparables_estimate}
                currentSalary={estimate.current_salary}
              />
            </section>

            {/* Mid grid: regression + cap context + sliders */}
            <section className="grid-mid">
              <SalaryEstimate
                type="regression"
                result={estimate.regression_estimate}
                currentSalary={estimate.current_salary}
              />
              <CapContext
                currentSalary={estimate.current_salary}
                comparablesEstimate={estimate.comparables_estimate}
                regressionEstimate={estimate.regression_estimate}
              />
              <StatSliders
                weights={weights}
                isGoalie={isGoalie}
                onWeightsChange={handleWeightsChange}
                faStatus={faStatus}
                onFaStatusChange={handleFaChange}
                positionFilter={positionFilter}
                onPositionFilterChange={handlePosFilterChange}
                loading={loading}
              />
            </section>

            {/* Comparables table */}
            <section>
              <ComparablesTable comparables={estimate.comparables} isGoalie={isGoalie} />
            </section>
          </>
        )}

        {!estimate && !loading && !error && <HeroPlaceholder />}

        <PageFooter />
      </main>
    </>
  );
}

const CAP_CEILING = 20_000_000;
const CAP_YEAR = '$92.4M';

function fmtM(n) {
  if (!n && n !== 0) return '—';
  return `$${(n / 1_000_000).toFixed(2)}M`;
}

function CapContext({ currentSalary, comparablesEstimate, regressionEstimate }) {
  const cur = currentSalary?.aav || 0;
  const comp = comparablesEstimate?.estimate || 0;
  const reg = regressionEstimate?.estimate || 0;
  const consensus = comp && reg ? (comp + reg) / 2 : comp || reg;

  const pct = (v) => Math.min(100, (v / CAP_CEILING) * 100).toFixed(1);
  const consPct = pct(consensus);

  function confBars(level) {
    const on = level === 'high' ? 3 : level === 'medium' ? 2 : 1;
    return [0,1,2,3].map((i) => <i key={i} className={i < on ? 'on' : 'off'} />);
  }

  return (
    <article className="card est-card">
      <div className="card-head">
        <div className="card-title"><span className="ix">04</span> Cap Context</div>
        <div className="card-tag">2026 ceiling · {fmtM(CAP_CEILING)}</div>
      </div>
      <div className="est-body">
        <div className="est-readout">
          <span className="est-value">{consPct}%</span>
          <span className="est-err">of '26 cap at consensus</span>
        </div>
        <div className="est-sub">Stacked horizontal scale, $0M → {fmtM(CAP_CEILING)} cap</div>

        <div className="stack-list">
          {cur > 0 && (
            <div className="stack-row">
              <div className="stack-top">
                <span className="lbl">Current</span>
                <b>{fmtM(cur)} · {pct(cur)}%</b>
              </div>
              <div className="stack-bar"><i className="cur" style={{ width: `${pct(cur)}%` }} /></div>
            </div>
          )}
          {comp > 0 && (
            <div className="stack-row">
              <div className="stack-top">
                <span className="lbl">Comparables</span>
                <b>{fmtM(comp)} · {pct(comp)}%</b>
              </div>
              <div className="stack-bar"><i className="comp" style={{ width: `${pct(comp)}%` }} /></div>
            </div>
          )}
          {reg > 0 && (
            <div className="stack-row">
              <div className="stack-top">
                <span className="lbl">Regression</span>
                <b>{fmtM(reg)} · {pct(reg)}%</b>
              </div>
              <div className="stack-bar"><i className="reg" style={{ width: `${pct(reg)}%` }} /></div>
            </div>
          )}
          {consensus > 0 && (
            <div className="stack-row">
              <div className="stack-top" style={{ color: 'var(--signal-2)' }}>
                <span className="lbl">Consensus</span>
                <b style={{ color: 'var(--signal-2)' }}>{fmtM(consensus)} · {consPct}%</b>
              </div>
              <div className="stack-bar"><i className="cons" style={{ width: `${consPct}%` }} /></div>
            </div>
          )}
          <div className="stack-row">
            <div className="stack-top" style={{ color: 'var(--ink-4)' }}>
              <span className="lbl">'26 cap ceiling</span>
              <span>{fmtM(CAP_CEILING)}</span>
            </div>
            <div className="stack-bar"><i className="ceil" style={{ width: '100%' }} /></div>
          </div>
        </div>

        <div className="stack-axis">
          <span>$0M</span><span>$5M</span><span>$10M</span><span>$15M</span><span>$20M</span>
        </div>
      </div>
      <div className="est-foot">
        <div>Cap year {CAP_YEAR}</div>
        <span className="conf-pill">
          <span className="b">{confBars('medium')}</span>
          Speculative
        </span>
      </div>
    </article>
  );
}

export default function App() {
  if (window.location.hash === '#admin') return <AdminPage />;
  return <MainApp />;
}

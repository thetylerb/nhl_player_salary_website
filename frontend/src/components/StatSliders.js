import React, { useCallback } from 'react';

const SKATER_LABELS = {
  goals_per_60:        { main: 'Goals',        sub: '/ 60' },
  assists_per_60:      { main: 'Assists',       sub: '/ 60' },
  points_per_60:       { main: 'Points',        sub: '/ 60' },
  toi_per_game:        { main: 'TOI',           sub: '/ game' },
  corsi_for_pct:       { main: 'Corsi',         sub: 'For %' },
  xgf_pct:             { main: 'xGF',           sub: '%' },
  penalty_diff_per_60: { main: 'Penalty Diff',  sub: '/ 60' },
};

const GOALIE_LABELS = {
  save_pct:           { main: 'Save %',         sub: '' },
  gaa:                { main: 'GAA',            sub: '' },
  quality_start_pct:  { main: 'Quality Start',  sub: '%' },
  games_started:      { main: 'Games Started',  sub: '' },
};

const SKATER_DEFAULTS = {
  goals_per_60: 1.0, assists_per_60: 0.8, points_per_60: 1.0,
  toi_per_game: 0.7, corsi_for_pct: 0.5, xgf_pct: 0.6, penalty_diff_per_60: 0.3,
};

const GOALIE_DEFAULTS = {
  save_pct: 1.0, gaa: 0.9, quality_start_pct: 0.7, games_started: 0.4,
};

export default function StatSliders({
  weights, isGoalie, onWeightsChange,
  faStatus, onFaStatusChange,
  positionFilter, onPositionFilterChange,
  loading,
}) {
  const labels = isGoalie ? GOALIE_LABELS : SKATER_LABELS;
  const defaults = isGoalie ? GOALIE_DEFAULTS : SKATER_DEFAULTS;

  const handleSlider = useCallback((key, val) => {
    onWeightsChange({ ...weights, [key]: parseFloat(val) });
  }, [weights, onWeightsChange]);

  const handleReset = () => onWeightsChange({ ...defaults });

  return (
    <article className="card sliders">
      <div className="card-head">
        <div className="card-title"><span className="ix">05</span> Stat Weights</div>
        <div className="card-tag">Live</div>
      </div>

      <div className="sliders-head">
        <div className="ctrl-row">
          <span className="ctrl-label">FA Status</span>
          <div className="seg">
            {['auto', 'RFA', 'UFA'].map((opt) => (
              <button
                key={opt}
                className={faStatus === opt ? 'on' : ''}
                onClick={() => onFaStatusChange(opt)}
              >
                {opt === 'auto' ? 'Auto' : opt}
              </button>
            ))}
          </div>
        </div>
        <div className="ctrl-row">
          <span className="ctrl-label">Position Filter</span>
          <div className="seg">
            <button className={positionFilter ? 'on' : ''} onClick={() => onPositionFilterChange(true)}>On</button>
            <button className={!positionFilter ? 'on' : ''} onClick={() => onPositionFilterChange(false)}>Off</button>
          </div>
        </div>
      </div>

      <div className="sliders-body">
        <div className="sliders-list">
          {Object.entries(labels).map(([key, { main, sub }]) => {
            const val = weights[key] ?? 0.5;
            const pct = (val / 2) * 100; // 0–2 range → 0–100%
            return (
              <div className="slider-row" key={key}>
                <div className="slider-row-top">
                  <span className="slider-key">
                    {main}
                    {sub && <span className="slider-key-sub">{sub}</span>}
                  </span>
                  <span className="slider-val">{val.toFixed(1)}</span>
                </div>
                <div className="slider-track">
                  <div className="slider-rail" />
                  <div className="slider-rail-fill" style={{ width: `${pct}%` }} />
                  <div className="slider-thumb" style={{ left: `${pct}%` }} />
                  <input
                    className="slider-native"
                    type="range"
                    min="0"
                    max="2"
                    step="0.1"
                    value={val}
                    onChange={(e) => handleSlider(key, e.target.value)}
                  />
                  <div className="slider-ticks">
                    <span>0</span><span>1</span><span>2</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="sliders-foot">
        <button className="reset-btn" onClick={handleReset}>↺ Reset</button>
        {loading && (
          <div className="recalc-tag">
            <span className="live-dot" />
            Recalculating…
          </div>
        )}
      </div>
    </article>
  );
}

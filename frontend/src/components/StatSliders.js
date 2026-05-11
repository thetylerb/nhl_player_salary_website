import React, { useCallback } from 'react';
import './StatSliders.css';

const SKATER_LABELS = {
  goals_per_60:       'Goals / 60',
  assists_per_60:     'Assists / 60',
  points_per_60:      'Points / 60',
  toi_per_game:       'TOI / Game',
  corsi_for_pct:      'Corsi For %',
  xgf_pct:            'xGF %',
  penalty_diff_per_60:'Penalty Differential / 60',
};

const GOALIE_LABELS = {
  save_pct:           'Save %',
  gaa:                'GAA',
  quality_start_pct:  'Quality Start %',
  games_started:      'Games Started',
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
}) {
  const labels = isGoalie ? GOALIE_LABELS : SKATER_LABELS;
  const defaults = isGoalie ? GOALIE_DEFAULTS : SKATER_DEFAULTS;

  const handleSlider = useCallback((key, val) => {
    onWeightsChange({ ...weights, [key]: parseFloat(val) });
  }, [weights, onWeightsChange]);

  const handleReset = () => onWeightsChange({ ...defaults });

  return (
    <div className="sliders-card">
      <div className="sliders-header">
        <span className="sliders-title">Stat Weights</span>
        <button className="reset-btn" onClick={handleReset}>Reset</button>
      </div>

      <div className="sliders-controls">
        <div className="control-row">
          <span className="control-label">FA Status</span>
          <div className="toggle-group">
            {['auto', 'RFA', 'UFA'].map((opt) => (
              <button
                key={opt}
                className={`toggle-btn ${faStatus === opt ? 'active' : ''}`}
                onClick={() => onFaStatusChange(opt)}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>

        <div className="control-row">
          <span className="control-label">Position filter</span>
          <div className="toggle-group">
            <button
              className={`toggle-btn ${positionFilter ? 'active' : ''}`}
              onClick={() => onPositionFilterChange(true)}
            >
              On
            </button>
            <button
              className={`toggle-btn ${!positionFilter ? 'active' : ''}`}
              onClick={() => onPositionFilterChange(false)}
            >
              Off
            </button>
          </div>
        </div>
      </div>

      <div className="sliders-body">
        {Object.entries(labels).map(([key, label]) => {
          const val = weights[key] ?? 0.5;
          return (
            <div className="slider-row" key={key}>
              <div className="slider-row-top">
                <span className="slider-key">{label}</span>
                <span className="slider-val">{val.toFixed(1)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={val}
                onChange={(e) => handleSlider(key, e.target.value)}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}

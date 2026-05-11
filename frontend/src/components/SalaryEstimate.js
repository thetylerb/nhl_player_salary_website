import React from 'react';
import './SalaryEstimate.css';

function fmtM(n) {
  if (!n && n !== 0) return '—';
  return `$${(n / 1_000_000).toFixed(2)}M`;
}

function RangeBar({ low, high, estimate, current }) {
  if (!low || !high) return null;
  const min = Math.min(low, current || low) * 0.9;
  const max = Math.max(high, current || high) * 1.1;
  const span = max - min || 1;

  const pct = (v) => Math.max(0, Math.min(100, ((v - min) / span) * 100));

  const fillLeft = pct(low);
  const fillWidth = pct(high) - fillLeft;

  return (
    <div className="range-bar-wrap">
      <div className="range-bar-labels">
        <span>{fmtM(low)}</span>
        <span>est. {fmtM(estimate)}</span>
        <span>{fmtM(high)}</span>
      </div>
      <div className="range-bar-track">
        <div
          className="range-bar-fill"
          style={{ left: `${fillLeft}%`, width: `${fillWidth}%` }}
        />
        {current && (
          <div
            className="range-bar-current"
            style={{ left: `${pct(current)}%` }}
            title={`Current: ${fmtM(current)}`}
          />
        )}
      </div>
    </div>
  );
}

function ConfidencePill({ level }) {
  return (
    <span className={`confidence-pill confidence-${level}`}>
      {level?.charAt(0).toUpperCase() + level?.slice(1)} confidence
    </span>
  );
}

function EstimateCard({ icon, title, subtitle, result, currentSalary }) {
  if (!result) return null;
  if (result.error && !result.estimate) {
    return (
      <div className="estimate-card">
        <div className="estimate-card-header">
          <span className="estimate-icon">{icon}</span>
          <div>
            <div className="estimate-title">{title}</div>
            <div className="estimate-subtitle">{subtitle}</div>
          </div>
        </div>
        <p className="estimate-error">{result.error}</p>
      </div>
    );
  }
  return (
    <div className="estimate-card">
      <div className="estimate-card-header">
        <span className="estimate-icon">{icon}</span>
        <div>
          <div className="estimate-title">{title}</div>
          <div className="estimate-subtitle">{subtitle}</div>
        </div>
      </div>
      <div className="estimate-value">{fmtM(result.estimate)}</div>
      <div className="estimate-range">Range: {fmtM(result.low)} – {fmtM(result.high)}</div>
      <RangeBar
        low={result.low}
        high={result.high}
        estimate={result.estimate}
        current={currentSalary?.aav}
      />
      <div className="confidence-row">
        <span className="confidence-label">Confidence:</span>
        <ConfidencePill level={result.confidence} />
      </div>
    </div>
  );
}

export default function SalaryEstimate({ comparablesEstimate, regressionEstimate, currentSalary }) {
  return (
    <div className="estimates-grid">
      <EstimateCard
        icon="📊"
        title="Comparables Engine"
        subtitle={`Based on ${comparablesEstimate?.n_comparables || '?'} similar players`}
        result={comparablesEstimate}
        currentSalary={currentSalary}
      />
      <EstimateCard
        icon="🤖"
        title="Regression Model"
        subtitle="Gradient boosting on stat + salary dataset"
        result={regressionEstimate}
        currentSalary={currentSalary}
      />
    </div>
  );
}

import React from 'react';

function fmtM(n) {
  if (!n && n !== 0) return '—';
  return `$${(n / 1_000_000).toFixed(2)}M`;
}

function fmtDelta(estimate, current) {
  if (!estimate || !current) return null;
  const diff = estimate - current;
  const sign = diff >= 0 ? '+' : '';
  return `${sign}${fmtM(diff)}`;
}

function confidenceBars(level) {
  const on = level === 'high' ? 3 : level === 'medium' ? 2 : 1;
  return [0, 1, 2, 3].map((i) => <i key={i} className={i < on ? 'on' : 'off'} />);
}

function confidenceLabel(level) {
  if (!level) return 'Unknown';
  return level.charAt(0).toUpperCase() + level.slice(1);
}

// Density curve for comparables — rendered as a smooth bell-ish SVG
function DensityGraph({ estimate, current, low, high }) {
  if (!estimate) return null;

  // Build axis tick labels
  const minVal = Math.min(low || estimate * 0.7, current || estimate * 0.7) * 0.9;
  const maxVal = Math.max(high || estimate * 1.3, current || estimate * 1.3) * 1.1;
  const span = maxVal - minVal || 1;

  const xOf = (v) => Math.max(0, Math.min(400, ((v - minVal) / span) * 400));

  const curX = current ? xOf(current) : null;
  const estX = xOf(estimate);

  const ticks = [minVal, minVal + span * 0.25, minVal + span * 0.5, minVal + span * 0.75, maxVal];

  return (
    <>
      <div className="graph">
        <svg viewBox="0 0 400 160" preserveAspectRatio="none">
          <line className="g-grid" x1="0" y1="125" x2="400" y2="125"/>
          <line className="g-grid" x1="0" y1="85" x2="400" y2="85"/>
          <line className="g-grid" x1="0" y1="45" x2="400" y2="45"/>

          {/* Bell curve roughly centered at estimate */}
          <path className="g-curve-fill" d={`M0 155
               C 30 153, 50 147, 70 137
               C 90 122, 110 105, ${estX - 110} 75
               C ${estX - 80} 40, ${estX - 40} 22, ${estX} 28
               C ${estX + 40} 34, ${estX + 80} 65, ${estX + 110} 100
               C ${estX + 140} 128, 380 150, 400 155
               L 400 158 L 0 158 Z`}/>
          <path className="g-curve-line" d={`M0 155
               C 30 153, 50 147, 70 137
               C 90 122, 110 105, ${estX - 110} 75
               C ${estX - 80} 40, ${estX - 40} 22, ${estX} 28
               C ${estX + 40} 34, ${estX + 80} 65, ${estX + 110} 100
               C ${estX + 140} 128, 380 150, 400 155`}/>

          {curX !== null && (
            <>
              <line className="g-marker-cur" x1={curX} y1="0" x2={curX} y2="155"/>
              <text x={curX} y="14" className="g-label cur" textAnchor="middle">CURRENT</text>
              <text x={curX} y="28" className="g-label-val cur" textAnchor="middle">{fmtM(current)}</text>
            </>
          )}
          <line className="g-marker-est-glow" x1={estX} y1="0" x2={estX} y2="155"/>
          <line className="g-marker-est" x1={estX} y1="0" x2={estX} y2="155"/>
          <text x={estX} y="14" className="g-label est" textAnchor="middle">ESTIMATE</text>
          <text x={estX} y="28" className="g-label-val est" textAnchor="middle">{fmtM(estimate)}</text>
        </svg>
      </div>
      <div className="density-axis">
        {ticks.map((t, i) => <span key={i}>{fmtM(t)}</span>)}
      </div>
      <div className="legend">
        <span className="legend-item"><span className="legend-swatch dist"/>&nbsp;Comparable distribution</span>
        <span className="legend-item"><span className="legend-swatch cur"/>&nbsp;Current AAV</span>
        <span className="legend-item"><span className="legend-swatch est"/>&nbsp;Point estimate</span>
      </div>
    </>
  );
}

// Bootstrap histogram for regression
function HistogramGraph({ estimate, current, low, high }) {
  if (!estimate) return null;

  const minVal = Math.min(low || estimate * 0.6, current || estimate * 0.6) * 0.85;
  const maxVal = Math.max(high || estimate * 1.4, current || estimate * 1.4) * 1.1;
  const span = maxVal - minVal || 1;

  const xOf = (v) => Math.max(0, Math.min(400, ((v - minVal) / span) * 400));
  const curX = current ? xOf(current) : null;
  const estX = xOf(estimate);

  // Generate 19 bars in a normal distribution centered at estimate
  const bars = [];
  const n = 19;
  for (let i = 0; i < n; i++) {
    const t = (i / (n - 1)); // 0..1
    const v = minVal + span * t;
    const dist = (v - estimate) / (span * 0.18);
    const h = Math.max(6, Math.round(120 * Math.exp(-0.5 * dist * dist)));
    const opacity = 0.35 + 0.65 * Math.exp(-0.5 * dist * dist);
    const xPx = 10 + i * 20;
    bars.push({ xPx, h, opacity });
  }

  const ticks = [minVal, minVal + span * 0.25, minVal + span * 0.5, minVal + span * 0.75, maxVal];

  return (
    <>
      <div className="graph" style={{ height: 150 }}>
        <svg viewBox="0 0 400 150" preserveAspectRatio="none">
          <line className="g-grid" x1="0" y1="120" x2="400" y2="120"/>
          <line className="g-grid" x1="0" y1="80" x2="400" y2="80"/>
          <line className="g-grid" x1="0" y1="40" x2="400" y2="40"/>
          <g>
            {bars.map((b, i) => (
              <rect key={i} x={b.xPx} y={140 - b.h} width="14" height={b.h} fill="#b8bcc7" opacity={b.opacity}/>
            ))}
          </g>
          {curX !== null && (
            <>
              <line className="g-marker-cur" x1={curX} y1="0" x2={curX} y2="145"/>
              <text x={curX} y="12" className="g-label cur" textAnchor="middle">{fmtM(current)}</text>
            </>
          )}
          <line className="g-marker-est-glow" x1={estX} y1="0" x2={estX} y2="145"/>
          <line className="g-marker-est" x1={estX} y1="0" x2={estX} y2="145"/>
          <text x={estX} y="12" className="g-label est" textAnchor="middle">{fmtM(estimate)}</text>
        </svg>
      </div>
      <div className="density-axis">
        {ticks.map((t, i) => <span key={i}>{fmtM(t)}</span>)}
      </div>
      <div className="legend">
        <span className="legend-item"><span className="legend-swatch dist"/>&nbsp;Bootstrap distribution</span>
        <span className="legend-item"><span className="legend-swatch cur"/>&nbsp;Current AAV</span>
        <span className="legend-item"><span className="legend-swatch est"/>&nbsp;Point estimate</span>
      </div>
    </>
  );
}

export default function SalaryEstimate({ type, result, currentSalary }) {
  if (!result) return null;

  const isComparables = type === 'comparables';
  const cardIndex = isComparables ? '02' : '03';
  const cardTitle = isComparables ? 'Comparables Engine' : 'Regression Model';
  const nComps = result.n_comparables;
  const algo = result.algo === 'GBR' ? 'GBR' : 'Ridge';
  const nSamples = result.n_samples;
  const tagText = isComparables
    ? (nComps ? `${nComps} comps · KNN` : 'KNN')
    : (nSamples ? `${algo} · n=${nSamples}` : algo);

  const estimate = result.estimate;
  const current = currentSalary?.aav;
  const rmse = result.rmse_dollars;
  const delta = fmtDelta(estimate, current);
  const rmseStr = rmse ? `± $${(rmse / 1_000_000).toFixed(1)}M` : null;

  const subText = isComparables
    ? `Posterior distribution over ${nComps || '?'} weighted neighbors`
    : (result.algo === 'GBR' ? `Gradient boosting · bootstrap resamples` : 'Ridge regression · bootstrap resamples');

  const footText = isComparables
    ? `Based on ${nComps || '?'} similar players · weighted by selected stats`
    : `${result.algo === 'GBR' ? 'Gradient boosting' : 'Ridge regression'} · trained 2013–2025`;

  if (result.error && !estimate) {
    return (
      <article className="card est-card">
        <div className="card-head">
          <div className="card-title"><span className="ix">{cardIndex}</span> {cardTitle}</div>
          <div className="card-tag">{tagText}</div>
        </div>
        <div className="est-body">
          <p style={{ color: 'var(--ink-3)', fontFamily: "'JetBrains Mono', monospace", fontSize: '12px' }}>
            {result.error}
          </p>
        </div>
      </article>
    );
  }

  return (
    <article className="card est-card">
      <div className="card-head">
        <div className="card-title"><span className="ix">{cardIndex}</span> {cardTitle}</div>
        <div className="card-tag">{tagText}</div>
      </div>
      <div className="est-body">
        <div className="est-readout">
          <span className="est-value">{fmtM(estimate)}</span>
          {rmseStr && <span className="est-err">{rmseStr}</span>}
          {delta && <span className="est-delta">{delta}</span>}
        </div>
        <div className="est-sub">{subText}</div>

        {isComparables ? (
          <DensityGraph
            estimate={estimate}
            current={current}
            low={result.low}
            high={result.high}
          />
        ) : (
          <HistogramGraph
            estimate={estimate}
            current={current}
            low={result.low}
            high={result.high}
          />
        )}
      </div>
      <div className="est-foot">
        <div>{footText}</div>
        <span className="conf-pill">
          <span className="b">{confidenceBars(result.confidence)}</span>
          {confidenceLabel(result.confidence)}
        </span>
      </div>
    </article>
  );
}

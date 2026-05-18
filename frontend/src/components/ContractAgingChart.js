import React from 'react';

function fmtM(n) {
  if (!n && n !== 0) return '—';
  return `$${(n / 1_000_000).toFixed(1)}M`;
}

function fmtMetric(v, isGoalie) {
  if (v == null) return '—';
  return isGoalie ? v.toFixed(3) : v.toFixed(2);
}

function confidenceBars(level) {
  const on = level === 'high' ? 3 : level === 'medium' ? 2 : 1;
  return [0, 1, 2, 3].map((i) => <i key={i} className={i < on ? 'on' : 'off'} />);
}

function confidenceLabel(level) {
  if (!level) return 'Unknown';
  return level.charAt(0).toUpperCase() + level.slice(1);
}

// ── SVG chart ─────────────────────────────────────────────────────────────────
function AgingChart({ career_stats, avg_curve, projection, position_group }) {
  const isGoalie = position_group === 'G';

  const W = 400, H = 155;
  const ML = 38, MR = 10, MT = 16, MB = 22;
  const PW = W - ML - MR;
  const PH = H - MT - MB;

  const cs = career_stats || [];
  const ac = avg_curve || [];
  const pr = projection || [];

  const allData = [...cs, ...ac, ...pr];
  if (allData.length === 0) return null;

  const allAges = allData.map((d) => d.age);
  const minAge = Math.max(18, Math.min(...allAges) - 0.5);
  const maxAge = Math.min(43, Math.max(...allAges) + 0.5);
  const ageSpan = maxAge - minAge || 1;

  const avgVis = ac.filter((d) => d.age >= minAge - 0.5 && d.age <= maxAge + 0.5);
  const allMetrics = [
    ...cs.map((d) => d.metric),
    ...avgVis.map((d) => d.metric),
    ...pr.map((d) => d.metric),
  ].filter((v) => v != null && !isNaN(v) && v > 0);

  if (allMetrics.length === 0) return null;

  const metricMin = isGoalie ? 0.88 : 0;
  const metricMax = isGoalie
    ? Math.min(0.952, Math.max(...allMetrics) * 1.01 + 0.004)
    : Math.max(3.0, Math.max(...allMetrics) * 1.18);
  const metricSpan = metricMax - metricMin || 1;

  const xOf = (age) => ML + ((age - minAge) / ageSpan) * PW;
  const yOf = (val) => MT + PH - ((val - metricMin) / metricSpan) * PH;

  // Avg curve paths
  const avgLine =
    avgVis.length > 1
      ? 'M ' + avgVis.map((d) => `${xOf(d.age).toFixed(1)},${yOf(d.metric).toFixed(1)}`).join(' L ')
      : null;
  const avgFill =
    avgVis.length > 1
      ? 'M ' +
        avgVis.map((d) => `${xOf(d.age).toFixed(1)},${yOf(d.metric).toFixed(1)}`).join(' L ') +
        ` L ${xOf(avgVis[avgVis.length - 1].age).toFixed(1)},${(MT + PH).toFixed(1)}` +
        ` L ${xOf(avgVis[0].age).toFixed(1)},${(MT + PH).toFixed(1)} Z`
      : null;

  // Career path
  const careerD =
    cs.length > 1
      ? 'M ' + cs.map((d) => `${xOf(d.age).toFixed(1)},${yOf(d.metric).toFixed(1)}`).join(' L ')
      : null;

  // Projection path — connect smoothly from last career point
  const projAnchor = cs.length > 0 ? cs[cs.length - 1] : null;
  const projPts = projAnchor ? [projAnchor, ...pr] : pr;
  const projD =
    projPts.length > 1
      ? 'M ' + projPts.map((d) => `${xOf(d.age).toFixed(1)},${yOf(d.metric).toFixed(1)}`).join(' L ')
      : null;

  // Contract region shade (age span covered by projection)
  const contractMinAge = pr.length > 0 ? Math.min(...pr.map((d) => d.age)) : null;
  const contractMaxAge = pr.length > 0 ? Math.max(...pr.map((d) => d.age)) : null;

  // X-axis ticks
  const tickStep = ageSpan > 14 ? 4 : ageSpan > 7 ? 2 : 1;
  const firstTick = Math.ceil(minAge / tickStep) * tickStep;
  const ageTicks = [];
  for (let a = firstTick; a <= maxAge; a += tickStep) ageTicks.push(a);

  // Y-axis ticks (4 evenly spaced)
  const yTicks = [0, 1, 2, 3, 4].map((i) => metricMin + (metricSpan * i) / 4);

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      style={{ width: '100%', height: '100%', display: 'block', overflow: 'visible' }}
    >
      {/* Contract span background */}
      {contractMinAge != null && contractMaxAge != null && (
        <rect
          x={xOf(contractMinAge)}
          y={MT}
          width={Math.max(2, xOf(contractMaxAge) - xOf(contractMinAge))}
          height={PH}
          fill="rgba(255,255,255,0.025)"
        />
      )}

      {/* Horizontal grid lines */}
      {yTicks.map((v, i) => (
        <line
          key={i}
          x1={ML} y1={yOf(v).toFixed(1)}
          x2={W - MR} y2={yOf(v).toFixed(1)}
          stroke="rgba(255,255,255,0.055)" strokeWidth="0.5"
        />
      ))}

      {/* Avg curve fill area */}
      {avgFill && <path d={avgFill} fill="rgba(184,188,199,0.07)" />}

      {/* Avg curve line */}
      {avgLine && (
        <path d={avgLine} fill="none" stroke="rgba(184,188,199,0.28)" strokeWidth="1" />
      )}

      {/* Projection (dashed white) */}
      {projD && (
        <path
          d={projD}
          fill="none"
          stroke="rgba(255,255,255,0.55)"
          strokeWidth="1.5"
          strokeDasharray="5 3"
        />
      )}

      {/* Career line (solid white) */}
      {careerD && (
        <path d={careerD} fill="none" stroke="rgba(255,255,255,0.88)" strokeWidth="1.8" />
      )}

      {/* Career dots */}
      {cs.map((d, i) => (
        <circle
          key={i}
          cx={xOf(d.age).toFixed(1)}
          cy={yOf(d.metric).toFixed(1)}
          r="2.8"
          fill="#ffffff"
          stroke="rgba(0,0,0,0.25)"
          strokeWidth="0.5"
        />
      ))}

      {/* Y-axis labels */}
      {yTicks.map((v, i) => (
        <text
          key={i}
          x={(ML - 4).toFixed(1)}
          y={(yOf(v) + 3.5).toFixed(1)}
          textAnchor="end"
          fontSize="7.5"
          fill="rgba(184,188,199,0.4)"
          fontFamily="'JetBrains Mono', monospace"
        >
          {isGoalie ? v.toFixed(3) : v.toFixed(1)}
        </text>
      ))}

      {/* X-axis (age) labels */}
      {ageTicks.map((a, i) => (
        <text
          key={i}
          x={xOf(a).toFixed(1)}
          y={(H - 6).toFixed(1)}
          textAnchor="middle"
          fontSize="7.5"
          fill="rgba(184,188,199,0.4)"
          fontFamily="'JetBrains Mono', monospace"
        >
          {a}
        </text>
      ))}

      {/* "AGE" x-axis label */}
      <text
        x={(ML + PW / 2).toFixed(1)}
        y={(H - 0.5).toFixed(1)}
        textAnchor="middle"
        fontSize="6.5"
        fill="rgba(184,188,199,0.25)"
        fontFamily="'JetBrains Mono', monospace"
        letterSpacing="0.12em"
      >
        AGE
      </text>
    </svg>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function ContractAgingChart({ data }) {
  if (!data) return null;

  const {
    career_stats = [],
    avg_curve = [],
    projection = [],
    contract,
    metric_label = 'Points / 60',
    position_group = 'F',
    confidence = 'medium',
  } = data;

  const isGoalie = position_group === 'G';
  const hasContract = contract && contract.yearly && contract.yearly.length > 0;
  const yearly = hasContract ? contract.yearly : [];

  const tagText = hasContract
    ? `${contract.years}yr · ${fmtM(contract.aav)}`
    : 'no contract';

  // Find the avg curve value closest to a given age
  function avgAtAge(age) {
    if (!avg_curve.length) return null;
    return avg_curve.reduce(
      (best, d) => (Math.abs(d.age - age) < Math.abs(best.age - age) ? d : best),
      avg_curve[0]
    ).metric;
  }

  return (
    <article className="card est-card">
      <div className="card-head">
        <div className="card-title">
          <span className="ix">02</span> Contract Aging
        </div>
        <div className="card-tag">{tagText}</div>
      </div>

      <div className="est-body">
        <div className="est-sub" style={{ marginBottom: 14 }}>
          {metric_label} by age · avg trajectory + {projection.length > 0 ? `${projection.length}-yr projection` : 'career arc'}
        </div>

        {/* Chart */}
        <div className="graph">
          <AgingChart
            career_stats={career_stats}
            avg_curve={avg_curve}
            projection={projection}
            position_group={position_group}
          />
        </div>

        {/* Contract year chips */}
        {yearly.length > 0 && (
          <div className="aging-years">
            {yearly.map((yr, i) => {
              const projPt = projection.find((p) => p.contract_year === yr.contract_year);
              const avg = avgAtAge(yr.age);
              const isAbove = projPt && avg != null && projPt.metric >= avg;
              return (
                <div key={i} className="aging-year-chip">
                  <div className="aging-yr-num">Yr {yr.contract_year}</div>
                  <div className="aging-yr-age">Age {yr.age}</div>
                  <div
                    className="aging-yr-cap"
                    style={{ color: isAbove ? 'var(--ink-2)' : 'var(--ink-3)' }}
                  >
                    {yr.cap_pct.toFixed(1)}%
                  </div>
                  <div className="aging-yr-caplabel">${(yr.cap / 1e6).toFixed(0)}M cap</div>
                  {projPt && (
                    <div
                      className="aging-yr-metric"
                      style={{ color: isAbove ? 'var(--signal-2)' : 'var(--ink-4)' }}
                    >
                      {fmtMetric(projPt.metric, isGoalie)}
                      <span style={{ color: 'var(--ink-5)', marginLeft: 2 }}>
                        {isGoalie ? 'sv%' : 'p/60'}
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Legend */}
        <div className="legend">
          <span className="legend-item">
            <span className="legend-swatch dist" />&nbsp;League avg
          </span>
          <span className="legend-item">
            <span
              className="legend-swatch"
              style={{ background: 'rgba(255,255,255,0.85)', height: 2 }}
            />&nbsp;Career
          </span>
          <span className="legend-item">
            <span
              className="legend-swatch"
              style={{ borderTop: '1.5px dashed rgba(255,255,255,0.5)', background: 'none' }}
            />&nbsp;Projected
          </span>
        </div>
      </div>

      <div className="est-foot">
        <div>
          {career_stats.length > 0
            ? `${career_stats.length} season${career_stats.length !== 1 ? 's' : ''} of data · cap grows with ceiling`
            : 'avg age curve only · no career data'}
        </div>
        <span className="conf-pill">
          <span className="b">{confidenceBars(confidence)}</span>
          {confidenceLabel(confidence)}
        </span>
      </div>
    </article>
  );
}

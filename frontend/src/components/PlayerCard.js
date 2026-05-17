import React, { useState } from 'react';

function fmtM(n) {
  if (!n && n !== 0) return '—';
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  return `$${n.toLocaleString()}`;
}

function fmtStat(val, decimals = 0) {
  if (val === null || val === undefined) return '—';
  return typeof val === 'number' ? val.toFixed(decimals) : String(val);
}

function positionLabel(pos) {
  const map = { C: 'Center', LW: 'Left Wing', L: 'Left Wing', RW: 'Right Wing', R: 'Right Wing', D: 'Defense', G: 'Goalie' };
  return map[pos?.toUpperCase()] || pos || '—';
}

function verdictClass(verdict) {
  if (!verdict) return '';
  const s = verdict.status || '';
  if (s === 'underpaid') return 'under';
  if (s === 'overpaid') return 'over';
  return 'fair';
}

function verdictLabel(verdict) {
  if (!verdict) return null;
  const map = { underpaid: 'Underpaid', overpaid: 'Overpaid', fair: 'Fair Value' };
  return map[verdict.status] || verdict.status || null;
}

export default function PlayerCard({ player, salary, verdict }) {
  const [imgError, setImgError] = useState(false);
  if (!player) return null;

  const { name, team, position, age, experience, headshot_url, jersey_number, stats, fa_type } = player;
  const isGoalie = position === 'G';
  const vClass = verdictClass(verdict);
  const vLabel = verdictLabel(verdict);
  const hasImg = headshot_url && !imgError;

  // Build stat cells
  const skaterCells = stats ? [
    { key: 'G',      val: fmtStat(stats.goals),                       delta: null },
    { key: 'A',      val: fmtStat(stats.assists),                     delta: null },
    { key: 'PTS',    val: fmtStat(stats.points),                      delta: null },
    { key: 'P/60',   val: fmtStat(stats.points_per_60, 2),            delta: null },
    { key: 'TOI/GP', val: fmtStat(stats.toi_per_game, 1),             delta: null },
    { key: 'CF%',    val: stats.corsi_for_pct != null ? fmtStat(stats.corsi_for_pct, 1) : fmtStat(stats.xgf_pct, 1), delta: null },
  ] : [];

  const goalieCells = stats ? [
    { key: 'GAA',    val: fmtStat(stats.gaa, 2),                      delta: null },
    { key: 'SV%',    val: stats.save_pct ? (stats.save_pct * 100).toFixed(1) + '%' : '—', delta: null },
    { key: 'GS',     val: fmtStat(stats.games_started),               delta: null },
    { key: 'QS%',    val: stats.quality_start_pct ? (stats.quality_start_pct * 100).toFixed(0) + '%' : '—', delta: null },
  ] : [];

  const cells = isGoalie ? goalieCells : skaterCells;

  return (
    <article className="card">
      <div className="card-head">
        <div className="card-title"><span className="ix">01</span> Player Profile</div>
        <div className="card-tag">Roster · Active</div>
      </div>
      <div className="player-card-inner">
        {/* Headshot */}
        <div className="headshot">
          {team && jersey_number && (
            <span className="headshot-tag">{team} · #{jersey_number}</span>
          )}
          {!team && jersey_number && (
            <span className="headshot-tag">#{jersey_number}</span>
          )}
          {team && !jersey_number && (
            <span className="headshot-tag">{team}</span>
          )}
          {hasImg ? (
            <img src={headshot_url} alt={name} onError={() => setImgError(true)} />
          ) : (
            <>
              <div className="headshot-jersey" />
              {jersey_number && <span className="headshot-num">{jersey_number}</span>}
            </>
          )}
        </div>

        {/* Player meta */}
        <div className="player-meta">
          <h2 className="player-name">{name}</h2>
          <div className="player-badges">
            {team && (
              <span className="chip chip-team">
                <span className="swatch" />
                {team}
              </span>
            )}
            <span className="chip">{positionLabel(position)}</span>
            {age > 0 && <span className="chip">Age {age}</span>}
            {experience > 0 && <span className="chip">{experience} yr exp</span>}
            {fa_type && <span className="chip chip-fa">{fa_type}</span>}
          </div>

          {cells.length > 0 && (
            <div className="player-stats">
              {cells.map((c) => (
                <div className="stat-cell" key={c.key}>
                  <span className="stat-key">{c.key}</span>
                  <span className="stat-val">{c.val}</span>
                  {c.delta && <span className="stat-delta">{c.delta}</span>}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Salary block */}
        <div className="salary-block">
          <span className="salary-label">Current Cap Hit (AAV)</span>
          {salary?.aav ? (
            <>
              <span className="salary-cur">{fmtM(salary.aav)}</span>
              <div className="salary-aux">
                {salary.contract_years && <span>{salary.contract_years} yr</span>}
                {salary.expiry_season && <span>Exp {salary.expiry_season}</span>}
              </div>
            </>
          ) : (
            <span className="salary-cur" style={{ fontSize: '18px', color: 'var(--ink-3)' }}>No contract data</span>
          )}

          {verdict && vLabel && (
            <div className={`verdict ${vClass}`}>
              {vLabel}
              {verdict.by != null && (
                <span className="verdict-amt">
                  {verdict.by > 0 ? '+' : ''}{fmtM(verdict.by)}
                  {verdict.pct != null ? ` · ${verdict.pct > 0 ? '+' : ''}${verdict.pct}%` : ''}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </article>
  );
}

import React, { useState } from 'react';
import './PlayerCard.css';

function fmt(n) {
  if (!n && n !== 0) return '—';
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  return `$${n.toLocaleString()}`;
}

function fmtStat(val, decimals = 0) {
  if (val === null || val === undefined) return '—';
  return typeof val === 'number' ? val.toFixed(decimals) : val;
}

function positionLabel(pos) {
  const map = { C: 'Center', LW: 'Left Wing', L: 'Left Wing', RW: 'Right Wing', R: 'Right Wing', D: 'Defense', G: 'Goalie' };
  return map[pos?.toUpperCase()] || pos || '—';
}

export default function PlayerCard({ player, salary, verdict }) {
  const [imgError, setImgError] = useState(false);
  if (!player) return null;

  const { name, team, position, age, experience, headshot_url, stats, fa_type } = player;
  const isGoalie = position === 'G';

  const verdictClass = verdict
    ? { underpaid: 'verdict-underpaid', overpaid: 'verdict-overpaid', fair: 'verdict-fair' }[verdict.status]
    : null;

  const verdictLabel = verdict
    ? { underpaid: 'Underpaid', overpaid: 'Overpaid', fair: 'Fair Value' }[verdict.status]
    : null;

  return (
    <div className="player-card">
      <div className="player-headshot-wrap">
        {headshot_url && !imgError ? (
          <img
            className="player-headshot"
            src={headshot_url}
            alt={name}
            onError={() => setImgError(true)}
          />
        ) : (
          <span>{isGoalie ? '🥅' : '🏒'}</span>
        )}
      </div>

      <div className="player-info">
        <div className="player-name">{name}</div>

        <div className="player-badges">
          {team && <span className="badge badge-team">{team}</span>}
          <span className="badge badge-position">{positionLabel(position)}</span>
          {age > 0 && <span className="badge badge-age">Age {age}</span>}
          {experience > 0 && <span className="badge badge-age">{experience} yr exp</span>}
          {fa_type && <span className="badge badge-fa">{fa_type}</span>}
        </div>

        <div className="player-salary-row">
          {salary?.aav ? (
            <>
              <div className="salary-block">
                <span className="salary-label">Cap Hit (AAV)</span>
                <span className="salary-value">{fmt(salary.aav)}</span>
              </div>
              {salary.contract_years && (
                <>
                  <div className="salary-divider" />
                  <div className="salary-block">
                    <span className="salary-label">Contract</span>
                    <span className="salary-meta-value">{salary.contract_years} yr</span>
                  </div>
                </>
              )}
              {salary.expiry_season && (
                <>
                  <div className="salary-divider" />
                  <div className="salary-block">
                    <span className="salary-label">Expires</span>
                    <span className="salary-meta-value">{salary.expiry_season}</span>
                  </div>
                </>
              )}
            </>
          ) : (
            <span className="no-salary">No contract data on file</span>
          )}

          {verdict && verdictClass && (
            <div className="verdict-badge">
              <span className="verdict-label">Verdict</span>
              <span className={`verdict-chip ${verdictClass}`}>{verdictLabel}</span>
              <span className="verdict-amount">
                {verdict.by > 0 ? '+' : ''}{fmt(verdict.by)} ({verdict.pct > 0 ? '+' : ''}{verdict.pct}%)
              </span>
            </div>
          )}
        </div>

        {stats && (
          <div className="player-stats-grid">
            {isGoalie ? (
              <>
                <div className="stat-item"><span className="stat-val">{fmtStat(stats.gaa, 2)}</span><span className="stat-key">GAA</span></div>
                <div className="stat-item"><span className="stat-val">{stats.save_pct ? (stats.save_pct * 100).toFixed(1) : '—'}%</span><span className="stat-key">SV%</span></div>
                <div className="stat-item"><span className="stat-val">{fmtStat(stats.games_started)}</span><span className="stat-key">GS</span></div>
                {stats.quality_start_pct && (
                  <div className="stat-item"><span className="stat-val">{(stats.quality_start_pct * 100).toFixed(0)}%</span><span className="stat-key">QS%</span></div>
                )}
              </>
            ) : (
              <>
                {stats.goals !== undefined && <div className="stat-item"><span className="stat-val">{fmtStat(stats.goals)}</span><span className="stat-key">G</span></div>}
                {stats.assists !== undefined && <div className="stat-item"><span className="stat-val">{fmtStat(stats.assists)}</span><span className="stat-key">A</span></div>}
                {stats.points !== undefined && <div className="stat-item"><span className="stat-val">{fmtStat(stats.points)}</span><span className="stat-key">PTS</span></div>}
                <div className="stat-item"><span className="stat-val">{fmtStat(stats.points_per_60, 1)}</span><span className="stat-key">P/60</span></div>
                <div className="stat-item"><span className="stat-val">{fmtStat(stats.toi_per_game, 1)}</span><span className="stat-key">TOI/GP</span></div>
                {stats.corsi_for_pct != null && (
                  <div className="stat-item"><span className="stat-val">{fmtStat(stats.corsi_for_pct, 1)}%</span><span className="stat-key">CF%</span></div>
                )}
                {stats.xgf_pct != null && (
                  <div className="stat-item"><span className="stat-val">{fmtStat(stats.xgf_pct, 1)}%</span><span className="stat-key">xGF%</span></div>
                )}
                {stats.plus_minus !== undefined && (
                  <div className="stat-item"><span className="stat-val">{stats.plus_minus > 0 ? '+' : ''}{fmtStat(stats.plus_minus)}</span><span className="stat-key">+/-</span></div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

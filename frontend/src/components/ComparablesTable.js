import React, { useState, useMemo } from 'react';
import './ComparablesTable.css';

function fmtM(n) {
  if (!n && n !== 0) return '—';
  return `$${(n / 1_000_000).toFixed(2)}M`;
}

function fmtStat(val, d = 1) {
  if (val === null || val === undefined) return '—';
  return Number(val).toFixed(d);
}

const SKATER_COLS = [
  { key: 'name',           label: 'Player',    fmt: (r) => r.name,                          cls: 'td-name' },
  { key: 'team',           label: 'Team',      fmt: (r) => r.team,                          cls: 'td-team' },
  { key: 'position',       label: 'Pos',       fmt: (r) => r.position,                      cls: 'td-pos' },
  { key: 'aav',            label: 'AAV',       fmt: (r) => fmtM(r.aav),                     cls: 'td-salary', num: true },
  { key: 'points_per_60',  label: 'P/60',      fmt: (r) => fmtStat(r.stats?.points_per_60), num: true },
  { key: 'goals_per_60',   label: 'G/60',      fmt: (r) => fmtStat(r.stats?.goals_per_60),  num: true },
  { key: 'toi_per_game',   label: 'TOI/GP',    fmt: (r) => fmtStat(r.stats?.toi_per_game),  num: true },
  { key: 'corsi_for_pct',  label: 'CF%',       fmt: (r) => fmtStat(r.stats?.corsi_for_pct), num: true },
  { key: 'xgf_pct',        label: 'xGF%',      fmt: (r) => fmtStat(r.stats?.xgf_pct),       num: true },
  { key: 'fa_type',        label: 'FA',        fmt: (r) => r.fa_type || '—',                cls: 'td-team' },
  { key: 'similarity',     label: 'Similarity',fmt: (r) => null,                            num: true },
];

const GOALIE_COLS = [
  { key: 'name',             label: 'Player',    fmt: (r) => r.name,                              cls: 'td-name' },
  { key: 'team',             label: 'Team',      fmt: (r) => r.team,                              cls: 'td-team' },
  { key: 'aav',              label: 'AAV',       fmt: (r) => fmtM(r.aav),                         cls: 'td-salary', num: true },
  { key: 'gaa',              label: 'GAA',       fmt: (r) => fmtStat(r.stats?.gaa, 2),             num: true },
  { key: 'save_pct',         label: 'SV%',       fmt: (r) => r.stats?.save_pct ? (r.stats.save_pct * 100).toFixed(1)+'%' : '—', num: true },
  { key: 'games_started',    label: 'GS',        fmt: (r) => r.stats?.games_started ?? '—',        num: true },
  { key: 'quality_start_pct',label: 'QS%',       fmt: (r) => r.stats?.quality_start_pct ? (r.stats.quality_start_pct * 100).toFixed(0)+'%' : '—', num: true },
  { key: 'fa_type',          label: 'FA',        fmt: (r) => r.fa_type || '—',                    cls: 'td-team' },
  { key: 'similarity',       label: 'Similarity',fmt: (r) => null,                                num: true },
];

function getSortValue(row, key) {
  if (key === 'similarity') return row.similarity;
  if (key === 'aav') return row.aav || 0;
  if (key === 'name') return row.name || '';
  if (key === 'team') return row.team || '';
  if (key === 'position') return row.position || '';
  if (key === 'fa_type') return row.fa_type || '';
  return row.stats?.[key] ?? 0;
}

export default function ComparablesTable({ comparables, isGoalie }) {
  const [sortKey, setSortKey] = useState('similarity');
  const [sortAsc, setSortAsc] = useState(false);

  const cols = isGoalie ? GOALIE_COLS : SKATER_COLS;

  const sorted = useMemo(() => {
    if (!comparables) return [];
    return [...comparables].sort((a, b) => {
      const va = getSortValue(a, sortKey);
      const vb = getSortValue(b, sortKey);
      if (typeof va === 'string') return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
      return sortAsc ? va - vb : vb - va;
    });
  }, [comparables, sortKey, sortAsc]);

  const handleSort = (key) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  };

  if (!comparables || comparables.length === 0) {
    return (
      <div className="comparables-card">
        <div className="comparables-header">
          <span className="comparables-title">Comparable Players</span>
        </div>
        <div className="empty-comparables">No comparable players found in dataset.</div>
      </div>
    );
  }

  return (
    <div className="comparables-card">
      <div className="comparables-header">
        <span className="comparables-title">Comparable Players</span>
        <span className="comp-count">{comparables.length} comps</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {cols.map((col) => (
                <th
                  key={col.key}
                  className={sortKey === col.key ? 'sorted' : ''}
                  onClick={() => handleSort(col.key)}
                >
                  {col.label}
                  {sortKey === col.key && (
                    <span className="sort-arrow">{sortAsc ? '▲' : '▼'}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, i) => (
              <tr key={row.player_id || i}>
                {cols.map((col) => {
                  if (col.key === 'similarity') {
                    const pct = Math.round((row.similarity || 0) * 100);
                    return (
                      <td key="similarity" className="td-sim">
                        <div className="sim-bar-wrap">
                          <div className="sim-bar" style={{ width: `${pct}px` }} />
                          <span>{pct}%</span>
                        </div>
                      </td>
                    );
                  }
                  return (
                    <td key={col.key} className={col.cls || ''}>
                      {col.fmt(row)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

import React, { useState, useMemo } from 'react';

function fmtM(n) {
  if (!n && n !== 0) return '—';
  return `$${(n / 1_000_000).toFixed(2)}M`;
}

function fmtStat(val, d = 1) {
  if (val === null || val === undefined) return '—';
  return Number(val).toFixed(d);
}

function initials(name) {
  if (!name) return '??';
  return name.split(' ').map((p) => p[0]).join('').slice(0, 2).toUpperCase();
}

const SKATER_COLS = [
  { key: 'name',          label: 'Player',    num: false },
  { key: 'team',          label: 'Team',      num: false },
  { key: 'position',      label: 'Pos',       num: false },
  { key: 'aav',           label: 'AAV',       num: true  },
  { key: 'points_per_60', label: 'P/60',      num: true  },
  { key: 'goals_per_60',  label: 'G/60',      num: true  },
  { key: 'toi_per_game',  label: 'TOI/GP',    num: true  },
  { key: 'corsi_for_pct', label: 'CF%',       num: true  },
  { key: 'xgf_pct',       label: 'xGF%',      num: true  },
  { key: 'fa_type',       label: 'FA',        num: false },
  { key: 'similarity',    label: 'Similarity', num: true  },
];

const GOALIE_COLS = [
  { key: 'name',              label: 'Player',    num: false },
  { key: 'team',              label: 'Team',      num: false },
  { key: 'aav',               label: 'AAV',       num: true  },
  { key: 'gaa',               label: 'GAA',       num: true  },
  { key: 'save_pct',          label: 'SV%',       num: true  },
  { key: 'games_started',     label: 'GS',        num: true  },
  { key: 'quality_start_pct', label: 'QS%',       num: true  },
  { key: 'fa_type',           label: 'FA',        num: false },
  { key: 'similarity',        label: 'Similarity', num: true  },
];

function getSortValue(row, key) {
  if (key === 'similarity') return row.similarity || 0;
  if (key === 'aav') return row.aav || 0;
  if (key === 'name') return row.name || '';
  if (key === 'team') return row.team || '';
  if (key === 'position') return row.position || '';
  if (key === 'fa_type') return row.fa_type || '';
  return row.stats?.[key] ?? 0;
}

function getCellContent(row, key, isGoalie, maxSalary) {
  if (key === 'name') {
    return (
      <div className="td-player">
        <div className="td-avatar">{initials(row.name)}</div>
        <div>
          <div className="td-name-text">{row.name}</div>
          {(row.age || row.experience) && (
            <div className="td-sub">
              {row.age ? `Age ${row.age}` : ''}
              {row.age && row.experience ? ' · ' : ''}
              {row.experience ? `${row.experience} yr` : ''}
            </div>
          )}
        </div>
      </div>
    );
  }
  if (key === 'team' || key === 'position' || key === 'fa_type') {
    const val = key === 'fa_type' ? (row.fa_type || '—') : (row[key] || '—');
    return <span className="pos-pill">{val}</span>;
  }
  if (key === 'aav') {
    const pct = maxSalary > 0 ? Math.min(100, (row.aav / maxSalary) * 100) : 0;
    return (
      <div className="sal-bar-wrap">
        <div className="sal-bar"><i style={{ width: `${pct}%` }} /></div>
        <span className="sal-val">{fmtM(row.aav)}</span>
      </div>
    );
  }
  if (key === 'similarity') {
    const pct = Math.round((row.similarity || 0) * 100);
    const hi = pct >= 85;
    return (
      <div className="sim-wrap">
        <div className={`sim-bar${hi ? ' hi' : ''}`}><i style={{ width: `${pct}%` }} /></div>
        <span className="sim-val">{pct}%</span>
      </div>
    );
  }
  // stat columns
  if (key === 'save_pct') {
    return row.stats?.save_pct ? (row.stats.save_pct * 100).toFixed(1) + '%' : '—';
  }
  if (key === 'quality_start_pct') {
    return row.stats?.quality_start_pct ? (row.stats.quality_start_pct * 100).toFixed(0) + '%' : '—';
  }
  if (key === 'gaa') return fmtStat(row.stats?.gaa, 2);
  if (key === 'games_started') return row.stats?.games_started ?? '—';
  if (key === 'points_per_60') return fmtStat(row.stats?.points_per_60);
  if (key === 'goals_per_60') return fmtStat(row.stats?.goals_per_60);
  if (key === 'toi_per_game') return fmtStat(row.stats?.toi_per_game);
  if (key === 'corsi_for_pct') return fmtStat(row.stats?.corsi_for_pct);
  if (key === 'xgf_pct') return fmtStat(row.stats?.xgf_pct);
  return '—';
}

export default function ComparablesTable({ comparables, isGoalie }) {
  const [sortKey, setSortKey] = useState('similarity');
  const [sortAsc, setSortAsc] = useState(false);
  const [filter, setFilter] = useState('');

  const cols = isGoalie ? GOALIE_COLS : SKATER_COLS;

  const filtered = useMemo(() => {
    if (!comparables) return [];
    if (!filter) return comparables;
    const q = filter.toLowerCase();
    return comparables.filter((r) =>
      (r.name || '').toLowerCase().includes(q) ||
      (r.team || '').toLowerCase().includes(q)
    );
  }, [comparables, filter]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const va = getSortValue(a, sortKey);
      const vb = getSortValue(b, sortKey);
      if (typeof va === 'string') return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
      return sortAsc ? va - vb : vb - va;
    });
  }, [filtered, sortKey, sortAsc]);

  const handleSort = (key) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  };

  const maxSalary = useMemo(() => {
    if (!comparables) return 0;
    return Math.max(...comparables.map((r) => r.aav || 0));
  }, [comparables]);

  if (!comparables || comparables.length === 0) {
    return (
      <article className="card">
        <div className="card-head">
          <div className="card-title"><span className="ix">06</span> Comparable Players</div>
          <div className="card-tag">0 comps</div>
        </div>
        <div style={{ padding: '24px', color: 'var(--ink-3)', fontFamily: "'JetBrains Mono', monospace", fontSize: '12px' }}>
          No comparable players found in dataset.
        </div>
      </article>
    );
  }

  return (
    <article className="card">
      <div className="card-head">
        <div className="card-title"><span className="ix">06</span> Comparable Players</div>
        <div className="card-tag">{comparables.length} of {comparables.length} · sorted by similarity</div>
      </div>

      <div className="comps-toolbar">
        <div className="comps-search">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
            <circle cx="11" cy="11" r="7"/>
            <path d="M21 21l-4-4"/>
          </svg>
          <input
            type="text"
            placeholder="Filter comparables…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </div>
      </div>

      <table className="comps">
        <thead>
          <tr>
            {cols.map((col) => (
              <th
                key={col.key}
                className={[
                  col.num ? 'num' : '',
                  sortKey === col.key ? 'sorted' : '',
                  sortKey === col.key && sortAsc ? 'asc' : '',
                ].filter(Boolean).join(' ')}
                onClick={() => handleSort(col.key)}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => (
            <tr key={row.player_id || i}>
              {cols.map((col) => (
                <td key={col.key} className={col.num ? 'num' : ''}>
                  {getCellContent(row, col.key, isGoalie, maxSalary)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </article>
  );
}

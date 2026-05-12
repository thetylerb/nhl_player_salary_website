import React, { useState, useEffect } from 'react';
import { getMissingData, triggerScrape } from '../services/api';

function fmt(aav) {
  if (!aav) return '—';
  return '$' + (aav / 1_000_000).toFixed(2) + 'M';
}

export default function AdminPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scraping, setScraping] = useState(false);
  const [scrapeResult, setScrapeResult] = useState(null);

  useEffect(() => {
    getMissingData()
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  async function handleScrape() {
    setScraping(true);
    setScrapeResult(null);
    try {
      const result = await triggerScrape();
      setScrapeResult(result);
      const fresh = await getMissingData();
      setData(fresh);
    } catch (e) {
      setScrapeResult({ error: e.message });
    } finally {
      setScraping(false);
    }
  }

  return (
    <div style={{ padding: '2rem', maxWidth: 1100, margin: '0 auto', color: '#e2e8f0' }}>
      <h1 style={{ color: '#4ade80', marginBottom: '0.25rem' }}>Admin — Missing Data Report</h1>
      <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>Season: {data?.season || '—'}</p>

      <button
        onClick={handleScrape}
        disabled={scraping}
        style={{
          background: scraping ? '#334155' : '#0ea5e9',
          color: '#fff',
          border: 'none',
          borderRadius: 8,
          padding: '0.6rem 1.4rem',
          cursor: scraping ? 'not-allowed' : 'pointer',
          fontWeight: 600,
          marginBottom: '1rem',
        }}
      >
        {scraping ? 'Scraping… (~60s)' : 'Trigger Full Scrape Now'}
      </button>

      {scrapeResult && (
        <div style={{ marginBottom: '1.5rem', padding: '0.75rem 1rem', background: '#1e293b', borderRadius: 8, fontSize: 14 }}>
          {scrapeResult.error
            ? <span style={{ color: '#f87171' }}>Error: {scrapeResult.error}</span>
            : <span style={{ color: '#4ade80' }}>Done — {scrapeResult.stats_rows} stat rows, {scrapeResult.salary_rows} salary rows updated</span>}
        </div>
      )}

      {loading && <p>Loading…</p>}
      {error && <p style={{ color: '#f87171' }}>Error: {error}</p>}

      {data && (
        <>
          <Section
            title={`Salary missing — has stats, no contract (${data.stats_no_salary.length} players)`}
            subtitle="These players have MoneyPuck stats but no matched salary. May need a manual scrape or a name mismatch fix."
            rows={data.stats_no_salary}
            columns={[
              { key: 'name', label: 'Player' },
              { key: 'team', label: 'Team' },
              { key: 'position', label: 'Pos' },
              { key: 'player_id', label: 'NHL ID' },
            ]}
          />

          <Section
            title={`Stats missing — has contract, no stats (${data.salary_no_stats.length} players)`}
            subtitle="These players have a PuckPedia salary record but no MoneyPuck stats. Likely minor-league, LTIR, or a pp_ ID mismatch."
            rows={data.salary_no_stats}
            columns={[
              { key: 'name', label: 'Player' },
              { key: 'team', label: 'Team' },
              { key: 'position', label: 'Pos' },
              { key: 'aav', label: 'AAV', render: fmt },
              { key: 'source', label: 'Source' },
              { key: 'player_id', label: 'ID' },
            ]}
          />
        </>
      )}
    </div>
  );
}

function Section({ title, subtitle, rows, columns }) {
  const [open, setOpen] = useState(true);

  return (
    <div style={{ marginBottom: '2.5rem' }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, textAlign: 'left' }}
      >
        <h2 style={{ color: '#f1f5f9', fontSize: '1.05rem', marginBottom: '0.25rem' }}>
          {open ? '▾' : '▸'} {title}
        </h2>
      </button>
      <p style={{ color: '#64748b', fontSize: 13, marginTop: 0, marginBottom: '0.75rem' }}>{subtitle}</p>

      {open && (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr>
                {columns.map(c => (
                  <th key={c.key} style={{ textAlign: 'left', padding: '6px 12px', background: '#1e293b', color: '#94a3b8', fontWeight: 600 }}>
                    {c.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.length === 0
                ? <tr><td colSpan={columns.length} style={{ padding: '12px', color: '#64748b' }}>None</td></tr>
                : rows.map((row, i) => (
                  <tr key={i} style={{ background: i % 2 === 0 ? '#0f172a' : '#1e293b' }}>
                    {columns.map(c => (
                      <td key={c.key} style={{ padding: '6px 12px', color: '#e2e8f0' }}>
                        {c.render ? c.render(row[c.key]) : (row[c.key] ?? '—')}
                      </td>
                    ))}
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

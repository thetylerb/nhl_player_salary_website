import React, { useState, useEffect, useRef } from 'react';
import { getMissingData, triggerScrape, triggerHistoricalScrape, importCsv } from '../services/api';

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
  const [historicalScraping, setHistoricalScraping] = useState(false);
  const [historicalResult, setHistoricalResult] = useState(null);
  const [csvImporting, setCsvImporting] = useState(false);
  const [csvResult, setCsvResult] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    getMissingData()
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  async function handleHistoricalScrape() {
    setHistoricalScraping(true);
    setHistoricalResult(null);
    try {
      const result = await triggerHistoricalScrape();
      setHistoricalResult(result);
      const fresh = await getMissingData();
      setData(fresh);
    } catch (e) {
      setHistoricalResult({ error: e.message });
    } finally {
      setHistoricalScraping(false);
    }
  }

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

  async function handleCsvImport(file) {
    setCsvImporting(true);
    setCsvResult(null);
    try {
      const result = await importCsv(file || null);
      setCsvResult(result);
      const fresh = await getMissingData();
      setData(fresh);
    } catch (e) {
      setCsvResult({ error: e.message });
    } finally {
      setCsvImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }

  function handleFileChange(e) {
    const file = e.target.files[0];
    if (file) handleCsvImport(file);
  }

  return (
    <div style={{ padding: '2rem', maxWidth: 1100, margin: '0 auto', color: '#e2e8f0' }}>
      <h1 style={{ color: '#4ade80', marginBottom: '0.25rem' }}>Admin — Missing Data Report</h1>
      <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '1.5rem', fontSize: 13, color: '#94a3b8' }}>
        <span>Season: <b style={{ color: '#e2e8f0' }}>{data?.season || '—'}</b></span>
        <span>Salary rows: <b style={{ color: '#e2e8f0' }}>{data?.salary_count ?? '—'}</b></span>
        <span>CSV rows: <b style={{ color: '#fbbf24' }}>{data?.csv_salary_count ?? '—'}</b></span>
        <span>Stats rows (current season): <b style={{ color: '#e2e8f0' }}>{data?.stats_count ?? '—'}</b></span>
      </div>

      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
        <button
          onClick={handleScrape}
          disabled={scraping}
          style={{
            background: scraping ? '#334155' : '#0ea5e9',
            color: '#fff', border: 'none', borderRadius: 8,
            padding: '0.6rem 1.4rem', cursor: scraping ? 'not-allowed' : 'pointer', fontWeight: 600,
          }}
        >
          {scraping ? 'Scraping… (~60s)' : 'Scrape Current Season (Stats + Salaries)'}
        </button>

        <button
          onClick={handleHistoricalScrape}
          disabled={historicalScraping}
          style={{
            background: historicalScraping ? '#334155' : '#7c3aed',
            color: '#fff', border: 'none', borderRadius: 8,
            padding: '0.6rem 1.4rem', cursor: historicalScraping ? 'not-allowed' : 'pointer', fontWeight: 600,
          }}
        >
          {historicalScraping ? 'Scraping history… (~2 min)' : 'Scrape Historical Stats (2019 → present)'}
        </button>

        <button
          onClick={() => handleCsvImport(null)}
          disabled={csvImporting}
          style={{
            background: csvImporting ? '#334155' : '#f59e0b',
            color: '#fff', border: 'none', borderRadius: 8,
            padding: '0.6rem 1.4rem', cursor: csvImporting ? 'not-allowed' : 'pointer', fontWeight: 600,
          }}
        >
          {csvImporting ? 'Importing…' : 'Re-import Bundled CSV'}
        </button>

        <label style={{
          background: csvImporting ? '#334155' : '#ea580c',
          color: '#fff', borderRadius: 8,
          padding: '0.6rem 1.4rem', cursor: csvImporting ? 'not-allowed' : 'pointer', fontWeight: 600,
          display: 'inline-block',
        }}>
          Upload New CSV
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            disabled={csvImporting}
            style={{ display: 'none' }}
          />
        </label>
      </div>

      {csvResult && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem 1rem', background: '#1e293b', borderRadius: 8, fontSize: 14 }}>
          {csvResult.error
            ? <span style={{ color: '#f87171' }}>CSV error: {csvResult.error}</span>
            : (
              <span style={{ color: '#fbbf24' }}>
                CSV import done — {csvResult.matched} matched, {csvResult.unmatched} unmatched
                {csvResult.unmatched_names?.length > 0 && (
                  <span style={{ color: '#94a3b8' }}>
                    {' '}({csvResult.unmatched_names.join(', ')})
                  </span>
                )}
              </span>
            )}
        </div>
      )}

      {historicalResult && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem 1rem', background: '#1e293b', borderRadius: 8, fontSize: 14 }}>
          {historicalResult.error
            ? <span style={{ color: '#f87171' }}>Error: {historicalResult.error}</span>
            : <span style={{ color: '#c084fc' }}>Historical scrape done — {historicalResult.rows} stat rows added</span>}
        </div>
      )}

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
            subtitle="These players have a salary record but no MoneyPuck stats. Likely minor-league, LTIR, or an ID mismatch."
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

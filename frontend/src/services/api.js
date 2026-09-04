import axios from 'axios';

// Same-origin by default: the built frontend is served by the same Flask app
// that serves /api/*, so an unset/blank REACT_APP_API_URL resolves to a
// relative path instead of a hardcoded host.
const BASE = process.env.REACT_APP_API_URL || '';

const api = axios.create({ baseURL: BASE, timeout: 30000 });

export async function searchPlayers(query) {
  const { data } = await api.get('/api/players/search', { params: { q: query } });
  return data.players || [];
}

export async function getPlayer(playerId) {
  const { data } = await api.get(`/api/player/${playerId}`);
  return data;
}

export async function estimateSalary({ player_id, weights, fa_status, position_filter, n_comparables }) {
  const { data } = await api.post('/api/estimate', {
    player_id,
    weights,
    fa_status: fa_status || 'auto',
    position_filter: position_filter !== false,
    n_comparables: n_comparables || 10,
  });
  return data;
}

export async function triggerScrape() {
  const { data } = await api.post('/api/admin/scrape');
  return data;
}

export async function getMissingData() {
  const { data } = await api.get('/api/admin/missing-data');
  return data;
}

export async function triggerHistoricalScrape() {
  const { data } = await api.post('/api/admin/scrape-historical');
  return data;
}

export async function importCsv(file) {
  if (file) {
    const form = new FormData();
    form.append('file', file);
    const { data } = await api.post('/api/admin/import-csv', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
    return data;
  }
  const { data } = await api.post('/api/admin/import-csv', null, { timeout: 60000 });
  return data;
}

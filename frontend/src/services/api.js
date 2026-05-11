import axios from 'axios';

const BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

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

const configuredBase = document.querySelector('meta[name="api-base"]')?.content;
export const API_BASE = (configuredBase || 'http://127.0.0.1:5000/api').replace(/\/+$/, '');

export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

export async function apiRequest(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, options);
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new ApiError(`Could not connect to the TruthLens API at ${API_BASE}. Start the backend and try again.`, 0, null);
  }

  let payload;
  try {
    payload = await response.json();
  } catch (error) {
    throw new ApiError('The API returned an unreadable response.', response.status, null);
  }

  if (!response.ok) {
    const message = payload?.error?.message || `Request failed with status ${response.status}.`;
    throw new ApiError(message, response.status, payload);
  }
  return payload;
}

export function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function formatBytes(value) {
  if (!Number.isFinite(value) || value < 0) return '—';
  if (value < 1024) return `${value} B`;
  const units = ['KB', 'MB', 'GB'];
  let amount = value / 1024;
  let unit = 0;
  while (amount >= 1024 && unit < units.length - 1) {
    amount /= 1024;
    unit += 1;
  }
  return `${amount.toFixed(1)} ${units[unit]}`;
}

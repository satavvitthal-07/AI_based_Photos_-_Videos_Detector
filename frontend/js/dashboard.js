import { apiRequest, formatDate, API_BASE } from './api.js';
import './app.js';

const tbody = document.querySelector('#recent-analyses');
const errorBox = document.querySelector('#dashboard-error');
const stats = document.querySelector('#stat-cards');
const distribution = document.querySelector('#result-distribution');

function setCell(row, value) {
  const cell = document.createElement('td');
  cell.textContent = value ?? '—';
  row.append(cell);
  return cell;
}

function setError(message) {
  errorBox.textContent = message;
  errorBox.classList.add('visible');
}

async function loadDashboard() {
  try {
    const [data, health] = await Promise.all([
      apiRequest('/dashboard/stats'),
      apiRequest('/health'),
    ]);
    stats.querySelector('[data-stat="total"]').textContent = String(data.total_analyses);
    stats.querySelector('[data-stat="images"]').textContent = String(data.image_analyses);
    stats.querySelector('[data-stat="videos"]').textContent = String(data.video_analyses);
    const model = health.detector?.available
      ? health.detector.model_id
      : health.detector?.configured
        ? 'Configured · lazy load'
        : 'Unavailable';
    stats.querySelector('[data-stat="model"]').textContent = model;
    const records = data.recent || [];
    tbody.replaceChildren();
    if (!records.length) {
      const row = document.createElement('tr');
      const cell = document.createElement('td');
      cell.colSpan = 5;
      const empty = document.createElement('div');
      empty.className = 'empty-state';
      empty.textContent = 'No analyses recorded yet. Upload an image or video to begin.';
      cell.append(empty);
      row.append(cell);
      tbody.append(row);
    } else {
      for (const record of records) {
        const row = document.createElement('tr');
        const file = setCell(row, record.display_name);
        const link = document.createElement('a');
        link.href = `result.html?id=${encodeURIComponent(record.analysis_id)}`;
        link.textContent = record.display_name || 'View report';
        file.replaceChildren(link);
        setCell(row, record.media_type);
        setCell(row, record.prediction);
        setCell(row, record.model_id || 'Unavailable');
        setCell(row, formatDate(record.created_at));
        tbody.append(row);
      }
    }
    const groups = data.result_distribution || [];
    const distributionTotal = groups.reduce((sum, group) => sum + group.count, 0);
    if (distributionTotal < 3) {
      distribution.textContent = 'Distribution appears after at least three completed analyses in the last 30 days.';
    } else {
      const maxCount = Math.max(...groups.map((group) => group.count));
      const list = document.createElement('div');
      list.className = 'distribution-list';
      for (const group of groups) {
        const row = document.createElement('div');
        row.className = 'distribution-row';
        const label = document.createElement('span');
        label.textContent = group.prediction;
        const track = document.createElement('div');
        track.className = 'distribution-track';
        const fill = document.createElement('div');
        fill.className = 'distribution-fill';
        fill.style.width = `${(group.count / maxCount) * 100}%`;
        track.append(fill);
        const count = document.createElement('strong');
        count.textContent = String(group.count);
        row.append(label, track, count);
        list.append(row);
      }
      distribution.replaceChildren(list);
    }
  } catch (error) {
    setError(`${error.message} API: ${API_BASE}`);
    distribution.textContent = 'Distribution data could not be loaded.';
    tbody.innerHTML = '<tr><td colspan="5"><div class="empty-state">Dashboard data could not be loaded.</div></td></tr>';
  }
}

document.querySelectorAll('[data-year]').forEach((element) => { element.textContent = String(new Date().getFullYear()); });
loadDashboard();

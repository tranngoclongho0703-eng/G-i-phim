// script.js
// Lưu ý: KHÔNG thay đổi endpoint /recommend nếu backend của bạn đang dùng đường đó.
// Nếu cần, chỉ sửa const API_URL = '/recommend';

const API_URL = 'http://127.0.0.1:5000/recommend';
const form = document.getElementById('searchForm');
const queryInput = document.getElementById('query');
const statusEl = document.getElementById('status');
const resultsSection = document.getElementById('resultsSection');
const resultsList = document.getElementById('resultsList');
const emptySection = document.getElementById('emptySection');

function setStatus(text, show = true) {
  if (!text) {
    statusEl.hidden = true;
    statusEl.textContent = '';
    return;
  }
  statusEl.hidden = !show;
  statusEl.textContent = text;
}

function clearResults() {
  resultsList.innerHTML = '';
  resultsSection.hidden = true;
}

function renderResults(results) {
  // results: array of { title: "...", similarity: number }
  clearResults();
  if (!results || results.length === 0) {
    emptySection.querySelector('.empty-note').textContent = 'Không tìm thấy phim phù hợp. Thử mô tả rõ hơn hoặc đổi từ khóa.';
    return;
  }

  results.forEach((item, idx) => {
    const li = document.createElement('li');
    li.className = 'result-item';
    li.setAttribute('role', 'listitem');

    const rank = document.createElement('div');
    rank.className = 'result-rank';
    rank.textContent = String(idx + 1);

    const meta = document.createElement('div');
    meta.className = 'result-meta';

    const title = document.createElement('p');
    title.className = 'result-title';
    title.textContent = item.title || 'Untitled';

    const sub = document.createElement('p');
    sub.className = 'result-sub';
    // IMPORTANT: Do not display similarity or any processed/original query.
    // We show a subtle category hint placeholder (optional). If you don't want this line, you can leave it empty.
    sub.textContent = ''; // intentionally left empty per requirements

    meta.appendChild(title);
    meta.appendChild(sub);

    li.appendChild(rank);
    li.appendChild(meta);

    resultsList.appendChild(li);
  });

  resultsSection.hidden = false;
}

/** fetchRecommendations(query)
 *  Sends POST to backend and returns JSON.
 *  Backend expected to return:
 *  {
 *    original_query: "...",
 *    processed_query: "...",
 *    results: [{title: "...", similarity: 0.3781}, ...]
 *  }
 */
async function fetchRecommendations(query) {
  // Minimal payload — keep same shape as existing frontend if any
  const payload = { query: query };

  const resp = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!resp.ok) {
    const text = await resp.text().catch(() => '');
    throw new Error(`Server trả lỗi: ${resp.status} ${resp.statusText} ${text}`);
  }
  return resp.json();
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const q = queryInput.value && queryInput.value.trim();
  if (!q) {
    queryInput.focus();
    return;
  }

  // UI: show loading
  setStatus('Đang tìm...', true);
  clearResults();
  emptySection.querySelector('.empty-note').textContent = '';

  try {
    const data = await fetchRecommendations(q);

    // Backend may return results already sorted by similarity.
    // IMPORTANT: Do not change ranking logic here; we only render what backend returns.
    const results = Array.isArray(data.results) ? data.results.slice(0, 5) : [];

    renderResults(results);

    setStatus('', false);
  } catch (err) {
    console.error(err);
    setStatus(`Có lỗi: ${err.message}`);
    // Leave any previous results cleared
  }
});

// Optional: allow Enter in input to submit (form submit already does that)
// Accessibility: focus input on load
window.addEventListener('load', () => {
  queryInput.focus();
});
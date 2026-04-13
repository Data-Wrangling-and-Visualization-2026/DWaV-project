const AICompare = (() => {
  function init() {
    setupTabs();
    const btn = document.getElementById('ai-run-btn');
    const input = document.getElementById('ai-prompt-input');
    if (!btn || !input) return;
    btn.addEventListener('click', runComparison);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') runComparison();
    });
  }

  function setupTabs() {
    document.querySelectorAll('.view-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const target = tab.dataset.tab;
        document.querySelectorAll('.view-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        document.querySelectorAll('.tab-content').forEach(panel => {
          const shouldShow = panel.dataset.tabContent === target;
          panel.classList.toggle('active', shouldShow);
        });
        const comparePanel = document.getElementById('compare-panel');
        if (comparePanel) comparePanel.style.display = target === 'ai' ? 'none' : '';
      });
    });
  }

  async function runComparison() {
    const input = document.getElementById('ai-prompt-input');
    const status = document.getElementById('ai-status');
    const errorsCard = document.getElementById('ai-errors-card');
    const errorsEl = document.getElementById('ai-errors');
    const annotationsEl = document.getElementById('ai-annotations-list');

    const prompt = (input?.value || '').trim();
    if (!prompt) {
      status.textContent = 'Please enter a query.';
      return;
    }

    status.textContent = 'Running AI parser and comparison...';
    errorsCard.style.display = 'none';
    errorsEl.textContent = '';
    annotationsEl.innerHTML = '';

    try {
      const resp = await fetch('/api/ai/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
      if (!resp.ok) throw new Error(`API error: ${resp.status}`);
      const payload = await resp.json();

      const errors = payload.errors || [];
      if (errors.length > 0) {
        errorsCard.style.display = '';
        errorsEl.innerHTML = errors.map(e => `<div>• ${escapeHtml(String(e))}</div>`).join('');
      }

      status.textContent = `Query parsed via ${payload.parser}. Rendering ${payload.result.series.length} series.`;
      safeUpdateAIChart(payload.result, status);
      renderAnnotations(payload.result.annotations || []);
    } catch (err) {
      status.textContent = `AI comparison failed: ${err.message}`;
      errorsCard.style.display = '';
      errorsEl.textContent = 'Please ensure backend is running and Ollama is available.';
    }
  }

  function safeUpdateAIChart(result, statusEl) {
    if (typeof Charts !== 'undefined' && typeof Charts.updateAIComparison === 'function') {
      Charts.updateAIComparison(result);
      return;
    }
    if (statusEl) {
      statusEl.textContent = 'AI comparison loaded, but chart renderer is outdated. Please hard refresh browser (Ctrl+Shift+R).';
    }
  }

  function renderAnnotations(items) {
    const container = document.getElementById('ai-annotations-list');
    if (!container) return;
    if (!items.length) {
      container.innerHTML = '<div class="event-empty">No major change annotations found for this query.</div>';
      return;
    }
    container.innerHTML = items.slice(0, 30).map(a => `
      <div class="event-item">
        <div class="event-head">
          <span class="event-date">Wave ${a.wave}</span>
          <span class="event-type">${a.country} / ${a.metric}</span>
        </div>
        <div class="event-title">${escapeHtml(a.label || '')}</div>
      </div>
    `).join('');
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  return { init };
})();

document.addEventListener('DOMContentLoaded', () => {
  AICompare.init();
});

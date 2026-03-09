/**
 * WVS Explorer — Comparison Panel
 * Multi-country overlay line chart + Welzel radar chart.
 */
const Compare = (() => {
  let compareTrendChart = null;
  let compareRadarChart = null;

  const PALETTE = [
    '#4fc3f7', '#ff7043', '#66bb6a', '#ffd54f', '#ab47bc',
    '#26c6da', '#ef5350', '#8d6e63', '#78909c', '#ec407a',
  ];

  function init(state) {
    document.getElementById('clear-compare-btn').addEventListener('click', clearAll);
  }

  function addCountry(cc) {
    const state = App.state;
    if (state.compareCountries.includes(cc)) return;
    if (state.compareCountries.length >= 10) return; // max 10

    state.compareCountries.push(cc);
    updateTags();
    updateCharts();
    updateCount();

    // Expand panel if first country
    const panel = document.getElementById('compare-panel');
    if (state.compareCountries.length === 1) {
      panel.classList.remove('compare-collapsed');
      panel.classList.add('compare-expanded');
    }
  }

  function removeCountry(cc) {
    const state = App.state;
    state.compareCountries = state.compareCountries.filter(c => c !== cc);
    updateTags();
    updateCharts();
    updateCount();

    if (state.compareCountries.length === 0) {
      const panel = document.getElementById('compare-panel');
      panel.classList.add('compare-collapsed');
      panel.classList.remove('compare-expanded');
    }
  }

  function clearAll() {
    App.state.compareCountries = [];
    updateTags();
    updateCharts();
    updateCount();
    const panel = document.getElementById('compare-panel');
    panel.classList.add('compare-collapsed');
    panel.classList.remove('compare-expanded');
  }

  function updateCount() {
    const n = App.state.compareCountries.length;
    document.getElementById('compare-count').textContent =
      `${n} ${n === 1 ? 'country' : 'countries'} selected`;
  }

  function updateTags() {
    const container = document.getElementById('compare-tags');
    const state = App.state;
    container.innerHTML = state.compareCountries.map((cc, i) => {
      const name = state.alphaToName[cc] || cc;
      const color = PALETTE[i % PALETTE.length];
      return `<div class="compare-tag" style="border-color: ${color}">
        <span style="color: ${color}">${name}</span>
        <span class="tag-remove" onclick="Compare.removeCountry('${cc}')">&times;</span>
      </div>`;
    }).join('');
  }

  async function updateCharts() {
    const state = App.state;
    const codes = state.compareCountries;

    if (codes.length === 0) {
      if (compareTrendChart) { compareTrendChart.destroy(); compareTrendChart = null; }
      if (compareRadarChart) { compareRadarChart.destroy(); compareRadarChart = null; }
      return;
    }

    // ── Trend comparison ──────────────────────────────────────
    try {
      const joinedCodes = codes.join(',');
      const trendData = await App.api(
        `/trend/${state.selectedTheme}/${state.selectedMetric}?countries=${joinedCodes}`
      );

      // All possible waves
      const allWaves = new Set();
      Object.values(trendData).forEach(arr => arr.forEach(d => allWaves.add(d.wave)));
      const sortedWaves = [...allWaves].sort((a, b) => a - b);
      const labels = sortedWaves.map(w => `W${w}`);

      const datasets = codes.map((cc, i) => {
        const color = PALETTE[i % PALETTE.length];
        const waveMap = {};
        (trendData[cc] || []).forEach(d => { waveMap[d.wave] = d.mean; });
        return {
          label: state.alphaToName[cc] || cc,
          data: sortedWaves.map(w => waveMap[w] ?? null),
          borderColor: color,
          backgroundColor: color + '22',
          fill: false,
          tension: 0.3,
          pointRadius: 4,
          pointHoverRadius: 6,
          borderWidth: 2,
          spanGaps: true,
        };
      });

      const ctx = document.getElementById('compare-trend-chart');
      if (compareTrendChart) compareTrendChart.destroy();
      compareTrendChart = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              position: 'bottom',
              labels: { color: '#8a9bb0', font: { size: 11 }, boxWidth: 12 },
            },
          },
          scales: {
            x: { ticks: { color: '#8a9bb0' }, grid: { color: 'rgba(255,255,255,0.08)' } },
            y: { ticks: { color: '#8a9bb0' }, grid: { color: 'rgba(255,255,255,0.08)' } },
          },
        },
      });
    } catch (err) {
      console.error('Trend comparison failed:', err);
    }

    // ── Radar: Welzel indices ──────────────────────────────────
    try {
      const welzelMetrics = ['emancip', 'secular', 'autonomy', 'equality', 'choice', 'voice'];
      const radarLabels = ['Emancipative', 'Secular', 'Autonomy', 'Equality', 'Choice', 'Voice'];

      // Fetch welzel data for all countries
      const welzelPromises = welzelMetrics.map(m =>
        App.api(`/trend/welzel_indices/${m}?countries=${codes.join(',')}`)
      );
      const welzelResults = await Promise.all(welzelPromises);

      const datasets = codes.map((cc, i) => {
        const color = PALETTE[i % PALETTE.length];
        const values = welzelMetrics.map((m, mi) => {
          const countryData = welzelResults[mi][cc] || [];
          // Use latest wave
          if (countryData.length === 0) return null;
          return countryData[countryData.length - 1].mean;
        });
        return {
          label: state.alphaToName[cc] || cc,
          data: values,
          borderColor: color,
          backgroundColor: color + '33',
          pointBackgroundColor: color,
          borderWidth: 2,
          pointRadius: 3,
        };
      });

      const ctx = document.getElementById('compare-radar-chart');
      if (compareRadarChart) compareRadarChart.destroy();
      compareRadarChart = new Chart(ctx, {
        type: 'radar',
        data: { labels: radarLabels, datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              position: 'bottom',
              labels: { color: '#8a9bb0', font: { size: 11 }, boxWidth: 12 },
            },
          },
          scales: {
            r: {
              beginAtZero: true,
              max: 1,
              ticks: { color: '#8a9bb0', backdropColor: 'transparent', font: { size: 10 } },
              grid: { color: 'rgba(255,255,255,0.1)' },
              angleLines: { color: 'rgba(255,255,255,0.1)' },
              pointLabels: { color: '#8a9bb0', font: { size: 11 } },
            },
          },
        },
      });
    } catch (err) {
      console.error('Radar chart failed:', err);
    }
  }

  return { init, addCountry, removeCountry, clearAll, updateCharts };
})();

/**
 * WVS Explorer — Chart.js Components
 * Trend line chart and distribution bar chart for the detail panel.
 */
const Charts = (() => {
  let trendChart = null;
  let distChart = null;
  let aiCompareChart = null;

  const CHART_COLORS = {
    line: '#4fc3f7',
    lineBg: 'rgba(79,195,247,0.15)',
    bar: '#4fc3f7',
    barHover: '#29b6f6',
    grid: 'rgba(255,255,255,0.08)',
    text: '#8a9bb0',
  };

  const COMMON_OPTIONS = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
    },
    scales: {
      x: {
        ticks: { color: CHART_COLORS.text, font: { size: 11 } },
        grid: { color: CHART_COLORS.grid },
      },
      y: {
        ticks: { color: CHART_COLORS.text, font: { size: 11 } },
        grid: { color: CHART_COLORS.grid },
      },
    },
  };

  function updateTrend(waveData, waveLabelMap) {
    const ctx = document.getElementById('trend-chart');
    if (trendChart) trendChart.destroy();

    const labels = waveData.map(d => `W${d.wave}`);
    const values = waveData.map(d => d.mean);

    trendChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          data: values,
          borderColor: CHART_COLORS.line,
          backgroundColor: CHART_COLORS.lineBg,
          fill: true,
          tension: 0.3,
          pointRadius: 5,
          pointHoverRadius: 7,
          pointBackgroundColor: CHART_COLORS.line,
          borderWidth: 2,
        }],
      },
      options: {
        ...COMMON_OPTIONS,
        plugins: {
          ...COMMON_OPTIONS.plugins,
          tooltip: {
            callbacks: {
              title: (items) => {
                const w = waveData[items[0].dataIndex];
                const label = waveLabelMap[String(w.wave)] || '';
                return `Wave ${w.wave} (${label})`;
              },
              label: (item) => {
                const w = waveData[item.dataIndex];
                return `Mean: ${item.raw?.toFixed(3) || 'N/A'}  (n=${(w.n || 0).toLocaleString()})`;
              },
            },
          },
        },
      },
    });
  }

  function updateDistribution(dist) {
    const ctx = document.getElementById('dist-chart');
    if (distChart) distChart.destroy();

    // Sort by count descending
    const entries = Object.entries(dist).sort((a, b) => b[1] - a[1]);
    const labels = entries.map(e => truncate(e[0], 25));
    const values = entries.map(e => e[1]);
    const total = values.reduce((a, b) => a + b, 0);

    distChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          data: values,
          backgroundColor: CHART_COLORS.bar,
          hoverBackgroundColor: CHART_COLORS.barHover,
          borderRadius: 4,
        }],
      },
      options: {
        ...COMMON_OPTIONS,
        indexAxis: 'y',
        plugins: {
          ...COMMON_OPTIONS.plugins,
          tooltip: {
            callbacks: {
              label: (item) => {
                const pct = total > 0 ? ((item.raw / total) * 100).toFixed(1) : 0;
                return `${item.raw.toLocaleString()} (${pct}%)`;
              },
            },
          },
        },
        scales: {
          ...COMMON_OPTIONS.scales,
          x: {
            ...COMMON_OPTIONS.scales.x,
            beginAtZero: true,
          },
          y: {
            ...COMMON_OPTIONS.scales.y,
            ticks: {
              ...COMMON_OPTIONS.scales.y.ticks,
              font: { size: 10 },
            },
          },
        },
      },
    });
  }

  function truncate(str, max) {
    return str.length > max ? str.slice(0, max - 2) + '..' : str;
  }

  function updateAIComparison(result) {
    const ctx = document.getElementById('ai-compare-chart');
    if (!ctx) return;
    if (aiCompareChart) aiCompareChart.destroy();

    const waves = result?.waves || [];
    const labels = waves.map(w => `W${w}`);
    const palette = ['#4fc3f7', '#ff7043', '#66bb6a', '#ffd54f', '#ab47bc', '#26c6da'];

    const datasets = (result?.series || []).map((s, i) => ({
      type: 'line',
      label: `${s.country_name} · ${s.metric_name}`,
      data: waves.map(w => {
        const point = (s.points || []).find(p => p.wave === w);
        return point ? point.mean : null;
      }),
      borderColor: palette[i % palette.length],
      backgroundColor: palette[i % palette.length] + '33',
      tension: 0.25,
      spanGaps: true,
      pointRadius: 3,
      borderWidth: 2,
    }));

    const annotationDataset = {
      type: 'scatter',
      label: 'Event annotations',
      data: (result?.annotations || []).map(a => ({ x: `W${a.wave}`, y: a.value, label: a.label })),
      pointBackgroundColor: '#ef5350',
      pointBorderColor: '#ef5350',
      pointRadius: 5,
      pointHoverRadius: 7,
      showLine: false,
    };
    if ((result?.annotations || []).length > 0) datasets.push(annotationDataset);

    aiCompareChart = new Chart(ctx, {
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: true, position: 'bottom', labels: { color: CHART_COLORS.text, boxWidth: 12 } },
          tooltip: {
            callbacks: {
              label: (item) => {
                if (item.dataset.type === 'scatter') {
                  return item.raw?.label || 'Annotation';
                }
                return `${item.dataset.label}: ${item.raw?.toFixed?.(3) ?? 'N/A'}`;
              },
            },
          },
        },
        scales: {
          x: { ticks: { color: CHART_COLORS.text }, grid: { color: CHART_COLORS.grid } },
          y: { ticks: { color: CHART_COLORS.text }, grid: { color: CHART_COLORS.grid } },
        },
      },
    });
  }

  return { updateTrend, updateDistribution, updateAIComparison };
})();

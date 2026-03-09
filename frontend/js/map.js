/**
 * WVS Explorer — D3 World Map Component
 * Choropleth map with zoom, tooltips, and country selection.
 */
const WorldMap = (() => {
  let svg, g, projection, path, colorScale, zoom;
  let appState;
  let worldGeo;
  let highlightedCC = null;

  const TOPO_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json';

  // Color palette: sequential blue
  const COLOR_RANGE = ['#e3f2fd', '#90caf9', '#42a5f5', '#1e88e5', '#1565c0', '#0d47a1'];
  const NO_DATA_COLOR = '#1a2634';
  const HIGHLIGHT_STROKE = '#ffd54f';

  async function init(state) {
    appState = state;
    const container = document.getElementById('map-container');
    const width = container.clientWidth;
    const height = container.clientHeight;

    svg = d3.select('#map-container')
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    g = svg.append('g');

    projection = d3.geoNaturalEarth1()
      .scale(width / 5.5)
      .translate([width / 2, height / 2]);

    path = d3.geoPath().projection(projection);

    colorScale = d3.scaleQuantize().range(COLOR_RANGE);

    // Zoom
    zoom = d3.zoom()
      .scaleExtent([1, 8])
      .on('zoom', (event) => g.attr('transform', event.transform));
    svg.call(zoom);

    // Load world topology
    const world = await d3.json(TOPO_URL);
    worldGeo = topojson.feature(world, world.objects.countries).features;

    // Draw countries
    g.selectAll('path.country')
      .data(worldGeo)
      .enter()
      .append('path')
      .attr('class', 'country')
      .attr('d', path)
      .attr('fill', NO_DATA_COLOR)
      .attr('stroke', '#2d3e50')
      .attr('stroke-width', 0.5)
      .on('mouseover', onHover)
      .on('mousemove', onMove)
      .on('mouseout', onOut)
      .on('click', onClick);

    // Resize handler
    window.addEventListener('resize', () => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      svg.attr('width', w).attr('height', h);
      projection.scale(w / 5.5).translate([w / 2, h / 2]);
      g.selectAll('path.country').attr('d', path);
    });
  }

  function getAlphaFromFeature(feature) {
    const numId = String(feature.id).padStart(3, '0');
    return appState.numericToAlpha[numId] || null;
  }

  function update(mapData) {
    if (!worldGeo) return;

    // Compute domain from data
    const values = Object.values(mapData).map(d => d.mean).filter(v => v != null);
    if (values.length > 0) {
      const extent = d3.extent(values);
      colorScale.domain(extent);
    }

    // Update fills
    g.selectAll('path.country')
      .transition()
      .duration(400)
      .attr('fill', function(d) {
        const cc = getAlphaFromFeature(d);
        if (!cc || !mapData[cc] || mapData[cc].mean == null) return NO_DATA_COLOR;
        return colorScale(mapData[cc].mean);
      });

    // Update legend
    updateLegend(colorScale);
  }

  function updateLegend(scale) {
    const legend = document.getElementById('map-legend');
    const domain = scale.domain();
    if (!domain || domain[0] == null) {
      legend.innerHTML = '';
      return;
    }

    const lo = domain[0], hi = domain[1];
    const gradient = COLOR_RANGE.map((c, i) => {
      const pct = (i / (COLOR_RANGE.length - 1)) * 100;
      return `${c} ${pct}%`;
    }).join(', ');

    legend.innerHTML = `
      <span>${lo.toFixed(2)}</span>
      <div class="legend-bar" style="background: linear-gradient(to right, ${gradient})"></div>
      <span>${hi.toFixed(2)}</span>
    `;
  }

  function highlight(cc) {
    highlightedCC = cc;
    g.selectAll('path.country')
      .attr('stroke', function(d) {
        return getAlphaFromFeature(d) === cc ? HIGHLIGHT_STROKE : '#2d3e50';
      })
      .attr('stroke-width', function(d) {
        return getAlphaFromFeature(d) === cc ? 2 : 0.5;
      });
  }

  // ── Tooltip Handlers ───────────────────────────────────────
  const tooltip = document.getElementById('map-tooltip');

  function onHover(event, d) {
    const cc = getAlphaFromFeature(d);
    const name = cc ? (appState.alphaToName[cc] || cc) : 'Unknown';
    const data = cc ? appState.mapData[cc] : null;

    let html = `<div class="tt-name">${name}</div>`;
    if (data && data.mean != null) {
      html += `<div class="tt-value">Value: <strong>${data.mean.toFixed(3)}</strong></div>`;
      html += `<div class="tt-n">n = ${(data.n || 0).toLocaleString()}</div>`;
    } else {
      html += `<div class="tt-value" style="color: var(--text-secondary)">No data</div>`;
    }
    tooltip.innerHTML = html;
    tooltip.style.display = 'block';

    d3.select(this).attr('opacity', 0.8);
  }

  function onMove(event) {
    tooltip.style.left = (event.clientX + 14) + 'px';
    tooltip.style.top = (event.clientY - 10) + 'px';
  }

  function onOut(event, d) {
    tooltip.style.display = 'none';
    d3.select(this).attr('opacity', 1);
  }

  function onClick(event, d) {
    const cc = getAlphaFromFeature(d);
    if (cc) App.selectCountry(cc);
  }

  return { init, update, highlight };
})();

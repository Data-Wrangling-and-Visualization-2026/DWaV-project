/**
 * WVS Explorer — Main App Logic
 * State management, API calls, and UI orchestration.
 */
const App = (() => {
  // ── Metric descriptions for new users ──────────────────────
  // Explains what each metric measures, its scale, and what high/low values mean
  const METRIC_DESC = {
    // Demographics
    sex:    { desc: "Biological sex of the respondent.", scale: "Male / Female" },
    age:    { desc: "Age of the respondent in years at the time of the survey.", scale: "Numeric (years)" },
    edu:    { desc: "Highest education level completed by the respondent.", scale: "Lower / Middle / Upper" },
    emp:    { desc: "Current employment status of the respondent.", scale: "Full time, Part time, Retired, Students, etc." },
    income: { desc: "How the respondent rates their own household income on a 10-step scale.", scale: "1 = lowest income group, 10 = highest income group" },
    marital:{ desc: "Current marital status of the respondent.", scale: "Married, Single, Divorced, Widowed, etc." },
    // Values & Happiness
    happy:      { desc: "\"Taking all things together, would you say you are happy?\" Measures general subjective well-being.", scale: "1 = Not at all happy, 4 = Very happy. Higher = happier." },
    life_sat:   { desc: "\"How satisfied are you with your life as a whole these days?\" A standard life satisfaction question.", scale: "1 = Completely dissatisfied, 10 = Completely satisfied." },
    health:     { desc: "\"How would you describe your state of health these days?\" Self-reported health status.", scale: "1 = Poor, 4 = Very good." },
    freedom:    { desc: "\"How much freedom of choice and control do you feel you have over your life?\"", scale: "1 = No choice at all, 10 = A great deal of choice." },
    imp_family: { desc: "\"How important is family in your life?\" Measures the value placed on family.", scale: "1 = Not at all important, 4 = Very important." },
    imp_work:   { desc: "\"How important is work in your life?\" Measures the value placed on work.", scale: "1 = Not at all important, 4 = Very important." },
    // Trust & Institutions
    trust:   { desc: "\"Generally speaking, would you say that most people can be trusted?\" A key measure of social capital.", scale: "0 = Need to be very careful, 1 = Most people can be trusted. Higher = more trusting." },
    gov:     { desc: "\"How much confidence do you have in the government?\"", scale: "1 = None at all, 4 = A great deal. Higher = more confidence." },
    police:  { desc: "\"How much confidence do you have in the police?\"", scale: "1 = None at all, 4 = A great deal." },
    army:    { desc: "\"How much confidence do you have in the armed forces?\"", scale: "1 = None at all, 4 = A great deal." },
    press:   { desc: "\"How much confidence do you have in the press?\"", scale: "1 = None at all, 4 = A great deal." },
    justice: { desc: "\"How much confidence do you have in the justice system / courts?\"", scale: "1 = None at all, 4 = A great deal." },
    // Politics
    interest: { desc: "\"How interested would you say you are in politics?\"", scale: "1 = Not at all interested, 4 = Very interested." },
    lr_scale: { desc: "\"In political matters, where would you place yourself?\" The classic left-right self-positioning scale.", scale: "1 = Far left, 10 = Far right. 5-6 = Center." },
    democracy:{ desc: "\"How important is it for you to live in a country that is governed democratically?\"", scale: "1 = Not at all important, 10 = Absolutely important." },
    sys_demo: { desc: "\"Would having a democratic political system be a good way of governing this country?\"", scale: "1 = Very bad, 4 = Very good." },
    sys_leader:{ desc: "\"Would having a strong leader who does not have to bother with parliament be good?\"", scale: "1 = Very bad, 4 = Very good. Higher = more support for authoritarianism." },
    econ_eq:  { desc: "\"Should incomes be made more equal, or do we need larger differences as incentives?\"", scale: "1 = Incomes should be more equal, 10 = Need larger differences." },
    // Social & Cultural
    religious:  { desc: "\"Would you say you are a religious person, not a religious person, or an atheist?\"", scale: "1 = Convinced atheist, 3 = A religious person." },
    god_imp:    { desc: "\"How important is God in your life?\"", scale: "1 = Not at all important, 10 = Very important." },
    nbr_race:   { desc: "\"Would you not like to have people of a different race as neighbors?\" Measures racial tolerance.", scale: "0 = Not mentioned (tolerant), 1 = Mentioned (intolerant). Lower = more tolerant." },
    nbr_immig:  { desc: "\"Would you not like to have immigrants/foreign workers as neighbors?\"", scale: "0 = Not mentioned (tolerant), 1 = Mentioned (intolerant). Lower = more tolerant." },
    nbr_homo:   { desc: "\"Would you not like to have homosexuals as neighbors?\"", scale: "0 = Not mentioned (tolerant), 1 = Mentioned (intolerant). Lower = more tolerant." },
    child_indep:{ desc: "\"Is independence an important quality for children to learn at home?\"", scale: "0 = Not mentioned, 1 = Important. Higher = more emphasis on independence." },
    // Moral Views
    bribe:   { desc: "\"Is it justifiable for someone to accept a bribe in the course of their duties?\"", scale: "1 = Never justifiable, 10 = Always justifiable." },
    homo:    { desc: "\"Is homosexuality justifiable?\" Measures moral acceptance of homosexuality.", scale: "1 = Never justifiable, 10 = Always justifiable." },
    abort:   { desc: "\"Is abortion justifiable?\" Measures moral acceptance of abortion.", scale: "1 = Never justifiable, 10 = Always justifiable." },
    divorce: { desc: "\"Is divorce justifiable?\"", scale: "1 = Never justifiable, 10 = Always justifiable." },
    suicide: { desc: "\"Is suicide justifiable?\"", scale: "1 = Never justifiable, 10 = Always justifiable." },
    postmat: { desc: "Post-Materialism Index (Inglehart). Measures whether people prioritize material security or self-expression.", scale: "1 = Materialist, 2 = Mixed, 3 = Post-materialist. Higher = more post-materialist." },
    // Welzel Indices
    emancip: { desc: "Welzel Emancipative Values Index. Combines autonomy, equality, choice, and voice. Higher values indicate stronger support for human empowerment.", scale: "0 to 1. Higher = more emancipative." },
    secular: { desc: "Welzel Secular Values Index. Measures how secular (vs. traditional/religious) a society's values are.", scale: "0 to 1. Higher = more secular." },
    autonomy:{ desc: "Welzel Autonomy Sub-index. Emphasizes independence and imagination as important child qualities.", scale: "0 to 1. Higher = more emphasis on autonomy." },
    equality:{ desc: "Welzel Equality Sub-index. Measures support for gender equality in jobs, politics, and education.", scale: "0 to 1. Higher = more gender-egalitarian." },
    choice:  { desc: "Welzel Choice Sub-index. Measures tolerance for personal lifestyle choices (homosexuality, abortion, divorce).", scale: "0 to 1. Higher = more tolerant." },
    voice:   { desc: "Welzel Voice Sub-index. Measures support for freedom of speech and political participation.", scale: "0 to 1. Higher = more support for voice/participation." },
  };

  // ── State ──────────────────────────────────────────────────
  const state = {
    countries: [],
    themes: [],
    waves: {},
    numericToAlpha: {},   // "840" -> "USA"
    alphaToName: {},      // "USA" -> "United States"
    selectedTheme: null,
    selectedMetric: null,
    selectedWave: null,   // null = latest
    selectedCountry: null,
    compareCountries: [],
    mapData: {},
  };

  // ── API ────────────────────────────────────────────────────
  async function api(path) {
    const resp = await fetch(`/api${path}`);
    if (!resp.ok) throw new Error(`API error: ${resp.status}`);
    return resp.json();
  }

  // ── Init ───────────────────────────────────────────────────
  async function init() {
    try {
      const [countries, themes, waves] = await Promise.all([
        api('/countries'), api('/themes'), api('/waves'),
      ]);

      state.countries = countries;
      state.themes = themes;
      state.waves = waves;

      // Build lookups
      countries.forEach(c => {
        if (c.numeric) state.numericToAlpha[c.numeric] = c.code;
        state.alphaToName[c.code] = c.name;
      });

      populateControls();
      setupSearch();
      setupDetailPanel();

      // Default selection
      state.selectedTheme = themes[1]?.id || themes[0]?.id; // values_and_happiness
      updateMetricDropdown();
      state.selectedMetric = document.getElementById('metric-select').value;

      await WorldMap.init(state);
      await updateMap();
      updateDescriptions();

      Compare.init(state);

      document.getElementById('loading-spinner').style.display = 'none';
    } catch (err) {
      console.error('Init failed:', err);
      document.getElementById('loading-spinner').textContent = 'Failed to load data. Is the backend running?';
    }
  }

  // ── Controls ───────────────────────────────────────────────
  function populateControls() {
    const themeSelect = document.getElementById('theme-select');
    state.themes.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.id;
      opt.textContent = t.name;
      themeSelect.appendChild(opt);
    });
    themeSelect.value = state.themes[1]?.id || state.themes[0]?.id;
    themeSelect.addEventListener('change', onThemeChange);

    const waveSelect = document.getElementById('wave-select');
    Object.entries(state.waves).sort((a, b) => +a[0] - +b[0]).forEach(([num, label]) => {
      const opt = document.createElement('option');
      opt.value = num;
      opt.textContent = `Wave ${num} (${label})`;
      waveSelect.appendChild(opt);
    });
    waveSelect.addEventListener('change', onWaveChange);

    document.getElementById('metric-select').addEventListener('change', onMetricChange);

    // Populate compare country dropdown
    const compareSelect = document.getElementById('compare-country-select');
    state.countries.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.code;
      opt.textContent = `${c.name} (${c.code})`;
      compareSelect.appendChild(opt);
    });
    compareSelect.addEventListener('change', (e) => {
      if (e.target.value) {
        Compare.addCountry(e.target.value);
        e.target.value = '';
      }
    });
  }

  function updateMetricDropdown() {
    const metricSelect = document.getElementById('metric-select');
    metricSelect.innerHTML = '';
    const theme = state.themes.find(t => t.id === state.selectedTheme);
    if (!theme) return;
    theme.metrics.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m.id;
      opt.textContent = m.name;
      metricSelect.appendChild(opt);
    });
    state.selectedMetric = metricSelect.value;
  }

  async function onThemeChange(e) {
    state.selectedTheme = e.target.value;
    updateMetricDropdown();
    updateDescriptions();
    await updateMap();
    if (state.selectedCountry) updateDetail(state.selectedCountry);
    Compare.updateCharts();
  }

  async function onMetricChange(e) {
    state.selectedMetric = e.target.value;
    updateDescriptions();
    await updateMap();
    if (state.selectedCountry) updateDetail(state.selectedCountry);
    Compare.updateCharts();
  }

  async function onWaveChange(e) {
    state.selectedWave = e.target.value || null;
    await updateMap();
    if (state.selectedCountry) updateDetail(state.selectedCountry);
  }

  // ── Search ─────────────────────────────────────────────────
  function setupSearch() {
    const input = document.getElementById('country-search');
    const dropdown = document.getElementById('search-results');

    input.addEventListener('input', () => {
      const q = input.value.toLowerCase().trim();
      if (!q) { dropdown.classList.remove('active'); return; }
      const matches = state.countries.filter(c =>
        c.name.toLowerCase().includes(q) || c.code.toLowerCase().includes(q)
      ).slice(0, 10);
      dropdown.innerHTML = matches.map(c =>
        `<div class="search-item" data-code="${c.code}">${c.name} (${c.code})</div>`
      ).join('');
      dropdown.classList.add('active');
      dropdown.querySelectorAll('.search-item').forEach(el => {
        el.addEventListener('click', () => {
          selectCountry(el.dataset.code);
          input.value = '';
          dropdown.classList.remove('active');
        });
      });
    });

    document.addEventListener('click', (e) => {
      if (!e.target.closest('.search-group')) dropdown.classList.remove('active');
    });
  }

  // ── Descriptions ──────────────────────────────────────────
  function updateDescriptions() {
    const mid = state.selectedMetric;
    const info = METRIC_DESC[mid];
    const metricName = document.getElementById('metric-select').selectedOptions[0]?.textContent || mid;
    const themeName = document.getElementById('theme-select').selectedOptions[0]?.textContent || '';

    // Top description bar
    const descBar = document.getElementById('metric-desc-text');
    if (info) {
      descBar.innerHTML = `<strong>${metricName}</strong> &mdash; ${info.desc}<br><span style="color:var(--accent)">Scale:</span> ${info.scale}`;
    } else {
      descBar.textContent = `Showing ${metricName} from the ${themeName} theme across 108 countries.`;
    }

    // Legend description
    const legendDesc = document.getElementById('map-legend-desc');
    if (info) {
      legendDesc.textContent = `Map color intensity = average ${metricName} score per country. ${info.scale}`;
    } else {
      legendDesc.textContent = `Map color = average value of ${metricName} per country.`;
    }

    // Trend chart description
    const trendDesc = document.getElementById('trend-desc');
    if (info) {
      trendDesc.innerHTML = `How <strong>${metricName}</strong> changed over time in this country. Each dot is the country average for that survey wave. ${info.scale}`;
    }

    // Distribution chart description
    const distDesc = document.getElementById('dist-desc');
    if (info) {
      distDesc.innerHTML = `Breakdown of how people in this country responded. Each bar shows the count for one answer option. ${info.desc}`;
    }
  }

  // ── Map Data ───────────────────────────────────────────────
  async function updateMap() {
    const { selectedTheme, selectedMetric, selectedWave } = state;
    if (!selectedTheme || !selectedMetric) return;
    const wavePart = selectedWave ? `?wave=${selectedWave}` : '';
    state.mapData = await api(`/map/${selectedTheme}/${selectedMetric}${wavePart}`);
    WorldMap.update(state.mapData);
  }

  // ── Country Selection ──────────────────────────────────────
  function selectCountry(cc) {
    state.selectedCountry = cc;
    WorldMap.highlight(cc);
    updateDetail(cc);
    const panel = document.getElementById('detail-panel');
    panel.classList.remove('panel-closed');
    // Hide hint after first interaction
    const hint = document.getElementById('map-hint');
    if (hint) hint.style.opacity = '0';
  }

  function setupDetailPanel() {
    document.getElementById('detail-close').addEventListener('click', () => {
      document.getElementById('detail-panel').classList.add('panel-closed');
      state.selectedCountry = null;
      WorldMap.highlight(null);
    });

    document.getElementById('add-compare-btn').addEventListener('click', () => {
      if (state.selectedCountry) {
        Compare.addCountry(state.selectedCountry);
      }
    });
  }

  async function updateDetail(cc) {
    const name = state.alphaToName[cc] || cc;
    document.getElementById('detail-country-name').textContent = name;
    document.getElementById('detail-country-code').textContent = cc;

    // Trend chart
    const trendData = await api(`/trend/${state.selectedTheme}/${state.selectedMetric}?countries=${cc}`);
    Charts.updateTrend(trendData[cc] || [], state.waves);

    // Distribution chart
    const wave = state.selectedWave || null;
    try {
      const distData = await api(`/distribution/${state.selectedTheme}/${state.selectedMetric}/${cc}${wave ? '?wave=' + wave : ''}`);
      const waveLabel = distData.wave ? `Wave ${distData.wave}` : 'Latest';
      document.getElementById('dist-title').textContent = `Distribution (${waveLabel}, n=${(distData.n || 0).toLocaleString()})`;
      Charts.updateDistribution(distData.dist || {});
    } catch {
      Charts.updateDistribution({});
      document.getElementById('dist-title').textContent = 'No distribution data';
    }
  }

  // ── Public ─────────────────────────────────────────────────
  return { init, state, api, selectCountry, updateMap };
})();

function toggleCompare() {
  const panel = document.getElementById('compare-panel');
  panel.classList.toggle('compare-collapsed');
  panel.classList.toggle('compare-expanded');
}

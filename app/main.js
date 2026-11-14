// Owner: 06 · App developer (Darius)
// The page logic. It reads products/<site>/ only (file contracts in docs/build-spec.md; design and the 06 handoff in
// docs/ui.md). No measured number is typed in this file: every value on screen comes from the products files.
import * as maplibregl from 'https://unpkg.com/maplibre-gl@6.15.0/dist/maplibre-gl.mjs';

// ------------------------------------------------------------------------------------------------ fixed UI settings
const ZOOM_OFFSET = 1;     // manifest.view.zoom uses 256 px tiles (Google Maps, D-002); MapLibre uses 512 px tiles
const SHARP_ZOOM = 10;     // MapLibre zoom below which Romania is blurred context (D-002)
const PLAY_MS = 600;       // one acquisition per step (docs/ui.md)
const LIMITED_PX = 10;     // a zone result resting on fewer pixels than this is flagged "Limited coverage"
const SATS = {
  nisar: { mark: '●', cls: 'mk-nisar', color: '#D97706', shape: 'dot', name: 'NISAR' },
  s1: { mark: '▲', cls: 'mk-s1', color: '#7C3AED', shape: 'tri', name: 'Sentinel-1' },
};
const ARROW = { Ascending: '↗', Descending: '↘' };
const VIEW_LABEL = { change: 'Change', rate: 'Rate', zones: 'Zones', agreement: 'Agreement', coverage: 'Coverage' };
const MEASURED_VIEWS = ['change', 'rate', 'zones'];
const SHEET_VIEWS = ['zones', 'agreement', 'coverage'];
const STATUS_ICON = { pass: '✔', warn: '!', fail: '✘', info: '·' };
const BASEMAPS = {
  light: {   // OpenFreeMap: free vector tiles, no API key
    label: 'Light',
    style: 'https://tiles.openfreemap.org/styles/positron',
    attribution: '<a href="https://openfreemap.org" target="_blank" rel="noopener">OpenFreeMap</a> © <a href="https://www.openmaptiles.org/" target="_blank" rel="noopener">OpenMapTiles</a>, data from <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>',
  },
  satellite: {
    label: 'Satellite',
    tiles: ['https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg'],
    maxzoom: 15,
    attribution: '<a href="https://s2maps.eu" target="_blank" rel="noopener">Sentinel-2 cloudless 2020</a> by EOX IT Services GmbH (contains modified Copernicus Sentinel data 2020)',
  },
};
const PLAY_PATH = 'M8 5v14l11-7z', PAUSE_PATH = 'M7 5h4v14H7zM13 5h4v14h-4z';

// ------------------------------------------------------------------------------------------------ helpers
const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const day = (d) => Date.parse(d + 'T00:00:00Z') / 864e5;
const iso = (t) => new Date(t * 864e5).toISOString().slice(0, 10);
const fmt = (v, digits) => (v === null || v === undefined || Number.isNaN(v)) ? 'n/a'
  : `${v > 0 ? '+' : v < 0 ? '−' : ''}${digits === undefined ? Math.abs(v) : Math.abs(v).toFixed(digits)}`;
const human = (d, year = true) => new Date(d + 'T00:00:00Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', ...(year ? { year: 'numeric' } : {}), timeZone: 'UTC' });
const nearest = (dates, d) => dates.reduce((a, b) => Math.abs(day(b) - day(d)) < Math.abs(day(a) - day(d)) ? b : a, dates[0]);
const inWindow = (d, w) => w && d >= w[0] && d <= w[1];
const isPlaceholder = (s) => !s || /^\s*(TODO|TBD)\b/i.test(s) || /___/.test(s);
async function getJSON(url) {
  const r = await fetch(url, { cache: 'no-cache' });
  if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
  return r.json();
}

// ------------------------------------------------------------------------------------------------ state
const S = {
  site: null, base: 'products/', dir: '', man: null, series: [], stations: null, checks: [], cov: null, sens: null,
  sat: 'nisar', track: {}, view: 'change', date: null, exp: false, basemap: 'light', window: null, scenario: 'baseline',
  split: 50, selected: null, playing: null, tables: new Set(), opacity: 0.7, note: null,
};
let mapA = null, mapB = null;

// ---- what the products offer
const sensors = () => S.man.sensors || {};
const sensorKeys = () => Object.keys(SATS).filter(k => sensors()[k]);
const win = () => S.sens?.windows?.[S.window] || null;
function frames(sat) {   // a windowed products set (sensitivity.json) overrides the manifest's default window
  if (sat === 's1' && win()?.frames) return win().frames;
  return sensors()[sat]?.frames || {};
}
function layers(sat) {
  if (sat === 's1' && win()?.layers) return win().layers;
  return sensors()[sat]?.layers || [];
}
const measured = (sat) => Object.keys(frames(sat)).length > 0;
const pointFile = (sat) => (sat === 's1' && win()?.points) ? win().points[S.track[sat]] : sensors()[sat]?.points?.[S.track[sat]];
const covOf = (sat) => S.cov?.[sat] || {};
const tracksOf = (sat) => { const f = Object.keys(frames(sat)); return f.length ? f : Object.keys(covOf(sat)); };
const datesOf = (sat, t) => frames(sat)[t]?.dates || covOf(sat)[t]?.dates || [];
const gapsOf = (sat, t) => frames(sat)[t]?.gaps || covOf(sat)[t]?.gaps || [];
const dirOf = (sat, t) => frames(sat)[t]?.direction || covOf(sat)[t]?.direction || '';
const pendingText = (sat) => sensors()[sat]?.pending || `${SATS[sat].name} measurements are not exported yet`;
const sideSats = () => S.sat === 'compare' ? ['nisar', 's1'] : [S.sat];
const zones = () => S.series.filter(p => p.kind === 'zone');
const control = () => S.series.find(p => p.kind === 'control');
const cleanLabel = (s) => String(s || '').replace(/\s*·\s*MOCK\b.*$/, '');
const zoneName = (p) => cleanLabel(p.label || p.id).replace(/^Salt zone\s*z?/i, 'Zone ');
const zoneShort = (p) => (p.id.match(/\d+/) || [p.id])[0];
const scenarios = () => S.sens?.scenarios || null;
const scenarioLabel = (k) => scenarios()?.[k] || k;
function viewAllowed(v, sat = S.sat) {
  if (!MEASURED_VIEWS.includes(v)) return true;
  return sat === 'compare' ? measured('nisar') && measured('s1') : measured(sat);
}
const compareReady = () => sensorKeys().length === 2 && measured('nisar') && measured('s1') && S.man.compare?.ready !== false;

// a point's series for one sensor and track, honouring the selected window and scenario (sensitivity.json)
function entry(point, sat, trk, scenario = S.scenario) {
  const v = sat === 's1' ? win()?.variants : null;
  if (v) return v[trk]?.[scenario]?.[point.id] ?? null;
  return point.series?.[`${sat}:${trk}`] ?? null;
}

function sliderDates() {
  if (S.sat !== 'compare') return measured(S.sat) ? datesOf(S.sat, S.track[S.sat]) : [];
  const w = S.man.common_window; const all = new Set();
  for (const s of ['nisar', 's1']) datesOf(s, S.track[s]).filter(d => !w || inWindow(d, w)).forEach(d => all.add(d));
  return [...all].sort();
}

// ------------------------------------------------------------------------------------------------ URL state
const readHash = () => Object.fromEntries(new URLSearchParams(location.hash.slice(1)).entries());
function writeHash() {
  const p = new URLSearchParams();
  if (S.site) p.set('site', S.site);
  p.set('sat', S.sat);
  p.set('track', S.sat === 'compare' ? `${S.track.nisar},${S.track.s1}` : S.track[S.sat]);
  p.set('view', S.view);
  if (S.date) p.set('date', S.date);
  p.set('exp', S.exp ? '1' : '0');
  if (S.window) p.set('window', S.window);
  if (S.sens) p.set('scenario', S.scenario);
  history.replaceState(null, '', '#' + p.toString().replace(/%2C/g, ','));
}
function applyHash(h) {
  const keys = sensorKeys();
  if (h.window && S.sens?.windows?.[h.window]) S.window = h.window;
  if (h.scenario && scenarios()?.[h.scenario]) S.scenario = h.scenario;
  if (h.sat && (keys.includes(h.sat) || (h.sat === 'compare' && compareReady()))) S.sat = h.sat;
  if (h.track) for (const t of h.track.split(',')) for (const s of keys) if (tracksOf(s).includes(t)) S.track[s] = t;
  if (h.view && (S.man.views || []).includes(h.view)) S.view = h.view;
  if (h.date && /^\d{4}-\d{2}-\d{2}$/.test(h.date)) { S.date = h.date; S.dateUser = true; }
  if (h.exp) S.exp = h.exp === '1';
  if (!viewAllowed(S.view)) S.view = 'coverage';
}

// ------------------------------------------------------------------------------------------------ loading
async function load() {
  const h = readHash();
  let index = [];
  try { index = await getJSON(S.base + 'index.json'); } catch (e) { /* a single site still works with #site= */ }
  const real = index.filter(s => !s.synthetic);
  S.site = h.site || new URLSearchParams(location.search).get('site') || (real[0] || index[0] || {}).site || 'mock';
  S.index = index;
  S.dir = `${S.base}${S.site}/`;
  const opt = (f) => getJSON(S.dir + f).catch(() => null);
  const [man, series, stations, checks, cov, sens, forecast] = await Promise.all([
    getJSON(S.dir + 'manifest.json'), getJSON(S.dir + 'series.json'),
    opt('stations.geojson'), opt('checks.json'), opt('coverage.json'), opt('sensitivity.json'), opt('forecast.json'),
  ]);
  Object.assign(S, { man, series, stations, checks: checks || [], cov, sens, forecast });
  S.window = sens ? (sens.default_window || Object.keys(sens.windows || {})[0]) : null;
  const d = man.default || {};
  S.sat = sensors()[d.sat] ? d.sat : sensorKeys()[0];
  for (const s of sensorKeys()) S.track[s] = tracksOf(s)[0];
  if (d.track && tracksOf(S.sat).includes(d.track)) S.track[S.sat] = d.track;
  S.view = (man.views || []).includes(d.view) ? d.view : 'change';
  applyHash(h);
  if (!viewAllowed(S.view)) S.view = 'coverage';
}

// ------------------------------------------------------------------------------------------------ map
function bboxCoords() {
  const [[s, w], [n, e]] = S.man.bounds;
  return [[w, n], [e, n], [e, s], [w, s]];
}
function styleFor(key) {
  const b = BASEMAPS[key];
  if (b.style) return b.style;
  return {
    version: 8,
    sources: { base: { type: 'raster', tiles: b.tiles, tileSize: 256, maxzoom: b.maxzoom, attribution: b.attribution } },
    layers: [{ id: 'base', type: 'raster', source: 'base' }],
  };
}
function makeMap(container, interactive) {
  const v = S.man.view;
  const m = new maplibregl.Map({
    container, style: styleFor(S.basemap), interactive,
    center: [v.center[1], v.center[0]],            // manifest is [lat, lon]; MapLibre wants [lon, lat]
    zoom: v.zoom - ZOOM_OFFSET,
    minZoom: (v.min_zoom ?? 6) - ZOOM_OFFSET,
    maxZoom: 16,
    attributionControl: false, dragRotate: false, pitchWithRotate: false,
  });
  m.touchZoomRotate?.disableRotation?.();
  m.on('load', () => { addOverlay(m); renderOverlays(); });
  return m;
}
let _px;
function transparentPixel() {
  if (!_px) { const c = document.createElement('canvas'); c.width = c.height = 1; _px = c.toDataURL(); }
  return _px;
}
function addOverlay(m) {
  if (m.getSource('ov')) return;
  m.addSource('ov', { type: 'image', url: transparentPixel(), coordinates: bboxCoords() });
  const firstLabel = m.getStyle().layers.find(l => l.type === 'symbol')?.id;   // keep place names above the colours
  m.addLayer({ id: 'ov', type: 'raster', source: 'ov', paint: { 'raster-opacity': S.opacity, 'raster-fade-duration': 0, 'raster-resampling': 'nearest' } }, firstLabel);
  m.addSource('pts', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
  m.addLayer({ id: 'pts', type: 'circle', source: 'pts', layout: { visibility: 'none' }, paint: {
    // a little larger than EGMS's 2.5 px dots, growing with zoom, with a thin outline so pale values show on a light map
    'circle-radius': ['interpolate', ['linear'], ['zoom'], 9, 1, 11, 1.8, 12, 2.6, 13, 3.6, 14, 5, 16, 9],
    'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], 10, 0, 12, 0.4, 14, 0.8],
    'circle-stroke-color': '#1C1917', 'circle-stroke-opacity': 0.35 * S.opacity, 'circle-opacity': S.opacity,
    'circle-color': '#F7F7F7',
  } }, firstLabel);
  m._pts = null;
  // the town's administrative boundary, a black line with a pale casing so it reads on both basemaps
  m.addSource('town', { type: 'geojson', data: 'app/ocnele_mari_boundary.geojson',
    attribution: 'Town boundary © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors' });
  m.addLayer({ id: 'town-casing', type: 'line', source: 'town', layout: { 'line-join': 'round' },
    paint: { 'line-color': '#FFFFFF', 'line-opacity': 0.8, 'line-width': ['interpolate', ['linear'], ['zoom'], 9, 3, 13, 6, 16, 9] } }, firstLabel);
  m.addLayer({ id: 'town-line', type: 'line', source: 'town', layout: { 'line-join': 'round' },
    paint: { 'line-color': '#111111', 'line-width': ['interpolate', ['linear'], ['zoom'], 9, 1.4, 13, 2.6, 16, 4] } }, firstLabel);
}

// ---- measurement dots: loaded once per file, then re-coloured per date by switching the property they read
const pointCache = {};
function loadPoints(file) {
  if (!pointCache[file]) pointCache[file] = getJSON(S.dir + file).then(d => {
    const feats = d.lon.map((lon, i) => {
      const props = {};
      if (d.rate[i] !== null) props.r = d.rate[i] * d.scale;
      d.change.forEach((col, k) => { if (col[i] !== null) props[`c${k}`] = col[i] * d.scale; });
      return { type: 'Feature', geometry: { type: 'Point', coordinates: [lon, d.lat[i]] }, properties: props };
    });
    return { type: 'FeatureCollection', features: feats, meta: { dates: d.dates, spacing: d.spacing_m, track: d.track } };
  });
  return pointCache[file];
}
function rdbuExpr(key, vmax) {
  return ['interpolate', ['linear'], ['get', key], -vmax, '#67001F', -vmax / 2, '#D6604D', 0, '#F7F7F7', vmax / 2, '#4393C3', vmax, '#053061'];
}
function setPoints(m, sat, L) {
  if (!m || !m.getLayer('pts')) return false;
  const file = pointFile(sat);
  const f = frames(sat)[S.track[sat]];
  const key = !L ? null : L.kind === 'rate' ? 'r' : L.kind === 'change' && L.date ? `c${f.dates.indexOf(L.date)}` : null;
  if (!file || !key) { m.setLayoutProperty('pts', 'visibility', 'none'); m._ptsWant = null; return false; }
  const want = { file, key, vmax: L.meta.vmax, label: `${sensors()[sat].label} ${S.track[sat]}`, date: L.date, units: L.meta.units };
  m._ptsWant = want;
  loadPoints(file).then(gj => {
    if (m._ptsWant !== want) return;            // the user moved on while the file loaded
    if (m._pts !== file) { m.getSource('pts').setData(gj); m._pts = file; S.spacing = gj.meta.spacing; renderLegend(); }
    m.setPaintProperty('pts', 'circle-color', rdbuExpr(key, want.vmax));
    m.setFilter('pts', ['has', key]);
    m.setLayoutProperty('pts', 'visibility', 'visible');
  }).catch(() => { m.setLayoutProperty('pts', 'visibility', 'none'); });
  return true;
}
function drawSide(m, sat) {
  const L = layerFor(sat);
  if (L && L.kind !== 'up' && pointFile(sat) && setPoints(m, sat, L)) setOverlay(m, null);
  else { setPoints(m, sat, null); setOverlay(m, L?.png); }
}
function setOverlay(m, png) {
  if (!m || !m.getSource('ov')) return;   // isStyleLoaded() is false while any tile is loading, so test the source
  m.getSource('ov').updateImage({ url: png ? S.dir + png : transparentPixel(), coordinates: bboxCoords() });
  m.setLayoutProperty('ov', 'visibility', png ? 'visible' : 'none');
}
function setBasemap(key) {
  S.basemap = key;
  for (const m of [mapA, mapB]) {
    if (!m) continue;
    m.setStyle(styleFor(key));
    m.once('style.load', () => { addOverlay(m); renderOverlays(); });
  }
  renderLayersMenu();
}
function updateBlur() {
  const z = mapA.getZoom();
  const stage = $('#stage');
  stage.classList.toggle('far', z < SHARP_ZOOM);
  stage.style.setProperty('--blur', `${Math.min(6, Math.max(0, (SHARP_ZOOM - z) * 1.6)).toFixed(1)}px`);
}

// markers: the salt zones, the stations, and the town label shown when zoomed out
function addMarkers(m) {
  for (const p of zones()) {
    const el = document.createElement('button');
    el.type = 'button'; el.className = 'marker zone'; el.dataset.id = p.id;
    el.title = zoneNote(p) ? `${zoneName(p)} · ${zoneNote(p).label}` : zoneName(p);
    el.setAttribute('aria-label', `${zoneName(p)}: show its history`);
    el.textContent = zoneShort(p);
    el.addEventListener('click', (e) => { e.stopPropagation(); select({ kind: 'zone', id: p.id }); });
    new maplibregl.Marker({ element: el }).setLngLat([p.lon, p.lat]).addTo(m);
  }
  for (const f of S.stations?.features || []) {
    const p = f.properties;
    const cls = p.agree === true ? 'yes' : p.agree === false ? 'no' : 'na';
    const el = document.createElement('button');
    el.type = 'button'; el.className = `marker station ${cls}`; el.dataset.id = p.station;
    el.setAttribute('aria-label', `Station ${p.station}: ${cls === 'yes' ? 'agrees' : cls === 'no' ? 'disagrees' : 'not tested'}`);
    el.innerHTML = `<i aria-hidden="true">${cls === 'yes' ? '✔' : cls === 'no' ? '✘' : '?'}</i>${esc(p.station)}`;
    el.addEventListener('click', (e) => { e.stopPropagation(); select({ kind: 'station', id: p.station }); });
    new maplibregl.Marker({ element: el }).setLngLat(f.geometry.coordinates).addTo(m);
  }
  const v = S.man.view;
  const town = document.createElement('button');
  town.type = 'button'; town.className = 'marker town';
  town.innerHTML = `${esc(S.man.name?.split(/[·,]/)[0]?.trim() || 'Ocnele Mari')}<small>zoom in for data</small>`;
  town.addEventListener('click', (e) => { e.stopPropagation(); m.flyTo({ center: [v.center[1], v.center[0]], zoom: v.zoom - ZOOM_OFFSET }); });
  new maplibregl.Marker({ element: town }).setLngLat([v.center[1], v.center[0]]).addTo(m);
}

// Compare: a second map, clipped to the right of the divider, that follows the first one
function ensureMapB() {
  if (mapB) return;
  $('#mapB').hidden = false;
  mapB = makeMap('mapB', false);
  addMarkers(mapB);
  const sync = () => mapB.jumpTo({ center: mapA.getCenter(), zoom: mapA.getZoom(), bearing: mapA.getBearing(), pitch: mapA.getPitch() });
  mapA.on('move', sync); sync();
}
function setSplit(pct) {
  S.split = Math.min(95, Math.max(5, pct));
  $('#divider').style.left = `${S.split}%`;
  $('#mapB').style.clipPath = `inset(0 0 0 ${S.split}%)`;
}

// ------------------------------------------------------------------------------------------------ what each side shows
function layerFor(sat) {
  if (!measured(sat) || S.view === 'coverage' && !measured(sat)) return null;
  const trk = S.track[sat];
  if (S.exp) {
    const up = layers(sat).find(l => l.id === 'up');
    if (up) return { png: up.png, meta: up, kind: 'up' };
  }
  if (S.view === 'rate') {
    const l = layers(sat).find(l => l.track === trk && !l.experimental);
    return l ? { png: l.png, meta: l, kind: 'rate' } : null;
  }
  const f = frames(sat)[trk]; if (!f) return null;
  const d = S.sat === 'compare' ? nearest(f.dates, S.date) : S.date;
  const i = f.dates.indexOf(d);
  return { png: i >= 0 ? f.pngs[i] : null, meta: f, kind: 'change', date: i >= 0 ? d : null, first: (i >= 0 && f.groups) ? f.dates[f.groups.indexOf(f.groups[i])] : f.dates[0] };   // grouped frames count from their group's first date
}
const hasUpLayer = () => sideSats().some(s => layers(s).some(l => l.id === 'up'));
function renderOverlays() {
  if (!mapA) return;
  if (S.sat === 'compare') { drawSide(mapA, 'nisar'); if (mapB) drawSide(mapB, 's1'); }
  else drawSide(mapA, S.sat);
}

// ------------------------------------------------------------------------------------------------ small UI kit
function pressGroup(container, items, isOn, onPick) {
  container.innerHTML = '';
  for (const it of items) {
    const b = document.createElement('button');
    b.type = 'button'; b.innerHTML = it.html;
    if (it.cls) b.className = it.cls;
    b.setAttribute('aria-pressed', isOn(it.key) ? 'true' : 'false');
    if (it.disabled) { b.disabled = true; b.title = it.disabled; b.setAttribute('aria-description', it.disabled); }
    else if (it.title) b.title = it.title;
    b.addEventListener('click', () => onPick(it.key));
    container.appendChild(b);
  }
  arrowKeys(container);
}
function arrowKeys(group) {
  group.onkeydown = (e) => {
    if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(e.key)) return;
    const bs = [...group.querySelectorAll('button:not(:disabled)')];
    const i = bs.indexOf(document.activeElement); if (i < 0) return;
    const fwd = e.key === 'ArrowRight' || e.key === 'ArrowDown';
    const j = e.key === 'Home' ? 0 : e.key === 'End' ? bs.length - 1 : (i + (fwd ? 1 : -1) + bs.length) % bs.length;
    bs[j].focus(); e.preventDefault();
  };
}
function wireMenu(btn, menu) {
  const set = (open) => { menu.hidden = !open; btn.setAttribute('aria-expanded', open ? 'true' : 'false'); };
  btn.addEventListener('click', (e) => { e.stopPropagation(); const open = menu.hidden; closeMenus(); set(open); if (open) menu.querySelector('button:not(:disabled), input:not(:disabled)')?.focus(); });
  menu.addEventListener('click', (e) => e.stopPropagation());
  menu._close = () => set(false);
}
function closeMenus() { document.querySelectorAll('.menu').forEach(m => m._close?.()); }

// ------------------------------------------------------------------------------------------------ top bar
function renderSat() {
  const sn = sensors();
  const cur = S.sat === 'compare'
    ? '<span aria-hidden="true">⇆</span> Compare'
    : `<span class="${SATS[S.sat].cls}" aria-hidden="true">${SATS[S.sat].mark}</span> ${esc(sn[S.sat].label)} <span class="meta sub">${esc(sn[S.sat].band)}</span>`;
  $('#sat-btn').innerHTML = `${cur} <span class="caret" aria-hidden="true">▼</span>`;
  const w = S.man.common_window;
  const items = ['nisar', 's1'].map(k => {
    const m = sn[k];
    const state = !m ? 'Not exported yet' : measured(k) ? [m.agency, `${m.band}, ${m.wavelength_cm} cm`, m.status].join(' · ') : `${m.band}, ${m.wavelength_cm} cm · catalog coverage · displacement fit pending`;
    return {
      key: k, cls: 'item', disabled: m ? null : `${SATS[k].name} is not in this products set`,
      html: `<span class="mk ${SATS[k].cls}" aria-hidden="true">${SATS[k].mark}</span><span><span class="t">${esc(m?.label || SATS[k].name)}</span><span class="d">${esc(state)}</span></span><span class="tick" aria-hidden="true">✓</span>`,
    };
  });
  const ready = compareReady();
  const why = sensorKeys().length < 2 ? 'Needs both satellites' : !measured('nisar') ? 'Pending: NISAR displacement fit' : !measured('s1') ? 'Pending: Sentinel-1 measurements' : S.man.compare?.ready === false ? (S.man.compare.reason || 'Not ready') : '';
  items.push({
    key: 'compare', cls: 'item', disabled: ready ? null : why,
    html: `<span class="mk" aria-hidden="true">⇆</span><span><span class="t">Compare</span><span class="d">${ready ? `Side by side, same months only${w ? `: ${human(w[0], false)} to ${human(w[1])}` : ''}` : esc(why)}</span></span><span class="tick" aria-hidden="true">✓</span>`,
  });
  pressGroup($('#sat-menu'), items, k => k === S.sat, (k) => { closeMenus(); pickSat(k); $('#sat-btn').focus(); });
}
function pickSat(k, keepDate = true) {
  if (k === S.sat) return;
  const prevDate = S.date;
  S.sat = k; S.note = null;
  if (k === 'compare') {
    const match = tracksOf('s1').find(t => dirOf('s1', t) === dirOf('nisar', S.track.nisar));   // ascending with ascending
    if (match) S.track.s1 = match;
    ensureMapB();
  }
  if (!viewAllowed(S.view)) { S.note = { kind: 'pending', sat: k }; S.view = 'coverage'; }
  if (keepDate && prevDate) { S.date = prevDate; S.dateUser = true; }
  changed();
}
function renderChecksButton() {
  const n = S.man.checks || {};
  $('#checks-btn').innerHTML = `<span class="c-pass">✔ ${n.pass ?? 0}</span><span class="c-warn">! ${n.warn ?? 0}</span><span class="c-fail">✘ ${n.fail ?? 0}</span>${n.info ? `<span class="c-info">· ${n.info}</span>` : ''}`;
  $('#checks-btn').setAttribute('aria-label', `Checks: ${n.pass ?? 0} pass, ${n.warn ?? 0} warn, ${n.fail ?? 0} fail, ${n.info ?? 0} info. Open the list.`);
}
function renderLayersMenu() {
  pressGroup($('#base-group'), Object.entries(BASEMAPS).map(([k, b]) => ({ key: k, html: b.label })), k => k === S.basemap, setBasemap);
  $('#opacity').value = Math.round(S.opacity * 100);
  $('#opacity-val').textContent = `${Math.round(S.opacity * 100)}%`;
  const up = hasUpLayer();
  $('#exp').disabled = !up;
  $('#exp').checked = S.exp && up;
  $('#exp').closest('label').title = up ? '' : 'No supported up/east export yet (O-19)';
  $('#exp-why').hidden = up;
}

// ------------------------------------------------------------------------------------------------ dock: views, tracks, timeline
function renderViews() {
  const views = S.man.views || ['change'];
  pressGroup($('#view-group'), views.map(v => ({
    key: v, html: esc(VIEW_LABEL[v] || v),
    disabled: viewAllowed(v) ? null : (S.sat === 'compare' ? 'Needs measurements from both satellites' : pendingText(S.sat)),
  })), k => k === S.view, (k) => { S.view = k; S.selected = null; S.note = null; changed(); });
}
function renderTracks() {
  const g = $('#track-group'); g.innerHTML = '';
  for (const s of sideSats()) {
    if (!sensors()[s]) continue;
    if (S.sat === 'compare') {
      const who = document.createElement('span'); who.className = 'who';
      who.innerHTML = `<span class="${SATS[s].cls}" aria-hidden="true">${SATS[s].mark}</span> ${esc(sensors()[s].label)}`; g.appendChild(who);
    }
    for (const t of tracksOf(s)) {
      const dir = dirOf(s, t);
      const b = document.createElement('button'); b.type = 'button';
      b.textContent = `${t} ${ARROW[dir] || ''}`;
      b.title = `Track ${t}, ${String(dir || '').toLowerCase()}`;
      b.setAttribute('aria-label', b.title);
      b.setAttribute('aria-pressed', S.track[s] === t ? 'true' : 'false');
      b.addEventListener('click', () => { S.track[s] = t; changed(); });
      g.appendChild(b);
    }
    // tracks in the catalogue but held off the map (e.g. a failed check): shown disabled, with the reason
    if (measured(s) && S.sat !== 'compare') for (const t of Object.keys(covOf(s)).filter(t => !tracksOf(s).includes(t))) {
      const b = document.createElement('button'); b.type = 'button'; b.disabled = true; b.className = 'held';
      b.textContent = `${t} · under review`;
      b.title = sensors()[s].pending || `${t} is not shown yet`;
      b.setAttribute('aria-label', `Track ${t}: ${b.title}`);
      g.appendChild(b);
    }
  }
  arrowKeys(g);
}
function axisRange() {
  const all = sensorKeys().flatMap(s => tracksOf(s).flatMap(t => datesOf(s, t))).sort();
  if (!all.length) { const t = Date.now() / 864e5; return { start: t - 365, end: t, x: () => 0 }; }
  const a = new Date(all[0] + 'T00:00:00Z'), b = new Date(all[all.length - 1] + 'T00:00:00Z');
  const start = Date.UTC(a.getUTCFullYear(), a.getUTCMonth(), 1) / 864e5;
  const end = Date.UTC(b.getUTCFullYear(), b.getUTCMonth() + 1, 1) / 864e5;
  return { start, end, x: (d) => ((day(d) - start) / (end - start)) * 100 };
}
function monthLabels(R) {
  const out = []; let i = 0;
  for (let t = R.start; t < R.end;) {
    const d = new Date(t * 864e5);
    const next = Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1) / 864e5;
    const lbl = d.toLocaleDateString('en-GB', { month: 'short', timeZone: 'UTC' }) + (d.getUTCMonth() === 0 || t === R.start ? ` ${d.getUTCFullYear()}` : '');
    out.push(`<span class="month m${i++ % 3}" style="left:${R.x(iso((t + next) / 2))}%">${lbl}</span>`);
    t = next;
  }
  return out.join('');
}
function dotsFor(s, t, R, lane, shown, hollow = false, dates = null) {
  return (dates || datesOf(s, t)).map(d => `<span class="dot ${SATS[s].shape === 'tri' ? 'tri' : ''} ${lane}${hollow ? ' hollow' : ''}${d === shown ? ' on' : ''}" style="left:${R.x(d)}%;--c:${SATS[s].color}" title="${esc(sensors()[s].label)} ${d}"></span>`).join('');
}
// Sentinel-1's window that covers NISAR's acquisition gap (sensitivity.json windows.<k>.fills_gap), if exported.
const gapFill = () => Object.entries(S.sens?.windows || {}).find(([, w]) => w.fills_gap?.sensor === 'nisar') || null;
function gapsFor(s, t, R) {
  const fill = s === 'nisar' ? gapFill() : null;
  return gapsOf(s, t).map(([a, b]) => {
    // a gap Sentinel-1 covers is not shown as missing data: it offers the Sentinel-1 view of those months instead
    const covers = fill && fill[1].fills_gap.gap[0] <= b && fill[1].fills_gap.gap[1] >= a;
    const label = covers ? '' : `<span><span class="long">No ${esc(sensors()[s].label)} data · ${human(a, false)} to ${human(b)}</span><span class="short">No data</span></span>`;
    return `<div class="gap${covers ? ' filled' : ''}" style="left:${R.x(a)}%;width:${R.x(b) - R.x(a)}%" title="${covers ? `${esc(sensors()[s].label)} did not image the town from ${a} to ${b}; Sentinel-1 covers these months` : `No ${esc(sensors()[s].label)} data from ${a} to ${b}`}">${label}${covers ? `<button type="button" class="gap-fill" data-fill="${esc(a)}|${esc(b)}">Sentinel-1 covers this →</button>` : ''}</div>`;
  }).join('');
}
// Show the gap months with Sentinel-1: same direction of flight, its January to October window, a date mid-gap.
function fillGap(a, b) {
  const fill = gapFill(); if (!fill) return;
  const [k, w] = fill;
  const dir = dirOf('nisar', S.track.nisar);
  stopPlay(); S.sat = 's1'; S.window = k; S.note = null;
  S.track.s1 = tracksOf('s1').find(t => dirOf('s1', t) === dir) || S.track.s1;
  const ds = w.frames[S.track.s1]?.dates || [];
  const mid = (day(a) + day(b)) / 2;
  S.date = ds.reduce((best, d) => Math.abs(day(d) - mid) < Math.abs(day(best) - mid) ? d : best, ds[0]); S.dateUser = true;
  if (!viewAllowed(S.view)) S.view = 'change';
  changed();
}
function renderTimeline() {
  const tl = $('#tl'); const R = axisRange(); const w = S.man.common_window; const cmp = S.sat === 'compare';
  const html = [];
  if (w) html.push(`<div class="window" style="left:${R.x(w[0])}%;width:${R.x(w[1]) - R.x(w[0])}%" title="Common window: ${w[0]} to ${w[1]}"></div>`);
  html.push('<div class="axis"></div>', monthLabels(R));
  for (const s of sideSats()) html.push(gapsFor(s, S.track[s], R));
  for (const s of sideSats()) html.push(dotsFor(s, S.track[s], R, cmp ? (s === 'nisar' ? 'lane-a' : 'lane-b') : '', cmp ? layerFor(s)?.date : S.date, !measured(s)));
  if (cmp && w) html.push(`<div class="shade" style="left:0;width:${R.x(w[0])}%"></div><div class="shade" style="left:${R.x(w[1])}%;right:0"></div>`);
  tl.innerHTML = html.join('');
  tl.querySelectorAll('[data-fill]').forEach(b => {
    b.addEventListener('pointerdown', (e) => e.stopPropagation());
    b.addEventListener('click', (e) => { e.stopPropagation(); const [a, c] = b.dataset.fill.split('|'); fillGap(a, c); });
  });
  const ds = sliderDates();
  tl.setAttribute('aria-valuemin', '1'); tl.setAttribute('aria-valuemax', String(Math.max(1, ds.length)));
  tl.setAttribute('aria-valuenow', String(Math.max(1, ds.indexOf(S.date) + 1)));
  tl.setAttribute('aria-valuetext', ds.length ? (S.date || 'no date') : 'no measured dates');
  const off = S.exp || S.view === 'rate' || !ds.length;
  tl.classList.toggle('disabled', off); tl.setAttribute('aria-disabled', off ? 'true' : 'false');
  $('#play').disabled = off;
}
function renderStatus() {
  const parts = [];
  for (const s of sideSats()) {
    const sn = sensors()[s]; if (!sn) continue;
    const trk = S.track[s]; const dir = dirOf(s, trk);
    let what;
    if (!measured(s)) what = `catalog coverage only, ${datesOf(s, trk).length} dates · displacement fit pending`;
    else if (S.exp) what = 'up and east (experimental), whole window';
    else if (S.view === 'rate') what = `rate: fitted annualized slope${win() ? `, ${win().label}` : ''}`;
    else { const L = layerFor(s); what = L?.date ? `${L.date} · change since ${L.first}` : `no acquisition on ${S.date}`; }
    parts.push(`<span class="${SATS[s].cls}" aria-hidden="true">${SATS[s].mark}</span> <b>${esc(sn.label)} ${esc(trk)} ${ARROW[dir] || ''}</b> · ${esc(what)} · ${esc(sn.status)}`);
  }
  if (sideSats().some(measured)) parts.push('positive = toward the satellite');
  $('#status').innerHTML = parts.join(' &nbsp;·&nbsp; ');
}
function setDate(d) { S.date = d; S.dateUser = true; changed(false); }
function stepDate(delta) {
  const ds = sliderDates(); if (!ds.length) return;
  let i = ds.indexOf(S.date); if (i < 0) i = ds.indexOf(nearest(ds, S.date));
  setDate(ds[Math.max(0, Math.min(ds.length - 1, i + delta))]);
}
function wireTimeline() {
  const tl = $('#tl');
  const pick = (ev) => {
    if (tl.classList.contains('disabled')) return;
    const r = tl.getBoundingClientRect(); const R = axisRange();
    const t = R.start + ((ev.clientX - r.left) / r.width) * (R.end - R.start);
    const ds = sliderDates(); if (!ds.length) return;
    const d = ds.reduce((a, b) => Math.abs(day(b) - t) < Math.abs(day(a) - t) ? b : a, ds[0]);
    if (d !== S.date) setDate(d);
  };
  tl.addEventListener('pointerdown', (e) => { tl.setPointerCapture(e.pointerId); stopPlay(); pick(e); });
  tl.addEventListener('pointermove', (e) => { if (tl.hasPointerCapture(e.pointerId)) pick(e); });
  tl.addEventListener('keydown', (e) => {
    if (tl.classList.contains('disabled')) return;
    const ds = sliderDates();
    if (e.key === 'ArrowRight' || e.key === 'ArrowUp') stepDate(1);
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') stepDate(-1);
    else if (e.key === 'Home') setDate(ds[0]);
    else if (e.key === 'End') setDate(ds[ds.length - 1]);
    else return;
    stopPlay(); e.preventDefault();
  });
  $('#play').addEventListener('click', () => S.playing ? stopPlay() : startPlay());
}
function startPlay() {
  const ds = sliderDates(); if (ds.length < 2) return;
  if (S.date === ds[ds.length - 1] || !ds.includes(S.date)) setDate(ds[0]);
  $('#play-icon').setAttribute('d', PAUSE_PATH); $('#play').setAttribute('aria-label', 'Pause');
  S.playing = setInterval(() => {
    const now = sliderDates(); const i = now.indexOf(S.date);
    if (i < 0 || i >= now.length - 1) return stopPlay();
    setDate(now[i + 1]);
  }, PLAY_MS);
}
function stopPlay() {
  if (S.playing) clearInterval(S.playing);
  S.playing = null;
  $('#play-icon').setAttribute('d', PLAY_PATH); $('#play').setAttribute('aria-label', 'Play through the acquisitions');
}

// ------------------------------------------------------------------------------------------------ legend, flags, compare tags
function renderLegend() {
  const L = layerFor(sideSats().find(measured) || sideSats()[0]);
  $('#legend').hidden = !L;
  if (!L) return;
  const m = L.meta || {};
  $('#legend-title').textContent = S.exp ? 'Vertical rate' : S.view === 'rate' ? 'Rate' : 'Change';
  $('#legend-units').textContent = m.units || '';
  $('#legend-min').textContent = fmt(m.vmin);
  $('#legend-max').textContent = fmt(m.vmax);
  $('#legend-neg').textContent = S.exp ? 'sinking' : 'away from satellite';
  $('#legend-pos').textContent = S.exp ? 'rising' : 'toward satellite';
  const notes = [];
  if (m.saturates) notes.push(`Beyond ${fmt(m.vmin)} or ${fmt(m.vmax)} shown at full colour`);
  if (S.sens && S.scenario !== (win()?.maps_scenario || 'baseline')) notes.push(`Baseline map: the ${scenarioLabel(S.scenario).toLowerCase()} run has no map`);
  else if (S.sens) notes.push('Baseline map');
  notes.push(pointFile(sideSats().find(measured) || S.sat) && !S.exp ? `One dot every ${S.spacing || 80} m · no dot = no data` : 'Transparent = no data');
  $('#legend-note').textContent = notes.join(' · ');
}
function renderFlags() {
  $('#sim').hidden = !S.man.synthetic;
  $('#exp-note').hidden = !(S.exp && hasUpLayer());
  const n = $('#notice'); n.hidden = true; n.innerHTML = '';
  const s1 = sensors().s1 && measured('s1');
  if (S.sat === 'nisar' && !measured('nisar')) {
    n.innerHTML = `<span><b>NISAR displacement fit pending.</b> Showing the public catalog coverage.</span>${s1 ? '<button type="button" data-go="s1">View Sentinel-1 measurements</button>' : ''}`;
  } else if (S.sat !== 'compare' && !S.exp && S.view !== 'rate' && S.view !== 'coverage') {
    const ds = sliderDates();
    if (S.date && ds.length && !ds.includes(S.date)) {
      const near = nearest(ds, S.date);
      n.innerHTML = `<span>No ${esc(sensors()[S.sat].label)} acquisition on ${esc(S.date)}. The nearest is ${esc(near)}.</span><button type="button" data-date="${esc(near)}">Show ${esc(near)}</button>`;
    }
  }
  if (!n.innerHTML) return;
  n.hidden = false;
  n.querySelector('[data-date]')?.addEventListener('click', (e) => setDate(e.currentTarget.dataset.date));
  n.querySelector('[data-go]')?.addEventListener('click', () => goSentinel());
}
function goSentinel() {
  S.sat = 's1'; S.note = null; S.selected = null;
  if (S.view === 'coverage' || !viewAllowed(S.view)) S.view = 'change';
  changed();
}
function renderCompare() {
  const on = S.sat === 'compare';
  $('#divider').hidden = !on; $('#mapB').hidden = !on; $('#cmp-tags').hidden = !on;
  if (!on) return;
  setSplit(S.split);
  const tag = (s) => {
    const L = layerFor(s);
    const what = S.exp ? 'up (experimental)' : S.view === 'rate' ? 'rate' : (L?.date ? L.date + (L.date !== S.date ? ' (nearest)' : '') : 'no date');
    return `<span class="${SATS[s].cls}" aria-hidden="true">${SATS[s].mark}</span> ${esc(sensors()[s].label)} ${esc(S.track[s])} · ${esc(what)}`;
  };
  $('#cmp-left').innerHTML = tag('nisar'); $('#cmp-right').innerHTML = tag('s1');
}

// ------------------------------------------------------------------------------------------------ charts
function chart({ lines, from, to, gaps = [], window = null, height = 130 }) {
  const W = 400, H = height, pl = 30, pr = 6, pt = 8, pb = 20;
  const t0 = day(from), t1 = day(to);
  const X = (d) => pl + ((day(d) - t0) / (t1 - t0)) * (W - pl - pr);
  let ymax = 1;
  for (const l of lines) for (const v of l.mm) if (v !== null && Number.isFinite(v)) ymax = Math.max(ymax, Math.abs(v));
  ymax = Math.ceil(ymax / 5) * 5;
  const Y = (v) => pt + ((ymax - v) / (2 * ymax)) * (H - pt - pb);
  const ph = H - pt - pb;
  const o = [`<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(lines.map(l => l.label).join(', '))}">`,
    '<defs><pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="7" stroke="#D6D3D1" stroke-width="3"/></pattern></defs>'];
  for (const [a, b] of gaps) {
    const xa = Math.max(pl, X(a)), xb = Math.min(W - pr, X(b));
    if (xb > xa) o.push(`<rect x="${xa}" y="${pt}" width="${xb - xa}" height="${ph}" fill="url(#hatch)" opacity=".7"/><text x="${(xa + xb) / 2}" y="${pt + 12}" text-anchor="middle">no data</text>`);
  }
  o.push(`<line x1="${pl}" x2="${W - pr}" y1="${Y(0)}" y2="${Y(0)}" stroke="#D6D3D1"/>`);
  o.push(`<text x="${pl - 5}" y="${Y(ymax) + 8}" text-anchor="end">+${ymax}</text><text x="${pl - 5}" y="${Y(0) + 4}" text-anchor="end">0</text><text x="${pl - 5}" y="${Y(-ymax)}" text-anchor="end">−${ymax}</text>`);
  o.push(`<text x="${pl}" y="${H - 4}">${esc(human(from))}</text><text x="${W - pr}" y="${H - 4}" text-anchor="end">${esc(human(to))}</text>`);
  for (const l of lines) {
    let seg = []; const segs = [];
    l.dates.forEach((d, i) => {
      const v = l.mm[i];
      const crosses = i > 0 && (l.gaps || []).some(([a, b]) => l.dates[i - 1] <= a && d >= b);
      if (v === null || v === undefined || crosses) { if (seg.length) segs.push(seg); seg = []; }
      if (v !== null && v !== undefined) seg.push([X(d), Y(v)]);
    });
    if (seg.length) segs.push(seg);
    for (const s of segs) o.push(`<polyline points="${s.map(p => p.map(n => n.toFixed(1)).join(',')).join(' ')}" fill="none" stroke="${l.color}" stroke-width="${l.dash ? 1.5 : 2}" stroke-linejoin="round" ${l.dash ? 'stroke-dasharray="4 3"' : ''}/>`);
    if (!l.dash) l.dates.forEach((d, i) => {
      const v = l.mm[i]; if (v === null || v === undefined) return;
      const x = X(d), y = Y(v); const tip = `<title>${esc(l.label)} ${d}: ${v} mm</title>`;
      o.push(l.shape === 'tri'
        ? `<path d="M${x.toFixed(1)},${(y - 4.5).toFixed(1)} l4.5,8 h-9z" fill="${l.color}" stroke="#fff" stroke-width=".8">${tip}</path>`
        : `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3" fill="${l.color}" stroke="#fff" stroke-width=".8">${tip}</circle>`);
    });
  }
  if (window) {   // veil outside the common window, drawn last so it dims the lines too
    o.push(`<rect x="${pl}" y="${pt}" width="${Math.max(0, X(window[0]) - pl)}" height="${ph}" fill="#fff" opacity=".75"/>`);
    o.push(`<rect x="${X(window[1])}" y="${pt}" width="${Math.max(0, W - pr - X(window[1]))}" height="${ph}" fill="#fff" opacity=".75"/>`);
  }
  o.push('</svg>');
  return o.join('');
}
function table(lines) {
  const dates = [...new Set(lines.flatMap(l => l.dates))].sort();
  const val = (l, d) => { const i = l.dates.indexOf(d); return i < 0 || l.mm[i] === null ? '' : (typeof l.mm[i] === 'number' ? l.mm[i].toFixed(2) : l.mm[i]); };
  return `<table class="data"><thead><tr><th>Date</th>${lines.map(l => `<th>${esc(l.label)}, mm</th>`).join('')}</tr></thead><tbody>${dates.map(d => `<tr><td>${d}</td>${lines.map(l => `<td>${val(l, d)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
}
function lineOf(point, sat, trk, opts = {}) {
  const e = entry(point, sat, trk, opts.scenario); if (!e) return null;
  return { label: opts.label || `${sensors()[sat].label} ${trk}`, color: opts.color || SATS[sat].color, shape: SATS[sat].shape,
    dates: e.dates, mm: e.mm, gaps: gapsOf(sat, trk), n: e.n_pixels, rate: e.rate, change: e.fitted_change_mm, dash: !!opts.dash };
}
function rangeOf(lines) {
  const ds = lines.flatMap(l => l.dates).sort();
  if (!ds.length) { const R = axisRange(); return [iso(R.start), iso(R.end)]; }
  const pad = Math.max(3, (day(ds[ds.length - 1]) - day(ds[0])) * 0.03);
  return [iso(day(ds[0]) - pad), iso(day(ds[ds.length - 1]) + pad)];
}
function block(id, title, right, lines, extra = {}) {
  const [from, to] = extra.range || rangeOf(lines);
  const open = S.tables.has(id);
  return `<div class="block"><h3><span>${title}</span>${right || ''}</h3>${extra.top || ''}
    ${lines.length ? chart({ lines, from, to, gaps: lines.flatMap(l => l.dash ? [] : l.gaps), window: extra.window }) : ''}
    <div class="foot"><span>${extra.foot || ''}</span>${lines.length ? `<button type="button" class="linkbtn" data-table="${esc(id)}">${open ? 'Hide table' : 'Show as table'}</button>` : ''}</div>
    ${open && lines.length ? table(lines) : ''}</div>`;
}
const keys = (lines) => `<div class="keys">${lines.map(l => `<span><i style="border-color:${l.color};${l.dash ? 'border-top-style:dashed' : ''}"></i>${esc(l.label)}</span>`).join('')}</div>`;

// direction of a zone's fitted change across every stored processing run, for one track
function direction(point, sat, trk) {
  if (!scenarios() || sat !== 's1') return null;
  const vals = Object.keys(scenarios()).map(sc => entry(point, sat, trk, sc)?.fitted_change_mm).filter(Number.isFinite);
  if (vals.length < 2) return null;
  const neg = vals.filter(v => v < 0).length, pos = vals.filter(v => v > 0).length;
  if (neg && pos) return { cls: 'warn', text: 'Direction changes with processing' };
  if (neg + pos !== vals.length) return { cls: 'warn', text: 'Some processing runs have zero fitted change' };
  return { cls: 'pass', text: `${neg ? 'Away from the satellite' : 'Toward the satellite'} in ${vals.length} available runs` };
}
function factRow(point, sat, trk) {
  const e = entry(point, sat, trk);
  const dir = dirOf(sat, trk);
  const head = `<span class="${SATS[sat].cls}" aria-hidden="true">${SATS[sat].mark}</span> ${esc(sensors()[sat].label)} ${esc(trk)} ${ARROW[dir] || ''}`;
  if (!e) return `<div class="fact"><span>${head}</span><span class="sub">${esc(emptyZoneLabel(sat))}</span></div>`;
  const change = e.fitted_change_mm !== undefined && e.fitted_change_mm !== null ? `<b>${fmt(e.fitted_change_mm, 1)} mm</b> fitted change` : `<b>${fmt(e.rate)} mm/yr</b>`;
  const limited = e.n_pixels !== undefined && e.n_pixels !== null && e.n_pixels < LIMITED_PX;
  const d = direction(point, sat, trk);
  const caveat = flipCaveat(point, sat, trk);
  return `<div class="fact"><span>${head}</span><span>${change} · ${esc(e.n_pixels ?? 'n/a')} pixels</span>
    <span class="tags">${limited ? `<span class="badge warn">Limited coverage · ${esc(e.n_pixels)} px</span>` : ''}${d ? `<span class="badge ${d.cls}">${esc(d.text)}</span>` : ''}${trackNote(point, sat, trk) ? `<span class="badge" title="${esc(trackNote(point, sat, trk).detail)}">${esc(trackNote(point, sat, trk).label)}</span>` : ''}</span>${caveat ? `<small class="sub">${esc(caveat)}</small>` : ''}</div>`;
}
// the products say how to label a zone with no series in the selected window (sensitivity.json, per window)
const EMPTY_ZONE_FALLBACK = { jan_oct: 'Insufficient continuous coverage' };   // docs/ui.md, if a products set omits the label
const emptyZoneLabel = (sat) => (sat === 's1' && (win()?.empty_zone_label || EMPTY_ZONE_FALLBACK[S.window])) || 'No connected series for this zone on this track';
// which stored runs flip the direction of the selected run, and by how much (from sensitivity.json; after Alexandru's
// Zone 1 and Zone 2 note in PR #12, generalised so the numbers come from the products)
function flipCaveat(point, sat, trk) {
  if (!scenarios() || sat !== 's1') return null;
  const base = entry(point, sat, trk)?.fitted_change_mm;
  if (!Number.isFinite(base) || base === 0) return null;
  const flips = Object.keys(scenarios()).filter(sc => sc !== S.scenario).map(sc => [sc, entry(point, sat, trk, sc)])
    .filter(([, e]) => Number.isFinite(e?.fitted_change_mm) && Math.sign(e.fitted_change_mm) === -Math.sign(base));
  if (!flips.length) return null;
  return flips.map(([sc, e]) => `${scenarioLabel(sc)} flips the fitted direction from ${fmt(base, 2)} mm to ${fmt(e.fitted_change_mm, 2)} mm, with ${e.n_pixels} pixel${e.n_pixels === 1 ? '' : 's'}.`).join(' ');
}
// interpretation notes from the products (03's zone review), shown as written
const zoneNote = (z) => S.man.zone_notes?.[z.id] || null;
const trackNote = (z, sat, trk) => { const n = S.man.track_notes?.[`${sat}:${trk}`]; return n && (!n.zones || n.zones.includes(z.id)) ? n : null; };
function notesBox(z, sats, full) {
  const out = [];
  const zn = zoneNote(z);
  if (zn) out.push(`<div class="zone-note"><b>${esc(zn.label)}</b>${full ? `<span>${esc(zn.detail)}</span><small>${esc(zn.source)}</small>` : ''}</div>`);
  if (full) for (const s of sats) for (const t of tracksOf(s)) {
    const tn = trackNote(z, s, t);
    if (tn) out.push(`<div class="zone-note quiet"><b>${esc(tn.label)} · ${esc(sensors()[s].label)} ${esc(t)}</b><span>${esc(tn.detail)}</span><small>${esc(tn.source)}</small></div>`);
  }
  return out.join('');
}

// ------------------------------------------------------------------------------------------------ processing choices
function choicesPanel() {
  if (!S.sens) return '';
  const wins = Object.entries(S.sens.windows || {});
  const scs = Object.entries(scenarios() || {});
  return `<details class="choices" ${S.choicesOpen ? 'open' : ''}><summary>Explore processing choices <span class="sub">· ${esc(win()?.label || '')} · ${esc(scenarioLabel(S.scenario))}</span></summary>
    <div class="menu-label">Observation window</div>
    <div class="seg" role="group" aria-label="Observation window">${wins.map(([k, w]) => `<button type="button" data-window="${esc(k)}" aria-pressed="${k === S.window}">${esc(w.label || k)}</button>`).join('')}</div>
    ${wins.length < 2 ? '<p class="sub small">The January to October window is not in this products set yet.</p>' : ''}
    <div class="menu-label">Processing run</div>
    <div class="radios" role="radiogroup" aria-label="Processing run">${scs.map(([k, l]) => `<label><input type="radio" name="scenario" value="${esc(k)}" ${k === S.scenario ? 'checked' : ''}> ${esc(l)}</label>`).join('')}</div>
    <p class="sub small">${esc(S.sens.note || 'These choose stored results. Maps exist for the baseline run only.')}</p>
  </details>`;
}
function wireChoices(root) {
  root.querySelector('details.choices')?.addEventListener('toggle', (e) => { S.choicesOpen = e.currentTarget.open; });
  root.querySelectorAll('[data-window]').forEach(b => b.onclick = () => { S.window = b.dataset.window; S.date = null; changed(); });
  root.querySelectorAll('input[name="scenario"]').forEach(r => r.onchange = () => { S.scenario = r.value; changed(false); });
}

// ------------------------------------------------------------------------------------------------ sheet contents
function forecastPanel() {
  const f = S.forecast;
  if (!f || S.man.synthetic || S.sat !== f.sensor || S.track[f.sensor] !== f.track ||
      S.window !== f.window || S.scenario !== f.scenario) return '';
  const supported = zones().find(z => z.id === f.zone);
  if (!supported) return '';
  const obs = entry(supported, f.sensor, f.track);
  if (!obs || obs.dates.length !== f.training_dates.length ||
      !obs.dates.every((date, index) => date === f.training_dates[index] &&
        Number.isFinite(obs.mm[index]) && Math.abs(obs.mm[index] - f.observed_mm[index]) <= .011)) return '';
  // Chronos-2 is the page's only forecast (team decision, 14 Nov 2026). The four simple models stay in forecast.json as
  // backtest baselines: they are named in the footnote as the comparison, never drawn as forecasts.
  const BASE = { persistence: 'persistence', theil_sen: 'Theil–Sen trend', gaussian_process: 'Gaussian process', long_term: 'EGMS long-term trend' };
  const model = 'chronos2';
  const path = f.model_paths_mm?.chronos2; const iv = f.intervals?.chronos2;
  if (!path || !iv) return '';
  const last = f.observed_mm.at(-1);
  const steps = [f.last_observation, ...f.dates];
  const val = [last, ...path], lo = [last, ...iv.q10], hi = [last, ...iv.q90];
  const k = Math.min(S.fcIdx ?? steps.length - 1, steps.length - 1);
  const lines = [
    { label: 'Radar estimate (Sentinel-1 029A)', color: SATS.s1.color, shape: SATS.s1.shape, dates: f.training_dates, mm: f.observed_mm, gaps: [] },
    { label: 'Chronos-2 forecast (median)', color: '#7C3AED', dates: steps, mm: val, dash: true, gaps: [] },
    { label: `${Math.round(iv.level * 100)} % range, low`, color: '#C4B5FD', dates: steps, mm: lo, dash: true, gaps: [] },
    { label: `${Math.round(iv.level * 100)} % range, high`, color: '#C4B5FD', dates: steps, mm: hi, dash: true, gaps: [] },
  ];
  const c = f.chronos2 || {};
  const bt = [c.janoct_30d && `30 days: ${Number(c.janoct_30d.mae_mm).toFixed(2)} mm over ${c.janoct_30d.n} cutoffs`,
              c.janoct_88d && `88 days: ${Number(c.janoct_88d.mae_mm).toFixed(2)} mm over ${c.janoct_88d.n} cutoffs`].filter(Boolean).join(' · ');
  const base = Object.entries(f.metrics).filter(([k2]) => k2 !== model && BASE[k2]).map(([k2, v]) => `${BASE[k2]} ${Number(v.mae_mm).toFixed(2)} mm`).join(', ');
  const nc = f.nisar_check;
  const ncText = nc ? `<p class="reason"><b>Check against NISAR</b> (129A, ${esc(nc.dates[0])} to ${esc(nc.dates[1])}, after the forecast started): NISAR ${fmt(nc.nisar_change_mm, 1)} mm, Chronos-2 ${fmt(nc.chronos2_change_mm, 1)} mm. NISAR's own date-to-date scatter here is about ${Number(nc.nisar_step_scatter_mm).toFixed(1)} mm, so this is consistent within noise, not a validation. Scaled into Sentinel-1's line of sight assuming vertical motion only.</p>` : '';
  const retro = f.status === 'retrospective' || f.end_date <= new Date().toISOString().slice(0, 10);
  return block('zone-forecast', `${esc(supported.label || f.zone)} · ${retro ? 'Retrospective forecast' : 'Forecast'} · Chronos-2`,
    `<span class="badge">${f.horizon_days} days · ${esc(f.track)} LOS</span>`, lines, {
      top: `<p class="reason">Chronos-2, a pretrained time-series model (amazon/chronos-2) used zero-shot, continues the radar series from ${esc(f.last_observation)} to ${esc(f.end_date)}. It extrapolates the shape of this one series; it knows nothing about salt, weather or the mine.</p>
        <div class="fc-slider"><label for="fc-range">Forecast date</label>
          <input id="fc-range" type="range" min="0" max="${steps.length - 1}" step="1" value="${k}" aria-valuetext="${esc(steps[k])}">
          <output id="fc-out" for="fc-range" aria-live="polite">${fcReadout(steps[k], val[k], lo[k], hi[k], iv.level, f.training_dates[0])}</output></div>
        ${ncText}${keys(lines.slice(0, 3).map((l, i) => i === 2 ? { ...l, label: `${Math.round(iv.level * 100)} % range (backtested)` } : l))}`,
      foot: `Backtest error (mean absolute, January to October 2026 series): ${bt}. Over the four summer cutoffs Chronos-2 scored ${Number(f.metrics.chronos2.mae_mm).toFixed(2)} mm against simple baselines (${base}). ${esc(f.interval_reason)}`,
    });
}
function fcReadout(d, v, lo, hi, level, ref) {
  return `<b>${esc(d)}</b> · ${fmt(v, 1)} mm <span class="sub">(${Math.round(level * 100)} % range ${fmt(lo, 1)} to ${fmt(hi, 1)} mm) relative to ${esc(ref)}</span>`;
}

function zonesSheet() {
  const sat = S.sat === 'compare' ? null : S.sat;
  const ctl = control();
  const sats = sideSats().filter(measured);
  const linesFor = (z) => {
    const ls = [];
    for (const s of sats) { const l = lineOf(z, s, S.track[s]); if (l) ls.push(l); }
    if (ctl) for (const s of sats) { const l = lineOf(ctl, s, S.track[s], { dash: true, color: '#A8A29E', label: `${cleanLabel(ctl.label)}${S.sat === 'compare' ? `, ${sensors()[s].label}` : ''}` }); if (l) ls.push(l); }
    return ls;
  };
  const zs = zones();
  const blocks = zs.map(z => {
    const facts = sat ? tracksOf(sat).map(t => factRow(z, sat, t)).join('') : sats.map(s => factRow(z, s, S.track[s])).join('');
    const lines = linesFor(z);
    const missing = sats.filter(s => !entry(z, s, S.track[s])).length;
    return block(`z-${z.id}`, esc(zoneName(z)), '', lines, { top: `${notesBox(z, sats, false)}<div class="facts">${facts}</div>`,
      foot: missing ? `${sats.filter(s => !entry(z, s, S.track[s])).map(s => S.track[s]).join(' and ')}: ${emptyZoneLabel(sat || 's1')}` : `Chart: ${sats.map(s => `${sensors()[s].label} ${S.track[s]}`).join(' and ')}` });
  });
  const ex = zs.length ? linesFor(zs.find(z => linesFor(z).length) || zs[0]) : [];
  return `<h2>Where did the ground move?</h2><p class="lead">Median line-of-sight change in each salt zone, in mm since the first date${win() ? `, ${esc(win().label)}` : ''}. Negative means away from the satellite, which is what sinking ground looks like. It is relative to nearby terrain, not an absolute or vertical value.</p>
    ${choicesPanel()}${forecastPanel()}${ex.length ? keys(ex) : ''}${blocks.join('') || '<p class="sub">No zone series in this products set.</p>'}`;
}
function checkForZone(z) {
  const num = (z.id.match(/\d+/) || [])[0];
  return S.checks.find(c => /^agree/i.test(c.id) && num && (c.id.match(/\d+/) || [])[0] === num);
}
function egmsPanel() {
  const e = S.man.egms; if (!e) return '';
  if (e.summary?.length) {
    const names = { z1: 'Zone 1', z2: 'Zone 2', z3: 'Zone 3', z4: 'Zone 4', stable: 'R05 stable-ground sample' };
    const rate = value => Number.isFinite(value) ? value.toFixed(1) : '—';
    const rows = e.summary.map(row => `<tr><th scope="row">${esc(names[row.id] || row.id)}</th><td>${esc(row.cells)}</td><td>${rate(row.up_mm_yr)}</td><td>${rate(row.east_mm_yr)}</td></tr>`).join('');
    return `<div class="block egms"><h3><span>${esc(e.label)}</span><span class="badge">Reported zone medians</span></h3>
      <p class="reason">${esc(e.detail)}</p>
      <table><caption>Historical median rates in mm/yr. Positive means up or east.</caption>
      <thead><tr><th scope="col">Area</th><th scope="col">Cells</th><th scope="col">Up</th><th scope="col">East–West</th></tr></thead>
      <tbody>${rows}</tbody></table>
      <p class="reason"><a href="${esc(e.source)}">R05 extraction and provenance</a></p></div>`;
  }
  return `<div class="block egms"><h3><span>${esc(e.label)}</span><span class="badge">${esc(e.status === 'pending' ? 'Pending verification' : e.status)}</span></h3>
    <div class="seg" role="group" aria-label="EGMS component"><button type="button" disabled aria-pressed="true">Up</button><button type="button" disabled aria-pressed="false">East–West</button></div>
    <p class="reason">${esc(e.detail)}</p></div>`;
}
function agreementSheet() {
  const w = S.man.common_window;
  const head = `<h2>Do the two radars agree?</h2><p class="lead">NISAR next to Sentinel-1 over the months both cover${w ? ` (${human(w[0], false)} to ${human(w[1])})` : ''}, each in its own line of sight. The verdict comes from the validator's checks, never from this page.</p>`;
  if (!(measured('nisar') && measured('s1')) || S.man.compare?.ready === false) {
    const why = !measured('nisar') ? 'NISAR displacement fit pending' : !measured('s1') ? 'Sentinel-1 measurements pending' : (S.man.compare.reason || 'not ready');
    return `${head}<div class="verdict na">Not testable yet · ${esc(why)}. O-19 (the shared quantity and geometry) is also open.</div>
      <p class="reason">NISAR and Sentinel-1 look from different sides, so their line-of-sight values are different quantities until 03 and 04 settle O-19.</p>${egmsPanel()}`;
  }
  const ctl = control(); const trk = S.track;
  const minus = (z, s) => {
    const a = entry(z, s, trk[s]), b = ctl && entry(ctl, s, trk[s]);
    if (!a || !b) return null;
    const mm = a.dates.map((d, i) => { const j = b.dates.indexOf(d); return j < 0 || a.mm[i] === null || b.mm[j] === null ? null : Math.round((a.mm[i] - b.mm[j]) * 10) / 10; });
    return { label: `${sensors()[s].label} ${trk[s]}`, color: SATS[s].color, shape: SATS[s].shape, dates: a.dates, mm, gaps: gapsOf(s, trk[s]), dash: false };
  };
  const range = w ? [iso(day(w[0]) - 20), iso(day(w[1]) + 20)] : undefined;
  const blocks = zones().map(z => {
    const lines = ['nisar', 's1'].map(s => minus(z, s)).filter(Boolean);
    const c = checkForZone(z);
    const word = c ? (c.status === 'pass' ? 'Agree' : c.status === 'fail' ? 'Disagree' : c.status === 'warn' ? 'Warning' : 'Info') : 'Not tested yet';
    const badge = `<span class="badge ${c ? esc(c.status) : ''}">${c ? STATUS_ICON[c.status] + ' ' : ''}${word}</span>`;
    const foot = (c ? `${esc(cleanLabel(c.title))}${c.detail ? ': ' + esc(c.detail) : ''}` : 'The validator has not reported on this zone') + (lines.length < 2 ? ' · one satellite has no data here: not testable' : '');
    return block(`a-${z.id}`, esc(zoneName(z)), badge, lines, { range, window: w, foot });
  });
  return `${head}<p class="sub small">Shown as the zone minus the outer comparison area, a proposed contrast until O-19 decides.</p>
    ${keys(['nisar', 's1'].map(s => ({ label: `${sensors()[s].label} ${trk[s]}`, color: SATS[s].color })))}${blocks.join('')}${egmsPanel()}`;
}
// every exported date of a track across Sentinel-1's windows (Jan to Oct and Jul to Oct), for the coverage overview
function allDates(s, t) {
  if (s !== 's1' || !S.sens?.windows) return datesOf(s, t);
  return [...new Set(Object.values(S.sens.windows).flatMap(w => w.frames?.[t]?.dates || []))].sort();
}
function coverageSheet() {
  const R = axisRange(); const w = S.man.common_window;
  const band = w ? `<div class="window" style="left:${R.x(w[0])}%;width:${R.x(w[1]) - R.x(w[0])}%;top:0;height:100%"></div>` : '';
  const rows = [];
  for (const s of sensorKeys()) for (const t of tracksOf(s)) {
    const pairs = covOf(s)[t]?.pairs;
    const nPairs = Array.isArray(pairs) ? pairs.length : pairs;
    const state = measured(s) ? '' : '<small class="pending">displacement fit pending</small>';
    rows.push(`<div class="cov-row"><div class="cov-label"><span class="${SATS[s].cls}" aria-hidden="true">${SATS[s].mark}</span> ${esc(sensors()[s].label)} ${esc(t)} ${ARROW[dirOf(s, t)] || ''}<small>${allDates(s, t).length} dates${nPairs && allDates(s, t).length === datesOf(s, t).length ? ` · ${nPairs} pairs` : ''}</small>${state}</div>
      <div class="tl cov-tl">${band}<div class="axis"></div>${gapsFor(s, t, R)}${dotsFor(s, t, R, '', null, !measured(s), allDates(s, t))}</div></div>`);
  }
  // usable zone pixels per measured track: a separate indicator from the acquisition ticks
  const px = [];
  for (const s of sensorKeys()) for (const t of tracksOf(s)) {
    const zp = covOf(s)[t]?.zone_pixels; if (!zp) continue;
    px.push(`<tr><td><span class="${SATS[s].cls}" aria-hidden="true">${SATS[s].mark}</span> ${esc(sensors()[s].label)} ${esc(t)}</td>${zones().map(z => `<td>${zp[z.id] ?? '<span class="sub">none</span>'}</td>`).join('')}</tr>`);
  }
  const s1 = sensors().s1 && measured('s1');
  return `<h2>When each satellite looked</h2><p class="lead">One mark per acquisition; hollow marks are catalog dates with no measurement yet. Hatched means no data. The shaded band${w ? `, ${human(w[0], false)} to ${human(w[1])},` : ''} is the common window both satellites cover.</p>
    ${!measured('nisar') && s1 ? '<p><button type="button" class="pill dark" data-go="s1">View Sentinel-1 measurements →</button></p>' : ''}
    <div class="cov-row cov-head"><div class="cov-label"></div><div class="tl cov-tl">${monthLabels(R)}</div></div>${rows.join('')}
    ${px.length ? `<h3 class="sub-h">Usable pixels in each zone</h3><table class="data"><thead><tr><th>Track</th>${zones().map(z => `<th>${esc(zoneName(z))}</th>`).join('')}</tr></thead><tbody>${px.join('')}</tbody></table>
      <p class="sub small">Pixels with a connected series over the whole window. A zone with none has no measurement on that track.</p>` : ''}`;
}
function stationSheet(id) {
  const f = S.stations?.features.find(f => f.properties.station === id); if (!f) return null;
  const p = f.properties;
  let html = `<h2>${esc(p.station)}</h2><div class="kicker">GNSS station · ${esc(cleanLabel(p.source))} · ${esc(p.dist_km)} km from the town</div>`;
  for (const s of sideSats()) {
    const t = p.tracks?.[`${s}:${S.track[s]}`];
    html += `<div class="block"><h3><span><span class="${SATS[s].cls}" aria-hidden="true">${SATS[s].mark}</span> ${esc(sensors()[s].label)} ${esc(S.track[s])} against GNSS</span></h3>`;
    html += t ? `<div class="nums"><div><small>${esc(sensors()[s].label)}</small><strong>${fmt(t.radar ?? t.nisar)}<span>mm/yr</span></strong></div><div><small>GNSS</small><strong>${fmt(t.gnss)}<span>mm/yr</span></strong></div><div><small>Difference</small><strong>${fmt(t.diff)}<span>mm/yr</span></strong></div><div><small>Tolerance</small><strong>±${esc(t.tol)}<span>mm/yr</span></strong></div></div>` : '<p class="reason">No comparison for this track.</p>';
    html += '</div>';
  }
  const v = p.agree === true ? ['yes', '✔', 'Satellite and station agree'] : p.agree === false ? ['no', '✘', 'Satellite and station disagree'] : ['na', '?', 'Not tested'];
  html += `<div class="verdict ${v[0]}"><span aria-hidden="true">${v[1]}</span> ${v[2]}</div><p class="reason">${esc(cleanLabel(p.reason) || p.reason)}</p>`;
  if (p.t_end) html += `<p class="reason">The GNSS series ends in ${esc(p.t_end)}, so it assumes steady motion since.</p>`;
  return html;
}
function zoneSheet(id) {
  const z = S.series.find(p => p.id === id); if (!z) return null;
  const sats = sideSats().filter(measured);
  let html = `<h2>${esc(zoneName(z))}</h2><div class="kicker">${z.place ? `${esc(z.place)} · ` : 'Salt zone · '}${esc(z.lat)}° N, ${esc(z.lon)}° E${win() && S.sat === 's1' ? ` · ${esc(win().label)}` : ''}</div>`;
  if (!sats.length) return html + `<div class="verdict na">${esc(pendingText(S.sat))}</div>`;
  const facts = S.sat === 'compare' ? sats.map(s => factRow(z, s, S.track[s])).join('') : tracksOf(S.sat).map(t => factRow(z, S.sat, t)).join('');
  html += `${notesBox(z, S.sat === 'compare' ? sats : [S.sat], true)}<div class="facts">${facts}</div>${choicesPanel()}`;
  const lines = sats.map(s => lineOf(z, s, S.track[s])).filter(Boolean);
  const ctl = control();
  if (ctl) for (const s of sats) { const l = lineOf(ctl, s, S.track[s], { dash: true, color: '#A8A29E', label: cleanLabel(ctl.label) }); if (l) lines.push(l); }
  // NISAR has no acquisitions from 18 Jan to 23 Jun 2026: Sentinel-1's January to October series fills those months,
  // in its own line of sight and reference (never spliced onto the NISAR line).
  const fill = S.sat === 'nisar' ? gapFill() : null;
  let fillNote = '';
  if (fill) {
    const st = tracksOf('s1').find(t => dirOf('s1', t) === dirOf('nisar', S.track.nisar));
    const e = st && fill[1].variants?.[st]?.baseline?.[z.id];
    if (e) {
      lines.push({ label: `Sentinel-1 ${st}, ${fill[1].label} (fills NISAR's gap)`, color: SATS.s1.color, shape: SATS.s1.shape,
        dates: e.dates, mm: e.mm, gaps: [], n: e.n_pixels, dash: false });
      fillNote = `<p class="reason">The purple line is Sentinel-1 ${esc(st)}, which kept imaging the town while NISAR had no acquisitions. It is in Sentinel-1's own line of sight and reference, so read its shape, not its offset from the NISAR line.</p>`;
    } else if (st) fillNote = `<p class="reason">Sentinel-1 ${esc(st)} has no continuous January to October series in this zone, so NISAR's gap stays empty here.</p>`;
  }
  html += fillNote;
  html += block(`d-${z.id}`, 'Change over time, mm', '', lines, { foot: lines.filter(l => !l.dash).map(l => `${l.label}: ${l.n ?? 'n/a'} pixels`).join(' · ') });
  if (scenarios() && S.sat === 's1') {
    const rows = Object.entries(scenarios()).map(([k, l]) => `<tr${k === S.scenario ? ' class="here"' : ''}><td>${esc(l)}</td>${tracksOf('s1').map(t => { const e = entry(z, 's1', t, k); return `<td>${e ? `${fmt(e.fitted_change_mm, 1)} mm · ${e.n_pixels} px` : '<span class="sub">no series</span>'}</td>`; }).join('')}</tr>`).join('');
    html += `<div class="block"><h3>Every processing run</h3><table class="data"><thead><tr><th>Run</th>${tracksOf('s1').map(t => `<th>${esc(t)} ${ARROW[dirOf('s1', t)] || ''}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div>`;
  }
  html += '<p class="reason">Line of sight, positive toward the satellite, relative to nearby terrain. A fitted change is the fitted line over the window, not the difference between the first and last dates.</p>';
  return html;
}
function renderSheet() {
  const sh = $('#sheet'); let html = null;
  if (S.selected) html = S.selected.kind === 'station' ? stationSheet(S.selected.id) : zoneSheet(S.selected.id);
  else if (S.view === 'zones') html = zonesSheet();
  else if (S.view === 'agreement') html = agreementSheet();
  else if (S.view === 'coverage') html = coverageSheet();
  sh.classList.toggle('wide', !S.selected && S.view === 'coverage');
  if (!html) { sh.hidden = true; return; }
  const top = sh.scrollTop;
  $('#sheet-body').innerHTML = html; sh.hidden = false; sh.scrollTop = top;
  sh.querySelectorAll('[data-table]').forEach(b => b.onclick = () => { const id = b.dataset.table; S.tables.has(id) ? S.tables.delete(id) : S.tables.add(id); renderSheet(); });
  sh.querySelectorAll('[data-go]').forEach(b => b.onclick = () => goSentinel());
  sh.querySelectorAll('[data-fill]').forEach(b => b.onclick = () => { const [a, c] = b.dataset.fill.split('|'); fillGap(a, c); });
  wireChoices(sh);
  const fr = sh.querySelector('#fc-range');
  if (fr) fr.oninput = () => {
    const f = S.forecast; const i = +fr.value; S.fcIdx = i;
    const steps = [f.last_observation, ...f.dates], last = f.observed_mm.at(-1), iv = f.intervals.chronos2;
    const v = [last, ...f.model_paths_mm.chronos2][i], lo = [last, ...iv.q10][i], hi = [last, ...iv.q90][i];
    fr.setAttribute('aria-valuetext', steps[i]);
    sh.querySelector('#fc-out').innerHTML = fcReadout(steps[i], v, lo, hi, iv.level, f.training_dates[0]);
  };
}
function select(sel) {
  S.selected = sel; closeMenus(); renderSheet(); $('#sheet').scrollTop = 0;
  document.querySelectorAll('.marker.zone').forEach(el => el.classList.toggle('on', sel?.kind === 'zone' && el.dataset.id === sel.id));
}
function closeSheet() {
  if (S.selected) return select(null);
  if (SHEET_VIEWS.includes(S.view)) { S.view = viewAllowed('change') ? 'change' : 'coverage'; if (S.view === 'coverage') { $('#sheet').hidden = true; return; } changed(); }
}

// ------------------------------------------------------------------------------------------------ about dialog
function renderAbout() {
  const sn = sensorKeys().map(s => sensors()[s]);
  const n = S.man.checks || {};
  const m = S.man.methods || {};
  const others = (S.index || []).filter(s => s.site !== S.site);
  $('#about-body').innerHTML = `<h2>Where did the ground move?</h2>
    <p class="lead">${isPlaceholder(S.man.story) ? esc(S.man.note || '') : esc(S.man.story)}</p>
    ${S.man.synthetic ? '<div class="verdict na">Simulated, not data. Every number on this site is invented.</div>' : ''}
    <h3>What this map can and cannot tell you</h3>
    <p>It shows ground motion measured by radar satellites, along each satellite's line of sight and relative to nearby terrain, over the months they observed. It is not a hazard forecast, an evacuation guide or a building safety assessment. For official notices, follow the Vâlcea emergency inspectorate (ISU Vâlcea) and the Ocnele Mari town hall.</p>
    <h3 id="checks-h">Checks · ${n.pass ?? 0} pass, ${n.warn ?? 0} warn, ${n.fail ?? 0} fail, ${n.info ?? 0} info</h3>
    <ul class="checks">${S.checks.map(c => `<li class="${esc(c.status)}"><span class="ic" title="${esc(c.status)}">${STATUS_ICON[c.status] || '·'}</span><div><div>${esc(c.title)}</div><div class="detail">${esc(c.detail)}${c.value !== null && c.value !== undefined ? ` · value ${esc(c.value)}` : ''}</div></div></li>`).join('') || '<li>No checks yet.</li>'}</ul>
    <h3>The two radars</h3>
    ${sn.map(x => `<p><b>${esc(x.label)}</b> · ${esc(x.agency)} · ${esc(x.band)}, ${esc(x.wavelength_cm)} cm · ${esc(x.status)}${x.look ? ` · looks ${esc(x.look)}` : ''}<br><span class="sub">${esc(x.product || '')}${x.product ? '. ' : ''}Reference: ${esc(x.reference)}</span>${x.pending ? `<br><span class="sub">${esc(x.pending)}</span>` : ''}</p>`).join('')}
    ${Object.keys(m).length ? `<h3>Methods</h3>${['s1', 'sign', 'rate', 'zones'].filter(k => m[k]).map(k => `<p class="sub">${esc(m[k])}</p>`).join('')}
      ${m.links ? `<p>${m.links.map(l => `<a href="${esc(l.href)}" target="_blank" rel="noopener">${esc(l.label)}</a>`).join(' · ')}</p>` : ''}` : ''}
    <h3>Credits</h3>
    <p class="sub">${esc(S.man.credits)}</p>
    ${sn.map(x => `<p class="sub">${esc(x.credit)}</p>`).join('')}
    <p class="sub">Maps: ${BASEMAPS.light.attribution}; ${BASEMAPS.satellite.attribution}. Map library: MapLibre GL JS.</p>
    <p class="sub">Built ${esc(S.man.built)}${others.length ? ` · Other products sets: ${others.map(s => `<a href="#site=${esc(s.site)}" data-site="${esc(s.site)}">${esc(s.name)}${s.synthetic ? ' (simulated)' : ''}</a>`).join(', ')}` : ''}</p>`;
  $('#about-body').querySelectorAll('[data-site]').forEach(a => a.onclick = (e) => { e.preventDefault(); location.hash = `site=${a.dataset.site}`; location.reload(); });
}

// ------------------------------------------------------------------------------------------------ main render
function changed(full = true) {
  const ds = sliderDates();
  if (ds.length && (!S.date || (!S.dateUser && !ds.includes(S.date)))) S.date = ds[ds.length - 1];   // first load: the satellite's own last date   // a kept date with no acquisition gets an explicit "nearest" offer
  if (full) { renderSat(); renderViews(); renderTracks(); }
  renderLayersMenu();
  renderCompare(); renderOverlays();
  renderTimeline(); renderStatus(); renderLegend(); renderFlags(); renderSheet();
  writeHash();
  requestAnimationFrame(measure);
}
function measure() {
  document.documentElement.style.setProperty('--dock-h', `${Math.round($('#dock').getBoundingClientRect().height)}px`);
}

async function main() {
  try { await load(); } catch (e) {
    const f = $('#fatal'); f.hidden = false;
    f.innerHTML = `<h2>Could not load the products</h2><p>${esc(e.message)}</p><p class="sub">Open the page through a web server: run <code>py -m http.server 8000</code> in the repository folder, then go to http://localhost:8000.</p>`;
    return;
  }
  $('#site-name').textContent = cleanLabel(S.man.name);
  document.title = `Dancing on Salt · ${cleanLabel(S.man.name)}`;
  mapA = makeMap('map', true);
  mapA.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
  mapA.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-left');
  addMarkers(mapA);
  // Docked layout (v4): the map shrinks to the space left of the menu column, then redraws at its new size.
  const side = () => {
    const sh = $('#sheet'); const open = !sh.hidden;
    document.body.classList.toggle('side-open', open);
    document.body.classList.toggle('side-wide', open && sh.classList.contains('wide'));
    setTimeout(() => { mapA?.resize(); mapB?.resize(); }, 220);
  };
  new MutationObserver(side).observe($('#sheet'), { attributes: true, attributeFilter: ['hidden', 'class'] });
  side();
  mapA.on('zoom', updateBlur);
  mapA.on('load', () => { updateBlur(); document.querySelector('#map .maplibregl-ctrl-attrib')?.classList.remove('maplibregl-compact-show'); });
  mapA.on('click', (e) => {
    closeMenus();
    const live = mapA.getLayer('pts') && mapA.getLayoutProperty('pts', 'visibility') === 'visible'
      && (S.sat !== 'compare' || e.point.x < window.innerWidth * S.split / 100);
    const hit = live ? mapA.queryRenderedFeatures([[e.point.x - 4, e.point.y - 4], [e.point.x + 4, e.point.y + 4]], { layers: ['pts'] })[0] : null;
    if (hit && mapA._ptsWant) {
      const w = mapA._ptsWant; const v = hit.properties[w.key];
      new maplibregl.Popup({ closeButton: false, className: 'dot-pop', offset: 8 }).setLngLat(hit.geometry.coordinates)
        .setHTML(`<b>${fmt(Math.round(v * 10) / 10)} ${esc(w.units)}</b><br>${esc(w.label)} · ${w.key === 'r' ? 'fitted rate' : esc(w.date)}<br><span>${v < 0 ? 'away from' : v > 0 ? 'toward' : 'no change relative to'} the satellite</span>`)
        .addTo(mapA);
      return;
    }
    if (S.selected) select(null);
  });
  mapA.on('mouseenter', 'pts', () => { mapA.getCanvas().style.cursor = 'pointer'; });
  mapA.on('mouseleave', 'pts', () => { mapA.getCanvas().style.cursor = ''; });
  if (S.sat === 'compare') ensureMapB();
  if (new URLSearchParams(location.search).has('debug')) window.dos = { S, map: () => mapA, mapB: () => mapB };   // for testing only

  wireMenu($('#sat-btn'), $('#sat-menu'));
  wireMenu($('#layers-btn'), $('#layers'));
  document.addEventListener('click', closeMenus);
  document.addEventListener('keydown', (e) => { if (e.key !== 'Escape') return; closeMenus(); if (!$('#sheet').hidden && !$('#about').open) closeSheet(); });
  $('#sheet-close').addEventListener('click', closeSheet);
  $('#about-btn').addEventListener('click', () => { $('#about').showModal(); $('#about').scrollTop = 0; });
  $('#checks-btn').addEventListener('click', () => { $('#about').showModal(); $('#checks-h').scrollIntoView(); });
  $('#about').addEventListener('click', (e) => { if (e.target === e.currentTarget) e.currentTarget.close(); });
  $('#exp').addEventListener('change', (e) => { S.exp = e.target.checked; changed(); });
  $('#opacity').addEventListener('input', (e) => {
    S.opacity = Number(e.target.value) / 100;
    $('#opacity-val').textContent = `${e.target.value}%`;
    for (const m of [mapA, mapB]) {
      if (m?.getLayer('ov')) m.setPaintProperty('ov', 'raster-opacity', S.opacity);
      if (m?.getLayer('pts')) { m.setPaintProperty('pts', 'circle-opacity', S.opacity); m.setPaintProperty('pts', 'circle-stroke-opacity', 0.35 * S.opacity); }
    }
  });
  window.addEventListener('resize', measure);
  window.addEventListener('hashchange', () => { applyHash(readHash()); if (S.sat === 'compare') ensureMapB(); changed(); });

  const handle = $('#divider-handle');   // Compare divider: drag, or arrow keys
  handle.addEventListener('pointerdown', (e) => handle.setPointerCapture(e.pointerId));
  handle.addEventListener('pointermove', (e) => { if (handle.hasPointerCapture(e.pointerId)) setSplit((e.clientX / window.innerWidth) * 100); });
  handle.addEventListener('keydown', (e) => { if (e.key === 'ArrowLeft') setSplit(S.split - 5); else if (e.key === 'ArrowRight') setSplit(S.split + 5); });

  wireTimeline(); renderChecksButton(); renderAbout();
  changed();
}
main();

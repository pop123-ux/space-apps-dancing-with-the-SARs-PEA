// Owner: 06 · App developer (Darius)
// The page logic. It reads products/<site>/ only (file contracts in docs/build-spec.md; design and the 06 handoff in
// docs/ui.md). No measured number is typed in this file: every value on screen comes from the products files.
import * as maplibregl from 'https://unpkg.com/maplibre-gl@6.15.0/dist/maplibre-gl.mjs';
import { initLang, setLang, getLang } from './i18n.js';

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
const VIEW_LABEL = { change: 'Change', rate: 'Rate', zones: 'Zones', agreement: 'Compare', coverage: 'Coverage' };
// Top-level navigation (15 Nov 2026): Motion (Change, Rate), Coverage, Compare. Internal view keys stay as before, so
// old links with view=zones, view=agreement and view=coverage still open.
const TABS = [{ key: 'motion', label: 'Motion', views: ['change', 'rate', 'zones'] }, { key: 'coverage', label: 'Coverage', views: ['coverage'] },
  { key: 'compare', label: 'Compare', views: ['agreement'] }];
const RUN_COLORS = ['#7C3AED', '#0E7490'];   // baseline, alternative run (never red against green)
const NEG_TEXT = 'Negative means motion away from the satellite along its line of sight.';
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
  sat: 'nisar', track: {}, view: 'change', date: null, exp: false, basemap: 'satellite', window: null, scenario: 'baseline',
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
  if (S.selected?.kind === 'zone') p.set('zone', S.selected.id);
  if (getLang() === 'ro') p.set('lang', 'ro');
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
  if (h.zone && zones().some(z => z.id === h.zone)) S.selected = { kind: 'zone', id: h.zone };
  if (h.preset === 'zone4') applyPreset(false);
  if (!viewAllowed(S.view)) S.view = 'coverage';
}
// "Investigate Zone 4": Sentinel-1 029A, January to October 2026, baseline run, Zone 4 selected (a shareable preset)
function applyPreset(render = true) {
  const w = S.sens?.windows?.jan_oct ? 'jan_oct' : S.window;
  S.sat = 's1'; S.track.s1 = tracksOf('s1').includes('029A') ? '029A' : S.track.s1; S.window = w; S.scenario = 'baseline';
  S.view = 'change'; S.selected = { kind: 'zone', id: 'z4' }; S.note = null;
  const ds = datesOf('s1', S.track.s1); S.date = ds[ds.length - 1] || null; S.dateUser = true;
  if (render) { changed(); flyToZone('z4'); }
}
function flyToZone(id) {
  const z = zones().find(p => p.id === id); if (!z || !mapA) return;
  mapA.flyTo({ center: [z.lon, z.lat], zoom: Math.max(mapA.getZoom(), 13.5) });
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
  S.updates = await opt('updates.json');   // update.py --check: acquisitions newer than the fits
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
  // the selected zone's footprint (a circle of the zone's radius), drawn over the dots
  m.addSource('zsel', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
  m.addLayer({ id: 'zsel-fill', type: 'fill', source: 'zsel', paint: { 'fill-color': '#1C1917', 'fill-opacity': 0.06 } });
  m.addLayer({ id: 'zsel-line', type: 'line', source: 'zsel', paint: { 'line-color': '#1C1917', 'line-width': 2, 'line-dasharray': [2, 1] } });
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
    const cov = S.view === 'coverage';   // Coverage: where a connected series exists, whatever its value
    m.setPaintProperty('pts', 'circle-color', cov ? (S.basemap === 'satellite' ? '#FAFAF9' : '#57534E') : rdbuExpr(key, want.vmax));
    m.setPaintProperty('pts', 'circle-stroke-color', S.basemap === 'satellite' ? '#0C0A09' : '#1C1917');
    m.setFilter('pts', ['has', cov ? 'r' : key]);
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
    m._pts = null; m._ptsWant = null;               // the new style starts with an empty point source
    m.setStyle(styleFor(key), { diff: false });
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
  const seen = {};   // one marker per monument: VLC1, VLC2 and their combined mean sit on the same spot
  for (const f of S.stations?.features || []) {
    const k = f.geometry.coordinates.map(v => v.toFixed(4)).join(',');
    (seen[k] = seen[k] || []).push(f);
  }
  for (const group of Object.values(seen)) {
    const f = group.find(g => g.properties.combined) || group[0];
    const p = { ...f.properties, station: f.properties.station };
    const names = group.filter(g => !g.properties.combined).map(g => g.properties.station).join(' · ');
    const cls = p.agree === true ? 'yes' : p.agree === false ? 'no' : 'na';
    const el = document.createElement('button');
    el.type = 'button'; el.className = `marker station ${cls}`; el.dataset.id = p.station;
    el.setAttribute('aria-label', `Station ${p.station}: ${cls === 'yes' ? 'agrees' : cls === 'no' ? 'disagrees' : 'not tested'}`);
    el.innerHTML = `<i aria-hidden="true">${p.status === 'warn' ? '!' : cls === 'yes' ? '✔' : cls === 'no' ? '✘' : '?'}</i>${esc(names || p.station)}`;
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
function zoneCircle(z, n = 64) {
  const R = 6371008.8, lat = z.lat * Math.PI / 180, ring = [];
  for (let i = 0; i <= n; i++) {
    const a = 2 * Math.PI * i / n;
    ring.push([z.lon + (z.r_m * Math.sin(a) / (R * Math.cos(lat))) * 180 / Math.PI, z.lat + (z.r_m * Math.cos(a) / R) * 180 / Math.PI]);
  }
  return { type: 'Feature', geometry: { type: 'Polygon', coordinates: [ring] }, properties: {} };
}
function renderFootprint() {
  const z = S.selected?.kind === 'zone' ? zones().find(p => p.id === S.selected.id) : null;
  for (const m of [mapA, mapB]) m?.getSource('zsel')?.setData({ type: 'FeatureCollection', features: z?.r_m ? [zoneCircle(z)] : [] });
  document.querySelectorAll('.marker.zone').forEach(el => el.classList.toggle('on', !!z && el.dataset.id === z.id));
}
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
    const pair = S.man.compare?.pairs?.[S.track.nisar];   // paired by viewing geometry when the products say so
    const match = tracksOf('s1').includes(pair) ? pair : tracksOf('s1').find(t => dirOf('s1', t) === dirOf('nisar', S.track.nisar));
    if (match) S.track.s1 = match;
    ensureMapB();
  }
  if (!viewAllowed(S.view)) { S.note = { kind: 'pending', sat: k }; S.view = 'coverage'; }
  if (keepDate && prevDate) { S.date = prevDate; S.dateUser = true; }
  changed();
}
// checks relevant to the active selection: the zone's comparison, the NISAR track's sign check, a station
function relevantChecks() {
  const out = [];
  if (S.selected?.kind === 'zone') { const n = S.selected.id.replace(/\D/g, ''); out.push(...S.checks.filter(c => new RegExp(`^agree-z${n}-`).test(c.id))); }
  if (S.selected?.kind === 'station') out.push(...S.checks.filter(c => c.id === `station-${S.selected.id}`));
  if (S.sat === 'nisar' || S.view === 'agreement') out.push(...S.checks.filter(c => c.id === `sign-${S.track.nisar}`));
  return out;
}
function renderChecksButton() {
  const rel = relevantChecks();
  const worst = ['fail', 'warn', 'pass', 'info'].find(k => rel.some(c => c.status === k));
  if (rel.length) {
    const c = rel.find(x => x.status === worst);
    $('#checks-btn').innerHTML = `<span class="c-${worst}">${STATUS_ICON[worst]}</span> ${esc(c.title)}${rel.length > 1 ? ` <span class="sub">+${rel.length - 1}</span>` : ''}`;
    $('#checks-btn').dataset.target = c.id;
    $('#checks-btn').setAttribute('aria-label', `Check for this selection: ${c.title}, ${worst}. Open the evidence`);
    return;
  }
  delete $('#checks-btn').dataset.target;
  $('#checks-btn').setAttribute('aria-label', 'All checks');
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
  $('#exp').closest('label').title = up ? '' : 'No supported up/east export yet (open team decision: how to compare the two radars)';
  $('#exp-why').hidden = up;
}

// ------------------------------------------------------------------------------------------------ dock: views, tracks, timeline
const tabOf = (v) => (TABS.find(t => t.views.includes(v)) || TABS[0]).key;
function renderViews() {
  const motionOk = viewAllowed('change');
  pressGroup($('#view-group'), TABS.map(t => ({
    key: t.key, html: esc(t.label),
    disabled: t.key === 'motion' && !motionOk ? (S.sat === 'compare' ? 'Needs measurements from both satellites' : pendingText(S.sat)) : null,
  })), k => k === tabOf(S.view), (k) => {
    S.note = null;
    S.view = k === 'motion' ? (['change', 'rate'].includes(S.view) ? S.view : 'change') : k === 'coverage' ? 'coverage' : 'agreement';
    changed();   // the selected zone stays selected across views
  });
  const sub = $('#sub-group');
  sub.hidden = tabOf(S.view) !== 'motion';
  pressGroup(sub, ['change', 'rate'].map(v => ({ key: v, html: esc(VIEW_LABEL[v]), disabled: viewAllowed(v) ? null : pendingText(S.sat) })),
    k => k === S.view || (k === 'change' && S.view === 'zones'), (k) => { S.view = k; changed(); });
}
// zone chips: every zone stays selectable even where markers overlap at the opening zoom (Zones 1 and 2)
function renderZoneChips() {
  const g = $('#zone-group');
  pressGroup(g, zones().map(z => ({ key: z.id, html: `<span class="zn">${esc(zoneShort(z))}</span><span class="zl"> ${esc(zoneName(z))}</span>`, title: `${zoneName(z)}: select, or click again to clear` })),
    k => S.selected?.kind === 'zone' && S.selected.id === k,
    (k) => { const on = S.selected?.kind === 'zone' && S.selected.id === k; select(on ? null : { kind: 'zone', id: k }); if (!on) flyToZone(k); });
}
// what the map shows right now: satellite, track, date or fit window, metric, run, reference, sign
function renderContext() {
  const s = S.sat === 'compare' ? null : S.sat;
  const parts = [];
  if (S.view === 'agreement') parts.push(`<b>Compare</b> · each satellite in its own line of sight${S.man.common_window ? ` · common window ${esc(S.man.common_window[0])} to ${esc(S.man.common_window[1])}` : ''}`);
  else if (s && measured(s)) {
    const trk = S.track[s]; const sn = sensors()[s];
    const head = `<b><span class="${SATS[s].cls}" aria-hidden="true">${SATS[s].mark}</span> ${esc(sn.label)} ${esc(trk)} ${ARROW[dirOf(s, trk)] || ''}</b>`;
    const ds = datesOf(s, trk);
    let metric;
    if (S.view === 'rate') metric = `Annualized line-of-sight rate (mm/yr) · fit window ${esc(ds[0] || '')} to ${esc(ds[ds.length - 1] || '')}`;
    else if (S.view === 'coverage') metric = `Usable measurements (a connected series) · ${esc(ds[0] || '')} to ${esc(ds[ds.length - 1] || '')}`;
    else { const L = layerFor(s); metric = L?.date ? `Line-of-sight change (mm) at <b>${esc(L.date)}</b> since <b>${esc(L.first)}</b>` : `No acquisition on ${esc(S.date || '')}`; }
    const run = s === 's1' && S.sens ? scenarioLabel(S.scenario) : 'Single run';
    const ref = s === 's1' && /west|east/.test(S.scenario) ? `${S.scenario.startsWith('west') ? 'West' : 'East'} half of the terrain band` : cleanLabel(sn.reference).replace(/\s*\(.*\)\s*$/, '');
    parts.push(head, metric, `Run: ${esc(run)}`, `Reference: ${esc(ref)}`);
    if (frames(s)[trk]?.flag) parts.push(`<span class="flagtxt">⚠ ${esc(frames(s)[trk].flag)}</span>`);
  } else parts.push(`<b>${esc(s ? sensors()[s].label : 'Compare')}</b> · ${esc(s ? pendingText(s) : 'side by side')}`);
  parts.push(`<span class="neg">${esc(NEG_TEXT)}</span>`);
  $('#ctx-what').innerHTML = parts.join('<span class="sep" aria-hidden="true"> · </span>');
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
      const flag = frames(s)[t]?.flag;
      b.textContent = `${t} ${ARROW[dir] || ''}${flag ? ' ⚠' : ''}`;
      if (flag) b.classList.add('flagged');
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
  const cov = S.view === 'coverage';
  $('#legend').classList.toggle('cov', cov);
  $('#legend-title').textContent = cov ? 'Usable measurements' : S.exp ? 'Vertical rate' : S.view === 'rate' ? 'Annualized line-of-sight rate' : 'Line-of-sight change';
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
  // a Sentinel-1 window can hold no pixel over the town for one track (Jan to Oct 007D: none stays connected through
  // 49 dates of C-band winter decorrelation); say so instead of showing an empty town, and offer the window that has it
  const cov = S.sat === 's1' && !n.innerHTML ? win()?.town_cover?.[S.track.s1] : null;
  if (cov != null && cov >= 0 && cov < 5) {
    const alt = Object.entries(S.sens?.windows || {}).filter(([k, w]) => k !== S.window && (w.town_cover?.[S.track.s1] ?? -1) >= 5)
      .sort((a, b) => b[1].town_cover[S.track.s1] - a[1].town_cover[S.track.s1])[0];
    n.innerHTML = `<span><b>Sentinel-1 ${esc(S.track.s1)} has almost no data over the town in ${esc(win().label)}</b> (${cov} % of it): a dot needs a connected series through every date, and C-band loses coherence in winter.${alt ? ` ${esc(alt[1].label)} covers ${alt[1].town_cover[S.track.s1]} %.` : ''}</span>`
      + (alt ? `<button type="button" data-window="${esc(alt[0])}">Show ${esc(alt[1].label)}</button>` : '');
  }
  if (!n.innerHTML) return;
  n.hidden = false;
  n.querySelector('[data-window]')?.addEventListener('click', (e) => { stopPlay(); S.window = e.currentTarget.dataset.window; S.note = null; S.date = null; changed(); });
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
function chart({ lines, from, to, gaps = [], window = null, height = 130, on = null, fits = [] }) {
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
  if (on && day(on) >= t0 && day(on) <= t1) o.push(`<line class="on-date" x1="${X(on).toFixed(1)}" x2="${X(on).toFixed(1)}" y1="${pt}" y2="${H - pb}" stroke="#1C1917" stroke-width="1" stroke-dasharray="2 2"><title>Map date ${esc(on)}</title></line>`);
  for (const f of fits) {   // fitted straight lines (a run's annualized slope over its window), drawn thin and dashed
    o.push(`<line x1="${X(f.from).toFixed(1)}" x2="${X(f.to).toFixed(1)}" y1="${Y(f.y0).toFixed(1)}" y2="${Y(f.y1).toFixed(1)}" stroke="${f.color}" stroke-width="1.6" stroke-dasharray="6 3" opacity=".9"><title>${esc(f.label)}</title></line>`);
  }
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
      const x = X(d), y = Y(v); const tip = `<title>${esc(l.label)} ${d}: ${v} mm · click to show this date on the map</title>`;
      const hit = d === on ? ' cpt on' : ' cpt';
      o.push(l.shape === 'tri'
        ? `<path class="${hit}" data-cdate="${esc(d)}" d="M${x.toFixed(1)},${(y - (d === on ? 5 : 3.6)).toFixed(1)} l${d === on ? 5 : 3.6},${d === on ? 5 : 3.6} l-${d === on ? 5 : 3.6},${d === on ? 5 : 3.6} l-${d === on ? 5 : 3.6},-${d === on ? 5 : 3.6}z" fill="${l.color}" stroke="${d === on ? '#1C1917' : '#fff'}" stroke-width="${d === on ? 1.4 : 0.8}">${tip}</path>`
        : `<circle class="${hit}" data-cdate="${esc(d)}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${d === on ? 4.5 : 3}" fill="${l.color}" stroke="${d === on ? '#1C1917' : '#fff'}" stroke-width="${d === on ? 1.6 : 0.8}">${tip}</circle>`);
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
// tables open in a dialog in front of the page; Export CSV downloads the same rows (15 Nov 2026)
const blockData = {};
function csvOf(lines) {
  const dates = [...new Set(lines.flatMap(l => l.dates))].sort();
  const q = (s) => `"${String(s).replace(/"/g, '""')}"`;
  const val = (l, d) => { const i = l.dates.indexOf(d); return i < 0 || l.mm[i] === null || l.mm[i] === undefined ? '' : l.mm[i]; };
  return [['date', ...lines.map(l => `${l.label} (mm)`)].map(q).join(','), ...dates.map(d => [d, ...lines.map(l => val(l, d))].join(','))].join('\n') + '\n';
}
function download(name, text) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], { type: 'text/csv;charset=utf-8' })); a.download = name;
  document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
}
function openTable(id) {
  const b = blockData[id]; if (!b) return;
  $('#table-body').innerHTML = `<h2>${b.title}</h2><p class="sub">${esc(NEG_TEXT)} Values in mm.</p>
    <p><button type="button" class="chip strong" id="table-csv">Export CSV</button></p>${b.html || table(b.lines)}`;
  $('#table-csv').onclick = () => download(`${S.site}_${id}.csv`, b.csv || csvOf(b.lines));
  $('#table-dlg').showModal();
}
function block(id, title, right, lines, extra = {}) {
  const [from, to] = extra.range || rangeOf(lines);
  blockData[id] = { title, lines };
  return `<div class="block"><h3><span>${title}</span>${right || ''}</h3>${extra.top || ''}
    ${lines.length ? chart({ lines, from, to, gaps: lines.flatMap(l => l.dash ? [] : l.gaps), window: extra.window, on: extra.on === undefined ? S.date : extra.on, fits: extra.fits || [] }) : ''}
    <div class="foot"><span>${extra.foot || ''}</span>${lines.length ? `<span class="tbtns"><button type="button" class="linkbtn" data-tview="${esc(id)}">Open table</button><button type="button" class="linkbtn" data-tcsv="${esc(id)}">Export CSV</button></span>` : ''}</div></div>`;
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
  if (!(measured('nisar') && measured('s1'))) {
    const why = !measured('nisar') ? 'NISAR displacement fit pending' : !measured('s1') ? 'Sentinel-1 measurements pending' : (S.man.compare.reason || 'not ready');
    return `${head}<div class="verdict na">Not testable yet · ${esc(why)}. How to compare the two radars on one shared quantity is also still undecided.</div>
      <p class="reason">NISAR and Sentinel-1 look from different sides, so their line-of-sight values are different quantities until the team decides how to put them on one shared quantity.</p>${egmsPanel()}`;
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
  const block_ = S.man.compare?.ready === false ? `<div class="verdict warn"><span>!</span> ${esc(S.man.compare.reason)}</div>` : '';
  return `${head}${block_}<p class="sub small">Shown as the zone minus the outer comparison area, a proposed contrast until the team decides how to compare the two radars. Select a zone (chips above the map) for its parallel observations.</p>
    ${keys(['nisar', 's1'].map(s => ({ label: `${sensors()[s].label} ${trk[s]}`, color: SATS[s].color })))}${blocks.join('')}<h3 class="sub-h">Historical context</h3>${egmsPanel()}`;
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
// one station panel per monument: every GNSS solution there, each against every radar track that covers it
function stationSheet(id) {
  const f0 = S.stations?.features.find(f => f.properties.station === id); if (!f0) return null;
  const k = f0.geometry.coordinates.map(v => v.toFixed(4)).join(',');
  const group = S.stations.features.filter(f => f.geometry.coordinates.map(v => v.toFixed(4)).join(',') === k)
    .sort((a, b) => (b.properties.combined ? 1 : 0) - (a.properties.combined ? 1 : 0));
  const label = (key) => { const [s, t] = key.split(':'); return `<span class="${SATS[s]?.cls || ''}" aria-hidden="true">${SATS[s]?.mark || ''}</span> ${esc(sensors()[s]?.label || s)} ${esc(t)}`; };
  let html = `<h2>${esc(group.filter(g => !g.properties.combined).map(g => g.properties.station).join(' · ') || f0.properties.station)}</h2>
    <div class="kicker">GNSS monument · ${esc(f0.properties.dist_km)} km from the town · ${group.length} solution${group.length > 1 ? 's' : ''}</div>
    <p class="reason">Each solution is compared with every radar track covering the station. A tolerance includes how much a station-sized patch of radar pixels scatters on stable ground (correlated noise), so a "disagree" inside a wide tolerance is not evidence. ${esc(NEG_TEXT)}</p>`;
  for (const f of group) {
    const p = f.properties;
    const v = p.status === 'warn' ? ['warn', '!', 'Inconclusive: radar noise wider than the test'] : p.agree === true ? ['yes', '✔', 'Satellite and station agree'] : p.agree === false ? ['no', '✘', 'Satellite and station disagree'] : ['na', '?', 'Not tested'];
    html += `<div class="block"><h3><span>${esc(p.station)}</span><span class="badge">${esc(p.period || '')}</span></h3><p class="sub small">${esc(cleanLabel(p.source))}${p.t_end ? ` · series ends ${esc(p.t_end)}, assumes steady motion since` : ''}</p>`;
    const rows = Object.entries(p.tracks || {});
    html += rows.length ? `<div class="tscroll"><table class="data"><thead><tr><th>Radar</th><th>Radar, mm/yr</th><th>GNSS in LOS, mm/yr</th><th>Difference</th><th>Tolerance</th><th>Pixels</th></tr></thead><tbody>${rows.map(([key, t]) => `<tr><td>${label(key)}</td><td>${fmt(t.radar ?? t.nisar)}</td><td>${fmt(t.gnss)}</td><td>${fmt(t.diff)}</td><td>±${esc(t.tol)}</td><td>${esc(t.n_px)} (${esc(t.radius_m)} m)</td></tr>`).join('')}</tbody></table></div>` : '<p class="reason">No radar track covers this station.</p>';
    html += `<div class="verdict ${v[0]}"><span aria-hidden="true">${v[1]}</span> ${v[2]}</div></div>`;
  }
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
  html += block(`d-${z.id}`, 'Change over time, mm', '', lines, { foot: `${lines.filter(l => !l.dash).map(l => `${l.label}: ${l.n ?? 'n/a'} pixels`).join(' · ')} · click a point to show that date on the map` });
  if (S.sat === 's1' && scenarios()) html += runsPanel(z, S.track.s1);
  if (scenarios() && S.sat === 's1') {
    const rows = Object.entries(scenarios()).map(([k, l]) => `<tr${k === S.scenario ? ' class="here"' : ''}><td>${esc(l)}</td>${tracksOf('s1').map(t => { const e = entry(z, 's1', t, k); return `<td>${e ? `${fmt(e.fitted_change_mm, 1)} mm · ${e.n_pixels} px` : '<span class="sub">no series</span>'}</td>`; }).join('')}</tr>`).join('');
    html += `<div class="block"><h3>Every processing run</h3><table class="data"><thead><tr><th>Run</th>${tracksOf('s1').map(t => `<th>${esc(t)} ${ARROW[dirOf('s1', t)] || ''}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div>`;
  }
  html += `<p class="reason">${esc(NEG_TEXT)} Values are line-of-sight change in mm, relative to nearby terrain. A fitted change is the fitted line over the window, not the difference between the first and last dates. EGMS vertical rates (mm/yr, 2020 to 2025) are historical context, under Compare.</p>`;
  return html;
}
// a window's stored series for one zone, track and run (sensitivity.json), whatever window is selected
const entryIn = (w, point, trk, sc) => S.sens?.windows?.[w]?.variants?.[trk]?.[sc]?.[point.id] ?? null;
function fitOf(e) {   // the run's fitted line: slope = its annualized rate, through the mean of its observations
  const pts = e.dates.map((d, i) => [d, e.mm[i]]).filter(([, v]) => v !== null && Number.isFinite(v));
  if (pts.length < 2 || !Number.isFinite(e.rate)) return null;
  const tm = pts.reduce((a, [d]) => a + day(d), 0) / pts.length, ym = pts.reduce((a, [, v]) => a + v, 0) / pts.length;
  const at = (d) => ym + e.rate * (day(d) - tm) / 365.25;
  return { from: pts[0][0], to: pts[pts.length - 1][0], y0: at(pts[0][0]), y1: at(pts[pts.length - 1][0]) };
}
function runRef(sc) {
  if (sc === 'west_reference') return 'West half of the 3 to 6.5 km terrain band';
  if (sc === 'east_reference') return 'East half of the 3 to 6.5 km terrain band';
  return 'Terrain band 3 to 6.5 km from the zones';
}
// "Compare processing runs": the baseline and one alternative on shared axes, observed points and fitted lines
function runsPanel(z, trk) {
  const all = Object.keys(scenarios() || {});
  const have = all.filter(sc => entry(z, 's1', trk, sc));
  const base = entry(z, 's1', trk, 'baseline');
  if (!base) return '';
  const flips = have.filter(sc => sc !== 'baseline' && Math.sign(entry(z, 's1', trk, sc).fitted_change_mm) === -Math.sign(base.fitted_change_mm));
  const alts = have.filter(sc => sc !== 'baseline');
  if (!alts.includes(S.cmpRun)) S.cmpRun = flips.includes('elevation_correction') ? 'elevation_correction' : (flips[0] || alts[0]);
  const alt = S.cmpRun && entry(z, 's1', trk, S.cmpRun);
  const runs = [['baseline', base, RUN_COLORS[0]], ...(alt ? [[S.cmpRun, alt, RUN_COLORS[1]]] : [])];
  const lines = runs.map(([sc, e, c], i) => ({ label: scenarioLabel(sc), color: c, shape: i ? 'dot' : 'tri', dates: e.dates, mm: e.mm, gaps: [], n: e.n_pixels }));
  const fits = runs.map(([sc, e, c]) => { const f = fitOf(e); return f && { ...f, color: c, label: `${scenarioLabel(sc)}: fitted ${fmt(e.fitted_change_mm, 2)} mm` }; }).filter(Boolean);
  const n = (e) => e.mm.filter(v => v !== null && Number.isFinite(v)).length;
  const rows = have.map(sc => { const e = entry(z, 's1', trk, sc);
    return `<tr${runs.some(r => r[0] === sc) ? ' class="here"' : ''}><td>${esc(scenarioLabel(sc))}</td><td><b>${fmt(e.fitted_change_mm, 2)} mm</b></td><td>${n(e)}</td><td>${e.n_pixels}${e.n_pixels < LIMITED_PX ? ` <span class="badge warn">only ${e.n_pixels} px</span>` : ''}</td><td>${esc(e.dates[0])} to ${esc(e.dates[e.dates.length - 1])}</td><td>${esc(runRef(sc))}</td></tr>`; }).join('');
  const missing = all.filter(sc => !have.includes(sc)).map(sc => {
    const elsewhere = Object.entries(S.sens.windows).filter(([w]) => w !== S.window && entryIn(w, z, trk, sc)).map(([, w]) => w.label);
    const why = sc === 'weather_model' && S.window === 'jan_oct'
      ? 'the acquisition-time weather correction needs each interferogram, and the January to October interferograms are not in the repository (job IDs only, sentinel1/analysis_jan_oct/README.md)'
      : 'no series is stored for this zone, track and window';
    return `<li><b>${esc(scenarioLabel(sc))}</b>: not available for ${esc(win()?.label || 'this window')}: ${esc(why)}.${elsewhere.length ? ` Available for ${esc(elsewhere.join(', '))}.` : ''}</li>`;
  }).join('');
  const q = (s) => `"${String(s).replace(/"/g, '""')}"`;
  blockData[`runs-${z.id}`] = { title: `${esc(zoneName(z))}: processing runs, ${esc(trk)}, ${esc(win()?.label || '')}`,
    html: `<div class="tscroll"><table class="data runs-t big"><thead><tr><th>Run</th><th>Fitted change</th><th>Acquisitions</th><th>Usable pixels</th><th>Window</th><th>Reference</th></tr></thead><tbody>${rows}</tbody></table></div>${table(have.map(sc => { const e = entry(z, 's1', trk, sc); return { label: scenarioLabel(sc), dates: e.dates, mm: e.mm }; }))}`,
    csv: ['run,fitted_change_mm,acquisitions,usable_pixels,window_start,window_end,reference', ...have.map(sc => { const e = entry(z, 's1', trk, sc);
      return [q(scenarioLabel(sc)), e.fitted_change_mm, n(e), e.n_pixels, e.dates[0], e.dates[e.dates.length - 1], q(runRef(sc))].join(','); })].join('\n') + '\n' };
  const lead = flips.length ? `<div class="lead-finding"><b>Fitted direction changes with processing</b><span>Baseline ${fmt(base.fitted_change_mm, 2)} mm; ${flips.map(sc => { const e = entry(z, 's1', trk, sc); return `${esc(scenarioLabel(sc))} ${fmt(e.fitted_change_mm, 2)} mm (${e.n_pixels} px)`; }).join('; ')}. The sign of this zone's result depends on how the data are processed, so it is not a settled finding.</span></div>` : '';
  return `${lead}<div class="block runs"><h3><span>Compare processing runs</span><span class="badge">${esc(trk)} · ${esc(win()?.label || '')}</span></h3>
    <label class="runpick">Overlay with <select id="cmp-run">${alts.map(sc => `<option value="${esc(sc)}"${sc === S.cmpRun ? ' selected' : ''}>${esc(scenarioLabel(sc))}</option>`).join('')}</select></label>
    ${keys(lines.map(l => ({ ...l, label: `${l.label}: observed` })).concat(fits.map(f => ({ label: `${f.label.split(':')[0]}: fitted line`, color: f.color, dash: true }))))}
    ${chart({ lines, ...(() => { const [a, b] = rangeOf(lines); return { from: a, to: b }; })(), fits, on: S.date })}
    <div class="tscroll"><table class="data runs-t"><thead><tr><th>Run</th><th>Fitted change</th><th>Acquisitions</th><th>Usable pixels</th><th>Window</th><th>Reference</th></tr></thead><tbody>${rows}</tbody></table></div>
    <p class="tbtns"><button type="button" class="linkbtn" data-tview="runs-${esc(z.id)}">Open table</button><button type="button" class="linkbtn" data-tcsv="runs-${esc(z.id)}">Export CSV</button></p>
    ${missing ? `<ul class="missing">${missing}</ul>` : ''}
    <p class="sub small">Observed points are the zone median at each acquisition; dashed lines are each run's fitted annualized slope over its window. The elevation correction is fitted to the data, so it can absorb real motion that follows elevation. ${esc(NEG_TEXT)}</p></div>`;
}
// Coverage for one zone: a support row per satellite and track for the active window, or the reason it has none
function zoneCoverage(id) {
  const z = S.series.find(p => p.id === id); if (!z) return null;
  const rows = [];
  for (const s of sensorKeys()) {
    const tracks = [...new Set([...tracksOf(s), ...Object.keys(covOf(s))])];
    for (const t of tracks) {
      const e = entry(z, s, t);
      const head = `<span class="${SATS[s].cls}" aria-hidden="true">${SATS[s].mark}</span> ${esc(sensors()[s].label)} ${esc(t)} ${ARROW[dirOf(s, t)] || ''}`;
      if (e) { rows.push(`<tr><td>${head}</td><td><b>${e.n_pixels}</b> px${e.n_pixels < LIMITED_PX ? ' <span class="badge warn">limited</span>' : ''}</td><td>${e.mm.filter(v => v !== null).length} acquisitions, ${esc(e.dates[0])} to ${esc(e.dates[e.dates.length - 1])}</td></tr>`); continue; }
      let why = s === 'nisar' && !tracksOf('nisar').includes(t) ? (sensors().nisar.pending || 'not on the page') : emptyZoneLabel(s);
      const other = tracksOf(s).find(o => o !== t && entry(z, s, o));
      const elsewhere = s === 's1' ? Object.entries(S.sens?.windows || {}).filter(([w]) => w !== S.window && entryIn(w, z, t, 'baseline')).map(([k, w]) => [k, w.label]) : [];
      rows.push(`<tr class="none"><td>${head}</td><td>none</td><td>${esc(why)}${other ? ` <button type="button" class="linkbtn" data-trk="${esc(s)}|${esc(other)}">Show ${esc(other)} for this zone</button>` : ''}${elsewhere.map(([k, l]) => ` <button type="button" class="linkbtn" data-win="${esc(k)}">${esc(l)} has a series</button>`).join('')}</td></tr>`);
    }
  }
  return `<h2>${esc(zoneName(z))}: coverage</h2><div class="kicker">${esc(win()?.label || '')} · usable pixels with a connected series</div>
    <p class="reason">The map shows every pixel with a connected series on the active track and window (grey dots, whatever their value). The timeline shows catalog acquisitions, which exist even where the ground is not coherent enough to measure.</p>
    <table class="data"><thead><tr><th>Track</th><th>Zone pixels</th><th>Support or reason</th></tr></thead><tbody>${rows.join('')}</tbody></table>`;
}
// Compare for one zone: parallel observations over the common window, each in its own line of sight
function zoneCompare(id) {
  const z = S.series.find(p => p.id === id); if (!z) return null;
  const w = S.man.common_window; const ctl = control();
  const look = (s) => sensors()[s]?.look ? `looks ${sensors()[s].look}` : '';
  const minus = (s, t, sel) => {
    const a = sel(z), b = ctl && sel(ctl);
    if (!a) return null;
    const mm = a.dates.map((d, i) => { if (!b) return a.mm[i]; const j = b.dates.indexOf(d); return j < 0 || a.mm[i] === null || b.mm[j] === null ? null : Math.round((a.mm[i] - b.mm[j]) * 10) / 10; });
    return { label: `${sensors()[s].label} ${t} (${(dirOf(s, t) || '').toLowerCase()}, ${look(s)})`, color: s === 'nisar' ? SATS.nisar.color : (dirOf(s, t) === 'Ascending' ? SATS.s1.color : '#A78BFA'), shape: SATS[s].shape, dates: a.dates, mm, gaps: gapsOf(s, t), n: a.n_pixels, dash: false };
  };
  const lines = [];
  for (const t of tracksOf('nisar')) { const l = minus('nisar', t, (p) => p.series?.[`nisar:${t}`]); if (l) lines.push(l); }
  for (const t of tracksOf('s1')) { const l = minus('s1', t, (p) => entryIn(S.sens?.default_window || 'jul_oct', p, t, 'baseline') || p.series?.[`s1:${t}`]); if (l) lines.push(l); }
  const c = checkForZone(z);
  const word = c ? (c.status === 'pass' ? 'Agree' : c.status === 'fail' ? 'Disagree' : c.status === 'warn' ? 'Inconclusive' : 'Not testable') : 'Not tested yet';
  const blockers = [S.man.compare?.ready === false ? S.man.compare.reason : null, sensors().nisar?.pending,
    'The two satellites look from opposite sides, so their line-of-sight values are different quantities until the team decides on a shared quantity and geometry.'].filter(Boolean);
  return `<h2>${esc(zoneName(z))}: compare</h2><div class="kicker">Zone minus the outer comparison area (6.5 to 8 km), each track in its own line of sight${w ? ` · common window ${esc(w[0])} to ${esc(w[1])}` : ''}</div>
    <div class="verdict ${c ? esc(c.status) : 'na'}"><span>${c ? STATUS_ICON[c.status] : '?'}</span> ${esc(word)} <span class="sub">(validator)</span></div>
    ${c ? `<p class="reason">${esc(c.detail)} <button type="button" class="linkbtn" data-chk="${esc(c.id)}">Evidence</button></p>` : '<p class="reason">The validator has not reported on this zone.</p>'}
    ${block(`c-${z.id}`, 'Parallel observations, mm', '', lines, { window: w, range: w ? [iso(day(w[0]) - 20), iso(day(w[1]) + 20)] : undefined, foot: lines.map(l => `${l.label}: ${l.n ?? 'n/a'} px`).join(' · ') })}
    <div class="block"><h3>Still inconclusive</h3><ul class="missing">${blockers.map(b => `<li>${esc(b)}</li>`).join('')}</ul></div>
    <h3 class="sub-h">Historical context</h3>${egmsPanel()}`;
}
function renderSheet() {
  const sh = $('#sheet'); let html = null;
  if (S.selected?.kind === 'zone' && S.view === 'coverage') html = zoneCoverage(S.selected.id);
  else if (S.selected?.kind === 'zone' && S.view === 'agreement') html = zoneCompare(S.selected.id);
  else if (S.selected) html = S.selected.kind === 'station' ? stationSheet(S.selected.id) : zoneSheet(S.selected.id);
  else if (S.view === 'zones') html = zonesSheet();
  else if (S.view === 'agreement') html = agreementSheet();
  else if (S.view === 'coverage') html = coverageSheet();
  sh.classList.toggle('wide', !S.selected && S.view === 'coverage');
  if (!html) { sh.hidden = true; return; }
  const top = sh.scrollTop;
  $('#sheet-body').innerHTML = html; sh.hidden = false; sh.scrollTop = top;
  sh.querySelectorAll('[data-tview]').forEach(b => b.onclick = () => openTable(b.dataset.tview));
  sh.querySelectorAll('[data-tcsv]').forEach(b => b.onclick = () => { const d = blockData[b.dataset.tcsv]; if (d) download(`${S.site}_${b.dataset.tcsv}.csv`, d.csv || csvOf(d.lines)); });
  sh.querySelectorAll('[data-go]').forEach(b => b.onclick = () => goSentinel());
  sh.querySelectorAll('[data-fill]').forEach(b => b.onclick = () => { const [a, c] = b.dataset.fill.split('|'); fillGap(a, c); });
  wireChoices(sh);
  sh.querySelectorAll('[data-cdate]').forEach(p => p.addEventListener('click', () => { stopPlay(); setDate(p.dataset.cdate); }));
  sh.querySelector('#cmp-run')?.addEventListener('change', (e) => { S.cmpRun = e.target.value; renderSheet(); });
  sh.querySelectorAll('[data-trk]').forEach(b => b.onclick = () => { const [s, t] = b.dataset.trk.split('|'); S.track[s] = t; changed(); });
  sh.querySelectorAll('[data-win]').forEach(b => b.onclick = () => { S.window = b.dataset.win; S.date = null; S.dateUser = false; changed(); });
  sh.querySelectorAll('[data-chk]').forEach(b => b.onclick = () => { $('#checks-btn').dataset.target = b.dataset.chk; $('#checks-btn').click(); });
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
  renderFootprint(); renderZoneChips(); renderChecksButton(); renderContext(); writeHash();
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
    <ul class="checks">${S.checks.map(c => `<li id="chk-${esc(c.id)}" class="${esc(c.status)}"><span class="ic" title="${esc(c.status)}">${STATUS_ICON[c.status] || '·'}</span><div><div>${esc(c.title)}</div><div class="detail">${esc(c.detail)}${c.value !== null && c.value !== undefined ? ` · value ${esc(c.value)}` : ''}</div></div></li>`).join('') || '<li>No checks yet.</li>'}</ul>
    ${S.updates ? `<h3>Data freshness</h3><p class="sub">${esc(S.updates.summary)} Checked ${esc(S.updates.checked)} (update.py).</p>` : ''}
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
  renderContext(); renderZoneChips(); renderFootprint(); renderChecksButton();
  writeHash();
  requestAnimationFrame(measure);
}
function measure() {
  document.documentElement.style.setProperty('--dock-h', `${Math.round($('#dock').getBoundingClientRect().height)}px`);
  document.documentElement.style.setProperty('--ctx-h', `${Math.round($('#context').getBoundingClientRect().height)}px`);
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
  $('#checks-btn').addEventListener('click', () => {
    $('#about').showModal();
    const id = $('#checks-btn').dataset.target; const li = id && document.getElementById(`chk-${id}`);
    document.querySelectorAll('.checks li.here').forEach(e => e.classList.remove('here'));
    if (li) { li.classList.add('here'); li.scrollIntoView({ block: 'center' }); } else $('#checks-h').scrollIntoView();
  });
  $('#preset-z4').addEventListener('click', () => applyPreset());
  $('#reset-site').addEventListener('click', () => {
    select(null); const v = S.man.view; mapA?.flyTo({ center: [v.center[1], v.center[0]], zoom: v.zoom - ZOOM_OFFSET });
  });
  $('#copy-link').addEventListener('click', async () => {
    writeHash();
    const b = $('#copy-link'); const was = b.textContent;
    try { await navigator.clipboard.writeText(location.href); b.textContent = 'Link copied'; }
    catch (e) { window.prompt('Copy this link', location.href); }
    setTimeout(() => { b.textContent = was; }, 1600);
  });
  $('#about').addEventListener('click', (e) => { if (e.target === e.currentTarget) e.currentTarget.close(); });
  $('#table-dlg').addEventListener('click', (e) => { if (e.target === e.currentTarget) e.currentTarget.close(); });
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
  initLang(readHash().lang);
  document.querySelectorAll('[data-lang]').forEach(b => b.addEventListener('click', () => { setLang(b.dataset.lang); writeHash(); }));
  changed();
}
main();

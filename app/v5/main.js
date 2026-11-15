// Owner: 06 · App developer (Darius)
// Layout v5 (15 Nov 2026): toolbar, map, timeline, and a menu that opens when the map is used. It reads
// products/<site>/ only; no measured number is typed in this file.
import * as maplibregl from 'https://unpkg.com/maplibre-gl@6.15.0/dist/maplibre-gl.mjs';

const DIR = '../../products/ocnele_mari/';
const INK = '#2A1A0F';
const SPAN = [2020, 2026];                       // the timeline runs from January 2020 to December 2026
const AREA_M = 500;                              // the legend's "area": dots within this distance of the click
const ZOOM_OFFSET = 1;                           // manifest zoom uses 256 px tiles; MapLibre uses 512 px tiles
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const SATELLITE_TILES = 'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg';

const S = { man: null, sens: null, sat: 's1', unit: 'years', period: null, date: null, pts: null, click: null };
let map = null;
const $ = (s) => document.querySelector(s);
const get = (f) => fetch(DIR + f, { cache: 'no-cache' }).then(r => { if (!r.ok) throw new Error(`${f}: HTTP ${r.status}`); return r.json(); });
const day = (d) => Date.parse(d + 'T00:00:00Z') / 864e5;
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// ------------------------------------------------------------------ data: one track per satellite, its longest window
function source(sat) {
  if (sat === 's1') {
    const ws = Object.values(S.sens?.windows || {});
    const all = ws.map(w => Object.entries(w.frames || {}).map(([t, f]) => ({ t, f, w }))).flat();
    // the longest series; among equally long ones, the track with the most measured points (S.s1Points, set at start)
    const best = all.sort((a, b) => b.f.dates.length - a.f.dates.length
      || (S.s1Points?.[b.w.points[b.t]] || 0) - (S.s1Points?.[a.w.points[a.t]] || 0) || (a.t > b.t ? 1 : -1))[0];
    return best ? { track: best.t, dates: best.f.dates, vmax: best.f.vmax, points: best.w.points[best.t] } : null;
  }
  const n = S.man.sensors.nisar; const flags = n.flags || {};
  const t = Object.keys(n.frames || {}).find(k => !flags[k]) || Object.keys(n.frames || {})[0];
  return t ? { track: t, dates: n.frames[t].dates, vmax: n.frames[t].vmax, points: n.points[t] } : null;
}
const cache = {};
function loadPoints(file) {
  cache[file] = cache[file] || get(file).then(d => ({
    dates: d.dates, scale: d.scale,
    gj: { type: 'FeatureCollection', features: d.lon.map((lon, i) => {
      const p = {}; d.change.forEach((col, k) => { if (col[i] !== null) p[`c${k}`] = col[i] * d.scale; });
      return { type: 'Feature', geometry: { type: 'Point', coordinates: [lon, d.lat[i]] }, properties: p };
    }) },
  }));
  return cache[file];
}

// ------------------------------------------------------------------ periods on the timeline
const periodOf = (d) => S.unit === 'years' ? d.slice(0, 4) : d.slice(0, 7);
const inPeriod = (d, p) => d.startsWith(p);
function pickDate() {   // the last acquisition inside the selected period, for the active satellite
  const src = source(S.sat); if (!src || !S.period) { S.date = null; return; }
  const ds = src.dates.filter(d => inPeriod(d, S.period));
  S.date = ds.length ? ds[ds.length - 1] : null;
}

// ------------------------------------------------------------------ map
function rdbu(key, v) {
  return ['interpolate', ['linear'], ['get', key], -v, '#67001F', -v / 2, '#D6604D', 0, '#F7F7F7', v / 2, '#4393C3', v, '#053061'];
}
function makeMap() {
  const v = S.man.view;
  map = new maplibregl.Map({
    container: 'map', center: [v.center[1], v.center[0]], zoom: v.zoom - ZOOM_OFFSET, maxZoom: 16, attributionControl: false,
    dragRotate: false, pitchWithRotate: false,
    style: { version: 8, sources: { base: { type: 'raster', tiles: [SATELLITE_TILES], tileSize: 256, maxzoom: 15,
      attribution: 'Sentinel-2 cloudless 2020 by EOX IT Services GmbH (contains modified Copernicus Sentinel data 2020)' } },
    layers: [{ id: 'base', type: 'raster', source: 'base' }] },
  });
  map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-left');
  map.on('load', () => {
    map.addSource('town', { type: 'geojson', data: '../ocnele_mari_boundary.geojson' });
    map.addLayer({ id: 'town', type: 'line', source: 'town', paint: { 'line-color': '#F4ECDB', 'line-width': 2 } });
    map.addSource('pts', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'pts', type: 'circle', source: 'pts', layout: { visibility: 'none' }, paint: {
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 9, 1, 12, 2.6, 14, 5, 16, 9],
      'circle-stroke-width': 0.5, 'circle-stroke-color': INK, 'circle-opacity': 0.85 } });
    map.addSource('area', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'area', type: 'line', source: 'area', paint: { 'line-color': INK, 'line-width': 2 } });
    drawPoints();
  });
  map.on('click', (e) => { S.click = [e.lngLat.lng, e.lngLat.lat]; $('#menu').hidden = false; drawArea(); renderMenu(); });
  map.on('zoomend', () => { if (!$('#menu').hidden) renderLegend(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { $('#menu').hidden = true; S.click = null; drawArea(); } });
}
async function drawPoints() {
  if (!map?.getSource('pts')) return;
  const src = source(S.sat);
  if (!src) { map.setLayoutProperty('pts', 'visibility', 'none'); return; }
  const P = await loadPoints(src.points);
  if (source(S.sat)?.points !== src.points) return;            // the satellite changed while loading
  S.pts = P;
  map.getSource('pts').setData(P.gj);
  const k = S.date ? P.dates.indexOf(S.date) : -1;
  if (k < 0) { map.setLayoutProperty('pts', 'visibility', 'none'); return; }
  map.setPaintProperty('pts', 'circle-color', rdbu(`c${k}`, src.vmax));
  map.setFilter('pts', ['has', `c${k}`]);
  map.setLayoutProperty('pts', 'visibility', 'visible');
}
function circle([lon, lat], r, n = 72) {
  const R = 6371008.8, ring = [];
  for (let i = 0; i <= n; i++) {
    const a = 2 * Math.PI * i / n;
    ring.push([lon + (r * Math.sin(a) / (R * Math.cos(lat * Math.PI / 180))) * 180 / Math.PI, lat + (r * Math.cos(a) / R) * 180 / Math.PI]);
  }
  return { type: 'Feature', geometry: { type: 'Polygon', coordinates: [ring] }, properties: {} };
}
function drawArea() {
  map?.getSource('area')?.setData({ type: 'FeatureCollection', features: S.click ? [circle(S.click, AREA_M)] : [] });
}
const distM = ([a, b], [c, d]) => Math.hypot((c - a) * 111320 * Math.cos(b * Math.PI / 180), (d - b) * 110540);

// ------------------------------------------------------------------ menu: graph and legend for the clicked place
function areaPoints() {
  if (!S.pts || !S.click) return [];
  return S.pts.gj.features.filter(f => distM(S.click, f.geometry.coordinates) <= AREA_M);
}
function renderMenu() { renderGraph(); renderLegend(); }
function renderGraph() {
  const el = $('#graph'); const pts = areaPoints();
  if (!S.pts) { el.innerHTML = ''; return; }
  // the area's median change at every acquisition, in mm
  const series = S.pts.dates.map((d, k) => {
    const v = pts.map(f => f.properties[`c${k}`]).filter(Number.isFinite).sort((a, b) => a - b);
    return [d, v.length ? v[Math.floor(v.length / 2)] : null];
  }).filter(([, v]) => v !== null);
  const W = 1000, H = 400, l = 70, r = 20, t = 20, b = 50;
  if (!series.length) { el.innerHTML = `<svg viewBox="0 0 ${W} ${H}"><text x="${W / 2}" y="${H / 2}" text-anchor="middle" font-size="22">No measurement within ${AREA_M} m</text></svg>`; return; }
  const ys = series.map(([, v]) => v);
  const ymin = Math.min(0, Math.floor(Math.min(...ys))), ymax = Math.max(0, Math.ceil(Math.max(...ys)));
  const t0 = day(series[0][0]), t1 = Math.max(day(series[series.length - 1][0]), t0 + 1);
  const X = (d) => l + (day(d) - t0) / (t1 - t0) * (W - l - r);
  const Y = (v) => t + (ymax - v) / Math.max(ymax - ymin, 1) * (H - t - b);
  const o = [`<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="Median line-of-sight change in the area, mm">`];
  o.push(`<line x1="${l}" x2="${l}" y1="${t}" y2="${H - b}" stroke="${INK}"/><line x1="${l}" x2="${W - r}" y1="${H - b}" y2="${H - b}" stroke="${INK}"/>`);
  o.push(`<line x1="${l}" x2="${W - r}" y1="${Y(0)}" y2="${Y(0)}" stroke="${INK}" stroke-opacity="0.5" stroke-dasharray="6 5"/>`);
  for (const v of [ymax, 0, ymin]) o.push(`<text x="${l - 10}" y="${Y(v) + 7}" text-anchor="end" font-size="20">${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v)} mm</text>`);
  const months = [...new Set(series.map(([d]) => d.slice(0, 7)))];
  const step = Math.max(1, Math.ceil(months.length / 8));
  months.forEach((m, i) => { if (i % step) return; const x = X(m + '-01') < l ? l : X(m + '-01');
    o.push(`<text x="${x}" y="${H - b + 28}" text-anchor="middle" font-size="18">${MONTHS[+m.slice(5) - 1]} ${m.slice(0, 4)}</text>`); });
  o.push(`<polyline fill="none" stroke="${INK}" stroke-width="2.5" points="${series.map(([d, v]) => `${X(d).toFixed(1)},${Y(v).toFixed(1)}`).join(' ')}"/>`);
  for (const [d, v] of series) o.push(`<rect x="${X(d) - 4}" y="${Y(v) - 4}" width="8" height="8" fill="${d === S.date ? '#E30B5C' : INK}"><title>${d}: ${v.toFixed(1)} mm</title></rect>`);
  o.push('</svg>');
  el.innerHTML = o.join('');
}
function renderLegend() {
  const el = $('#legend'); const src = source(S.sat);
  if (!src) { el.innerHTML = ''; return; }
  const k = S.pts && S.date ? S.pts.dates.indexOf(S.date) : -1;
  const vals = k < 0 ? [] : areaPoints().map(f => f.properties[`c${k}`]).filter(Number.isFinite).sort((a, b) => a - b);
  const med = vals.length ? Math.floor(vals[Math.floor(vals.length / 2)]) : null;
  const v = src.vmax;
  // interpretation scale: how many metres one centimetre of screen covers at this zoom and latitude
  const lat = map.getCenter().lat, mpp = 40075016.686 * Math.cos(lat * Math.PI / 180) / (512 * 2 ** map.getZoom());
  const cmPx = 96 / 2.54, perCm = mpp * cmPx;
  const nice = perCm >= 1000 ? `${(perCm / 1000).toFixed(perCm >= 10000 ? 0 : 1)} km` : `${Math.round(perCm / 10) * 10} m`;
  const W = 1000, H = 60;
  const x = (val) => 20 + (Math.max(-v, Math.min(v, val)) + v) / (2 * v) * 560;
  el.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="Colour scale and map scale">
    <defs><linearGradient id="rdbu"><stop offset="0" stop-color="#67001F"/><stop offset=".25" stop-color="#D6604D"/><stop offset=".5" stop-color="#F7F7F7"/><stop offset=".75" stop-color="#4393C3"/><stop offset="1" stop-color="#053061"/></linearGradient></defs>
    <rect x="20" y="6" width="560" height="16" fill="url(#rdbu)" stroke="${INK}"/>
    <text x="20" y="44" font-size="15">−${v} mm</text><text x="300" y="44" font-size="15" text-anchor="middle">0</text><text x="580" y="44" font-size="15" text-anchor="end">+${v} mm</text>
    ${med !== null ? `<line x1="${x(med)}" x2="${x(med)}" y1="2" y2="26" stroke="${INK}" stroke-width="3"/><text x="${x(med)}" y="58" font-size="14" text-anchor="middle">area median ${med > 0 ? '+' : med < 0 ? '−' : ''}${Math.abs(med)} mm</text>` : ''}
    <line x1="700" x2="${700 + cmPx * 2}" y1="16" y2="16" stroke="${INK}" stroke-width="3"/><line x1="700" x2="700" y1="10" y2="22" stroke="${INK}"/><line x1="${700 + cmPx * 2}" x2="${700 + cmPx * 2}" y1="10" y2="22" stroke="${INK}"/>
    <text x="700" y="44" font-size="15">1 cm on screen = ${nice} on the map</text></svg>`;
}

// ------------------------------------------------------------------ timeline
function renderTimeline() {
  const svg = $('#tl-svg'); const W = svg.clientWidth || 1000, H = svg.clientHeight || 120;
  const pad = 20, y = H * 0.45, x0 = pad, x1 = W - pad;
  const years = []; for (let yr = SPAN[0]; yr <= SPAN[1]; yr++) years.push(yr);
  const units = S.unit === 'years' ? years.map(yr => String(yr)) : years.flatMap(yr => MONTHS.map((_, m) => `${yr}-${String(m + 1).padStart(2, '0')}`));
  const w = (x1 - x0) / units.length;
  const o = [`<line x1="${x0}" x2="${x1}" y1="${y}" y2="${y}" stroke-width="1.5"/>`];
  units.forEach((u, i) => {
    const x = x0 + i * w;
    if (u === S.period) o.push(`<rect x="${x}" y="${y - H * 0.28}" width="${w}" height="${H * 0.56}" fill="rgba(227, 11, 92, 0.7)"/>`);
    const major = S.unit === 'years' || u.endsWith('-01');
    o.push(`<line x1="${x}" x2="${x}" y1="${y - (major ? 14 : 6)}" y2="${y + (major ? 14 : 6)}"/>`);
    if (S.unit === 'years') o.push(`<text x="${x + w / 2}" y="${y + 34}" text-anchor="middle" font-size="15">${u}</text>`);
    else {
      if (w > 11) o.push(`<text x="${x + w / 2}" y="${y + 26}" text-anchor="middle" font-size="${Math.min(12, w * 0.8)}">${MONTHS[+u.slice(5) - 1][0]}</text>`);
      if (u.endsWith('-01')) o.push(`<text x="${x + 2}" y="${y + 46}" font-size="14">${u.slice(0, 4)}</text>`);
    }
    o.push(`<rect class="hit" data-p="${u}" x="${x}" y="0" width="${w}" height="${H}" fill="transparent"><title>${u}</title></rect>`);
  });
  o.push(`<line x1="${x1}" x2="${x1}" y1="${y - 14}" y2="${y + 14}"/>`);
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.innerHTML = o.join('');
  svg.setAttribute('aria-valuetext', S.period || 'none');
  svg.querySelectorAll('.hit').forEach(r => r.addEventListener('click', () => setPeriod(r.dataset.p)));
}
function setPeriod(p) { S.period = p; pickDate(); render(); }

// ------------------------------------------------------------------ settings
function wireSettings() {
  document.querySelectorAll('[data-sat]').forEach(b => b.addEventListener('click', () => {
    S.sat = b.dataset.sat; if (!S.period) defaultPeriod(); pickDate(); render(); }));
  document.querySelectorAll('[data-unit]').forEach(b => b.addEventListener('click', () => {
    const was = S.date || S.period;
    S.unit = b.dataset.unit; S.period = was ? periodOf(was.length >= 7 ? was : `${was}-12`) : null; pickDate(); render(); }));
  const svg = $('#tl-svg');
  svg.addEventListener('keydown', (e) => {   // arrow keys move one period
    if (!['ArrowLeft', 'ArrowRight'].includes(e.key)) return;
    const hits = [...svg.querySelectorAll('.hit')].map(r => r.dataset.p); const i = hits.indexOf(S.period);
    const j = Math.max(0, Math.min(hits.length - 1, (i < 0 ? hits.length - 1 : i) + (e.key === 'ArrowRight' ? 1 : -1)));
    setPeriod(hits[j]); e.preventDefault();
  });
}
function defaultPeriod() { const src = source(S.sat); S.period = src?.dates.length ? periodOf(src.dates[src.dates.length - 1]) : null; }
function render() {
  document.querySelectorAll('[data-sat]').forEach(b => b.setAttribute('aria-checked', String(b.dataset.sat === S.sat)));
  document.querySelectorAll('[data-unit]').forEach(b => b.setAttribute('aria-checked', String(b.dataset.unit === S.unit)));
  renderTimeline();
  drawPoints().then(() => { if (!$('#menu').hidden) renderMenu(); });
}

async function main() {
  [S.man, S.sens] = await Promise.all([get('manifest.json'), get('sensitivity.json').catch(() => null)]);
  // count the measured points of the longest Sentinel-1 series, to choose between equally long tracks
  const ws = Object.values(S.sens?.windows || {});
  const n = Math.max(0, ...ws.flatMap(w => Object.values(w.frames || {}).map(f => f.dates.length)));
  const files = ws.flatMap(w => Object.entries(w.frames || {}).filter(([, f]) => f.dates.length === n).map(([t]) => w.points[t]));
  S.s1Points = Object.fromEntries(await Promise.all(files.map(async f => [f, (await loadPoints(f)).gj.features.length])));
  if (!source('s1')) S.sat = 'nisar';
  defaultPeriod(); pickDate();
  makeMap(); wireSettings(); render();
  window.addEventListener('resize', renderTimeline);
  if (new URLSearchParams(location.search).has('debug')) window.dos = { S, map: () => map };   // tests only
}
main();

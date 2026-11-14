// Owner: 06 · App developer (Darius)
// English / Romanian interface (15 Nov 2026). The page renders in English; this layer relabels the interface text in
// place when Romanian is chosen, so no rendering code changes and no number is touched. Explanations written by the
// pipeline and the validator (check details, zone notes, method notes) stay in English until the products carry both.

const WORDS = {   // whole labels (a text node that is exactly this, ignoring spaces)
  'Motion': 'Mișcare', 'Coverage': 'Acoperire', 'Compare': 'Comparare', 'Change': 'Schimbare', 'Rate': 'Rată', 'Zones': 'Zone',
  'Investigate Zone 4': 'Investighează Zona 4', 'Zone 4': 'Zona 4', 'Copy view link': 'Copiază linkul', 'Link': 'Link',
  'Link copied': 'Link copiat', 'Reset to site': 'Revino la sit', 'Reset': 'Revino', 'Map': 'Hartă', 'Light': 'Deschisă',
  'Satellite': 'Satelit', 'Colour overlay': 'Strat de culoare', 'Usable measurements': 'Măsurători utilizabile',
  'Line-of-sight change': 'Deplasare pe linia de vizare', 'Annualized line-of-sight rate': 'Rată anualizată pe linia de vizare',
  'away from satellite': 'departe de satelit', 'toward satellite': 'spre satelit', 'Ocnele Mari town boundary': 'Limita orașului Ocnele Mari',
  'near 0 (pale dot)': 'aproape 0 (punct pal)', 'no dot = no data': 'fără punct = fără date', 'since': 'față de',
  'Change over time, mm': 'Schimbare în timp, mm', 'Compare processing runs': 'Compară procesările',
  'Fitted direction changes with processing': 'Direcția ajustată se schimbă în funcție de procesare', 'Overlay with': 'Suprapune cu',
  'Open table': 'Deschide tabelul', 'Export CSV': 'Exportă CSV', 'Every processing run': 'Toate procesările',
  'Explore processing choices': 'Explorează opțiunile de procesare', 'When each satellite looked': 'Când a privit fiecare satelit',
  'Usable pixels in each zone': 'Pixeli utilizabili în fiecare zonă', 'Historical context': 'Context istoric',
  'Still inconclusive': 'Încă neconcludent', 'Parallel observations, mm': 'Observații paralele, mm',
  'Do the two radars agree?': 'Concordă cele două radare?', 'Sentinel-1 covers this →': 'Sentinel-1 acoperă perioada →',
  'Forecast date': 'Data prognozei', 'Inconclusive': 'Neconcludent', 'Agree': 'Concordă', 'Disagree': 'Nu concordă',
  'Not tested yet': 'Netestat încă', 'Not testable': 'Netestabil', 'Run': 'Procesare', 'Fitted change': 'Schimbare ajustată',
  'Acquisitions': 'Achiziții', 'Usable pixels': 'Pixeli utilizabili', 'Window': 'Fereastră', 'Reference': 'Referință', 'Track': 'Orbită',
  'Date': 'Data', 'Satellite and station agree': 'Satelitul și stația concordă', 'Satellite and station disagree': 'Satelitul și stația nu concordă',
  'Not tested': 'Netestat', 'What this map can and cannot tell you': 'Ce poate și ce nu poate spune această hartă',
  'The two radars': 'Cele două radare', 'Methods': 'Metode', 'Credits': 'Surse', 'Single run': 'O singură procesare',
  'Baseline (coherence ≥ 0.35)': 'De bază (coerență ≥ 0,35)', 'Stricter coherence (≥ 0.55)': 'Coerență mai strictă (≥ 0,55)',
  'West reference area only': 'Doar zona de referință vest', 'East reference area only': 'Doar zona de referință est',
  'Elevation correction (fitted to the data)': 'Corecție de altitudine (ajustată pe date)',
  'Weather-model troposphere (ECMWF IFS, acquisition time)': 'Troposferă din model meteo (ECMWF IFS, la achiziție)',
  'Radar estimate (Sentinel-1 029A)': 'Estimare radar (Sentinel-1 029A)', 'Chronos-2 forecast (median)': 'Prognoză Chronos-2 (mediană)',
  'Experimental forecast': 'Prognoză experimentală', 'Retrospective forecast': 'Prognoză retrospectivă',
  'Check against NISAR': 'Verificare cu NISAR', 'Ascending': 'Ascendent', 'Descending': 'Descendent', 'operational': 'operațional',
  'beta/provisional': 'beta/provizoriu', 'under review': 'în analiză',
};
const PHRASES = [   // longer phrases inside mixed text, applied longest first
  ['Negative means motion away from the satellite along its line of sight.', 'Valorile negative înseamnă îndepărtare de satelit, pe linia de vizare.'],
  ['Line-of-sight change (mm) at', 'Deplasare pe linia de vizare (mm) la'],
  ['Annualized line-of-sight rate (mm/yr)', 'Rată anualizată pe linia de vizare (mm/an)'],
  ['Usable measurements (a connected series)', 'Măsurători utilizabile (serie continuă)'],
  ['relative to surrounding terrain, a 3 to 6.5 km band', 'relativ la terenul înconjurător, bandă de 3–6,5 km'],
  ['tied to the EuVeM2022 velocity model', 'legat de modelul de viteze EuVeM2022'],
  ['each satellite in its own line of sight', 'fiecare satelit pe propria linie de vizare'],
  ['common window', 'fereastră comună'], ['fit window', 'fereastra de ajustare'], ['No acquisition on', 'Nicio achiziție la'],
  ['Run: ', 'Procesare: '], ['Reference: ', 'Referință: '], ['change since', 'schimbare față de'],
  ['positive = toward the satellite', 'pozitiv = spre satelit'], ['mm since first date', 'mm de la prima dată'],
  ['mm since the first date of its acquisition group', 'mm de la prima dată a grupului de achiziții'],
  ['click a point to show that date on the map', 'apasă un punct pentru a vedea data pe hartă'],
  ['pixels', 'pixeli'], [' dates', ' date'], [' pairs', ' perechi'], ['only ', 'doar '], ['(validator)', '(validator)'],
  [': coverage', ': acoperire'], [': compare', ': comparare'], ['January to October 2026', 'ianuarie–octombrie 2026'],
  ['July to October 2026', 'iulie–octombrie 2026'], ['Salt zone', 'Zonă de sare'], ['GNSS station', 'Stație GNSS'],
  ['against GNSS', 'față de GNSS'], ['against Sentinel-1', 'față de Sentinel-1'], ['against NISAR', 'față de NISAR'],
];
for (const k of ['Baseline (coherence ≥ 0.35)', 'Stricter coherence (≥ 0.55)', 'West reference area only', 'East reference area only',
  'Elevation correction (fitted to the data)', 'Weather-model troposphere (ECMWF IFS, acquisition time)', 'Single run']) PHRASES.push([k, WORDS[k]]);
const RX = [[/(\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})/g, '$1 – $2']];
PHRASES.sort((a, b) => b[0].length - a[0].length);

let lang = 'en', busy = false;
const orig = new WeakMap();
function translateNode(n) {
  if (!orig.has(n)) orig.set(n, n.nodeValue);
  const en = orig.get(n);
  if (lang === 'en') { if (n.nodeValue !== en) n.nodeValue = en; return; }
  const key = en.trim();
  let ro = WORDS[key] !== undefined ? en.replace(key, WORDS[key]) : en;
  if (ro === en) { for (const [a, b] of PHRASES) if (ro.includes(a)) ro = ro.split(a).join(b); for (const [r, s] of RX) ro = ro.replace(r, s); }
  if (n.nodeValue !== ro) n.nodeValue = ro;
}
export function translate(root = document.body) {
  if (busy) return;
  busy = true;
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode: (n) => (n.parentElement?.closest('.maplibregl-canvas-container, script, style, .maplibregl-ctrl-attrib') || !n.nodeValue.trim())
      ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT });
  for (let n = w.nextNode(); n; n = w.nextNode()) translateNode(n);
  document.documentElement.lang = lang;
  document.querySelectorAll('[data-lang]').forEach(b => b.setAttribute('aria-pressed', b.dataset.lang === lang ? 'true' : 'false'));
  busy = false;
}
export function setLang(l) {
  lang = l === 'ro' ? 'ro' : 'en';
  try { localStorage.setItem('dos-lang', lang); } catch (e) { /* private mode: the link still carries it */ }
  translate();
}
export const getLang = () => lang;
export function initLang(fromHash) {
  let saved = null;
  try { saved = localStorage.getItem('dos-lang'); } catch (e) { /* ignore */ }
  lang = fromHash || saved || ((navigator.language || '').toLowerCase().startsWith('ro') ? 'ro' : 'en');
  let pending = false;
  new MutationObserver(() => {
    if (busy || pending) return;
    pending = true; requestAnimationFrame(() => { pending = false; translate(); });
  }).observe(document.body, { childList: true, subtree: true, characterData: true });
  translate();
}

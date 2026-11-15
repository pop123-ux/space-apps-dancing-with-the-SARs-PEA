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
PHRASES.push(['How the two radars differ, and how they fill each other\'s gaps', 'Cum diferă cele două radare și cum se completează'],
  ['What already agrees', 'Ce concordă deja'], ['What would settle it', 'Ce ar lămuri rezultatul'], ['Same direction:', 'Aceeași direcție:'],
  ['Opposite directions:', 'Direcții opuse:'], ['More dates:', 'Mai multe date:'], ['Larger comparison areas:', 'Zone de comparație mai mari:'],
  ['One stated assumption:', 'O ipoteză declarată:'], ['Sentinel-1 fills NISAR\'s gap:', 'Sentinel-1 acoperă golul NISAR:'],
  ['NISAR adds earlier dates:', 'NISAR adaugă date mai vechi:'], ['Opposite look sides:', 'Priviri din părți opuse:'],
  ['Different wavelengths:', 'Lungimi de undă diferite:'], ['Wavelength', 'Lungime de undă'], ['Looks', 'Privește'],
  ['Track shown here', 'Orbita afișată'], ['Acquisitions', 'Achiziții'], ['Period', 'Perioadă'], ['Grid', 'Grilă'],
  ['Pixel noise on stable ground', 'Zgomot pe teren stabil']);
PHRASES.sort((a, b) => b[0].length - a[0].length);
const RX = [[/(\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})/g, '$1 – $2']];
// strings from the 15 Nov text pass (folded explanations, Agreement on the geometry pair, forecast shortcut)
Object.assign(WORDS, {
  'What the check found': 'Ce a găsit verificarea', 'How good is this forecast?': 'Cât de bună este prognoza?',
  'Which run changes it?': 'Ce procesare o schimbă?', 'About this table': 'Despre acest tabel', 'Source and method': 'Sursă și metodă',
  'Loading measurements…': 'Se încarcă măsurătorile…', 'Methods': 'Metode', 'Stable ground nearby': 'Teren stabil din apropiere',
  'One satellite has no series here': 'Un satelit nu are serie aici', 'Sentinel-1 history': 'Istoric Sentinel-1',
  'No automatic check for this zone yet': 'Încă nicio verificare automată pentru această zonă',
});
PHRASES.push(
  ['See the forecast to', 'Vezi prognoza până la'], ['Typical past error: ', 'Eroare tipică în trecut: '],
  [' at 30 days', ' la 30 de zile'], [' at 88 days', ' la 88 de zile'], ['Before 2026: ', 'Înainte de 2026: '],
  ['NISAR next to Sentinel-1 over the months both cover', 'NISAR alături de Sentinel-1 în lunile acoperite de amândoi'],
  ['. The verdicts come from the automatic checks.', '. Verdictele vin din verificările automate.'],
  ['Each line is the zone minus the terrain 6.5 to 8 km away.', 'Fiecare linie este zona minus terenul aflat la 6,5–8 km.'],
  [' is paired with ', ' este asociat cu '], ['because both see east-west motion the same way.', 'deoarece amândoi văd la fel mișcarea est-vest.'],
  ['A wide tolerance means agreeing proves little yet.', 'O toleranță largă înseamnă că acordul încă dovedește puțin.'],
  ["Change in each salt zone along the radar's line of sight", 'Schimbarea în fiecare zonă de sare pe linia de vizare a radarului'],
  ['Negative = away from the satellite, which is what sinking looks like. Relative to nearby terrain.',
   'Negativ = departe de satelit, adică așa arată tasarea. Relativ la terenul din jur.'],
  ['A pretrained time-series model (Chronos-2) extends this radar series to',
   'Un model preantrenat de serii temporale (Chronos-2) prelungește această serie radar până la'],
  ['It sees only the series: nothing about salt, weather or the mine.', 'Vede doar seria: nimic despre sare, vreme sau mină.'],
  ['Median rates in mm/yr, December 2020 to November 2025. Positive = up or east.',
   'Rate mediane în mm/an, decembrie 2020 – noiembrie 2025. Pozitiv = în sus sau spre est.'],
  ["Ground motion measured by two radar satellites, along each one's line of sight and relative to nearby terrain.",
   'Mișcarea terenului măsurată de doi sateliți radar, pe linia de vizare a fiecăruia și relativ la terenul din jur.'],
  ['It is not a hazard forecast, an evacuation guide or a building safety assessment.',
   'Nu este o prognoză de hazard, un ghid de evacuare sau o evaluare a siguranței clădirilor.'],
  ['For official notices, follow ISU Vâlcea and the Ocnele Mari town hall.', 'Pentru anunțuri oficiale, urmăriți ISU Vâlcea și Primăria Ocnele Mari.'],
  ['has almost no data over the town in', 'nu are aproape deloc date deasupra orașului în'],
  ['a dot needs a connected series through every date, and C-band loses coherence in winter.',
   'un punct are nevoie de o serie continuă la toate datele, iar banda C pierde coerența iarna.'],
  ['1 dot = ', '1 punct = '], ['Map shows the baseline run', 'Harta arată procesarea de bază'],
);
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

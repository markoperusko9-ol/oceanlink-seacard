// Loads every tool page in headless Chrome and checks what the page shows against the tested maths.
// Run: NODE_PATH=<dir with puppeteer-core>/node_modules node scripts/tools/tests/pages.browser.js [screenshot dir]
const http = require('http'), fs = require('fs'), path = require('path');
const puppeteer = require('puppeteer-core');
const ROOT = path.join(__dirname, '../../..');
const C = require(path.join(ROOT, 'tools/assets/calc.js'));
const SHOTS = process.argv[2];
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.xml': 'text/xml', '.jpg': 'image/jpeg' };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]); if (p.endsWith('/')) p += 'index.html';
  const f = path.join(ROOT, p);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end('not found'); }
  res.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(res);
});
let fails = 0, checks = 0;
const ok = (cond, msg) => { checks++; if (!cond) { fails++; console.log('   FAIL: ' + msg); } };
const eq = (got, want, msg) => ok(got === want, `${msg}: got "${got}", want "${want}"`);
const brg = (x, dp = 1) => { let r = parseFloat(C.norm360(x).toFixed(dp)); if (r >= 360) r = 0; const s = r.toFixed(dp); return ('000' + s.split('.')[0]).slice(-3) + (dp ? '.' + s.split('.')[1] : '') + '°'; };

(async () => {
  await new Promise(r => server.listen(0, r));
  const base = 'http://localhost:' + server.address().port;
  const browser = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', args: ['--no-sandbox', '--disable-gpu'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2 });
  let errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error' && !/fonts\.g|ERR_|Failed to load resource/.test(m.text())) errors.push('console: ' + m.text()); });
  page.on('response', r => { if (r.url().startsWith(base) && r.status() >= 400) errors.push('HTTP ' + r.status() + ' ' + r.url()); });
  const set = (id, v) => page.evaluate((id, v) => { const el = document.getElementById(id); el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); }, id, v);
  const seg = (id, v) => page.evaluate((id, v) => document.querySelector('#' + id + ' button[data-v="' + v + '"]').click(), id, v);
  const txt = (sel) => page.evaluate(sel => { const el = document.querySelector(sel); return el ? el.textContent.replace(/\s+/g, ' ').trim() : null; }, sel);
  const res = () => txt('#res');
  async function open(slug, embed) {
    errors = [];
    await page.goto(base + '/tools/' + (slug ? slug + '/' : '') + (embed ? '?embed=1' : ''), { waitUntil: 'load' });
    console.log((slug || 'hub') + (embed ? ' (in-app mode)' : ''));
  }
  async function done(slug) {
    ok(errors.length === 0, 'script or loading errors: ' + errors.join(' | '));
    const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    ok(over <= 0, 'page is wider than a 390 px phone by ' + over + ' px');
    await page.setViewport({ width: 320, height: 700, deviceScaleFactor: 1 });
    const over2 = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    ok(over2 <= 0, 'page is wider than a 320 px phone by ' + over2 + ' px');
    await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2 });
    if (SHOTS) await page.screenshot({ path: path.join(SHOTS, (slug || 'hub') + '.png'), fullPage: true });
  }

  // ---- hub ----
  await open('');
  eq(await page.evaluate(() => document.querySelectorAll('a.tool').length), 12, 'tool cards on the hub');
  const links = await page.evaluate(() => [...document.querySelectorAll('a.tool')].map(a => a.getAttribute('href')));
  for (const l of links) ok(fs.existsSync(path.join(ROOT, l, 'index.html')), 'hub link target missing ' + l);
  await done('');
  await open('', true);
  ok(await page.evaluate(() => getComputedStyle(document.querySelector('.bar')).display === 'none'), 'header hidden in the app');
  ok(await page.evaluate(() => [...document.querySelectorAll('a.tool')].every(a => a.getAttribute('href').endsWith('?embed=1'))), 'tool links keep in-app mode');

  // ---- Sun compass error ----
  await open('sun-compass-error-calculator');
  const sunCase = async (date, h, m, s, latd, latm, lath, lond, lonm, lonh) => {
    await set('date', date); await set('hh', h); await set('mm', m); await set('ss', s);
    await set('latd', latd); await set('latm', latm); await set('lath', lath); await set('lond', lond); await set('lonm', lonm); await set('lonh', lonh);
    const p = date.split('-').map(Number), ms = Date.UTC(p[0], p[1] - 1, p[2], +h, +m, +s);
    const lat = (+latd + +latm / 60) * (lath === 'S' ? -1 : 1), lon = (+lond + +lonm / 60) * (lonh === 'W' ? -1 : 1);
    return C.sunPosition(ms, lat, lon);
  };
  let s = await sunCase('2027-05-01', '15', '30', '20', '20', '00.0', 'N', '060', '00.0', 'W');
  let az = parseFloat(s.az.toFixed(1));
  eq(await txt('#r_az'), brg(az) + 'T', 'Sun azimuth (N lat, W long)');
  ok((await res()).includes('Altitude ' + s.alt.toFixed(1) + '°'), 'altitude shown');
  await set('cb', (az + 1).toFixed(1));
  eq(await txt('#r_err'), '1.0° W gyro high', 'gyro error naming');
  await set('cb', (az - 0.7).toFixed(1));
  eq(await txt('#r_err'), '0.7° E gyro low', 'gyro error naming');
  await seg('cmode', 'mag'); await set('cb', (az + 4).toFixed(1)); await set('var', '2'); await set('varh', 'E');
  eq(await txt('#r_err'), '4.0° W', 'compass error'); eq(await txt('#r_dev'), '6.0° W for the present heading', 'deviation (guide example 1)');
  await set('varh', 'W'); eq(await txt('#r_dev'), '2.0° W for the present heading', 'deviation with westerly variation');
  s = await sunCase('2026-12-21', '21', '05', '00', '33', '51.5', 'S', '151', '12.6', 'E');
  eq(await txt('#r_az'), brg(parseFloat(s.az.toFixed(1))) + 'T', 'Sun azimuth (S lat, E long)');
  const amp = C.amplitude(-(33 + 51.5 / 60), s.dec);
  ok((await res()).includes('E ' + Math.abs(amp.amp).toFixed(1) + '° S (' + brg(amp.rise) + 'T)'), 'amplitude at sunrise shown: ' + (await res()));
  await set('hh', '12'); ok((await res()).includes('below the horizon'), 'night-time warning');
  await set('latm', '75'); ok((await res()).includes('Enter the date'), 'minutes of 60 or more rejected');
  await set('latm', '51.5'); await set('hh', '02');
  ok(await page.evaluate(() => document.querySelector('#dia svg') !== null), 'diagram drawn');
  await done('sun-compass-error-calculator');

  // ---- Great circle ----
  await open('great-circle-rhumb-line-calculator');
  eq(await txt('#r_gc'), '4,489.4 nm', 'WGS84 great circle'); eq(await txt('#r_rh'), '4,723.4 nm', 'rhumb line');
  let t = await res();
  for (const w of ['Initial course 055.3°T', 'Final course 122.5°T', 'Course 088.5°T', '234.0 nm', "47°39.8'N 169°38.4'W", '4,476.3 nm', '147.7']) ok(t.includes(w), 'great circle result should show ' + w + ' :: ' + t);
  ok(await page.evaluate(() => document.querySelector('#dia polyline') !== null), 'track plot drawn');
  await set('alat' + 'd', '10'); await set('alond', '020'); await set('alonh', 'E'); await set('blatd', '60'); await set('blond', '020'); await set('blonh', 'E');
  t = await res(); ok(t.includes('Initial course 000.0°T') && t.includes('At the pole'), 'meridian sailing :: ' + t);
  await set('alatd', '33'); await set('alatm', '54'); await set('alath', 'S'); await set('alond', '018'); await set('alonm', '24'); await set('blatd', '34'); await set('blatm', '36'); await set('blath', 'S'); await set('blond', '058'); await set('blonm', '24'); await set('blonh', 'W');
  const gS = C.gcSphere(-33.9, 18.4, -34.6, -58.4);
  ok((await res()).includes(gS.distNm.toFixed(1).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + ' nm'), 'southern hemisphere, west-going: sphere distance shown');
  await done('great-circle-rhumb-line-calculator');

  // ---- Set and drift ----
  await open('set-and-drift-course-to-steer-calculator');
  eq(await txt('#r_main'), '101.5°T', 'course to steer (guide example)'); eq(await txt('#r_smg'), '9.8 kn', 'speed made good');
  ok((await res()).includes('Allow 11.5° to starboard'), 'allowance side');
  await set('cset', '180'); eq(await txt('#r_main'), '078.5°T', 'stream from the other side'); ok((await res()).includes('to port'), 'allowance to port');
  await set('crate', '12'); ok((await res()).includes('too strong'), 'stream too strong message');
  await seg('mode', 'sd');
  const sd = C.setDrift(45, 10, 2, 53.5, 20.2);
  eq(await txt('#r_main'), brg(sd.set, 0) + 'T', 'set'); eq(await txt('#r_rate'), sd.rate.toFixed(1) + ' kn', 'rate');
  ok(Math.abs(sd.set - 135) < 2 && Math.abs(sd.rate - 1.5) < 0.05, 'set and drift near the guide example (135°, 1.5 kn)');
  await seg('mode', 'cmg'); eq(await txt('#r_main'), '090.0°T', 'course made good'); eq(await txt('#r_smg'), '9.8 kn', 'speed made good');
  ok(await page.evaluate(() => document.querySelector('#dia svg') !== null), 'triangle drawn');
  await done('set-and-drift-course-to-steer-calculator');

  // ---- ETA ----
  await open('eta-speed-distance-time-calculator');
  await set('ddate', '2026-11-23'); await set('dtime', '08:00'); await set('dzone', '1'); await set('azone', '8');
  eq(await txt('#r_main'), 'Fri 27 Nov 2026, 19:00', 'ETA in ship\'s time'); eq(await txt('#r_utc'), 'Fri 27 Nov 2026, 11:00', 'ETA in UTC'); eq(await txt('#r_time'), '4 d 04 h 00 min', 'steaming time');
  await set('ddate', '2026-01-01'); await set('dtime', '22:00'); await set('dzone', '12'); await set('azone', '-11'); await set('dist', '240'); await set('speed', '10');
  eq(await txt('#r_main'), 'Thu 1 Jan 2026, 23:00', 'ETA across the date line');
  await seg('mode', 'spd'); await set('ddate', '2026-11-23'); await set('dtime', '08:00'); await set('dzone', '1'); await set('azone', '8'); await set('dist', '1200'); await set('adate', '2026-11-27'); await set('atime', '19:00');
  eq(await txt('#r_main'), '12.0 kn', 'required speed');
  await set('adate', '2026-11-20'); ok((await res()).includes('not after'), 'arrival before departure message');
  await seg('mode', 'sdt'); eq(await txt('#r_main'), '8 h 20 min', 'time from distance and speed');
  await set('s2', ''); await set('th', '8'); await set('tm', '20'); eq(await txt('#r_main'), '12.0 kn', 'speed from distance and time');
  await set('d2', ''); await set('s2', '15'); eq(await txt('#r_main'), '125.0 nm', 'distance from speed and time');
  await done('eta-speed-distance-time-calculator');

  // ---- True wind ----
  await open('true-wind-calculator');
  eq(await txt('#r_main'), '135°T', 'true wind direction'); eq(await txt('#r_spd'), '14.1 kn', 'true wind speed'); eq(await txt('#r_bf'), 'Force 4, Moderate breeze', 'Beaufort');
  await seg('side', 'port'); eq(await txt('#r_main'), '225°T', 'wind on the port side');
  await seg('unit', 'ms'); const w = C.trueWind(0, 10, 270, 10 / 0.514444444);
  eq(await txt('#r_main'), brg(w.dir, 0) + 'T', 'm/s input direction'); eq(await txt('#r_spd'), w.speed.toFixed(1) + ' kn', 'm/s input speed');
  await seg('unit', 'kn'); await set('rel', '0'); eq(await txt('#r_main'), 'Calm', 'calm when relative wind equals ship speed from ahead');
  await set('hdg', '350'); await set('spd', '15'); await set('rel', '30'); await seg('side', 'stbd'); await set('ws', '25');
  const w2 = C.trueWind(350, 15, 30, 25); eq(await txt('#r_main'), brg(w2.dir, 0) + 'T', 'heading near north');
  await done('true-wind-calculator');

  // ---- CPA ----
  await open('cpa-tcpa-calculator');
  const c = C.cpa(0, 12, 37, 10, 45, 5.7, 12);
  eq(await txt('#r_cpa'), c.cpa.toFixed(2) + ' nm', 'CPA'); eq(await txt('#r_tcpa'), c.tcpaMin.toFixed(0) + ' min', 'TCPA');
  eq(await txt('#r_at'), '12:27', 'time of CPA (guide: about 1227)'); eq(await txt('#r_tco'), '232°T', 'target course (guide: about 232°)'); eq(await txt('#r_tsp'), '12.6 kn', 'target speed (guide: about 12.6 kn)');
  ok(Math.abs(c.cpa - 1.8) < 0.06, 'CPA near the guide figure of 1.8 nm');
  await set('t1', '23:54'); await set('t2', '00:06'); eq(await txt('#r_at'), '00:21', 'plots across midnight');
  await set('b1', '000'); await set('r1', '10'); await set('b2', '000'); await set('r2', '8'); ok((await res()).includes('CPA is zero'), 'collision course message');
  await set('r2', '11'); ok((await res()).includes('range is now opening'), 'opening range message');
  ok(await page.evaluate(() => document.querySelector('#dia svg') !== null), 'plot drawn');
  await done('cpa-tcpa-calculator');

  // ---- Squat ----
  await open('squat-ukc-calculator');
  eq(await txt('#r_squat'), '1.02 m', 'squat (guide example)'); eq(await txt('#r_ukc'), '0.60 m', 'net UKC (guide example)'); eq(await txt('#r_static'), '3.30 m', 'static UKC');
  await set('v', '6'); await set('tide', '2.60'); eq(await txt('#r_ukc'), '1.54 m', 'net UKC, revised plan (guide)');
  await seg('water', 'open'); eq(await txt('#r_squat'), '0.29 m', 'open water squat');
  await set('tide', '-0.3'); ok((await txt('#r_static')) === '0.90 m', 'negative tide');
  await set('v', '16'); await seg('water', 'conf'); ok((await res()).includes('touches bottom'), 'no clearance message');
  ok(await page.evaluate(() => document.querySelector('#dia polyline') !== null), 'chart drawn');
  await done('squat-ukc-calculator');

  // ---- Slip ----
  await open('propeller-slip-calculator');
  eq(await txt('#r_main'), '5.23 %', 'slip'); eq(await txt('#r_ed'), '443.2 nm', 'engine distance');
  await set('od', '450'); ok((await res()).includes('Negative slip'), 'negative slip note');
  await seg('mode', 'now'); eq(await txt('#r_main'), '5.23 %', 'slip from speed'); eq(await txt('#r_ed'), '18.47 kn', 'engine speed');
  await done('propeller-slip-calculator');

  // ---- Fuel ----
  await open('fuel-consumption-calculator');
  eq(await txt('#r_daily'), '30.0 t/day', 'daily consumption'); eq(await txt('#r_days'), '20.0 days', 'days left'); eq(await txt('#r_range'), '6,720 nm', 'range');
  eq(await txt('#r_voy'), '267.9 t', 'voyage fuel'); eq(await txt('#r_arr'), '332.1 t', 'ROB on arrival');
  await set('newspeed', '12'); eq(await txt('#r_cube'), '18.9 t/day', 'cube law');
  await set('cons', '14.5'); await set('hours', '12'); eq(await txt('#r_daily'), '29.0 t/day', 'part-day consumption');
  await set('dist', '20000'); ok((await res()).includes('Not enough fuel'), 'shortfall message');
  await done('fuel-consumption-calculator');

  // ---- FWA / DWA ----
  await open('fwa-dwa-calculator');
  eq(await txt('#r_dwa'), '113 mm', 'DWA'); eq(await txt('#r_fwa'), '187.5 mm', 'FWA'); ok(/^9\.71[23] m$/.test(await txt('#r_dr')), 'draught in dock water');
  await set('dens', '1010'); eq(await txt('#r_dwa'), '113 mm', 'density typed as 1010');
  await seg('mode', 'known'); eq(await txt('#r_dwa'), '113 mm', 'DWA from a known FWA of 188 (guide: 112.8)'); ok((await res()).includes('112.8 mm'), 'unrounded DWA');
  await set('dens', '1.000'); eq(await txt('#r_dwa'), '188 mm', 'fresh water'); await set('dens', '1.025'); eq(await txt('#r_dwa'), '0 mm', 'sea water');
  await set('dens', '1.030'); eq(await txt('#r_dwa'), 'None', 'denser than sea water');
  await done('fwa-dwa-calculator');

  // ---- List and GM ----
  await open('list-and-gm-calculator');
  eq(await txt('#r_gm'), '0.78 m', 'fluid GM (guide)'); eq(await txt('#r_list'), '2.7° to starboard', 'list (guide)'); eq(await txt('#r_solid'), '1.207 m', 'solid GM'); eq(await txt('#r_fsc'), '0.427 m', 'free surface correction');
  await seg('side', 'port'); eq(await txt('#r_list'), '2.7° to port', 'list to port');
  await set('disp', '10000'); await set('km', '8.80'); await set('kg', '8.00'); await set('fsm', ''); await set('w', '50'); await set('d', '8'); eq(await txt('#r_list'), '2.9° to port', 'list (loll guide example 2.86°)');
  await set('kg', '8.90'); ok((await res()).includes('angle of loll'), 'negative GM message'); ok((await txt('#r_list')) === null, 'no list given with negative GM');
  await set('kg', '8.00');
  await done('list-and-gm-calculator');

  // ---- Units ----
  await open('marine-unit-converter');
  eq(await txt('[data-u="m/s"]'), '5.14444', '10 kn in m/s'); eq(await txt('[data-u="km/h"]'), '18.52', '10 kn in km/h'); eq(await txt('[data-u="bf"]'), 'Force 3, Gentle breeze', 'Beaufort for 10 kn');
  await set('group', 'pressure'); await set('value', '1'); await set('unit', 'bar'); eq(await txt('[data-u="psi"]'), '14.5038', '1 bar in psi');
  await set('group', 'temp'); await set('value', '100'); await set('unit', 'C'); eq(await txt('[data-u="F"]'), '212.00', '100 °C in °F');
  await set('value', '-40'); eq(await txt('[data-u="F"]'), '-40.00', '-40 °C in °F');
  await set('group', 'volume'); await set('value', '1'); await set('unit', 'm³'); eq(await txt('[data-u="US barrel"]'), '6.28981', '1 m³ in barrels');
  await set('group', 'depth'); await set('value', '1'); await set('unit', 'shackle (27.5 m)'); eq(await txt('[data-u="fathom"]'), '15.0372', 'shackle in fathoms');
  await set('group', 'vm'); eq(await txt('#r_main'), '450 t', 'volume to mass'); await seg('dir', 'm2v'); await set('q', '450'); eq(await txt('#r_main'), '1,000 m³', 'mass to volume');
  await set('group', 'speed'); await set('value', '10'); await set('unit', 'm/s');
  await done('marine-unit-converter');

  await browser.close(); server.close();
  console.log(`\n${checks - fails} of ${checks} page checks passed`);
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });

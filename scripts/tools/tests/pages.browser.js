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
  if (p === '/__app') { res.writeHead(200, { 'content-type': 'text/html' }); return res.end(HARNESS); }
  const f = path.join(ROOT, p);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end('not found'); }
  res.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(res);
});
// Stand-in for the Ocean Link app page that frames the tools (same script as the Bubble HTML element).
const HARNESS = `<!DOCTYPE html><body style="margin:0;background:#050609"><div style="height:300px"></div>
<iframe id="oltools" src="/tools/?embed=1" title="Seafarer tools" style="width:100%;height:1800px;border:0;display:block"></iframe>
<script>(function(){var f=document.getElementById('oltools');window.addEventListener('message',function(e){if(e.origin!==location.origin||!e.data||e.data.olTools!==1)return;if(e.data.height)f.style.height=e.data.height+'px';if(e.data.nav){var t=f.getBoundingClientRect().top;if(t<0)window.scrollTo(0,window.scrollY+t-80);}});})();</script></body>`;
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
  page.on('response', r => { if (r.url().startsWith(base) && r.status() >= 400 && !r.url().endsWith('/favicon.ico')) errors.push('HTTP ' + r.status() + ' ' + r.url()); });
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
  eq(await page.evaluate(() => document.querySelectorAll('a.tool').length), 20, 'tool cards on the hub');
  const links = await page.evaluate(() => [...document.querySelectorAll('a.tool')].map(a => a.getAttribute('href')));
  for (const l of links) ok(fs.existsSync(path.join(ROOT, l, 'index.html')), 'hub link target missing ' + l);
  await done('');
  await open('', true);
  ok(await page.evaluate(() => getComputedStyle(document.querySelector('.bar')).display === 'none'), 'header hidden in the app');
  ok(await page.evaluate(() => document.querySelector('a.back') === null), 'no back link on the list itself');
  ok(await page.evaluate(() => [...document.querySelectorAll('a.tool')].every(a => a.getAttribute('href').endsWith('?embed=1'))), 'tool links keep in-app mode');

  // ---- framed inside the app ----
  errors = []; await page.goto(base + '/__app', { waitUntil: 'load' }); console.log('framed inside an app page');
  await new Promise(r => setTimeout(r, 400));
  const frame = () => page.frames().find(f => f.url().includes('/tools/'));
  const hubH = await page.evaluate(() => parseInt(document.getElementById('oltools').style.height));
  const hubReal = await frame().evaluate(() => Math.ceil(document.documentElement.getBoundingClientRect().height));
  ok(hubH === hubReal + 1 && hubH > 800, 'frame takes the hub height: ' + hubH + ' vs ' + hubReal);
  const spill = () => frame().evaluate(() => Math.max(0, document.documentElement.scrollHeight - document.documentElement.clientHeight));
  ok((await spill()) === 0, 'hub fits the frame with nothing left to scroll (spills ' + (await spill()) + ' px)');
  ok(await frame().evaluate(() => getComputedStyle(document.querySelector('h1')).display === 'none'), 'hub heading hidden in the app');
  await page.evaluate(() => window.scrollTo(0, 900));
  await frame().evaluate(() => document.querySelector('a.tool[href*="true-wind"]').click());
  await new Promise(r => setTimeout(r, 900));
  ok(frame().url().includes('true-wind-calculator/?embed=1'), 'tool opens inside the frame: ' + frame().url());
  const toolH = await page.evaluate(() => parseInt(document.getElementById('oltools').style.height));
  const toolReal = await frame().evaluate(() => Math.ceil(document.documentElement.getBoundingClientRect().height));
  ok(toolH === toolReal + 1 && toolH !== hubH, 'frame resizes to the tool: ' + toolH + ' vs ' + toolReal);
  ok((await spill()) === 0, 'tool fits the frame with nothing left to scroll (spills ' + (await spill()) + ' px)');
  ok(await page.evaluate(() => Math.abs(document.getElementById('oltools').getBoundingClientRect().top - 80) < 3), 'app scrolls back to the top of the tool');
  eq(await frame().evaluate(() => document.getElementById('r_main').textContent), '135°T', 'tool works inside the frame');
  ok(await frame().evaluate(() => [...document.querySelectorAll('a[href^="/guides/"]')].every(a => a.target === '_blank')), 'guide links open outside the frame');
  ok(await frame().evaluate(() => { const b = document.querySelector('a.back'); const r = b.getBoundingClientRect(); return getComputedStyle(b).display !== 'none' && b.textContent === '‹ All tools' && r.height >= 44 && r.top < 60; }), 'a back link sits at the top of the tool, big enough to tap');
  await page.evaluate(() => window.scrollTo(0, 1200));
  await frame().evaluate(() => document.querySelector('a.back').click());
  await new Promise(r => setTimeout(r, 900));
  ok(/\/tools\/\?embed=1$/.test(frame().url()), 'back link returns to the list of tools: ' + frame().url());
  ok(await page.evaluate(() => parseInt(document.getElementById('oltools').style.height)) === hubH, 'frame goes back to the hub height');
  ok(await page.evaluate(() => Math.abs(document.getElementById('oltools').getBoundingClientRect().top - 80) < 3), 'app scrolls to the top of the list');
  ok(errors.length === 0, 'errors: ' + errors.join(' | '));

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
  await set('b1', '000'); await set('r1', '10'); await set('b2', '000'); await set('r2', '8'); ok((await res()).includes('CPA is 0.05 nm or less'), 'collision course message');
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

  // ================= second set of tools =================
  // ---- Bunker quantity ----
  await open('bunker-quantity-calculator');
  eq(await txt('#r_main'), '157.85 t', 'bunker weight in air (published survey example)'); eq(await txt('#r_vcf'), '0.9870', 'VCF'); eq(await txt('#r_gsv'), '159.578 m³', 'standard volume'); eq(await txt('#r_wcf'), '0.9892', 'weight factor');
  await set('dens', '990.3'); eq(await txt('#r_main'), '157.85 t', 'density typed as 990.3');
  await set('vol', '1000'); await set('temp', '40'); await set('dens', '840'); eq(await txt('#r_vcf'), '0.9788', 'diesel at 40 C (Measurement Canada table)'); ok((await res()).includes('Fuel oils'), 'fuel oil group');
  await set('dens', '0.800'); eq(await txt('#r_vcf'), '0.9766', 'jet fuel at 40 C (Measurement Canada table)'); ok((await res()).includes('Jet fuels'), 'jet group');
  await set('temp', '15'); eq(await txt('#r_vcf'), '1.0000', 'no correction at 15 C'); eq(await txt('#r_main'), '798.90 t', '1000 m3 at 15 C');
  await set('temp', '-5'); await set('dens', '840'); eq(await txt('#r_vcf'), '1.0168', 'cold oil');
  await set('temp', '160'); ok((await res()).includes('outside it'), 'temperature range warning');
  await set('dens', '0.5'); ok((await res()).includes('0.6530 to 1.0750'), 'density range message'); await set('dens', ''); ok((await res()).includes('Enter the volume'), 'empty field message');
  await set('vol', '161.68'); await set('temp', '34'); await set('dens', '0.9903');
  await done('bunker-quantity-calculator');

  // ---- Draft survey ----
  await open('draft-survey-calculator');
  eq(await txt('#r_mmm'), '5.0357 m', 'mean of means (UK P&I Club example)'); eq(await txt('#r_f'), '4.6135 m', 'forward at FP'); eq(await txt('#r_m'), '5.0069 m', 'midships'); eq(await txt('#r_a'), '5.6308 m', 'aft at AP');
  eq(await txt('#r_trim'), '1.0173 m by the stern', 'true trim'); eq(await txt('#r_ftc'), '−102.61 t', 'first trim correction'); eq(await txt('#r_stc'), '+3.03 t', 'second trim correction');
  eq(await txt('#r_dt'), '19,794.79 t', 'displacement corrected for trim'); eq(await txt('#r_true'), '19,669.26 t', 'true displacement'); eq(await txt('#r_disp'), '19,669.3 t', 'headline displacement');
  await set('ded', '11000'); eq(await txt('#r_net'), '8,669.26 t', 'less deductibles'); await set('ls', '8400'); eq(await txt('#r_ls'), '269.26 t', 'less light ship');
  await set('rho', '1018.5'); eq(await txt('#r_true'), '19,669.26 t', 'density typed as 1018.5');
  await set('disp', ''); ok((await res()).includes('Check the hydrostatic figures'), 'partial hydrostatics message'); eq(await txt('#r_mmm'), '5.0357 m', 'mean of means still shown');
  // the Ocean Link guide example
  for (const [id, v] of [['fp', '5.62'], ['fs', '5.58'], ['mp', '6.47'], ['ms', '6.43'], ['ap', '7.33'], ['as', '7.27'], ['lbp', '180'], ['xf', '2.50'], ['xa', '6.00'], ['xm', '0'], ['disp', '20861.4'], ['tpc', '28.40'], ['lcf', '2.10'], ['lcfd', 'aft'], ['mtcp', '236.5'], ['mtcm', '224.0'], ['rho', '1.018'], ['ded', '11965'], ['ls', '8520']]) await set(id, v);
  eq(await txt('#r_mmm'), '6.4543 m', 'guide: quarter mean 6.454'); eq(await txt('#r_trim'), '1.7843 m by the stern', 'guide: trim 1.784'); eq(await txt('#r_defl'), 'Hogged 1.7 cm', 'guide: hogged 17 mm');
  const gd = C.draftSurvey(5.62, 5.58, 6.47, 6.43, 7.33, 7.27, 180, 2.5, 0, 6), gr = C.draftSurveyDisp(gd.trim, 180, 20861.4, 28.40, 2.10, 236.5, 224.0, 1.018, 1.025);
  ok(Math.abs(gr.dispTrue - 20788.7) < 0.2 && Math.abs(gr.dispTrue - 11965 - 8520 - 303.7) < 0.2, 'guide: 20,788.7 t and constant 303.7 t');
  ok((await txt('#r_ftc')).startsWith('+59.1'), 'guide: first trim correction +59.1');
  await set('lcfd', 'fwd'); ok((await txt('#r_ftc')).startsWith('−59.1'), 'LCF forward reverses the sign');
  await set('fp', '7.33'); await set('fs', '7.27'); await set('ap', '5.62'); await set('as', '5.58'); ok((await txt('#r_trim')).endsWith('by the head'), 'trim by the head'); ok((await txt('#r_ftc')).startsWith('+'), 'LCF forward, trim by the head: added');
  ok(parseFloat(await txt('#r_f')) > 7.3, 'by the head with marks abaft the FP: deeper at the FP than at the marks'); await set('xfd', 'fwd'); ok(parseFloat(await txt('#r_f')) < 7.3, 'marks forward of the FP move the correction the other way');
  await set('lbp', ''); ok((await res()).includes('six draughts'), 'missing LBP message');
  await done('draft-survey-calculator');

  // ---- LNG ----
  await open('lng-conversion-boil-off-calculator');
  eq(await txt('#r_main'), '76,500 t', '170,000 m3 at 450 kg/m3'); eq(await txt('#r_mmbtu'), '3,978,000 MMBtu', 'energy at 52 MMBtu/t'); eq(await txt('#r_nm3'), '99,450,000 Nm³', 'gas volume');
  await set('qty', '1'); await set('unit', 't'); await set('heat', '53.38'); eq(await txt('#r_main'), '2 m³ of LNG', 'IGU: 1 t = 2.22 m3 (rounded)'); eq(await txt('#r_sm3'), '1,372 Sm³', 'IGU: 1,372 Sm3 per tonne'); eq(await txt('#r_mmbtu'), '53 MMBtu', 'IGU: 53.38 MMBtu per tonne');
  await set('qty', '1000'); await set('unit', 'm3'); eq(await txt('#r_mmbtu'), '24,021 MMBtu', 'IGU: 24.02 MMBtu per m3'); eq(await txt('#r_nm3'), '585,000 Nm³', 'IGU: 585 Nm3 per m3'); eq(await txt('#r_sm3'), '617,349 Sm³', 'IGU: 617 Sm3 per m3');
  await set('heatd', 'mj'); await set('heat', '54.863'); eq(await txt('#r_mmbtu'), '23,400 MMBtu', '54.863 MJ/kg = 52 MMBtu/t');
  await set('qty', '52'); await set('unit', 'mmbtu'); await set('heatd', 'mmbtu'); await set('heat', '52'); eq(await txt('#r_t'), '1.0 t', '52 MMBtu back to one tonne');
  await set('v0', '170000'); await set('v1', '169660'); await set('hrs', '48'); eq(await txt('#r_bor'), '0.100 % per day', 'boil-off rate'); eq(await txt('#r_bm3'), '170.0 m³', 'boil-off per day'); eq(await txt('#r_bt'), '76.5 t', 'boil-off tonnes per day');
  await set('v1', '171000'); ok((await res()).includes('larger than at the start'), 'volume increase message');
  await set('dens', '45'); ok((await res()).includes('between 380 and 520'), 'density range message'); await set('dens', '450');
  await done('lng-conversion-boil-off-calculator');

  // ---- Dew point ----
  await open('dew-point-calculator');
  const po = C.psychro(28, 25); eq(await txt('#r_dew'), po.dew.toFixed(1) + ' °C', 'dew point'); eq(await txt('#r_dew'), '23.9 °C', 'dew point of the page example'); eq(await txt('#r_rh'), '78 %', 'relative humidity');
  await set('hdry', '24'); await set('hwet', '20'); eq(await txt('#r_hdew'), '18.0 °C', 'hold dew point'); ok((await txt('#r_rule')).includes('do not ventilate'), 'outside wetter: do not ventilate');
  await set('dry', '18'); await set('wet', '13'); ok((await txt('#r_rule')).endsWith('ventilate.') && !(await txt('#r_rule')).includes('not'), 'outside drier: ventilate');
  await set('hdry', '18'); await set('hwet', '13.2'); ok((await txt('#r_rule')).includes('no clear answer'), 'dew points too close to call');
  await set('dry', '25.5556'); await set('wet', '18.3333'); eq(await txt('#r_rh'), '49 %', '78/65 F chart example: 50%');
  await set('wet', '25.5556'); eq(await txt('#r_rh'), '100 %', 'saturated air'); eq(await txt('#r_dew'), '25.6 °C', 'dew point equals the temperature when saturated');
  await set('wet', '27'); ok((await res()).includes('cannot read higher'), 'wet above dry message'); await set('dry', '5'); await set('wet', '-1'); ok((await res()).includes('ice'), 'freezing wet bulb message');
  await set('dry', '40'); await set('wet', '8'); ok((await res()).includes('cannot occur together'), 'impossible pair message');
  await set('dry', '28'); await set('wet', '25');
  await done('dew-point-calculator');

  // ---- Sunrise and twilight ----
  await open('sunrise-sunset-twilight-calculator');
  for (const [id, v] of [['date', '1994-09-01'], ['zone', '-5'], ['latd', '36'], ['latm', '14'], ['lath', 'N'], ['lond', '069'], ['lonm', '26'], ['lonh', 'W']]) await set(id, v);
  eq(await txt('#r_set'), '18:06', 'sunset 1 Sep 1994 (Nautical Almanac example: LMT 1827 = 1805 zone time)'); eq(await txt('#r_rise'), '05:09', 'sunrise'); eq(await txt('#r_mp'), '11:38', 'meridian passage');
  const sv = C.sunEvents(Date.UTC(1994, 8, 1, 5), 36 + 14 / 60, -(69 + 26 / 60)), hm = ms => { const d = new Date(Math.round((ms - 5 * 3600000) / 60000) * 60000); return ('0' + d.getUTCHours()).slice(-2) + ':' + ('0' + d.getUTCMinutes()).slice(-2); };
  eq(await txt('#r_cb'), hm(sv.civilBegin), 'civil twilight begins'); eq(await txt('#r_ne'), hm(sv.nautEnd), 'nautical twilight ends'); eq(await txt('#r_saz'), brg(sv.setAz, 0) + 'T', 'bearing at sunset');
  await set('zone', '0'); eq(await txt('#r_set'), '23:06', 'same sunset in UTC');
  for (const [id, v] of [['date', '2027-06-21'], ['zone', '1'], ['latd', '78'], ['latm', '0'], ['lond', '015'], ['lonm', '0'], ['lonh', 'E']]) await set(id, v);
  eq(await txt('#r_rise'), 'Does not set', 'midnight sun'); eq(await txt('#r_cb'), 'Sun stays above', 'no twilight in polar day');
  await set('date', '2027-12-21'); eq(await txt('#r_rise'), 'Does not rise', 'polar night'); eq(await txt('#r_alt'), 'Below the horizon', 'noon altitude in polar night');
  for (const [id, v] of [['date', '2027-06-21'], ['zone', '1'], ['latd', '56'], ['latm', '0'], ['lond', '010']]) await set(id, v);
  eq(await txt('#r_ne'), 'Sun stays above', 'no nautical darkness at 56N in June'); ok(/^\d\d:\d\d$/.test(await txt('#r_ce')) || /next day$/.test(await txt('#r_ce')), 'civil twilight still ends');
  await set('latd', '95'); ok((await res()).includes('Enter the date'), 'bad latitude message'); await set('latd', '20');
  await done('sunrise-sunset-twilight-calculator');

  // ---- Rate of turn ----
  await open('rate-of-turn-calculator');
  eq(await txt('#r_main'), '11.5 °/min', 'rate of turn'); eq(await txt('#r_time'), '3 min 56 s', 'time for 45 degrees'); eq(await txt('#r_arc'), '0.79 nm (7.9 cables)', 'arc length'); eq(await txt('#r_wo'), '0.41 nm (4.1 cables)', 'tangent distance');
  await set('spd', '15'); await set('rad', '1.5'); eq(await txt('#r_main'), '9.5 °/min', '15 kn on 1.5 nm (bridge rule: 10)'); ok((await res()).includes('gives 10.0'), 'bridge rule shown');
  await seg('mode', 'rad'); await set('rot', '9.549'); eq(await txt('#r_main'), '1.50 nm', 'radius from rate of turn');
  await set('ang', '200'); ok((await res()).includes('less than 180'), 'course change limit'); await set('ang', ''); ok((await txt('#r_time')) === null, 'no turn rows without a course change');
  await set('rot', '0'); ok((await res()).includes('Enter the rate of turn'), 'zero rate message'); await set('rot', '11.5'); await set('ang', '45');
  await done('rate-of-turn-calculator');

  // ---- Horizon ----
  await open('distance-to-horizon-calculator');
  eq(await txt('#r_hor'), '10.4 nm', 'sea horizon'); eq(await txt('#r_dip'), '23.6 nm', 'dipping range');
  await set('ant', '30'); eq(await txt('#r_rad'), '12.1 nm', 'radar horizon'); eq(await txt('#r_rado'), (2.21 * (Math.sqrt(30) + Math.sqrt(40))).toFixed(1) + ' nm', 'radar range to the object');
  await set('obj', ''); eq(await txt('#r_span'), '10.2 to 10.6 nm', 'range of published tables (2.03 x 5 = 10.15, rounded half up as on paper)'); ok((await txt('#r_dip')) === null, 'no dipping range without a light');
  await set('eye', '30.48'); ok((await txt('#r_span')).endsWith('11.7 nm'), 'Bowditch Table 12: 100 ft gives 11.7 nm');
  await set('eye', '0'); ok((await res()).includes('height of eye'), 'zero height message'); await set('eye', '25'); await set('obj', '40');
  await done('distance-to-horizon-calculator');

  // ---- Rolling period ----
  await open('rolling-period-gm-calculator');
  eq(await txt('#r_main'), '13.9 s', 'rolling period'); eq(await txt('#r_c'), '0.340', 'IS Code coefficient');
  await set('tw', '10'); await set('spd', '15'); await set('wang', '0'); eq(await txt('#r_te'), '6.7 s', 'encounter period in a head sea'); eq(await txt('#r_wl'), '156 m', 'wave length'); eq(await txt('#r_ratio'), '0.48', 'ratio'); ok((await txt('#r_flag')).includes('half the rolling period'), 'parametric rolling flag');
  await set('wang', '90'); eq(await txt('#r_te'), '10.0 s', 'beam sea: encounter period equals the wave period'); ok((await txt('#r_flag')) === null, 'no flag at a ratio of 0.72');
  await set('tw', '14'); ok((await txt('#r_flag')).includes('synchronous'), 'synchronous rolling flag');
  await set('tw', '8'); await set('spd', '26'); await set('wang', '180'); eq(await txt('#r_te'), 'None', 'overtaking the waves'); ok((await res()).includes('keeps pace'), 'following sea warning');
  await seg('mode', 'gm'); await set('per', '13.853'); eq(await txt('#r_main'), '2.50 m', 'GM back from the period');
  await seg('mode', 't'); await set('gm', '0'); ok((await res()).includes('must be positive'), 'zero GM message'); await set('gm', '2.50');
  await set('tw', ''); await set('spd', ''); await set('wang', '');
  await done('rolling-period-gm-calculator');

  // ---- new tools inside the app frame ----
  await open('draft-survey-calculator', true);
  ok(await page.evaluate(() => getComputedStyle(document.querySelector('.back')).display !== 'none'), 'back link shown in the app'); ok(await page.evaluate(() => getComputedStyle(document.querySelector('.bar')).display === 'none'), 'site header hidden in the app');
  await done('draft-survey-calculator-embed');

  // ---- regressions from the independent audit of 26 Nov 2026 ----
  await open('true-wind-calculator');
  await set('hdg', '045'); await set('spd', '14'); await set('rel', '30'); await set('ws', '25');
  eq(await txt('#r_main'), '104°T', 'true wind, course left empty'); eq(await txt('#r_spd'), '14.7 kn', 'true wind speed, course left empty');
  await set('cog', '052'); eq(await txt('#r_main'), '099°T', 'true wind with a course over the ground of 052'); eq(await txt('#r_spd'), '13.3 kn', 'true wind speed with a course over the ground');
  await set('cog', '400'); ok((await res()).includes('course over the ground'), 'bad course over the ground is refused'); await set('cog', '');
  await done('true-wind-calculator-cog');

  await open('sunrise-sunset-twilight-calculator');
  const polar = async (date) => { await page.evaluate(() => { document.getElementById('zone').value = '1'; document.getElementById('lath').value = 'N'; document.getElementById('lonh').value = 'E'; }); await set('latd', '70'); await set('latm', '00.0'); await set('lond', '015'); await set('lonm', '00.0'); await set('date', date); };
  await polar('2027-07-27'); eq(await txt('#r_rise'), 'None', 'day the midnight sun ends: no sunrise'); eq(await txt('#r_set'), '23:46', 'day the midnight sun ends: sunset shown'); ok((await txt('#r_note')).includes('No sunrise'), 'note explains the missing sunrise'); ok((await txt('#r_len')) === null, 'no day length with one event');
  await polar('2027-05-16'); eq(await txt('#r_set'), 'None', 'day the midnight sun begins: no sunset, never a made-up time'); eq(await txt('#r_rise'), '00:28', 'day the midnight sun begins: sunrise shown'); ok(!(await res()).includes('previous day'), 'no bogus previous-day sunset');
  await polar('2027-06-21'); eq(await txt('#r_rise'), 'Does not set', 'midnight sun'); await polar('2027-12-21'); eq(await txt('#r_rise'), 'Does not rise', 'polar night');
  await done('sunrise-polar');

  await open('cpa-tcpa-calculator');
  await set('r1', '999999999'); ok((await res()).includes('up to 120'), 'absurd range is refused and the page stays alive'); await set('r1', '10.0'); eq(await txt('#r_cpa'), '1.79 nm', 'CPA still right afterwards');
  await done('cpa-range');

  await open('squat-ukc-calculator');
  await set('depth', '999999999'); eq(await txt('#r_squat'), '1.02 m', 'absurd depth does not freeze the chart'); await set('depth', '12.40'); eq(await txt('#r_ukc'), '0.60 m', 'net UKC still right afterwards');
  await done('squat-depth');

  await open('eta-speed-distance-time-calculator');
  await set('dist', '1000000'); await set('speed', '0.0001'); ok((await res()).includes('ten years'), 'a steaming time beyond any calendar is refused, not printed as NaN');
  await set('speed', '12'); await set('dist', '1,200'); ok(((await txt('#rd_dist')) || '').includes('decimal point: 1.2'), 'a typed comma is read as a decimal point and the page says so');
  await set('dist', '1200'); ok((await txt('#rd_dist')) === null, 'the note goes when the comma goes');
  await set('speed', '12,5'); ok((await txt('#rd_speed')) === null, 'an ordinary decimal comma needs no note'); eq(await txt('#r_time'), '4 d 00 h 00 min', '12,5 knots read as 12.5'); await set('speed', '12');
  await done('eta-guards');

  await open('rolling-period-gm-calculator');
  await set('tw', '10'); await set('spd', '15'); await set('wang', '0'); ok((await txt('#r_est')).includes('estimated by the formula'), 'wave comparison on an estimated period says so');
  await seg('mode', 'gm'); ok((await txt('#r_est')) === null, 'no such note when the period was timed');
  await done('rolling-estimate-note');

  // ---- figures that sit exactly on a limit (boundary audit of 26 Nov 2026) ----
  // Each of these is a round-number case where binary arithmetic leaves a residue (10.3 + 0.7 - 10.1 - 0.7 - 0.2 is not 0).
  await open('squat-ukc-calculator');
  await seg('water', 'open'); await set('cb', '0.70'); await set('v', '10'); await set('depth', '10.3'); await set('tide', '0.7'); await set('draught', '10.1'); await set('other', '0.2');
  eq(await txt('#r_ukc'), '0.00 m', 'net UKC exactly nil'); ok((await res()).includes('No clearance'), 'a net UKC of 0.00 m carries the grounding warning');
  await set('other', '0.196'); eq(await txt('#r_ukc'), '0.00 m', 'net UKC of 4 mm prints as 0.00'); ok((await res()).includes('No clearance'), 'and still carries the grounding warning');
  await set('other', '0.19'); eq(await txt('#r_ukc'), '0.01 m', 'net UKC of 1 cm'); ok(!(await res()).includes('No clearance'), 'no grounding warning with 1 cm printed');
  await set('cb', '0.44'); await set('v', '8.9'); await set('depth', '5.24'); await set('tide', '3.64'); await set('draught', '7.59'); await set('other', '1.29');
  ok(!(await res()).includes('falls to zero'), 'no zero-clearance speed when the clearance before squat is exactly nil');
  await seg('water', 'conf'); await set('cb', '0.99'); await set('v', '10.2'); await set('depth', '25.71'); await set('tide', '2.57'); await set('draught', '20.20'); await set('other', '0');
  ok((await res()).includes('1.40') && !(await res()).includes('1.1 to 1.4'), 'a ratio of exactly 1.40 is inside the range of the formula');
  await set('depth', '25.92'); ok((await res()).includes('1.41') && (await res()).includes('1.1 to 1.4'), 'a ratio of 1.41 is outside it');
  await done('squat-limits');

  await open('list-and-gm-calculator');
  await set('disp', '13500'); await set('km', '7.62'); await set('kg', '7.193'); await set('fsm', '5764.5'); await set('w', '50'); await set('d', '10');
  eq(await txt('#r_gm'), '0.00 m', 'fluid GM exactly nil'); ok((await res()).includes('GM is zero or negative'), 'a GM of 0.00 m carries the unstable warning'); ok((await txt('#r_list')) === null, 'and no list is quoted beside it');
  await set('kg', '7.183'); eq(await txt('#r_gm'), '0.01 m', 'GM of 1 cm'); ok(!(await res()).includes('GM is zero or negative'), 'no unstable warning at 1 cm'); ok((await txt('#r_list')).includes('to starboard'), 'list quoted again');
  await done('gm-limits');

  await open('fuel-consumption-calculator');
  await set('cons', '20'); await set('hours', '24'); await set('rob', '20'); await set('speed', '11.2'); await set('dist', '268.8'); await set('newspeed', '');
  eq(await txt('#r_arr'), '0.0 t', 'fuel runs out exactly on arrival'); ok(!(await res()).includes('Not enough fuel'), 'no shortfall warning with 0.0 t on arrival');
  await set('rob', '19.9'); eq(await txt('#r_arr'), '-0.1 t', '100 kg short'); ok((await res()).includes('Short by 0.1 t'), 'shortfall of 0.1 t is warned');
  await done('fuel-limits');

  await open('propeller-slip-calculator');
  await seg('mode', 'per'); await set('pitch', '4.63'); await set('rpm', '100'); await set('ph', '1'); await set('pm', '00'); await set('od', '15.0005');
  eq(await txt('#r_main'), '0.00 %', 'slip that prints as nil'); ok(!(await res()).includes('Negative slip'), 'no negative-slip note beside 0.00 %');
  await set('od', '15.01'); eq(await txt('#r_main'), '-0.07 %', 'negative slip'); ok((await res()).includes('Negative slip'), 'negative-slip note when the figure is negative');
  await done('slip-limits');

  await open('set-and-drift-course-to-steer-calculator');
  await seg('mode', 'cts'); await set('ctrack', '000'); await set('cstw', '10'); await set('cset', '090'); await set('crate', '10');
  ok((await res()).includes('too strong'), 'stream abeam as fast as the ship: no headway, track cannot be held');
  await set('cstw', '5'); await set('cset', '330'); eq(await txt('#r_main'), '090.0°T', 'cross-track stream equal to the speed: steer 90 degrees off'); eq(await txt('#r_smg'), '8.7 kn', 'and make 8.7 kn along the track');
  await done('cts-limits');

  await open('true-wind-calculator');
  await set('spd', '0'); await set('cog', ''); await set('rel', '40'); await set('ws', '3.5');
  for (const h of ['000', '139.5', '020', '294.5', '251']) { await set('hdg', h); eq(await txt('#r_bf'), 'Force 2, Light breeze', '3.5 kn is Force 2 on a heading of ' + h); }
  await done('beaufort-limits');

  await open('rolling-period-gm-calculator');
  await seg('mode', 'gm'); await set('per', '7.5'); await set('tw', '11'); await set('spd', '11'); await set('wang', '0');
  eq(await txt('#r_ratio'), '1.10', 'encounter period 10% above the rolling period'); ok((await txt('#r_flag')).includes('synchronous'), 'a ratio of exactly 1.10 is flagged');
  await set('per', '15'); eq(await txt('#r_ratio'), '0.55', 'encounter period 10% above half the rolling period'); ok((await txt('#r_flag')).includes('half the rolling period'), 'a ratio of exactly 0.55 is flagged');
  await set('per', '14.6'); eq(await txt('#r_ratio'), '0.57', 'ratio of 0.57'); ok((await txt('#r_flag')) === null, 'no flag at 0.57');
  await done('rolling-limits');

  await open('dew-point-calculator');
  await set('dry', '18.9'); await set('wet', '16.0'); await set('hdry', '16.3'); await set('hwet', '15.3');
  { const o = parseFloat(await txt('#r_dew')), i = parseFloat(await txt('#r_hdew')), rule = await txt('#r_rule'), d = Math.round((o - i) * 10) / 10;
    eq(d, -0.5, 'printed dew points half a degree apart'); ok(rule.includes('lower than in the hold by 0.5°C') && rule.endsWith('ventilate.') && !rule.includes('not'), 'the rule quotes the difference of the printed dew points'); }
  await done('dew-limits');

  await open('cpa-tcpa-calculator');
  await set('oc', '330'); await set('os', '22.5'); await set('b1', '066.7'); await set('r1', '4.54'); await set('b2', '067.0'); await set('r2', '3.13');
  eq(await txt('#r_cpa'), '0.05 nm', 'CPA printed as 0.05 nm'); ok((await res()).includes('CPA is 0.05 nm or less'), 'a printed CPA of 0.05 nm carries the collision warning');
  await done('cpa-limits');

  await open('eta-speed-distance-time-calculator');
  await seg('mode', 'eta'); await page.evaluate(() => { for (const id of ['dzone', 'azone']) { const e = document.getElementById(id); e.value = '0'; e.dispatchEvent(new Event('change', { bubbles: true })); } });
  await set('ddate', '2026-11-23'); await set('dtime', '08:00'); await set('speed', '12'); await set('dist', '0.7');
  eq(await txt('#r_time'), '0 h 04 min', '3.5 minutes under way is shown as 4'); eq(await txt('#r_main'), 'Mon 23 Nov 2026, 08:04', 'and the ETA is the departure plus those 4 minutes');
  await set('dist', '4322.9'); eq(await txt('#r_time'), '15 d 00 h 15 min', '21614.5 minutes under way is shown as 21615'); eq(await txt('#r_utc'), 'Tue 8 Dec 2026, 08:15', 'and the ETA agrees with it');
  await done('eta-half-minute');

  await open('draft-survey-calculator');
  await set('fp', '10.02'); await set('fs', '10.02'); await set('mp', '10.10'); await set('ms', '10.10'); await set('ap', '9.99'); await set('as', '9.99'); await set('lbp', '100'); await set('xf', '6'); await set('xa', '2'); await set('xm', '4');
  await page.evaluate(() => { for (const [id, v] of [['xfd', 'aft'], ['xad', 'aft'], ['xmd', 'fwd']]) { const e = document.getElementById(id); e.value = v; e.dispatchEvent(new Event('change', { bubbles: true })); } });
  eq(await txt('#r_m'), '10.0988 m', 'a corrected draught of exactly 10.09875 m is rounded up, as on a surveyor\'s sheet'); eq(await txt('#r_mmm'), '10.0757 m', 'mean of means from the rounded draughts');
  eq(await txt('#r_ftc'), '+5.74 t', 'first trim correction'); eq(await txt('#r_stc'), '+0.01 t', 'second trim correction'); eq(await txt('#r_dt'), '19,900.12 t', 'the column adds up: 19,894.37 + 5.74 + 0.01');
  eq(await txt('#r_true'), '19,773.92 t', 'the density line is worked from the line above as printed: 19,900.12 x 1.0185 / 1.025 = 19,773.924');
  await done('survey-half');

  await open('lng-conversion-boil-off-calculator');
  await page.evaluate(() => { const e = document.getElementById('heatd'); e.value = 'mj'; e.dispatchEvent(new Event('change', { bubbles: true })); });
  await set('heat', '47'); ok((await res()).includes('47.5 to 60.1 MJ/kg'), 'heating value limits quoted in MJ/kg are the ones applied'); await set('heat', '47.5'); ok(!(await res()).includes('Enter the heating value'), '47.5 MJ/kg is accepted');
  await set('heat', '60.1'); ok(!(await res()).includes('Enter the heating value'), '60.1 MJ/kg is accepted'); await set('heat', '60.2'); ok((await res()).includes('Enter the heating value'), '60.2 MJ/kg is refused');
  await done('lng-limits');

  await browser.close(); server.close();
  console.log(`\n${checks - fails} of ${checks} page checks passed`);
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });

// Run: node --test scripts/tools/tests/
const test = require('node:test');
const assert = require('node:assert');
const path = require('path');
const C = require(path.join(__dirname, '../../../tools/assets/calc.js'));
const geodesic = require(path.join(__dirname, '../../../tools/assets/geodesic.min.js'));
const FX = require('./fixtures.json');

const near = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg || ''} got ${a}, want ${b} ±${tol}`);
const angNear = (a, b, tol, msg) => near(C.norm180(a - b), 0, tol, `${msg || ''} (${a} vs ${b})`);
let seed = 12345;
const rnd = (a, b) => { seed = (seed * 1664525 + 1013904223) % 4294967296; return a + (b - a) * seed / 4294967296; };

test('sun: azimuth, altitude, declination and GHA against astropy (1500 cases, 2026-2040)', () => {
  let maxAz = 0, maxAlt = 0, maxDec = 0, maxGha = 0, n = 0;
  for (const f of FX.sun) {
    const s = C.sunPosition(f.ms, f.lat, f.lon);
    maxDec = Math.max(maxDec, Math.abs(s.dec - f.dec));
    maxGha = Math.max(maxGha, Math.abs(C.norm180(s.gha - f.gha)));
    maxAlt = Math.max(maxAlt, Math.abs(s.alt - f.alt));
    if (f.alt >= -1 && f.alt <= 80) { n++; maxAz = Math.max(maxAz, Math.abs(C.norm180(s.az - f.az))); }
  }
  console.log(`   sun max error: azimuth ${maxAz.toFixed(4)}° (${n} cases, sun above the horizon and below 80°), altitude ${maxAlt.toFixed(4)}°, declination ${maxDec.toFixed(4)}°, GHA ${maxGha.toFixed(4)}°`);
  assert.ok(maxAz < 0.03); assert.ok(maxAlt < 0.015); assert.ok(maxDec < 0.005); assert.ok(maxGha < 0.012);
});

test('amplitude and azimuth: worked examples from the Ocean Link guide', () => {
  const a = C.amplitude(20, 15);
  near(a.amp, 16.0, 0.05); assert.equal(a.name, 'N'); near(a.set, 286.0, 0.05); near(a.rise, 74.0, 0.05);
  near(C.compassError(286.0, 287.0), -1.0, 1e-9); // gyro 1° high = West
  near(C.compassError(286.0, 290.0), -4.0, 1e-9);
  near(C.bodyAzAlt(30, -10, 40).az, 230.2, 0.05); // ABC example
  near(C.compassError(230.2, 229.5), 0.7, 1e-9);  // East, gyro low
  near(C.compassError(359.5, 0.5), -1, 1e-9); near(C.compassError(0.5, 359.5), 1, 1e-9);
  assert.equal(C.amplitude(80, 23), null); // midnight sun: no rising or setting
  const s = C.amplitude(-35, -20); assert.equal(s.name, 'S'); near(s.rise, 90 + 24.68, 0.01); near(s.set, 270 - 24.68, 0.01);
});

test('true wind: known cases and round trip', () => {
  let w = C.trueWind(0, 10, 0, 10); near(w.speed, 0, 1e-9); assert.equal(w.dir, null);
  w = C.trueWind(0, 10, 90, 10); near(w.speed, Math.SQRT2 * 10, 1e-9); angNear(w.dir, 135, 1e-9);
  w = C.trueWind(0, 10, 270, 10); angNear(w.dir, 225, 1e-9);
  w = C.trueWind(90, 12, 0, 30); near(w.speed, 18, 1e-9); angNear(w.dir, 90, 1e-9);   // head wind
  w = C.trueWind(90, 12, 180, 5); near(w.speed, 17, 1e-9); angNear(w.dir, 270, 1e-9); // following wind faster than ship
  w = C.trueWind(350, 15, 30, 25); // hand-worked: apparent from 020
  const ax = 25 * Math.sin(20 * Math.PI / 180) - 15 * Math.sin(350 * Math.PI / 180), ay = 25 * Math.cos(20 * Math.PI / 180) - 15 * Math.cos(350 * Math.PI / 180);
  near(w.speed, Math.hypot(ax, ay), 1e-9);
  for (let i = 0; i < 2000; i++) { // build apparent wind from a true wind, then recover it
    const h = rnd(0, 360), vs = rnd(0, 25), td = rnd(0, 360), ts = rnd(0.5, 60);
    const x = ts * Math.sin(C.rad(td)) + vs * Math.sin(C.rad(h)), y = ts * Math.cos(C.rad(td)) + vs * Math.cos(C.rad(h));
    const rel = C.norm360(C.dirOf(x, y) - h), as = Math.hypot(x, y);
    const r = C.trueWind(h, vs, rel, as);
    near(r.speed, ts, 1e-8); angNear(r.dir, td, 1e-6);
  }
});

test('Beaufort table boundaries', () => {
  const want = [[0, 0], [0.4, 0], [1, 1], [3, 1], [4, 2], [6, 2], [7, 3], [10, 3], [11, 4], [16, 4], [17, 5], [21, 5], [22, 6], [27, 6],
    [28, 7], [33, 7], [34, 8], [40, 8], [41, 9], [47, 9], [48, 10], [55, 10], [56, 11], [63, 11], [64, 12], [90, 12]];
  for (const [k, f] of want) assert.equal(C.beaufort(k).force, f, `knots ${k}`);
  assert.equal(C.beaufort(35).desc, 'Gale');
});

test('ETA and required speed with time zones', () => {
  const dep = Date.UTC(2026, 10, 23, 8, 0); // 23 Nov 08:00 local, UTC+1
  const e = C.eta(dep, 1, 8, 1200, 12);
  near(e.hours, 100, 1e-9);
  assert.equal(e.utcMs, Date.UTC(2026, 10, 27, 11, 0));
  assert.equal(e.arrLocalMs, Date.UTC(2026, 10, 27, 19, 0));
  const r = C.requiredSpeed(dep, 1, Date.UTC(2026, 10, 27, 19, 0), 8, 1200);
  near(r.hours, 100, 1e-9); near(r.speed, 12, 1e-9);
  const w = C.eta(Date.UTC(2026, 0, 1, 22, 0), 12, -11, 240, 10); // date line: UTC+12 to UTC-11, one day in hand
  assert.equal(w.utcMs, Date.UTC(2026, 0, 2, 10, 0)); assert.equal(w.arrLocalMs, Date.UTC(2026, 0, 1, 23, 0));
  assert.equal(C.requiredSpeed(dep, 0, dep, 0, 100).speed, null);
});

test('great circle (sphere): guide example Japan to San Francisco and special cases', () => {
  const g = C.gcSphere(35, 140, 37, -123);
  near(g.distNm, 4476, 1.5); near(g.initial, 55.3, 0.06); near(g.final, 122.5, 0.06);
  near(g.vertex.lat, 47.7, 0.06); near(g.vertex.lon, -169.6, 0.06); assert.equal(g.vertex.onTrack, true);
  let m = C.gcSphere(10, 20, 60, 20); near(m.distNm, 3000, 1e-6); angNear(m.initial, 0, 1e-9); near(m.vertex.lat, 90, 1e-6);
  m = C.gcSphere(0, 10, 0, 100); near(m.distNm, 5400, 1e-6); angNear(m.initial, 90, 1e-9); assert.equal(m.vertex, null);
  m = C.gcSphere(-33.9, 18.4, -34.6, -58.4); assert.ok(m.vertex.lat < 0); // southern hemisphere vertex
  m = C.gcSphere(20, 179, 21, -179); assert.ok(m.distNm < 130); assert.ok(m.initial > 0 && m.initial < 90); // date line, short way
  // independent check with the haversine and cosine formulas
  for (let i = 0; i < 2000; i++) {
    const a = rnd(-85, 85), b = rnd(-180, 180), c = rnd(-85, 85), d = rnd(-180, 180);
    const r = C.gcSphere(a, b, c, d), R = Math.PI / 180;
    const hav = Math.sin((c - a) * R / 2) ** 2 + Math.cos(a * R) * Math.cos(c * R) * Math.sin((d - b) * R / 2) ** 2;
    near(r.distNm, 2 * Math.asin(Math.sqrt(hav)) / R * 60, 1e-6);
    // the vertex must lie on the great circle and be its highest latitude: cos Lv = cos L1 * |sin C|
    near(Math.cos(r.vertex.lat * R), Math.cos(a * R) * Math.abs(Math.sin(r.initial * R)), 1e-9);
  }
});

test('rhumb line and meridional parts (WGS84) against numerical integration', () => {
  let maxD = 0, maxC = 0;
  for (const f of FX.rhumb) {
    const r = C.rhumb(f.lat1, f.lon1, f.lat2, f.lon2);
    maxD = Math.max(maxD, Math.abs(r.distNm - f.distNm)); maxC = Math.max(maxC, Math.abs(C.norm180(r.course - f.course)));
    near(r.dmp, f.dmp, 1e-6);
  }
  console.log(`   rhumb max error: distance ${maxD.toExponential(2)} nm, course ${maxC.toExponential(2)}° (${FX.rhumb.length} cases)`);
  assert.ok(maxD < 1e-4); assert.ok(maxC < 1e-7);
  for (const f of FX.mp) near(C.meridionalParts(f.lat), f.mp, 1e-6);
  near(C.meridionalParts(35), 2231.1, 0.06); near(C.meridionalParts(37), 2378.8, 0.06); // figures quoted in the guide
  const g = C.rhumb(35, 140, 37, -123); near(g.course, 88.5, 0.06);
  const p = C.rhumb(50, -5, 50, -60); angNear(p.course, 270, 1e-9); // parallel sailing
  assert.equal(C.rhumb(90, 0, 10, 0), null);
});

test('geodesic library (WGS84, as ECDIS) against PROJ, including near-antipodal points', () => {
  let maxD = 0, maxA = 0;
  FX.geodesic.forEach((f, i) => {
    const r = geodesic.Geodesic.WGS84.Inverse(f.lat1, f.lon1, f.lat2, f.lon2);
    maxD = Math.max(maxD, Math.abs(r.s12 / 1852 - f.distNm));
    if (i < 400) maxA = Math.max(maxA, Math.abs(C.norm180(r.azi1 - f.initial)), Math.abs(C.norm180(r.azi2 - f.final)));
  });
  console.log(`   geodesic max error: distance ${maxD.toExponential(2)} nm, course ${maxA.toExponential(2)}° (${FX.geodesic.length} cases)`);
  assert.ok(maxD < 1e-5); assert.ok(maxA < 1e-6);
});

test('CPA/TCPA: guide example and brute-force simulation', () => {
  const g = C.cpa(0, 12, 37, 10.0, 45, 5.7, 12);
  near(g.cpa, 1.8, 0.06); near(g.cpaBrg, 117, 1.0); near(g.tcpaMin, 15, 0.8);
  near(g.targetCourse, 232, 1.0); near(g.targetSpeed, 12.6, 0.15); near(g.relCourse, 207, 1.0); near(g.relSpeed, 22, 0.3);
  for (let i = 0; i < 1500; i++) {
    const oc = rnd(0, 360), os = rnd(0, 22), tc = rnd(0, 360), ts = rnd(1, 25);
    const b0 = rnd(0, 360), r0 = rnd(3, 14), dt = rnd(3, 12);
    const pos = (tmin) => { // target position relative to own ship at t minutes
      const h = tmin / 60;
      return [r0 * Math.sin(C.rad(b0)) + (ts * Math.sin(C.rad(tc)) - os * Math.sin(C.rad(oc))) * h,
              r0 * Math.cos(C.rad(b0)) + (ts * Math.cos(C.rad(tc)) - os * Math.cos(C.rad(oc))) * h];
    };
    const p1 = pos(0), p2 = pos(dt);
    const r = C.cpa(oc, os, C.dirOf(p1[0], p1[1]), Math.hypot(...p1), C.dirOf(p2[0], p2[1]), Math.hypot(...p2), dt);
    angNear(r.targetCourse, tc, 1e-6); near(r.targetSpeed, ts, 1e-7);
    // brute force: scan time for the minimum range
    let best = Infinity, bt = 0;
    for (let t = -600; t <= 600; t += 0.05) { const p = pos(dt + t); const d = Math.hypot(p[0], p[1]); if (d < best) { best = d; bt = t; } }
    if (Math.abs(bt) < 599) { near(r.cpa, best, 2e-3); near(r.tcpaMin, bt, 0.06); }
    const asp = C.norm180(C.norm360(C.dirOf(p2[0], p2[1]) + 180) - tc); near(C.norm180(r.aspect - asp), 0, 1e-6);
  }
  const s = C.cpa(90, 10, 45, 5, 45, 5, 6); near(s.cpa, 5, 1e-9); assert.equal(s.tcpaMin, null); // same course and speed
  near(s.targetSpeed, 10, 1e-9); angNear(s.targetCourse, 90, 1e-9);
  const h = C.cpa(0, 10, 0, 10, 0, 8, 6); near(h.cpa, 0, 1e-9); near(h.tcpaMin, 24, 1e-9); // collision course, dead ahead
  const past = C.cpa(0, 10, 180, 2, 180, 3, 6); assert.ok(past.tcpaMin < 0); // opening astern: CPA already passed
});

test('current triangle: guide examples and round trips', () => {
  const c = C.courseToSteer(90, 10, 0, 2);
  near(c.cts, 101.5, 0.05); near(c.smg, 9.8, 0.005);
  const sd = C.setDrift(45, 10, 2, 45 + C.deg(Math.atan(3 / 20)), Math.sqrt(409));
  angNear(sd.set, 135, 1e-6); near(sd.drift, 3.0, 1e-9); near(sd.rate, 1.5, 1e-9);
  assert.equal(C.courseToSteer(90, 3, 0, 4), null);   // stream stronger than the ship across the track
  assert.equal(C.courseToSteer(90, 3, 270, 4), null); // cannot make way against the stream
  for (let i = 0; i < 2000; i++) {
    const tr = rnd(0, 360), v = rnd(4, 25), set = rnd(0, 360), rate = rnd(0, 3.5);
    const r = C.courseToSteer(tr, v, set, rate);
    const mg = C.madeGood(r.cts, v, set, rate);
    angNear(mg.cmg, tr, 1e-7); near(mg.smg, r.smg, 1e-9);
    const hrs = rnd(0.5, 6), back = C.setDrift(r.cts, v, hrs, mg.cmg, mg.smg * hrs);
    if (rate > 0.01) angNear(back.set, set, 1e-5); near(back.rate, rate, 1e-8);
  }
});

test('squat and UKC: guide examples', () => {
  near(C.squat(0.82, 10, true), 1.64, 1e-9); near(C.squat(0.82, 7, true), 0.8036, 1e-9);
  near(C.squat(0.60, 16, true), 3.072, 1e-9); near(C.squat(0.80, 8, false), 0.512, 1e-9);
  let u = C.ukc(12.40, 2.10, 11.20, C.squat(0.80, 8, true), 0.28 + 1.25 + 0.15);
  near(u.depth, 14.50, 1e-9); near(u.staticUkc, 3.30, 1e-9); near(u.net, 0.60, 0.006);
  u = C.ukc(12.40, 2.60, 11.20, C.squat(0.80, 6, true), 0.28 + 1.25 + 0.15); near(u.net, 1.54, 0.006);
  u = C.ukc(10, -0.3, 9.5, 0.2, 0); near(u.net, 0, 1e-9); // negative tide
});

test('propeller slip', () => {
  const ed = C.engineDistance(6.0, 95 * 60 * 24); near(ed, 443.196, 0.001);
  near(C.slipPercent(ed, 420), 5.234, 0.001);
  near(C.engineSpeed(6.0, 95), 18.4665, 0.0001);
  assert.ok(C.slipPercent(400, 410) < 0); // negative slip
});

test('fuel', () => {
  const f = C.fuel(30, 24, 600, 14, 3000);
  near(f.daily, 30, 1e-9); near(f.daysLeft, 20, 1e-9); near(f.rangeNm, 6720, 1e-9);
  near(f.voyageDays, 8.9286, 1e-4); near(f.voyageFuel, 267.857, 1e-3); near(f.robArrival, 332.143, 1e-3);
  near(C.fuel(14.5, 12, 100, 0, -1).daily, 29, 1e-9);
  near(C.cubeLaw(30, 14, 12), 18.892, 1e-3); near(C.cubeLaw(30, 14, 14), 30, 1e-9);
});

test('FWA and DWA: guide example', () => {
  near(C.fwa(31500, 42), 187.5, 1e-9); near(C.dwa(188, 1010), 112.8, 1e-9);
  near(C.dwa(188, 1000), 188, 1e-9); near(C.dwa(188, 1025), 0, 1e-9); assert.ok(C.dwa(188, 1030) < 0);
});

test('GM, free surface and list: guide examples', () => {
  let s = C.stability(13500, 8.40, 97100 / 13500, 5765.625, 50, 10);
  near(s.gmSolid, 1.207, 0.001); near(s.fsc, 0.427, 0.001); near(s.gmFluid, 0.78, 0.001); near(s.list, 2.7, 0.05);
  s = C.stability(10000, 8.80, 8.00, 0, 50, 8); near(s.gmFluid, 0.80, 1e-9); near(s.list, 2.86, 0.005);
  s = C.stability(10000, 8.00, 8.10, 0, 50, 8); assert.ok(s.gmFluid < 0); assert.equal(s.list, null);
});

test('unit conversions', () => {
  near(C.convert('speed', 1, 'kn', 'm/s'), 0.514444, 1e-6); near(C.convert('speed', 10, 'm/s', 'kn'), 19.4384, 1e-4);
  near(C.convert('speed', 1, 'kn', 'km/h'), 1.852, 1e-12); near(C.convert('distance', 1, 'nm', 'km'), 1.852, 1e-12);
  near(C.convert('distance', 1, 'nm', 'cable'), 10, 1e-12); near(C.convert('distance', 1, 'nm', 'statute mile'), 1.150779, 1e-6);
  near(C.convert('depth', 1, 'fathom', 'm'), 1.8288, 1e-12); near(C.convert('depth', 10, 'm', 'ft'), 32.8084, 1e-4);
  near(C.convert('pressure', 1, 'bar', 'psi'), 14.5038, 1e-4); near(C.convert('pressure', 1, 'atm', 'bar'), 1.01325, 1e-12);
  near(C.convert('pressure', 1, 'kgf/cm²', 'bar'), 0.980665, 1e-12); near(C.convert('pressure', 760, 'mmHg', 'atm'), 1, 1e-6);
  near(C.convert('volume', 1, 'US barrel', 'litre'), 158.987, 1e-3); near(C.convert('volume', 1, 'm³', 'US barrel'), 6.28981, 1e-5);
  near(C.convert('volume', 1, 'Imperial gallon', 'litre'), 4.54609, 1e-9); near(C.convert('volume', 1, 'US gallon', 'litre'), 3.785412, 1e-6);
  near(C.convert('mass', 1, 'long ton', 'tonne'), 1.0160469, 1e-7); near(C.convert('mass', 1, 'tonne', 'lb'), 2204.6226, 1e-4);
  near(C.convert('power', 1, 'kW', 'hp (metric, PS)'), 1.35962, 1e-5); near(C.convert('power', 1, 'kW', 'hp (imperial, bhp)'), 1.34102, 1e-5);
  near(C.convertTemp(100, 'C', 'F'), 212, 1e-9); near(C.convertTemp(-40, 'F', 'C'), -40, 1e-9); near(C.convertTemp(0, 'C', 'K'), 273.15, 1e-9);
});

// Checks against published sources outside Ocean Link. Run: node --test scripts/tools/tests/
// Every case names the source it was taken from. Tolerances allow for the rounding in the printed answers.
const test = require('node:test');
const assert = require('node:assert');
const path = require('path');
const C = require(path.join(__dirname, '../../../tools/assets/calc.js'));
const geodesic = require(path.join(__dirname, '../../../tools/assets/geodesic.min.js'));
const near = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg || ''}: got ${a}, published ${b} (allowed ±${tol})`);
const ang = (a, b, tol, msg) => near(C.norm180(a - b), 0, tol, `${msg || ''} (${a} vs ${b})`);
const dm = (d, m, s) => d + m / 60 + (s || 0) / 3600;
const log = (...a) => console.log('   ' + a.join(' '));

test('true wind: reference test data of Smith, Bourassa and Sharp (COAPS, Florida State University)', () => {
  // https://www.coaps.fsu.edu/woce/truewind/c-codes/test.c and .../results  (course, speed, heading, vane direction, vane speed -> true direction, true speed)
  const rows = [[0, 0, 0, 90, 5, 90, 5], [0, 0, 90, 90, 5, 180, 5], [0, 5, 0, 0, 5, null, 0], [0, 5, 0, 0, 0, 180, 5], [180, 5, 180, 180, 5, 360, 10],
    [90, 5, 90, 90, 5, 225, 7.1], [90, 5, 45, 135, 5, 225, 7.1], [225, 5, 225, 270, 5, 90, 7.1], [270, 3, 270, 90, 4, 36.9, 5.0]];
  rows.forEach(([crse, cspd, hd, wdir, wspd, tdir, tspd], i) => {
    const r = C.trueWind(hd, cspd, wdir, wspd, crse);
    near(r.speed, tspd, 0.05, `row ${i + 1} speed`);
    if (tdir !== null) ang(r.dir, tdir, 0.05, `row ${i + 1} direction`);
  });
});

test('Beaufort force: Met Office table of wind speed limits in knots', () => {
  // https://www.metoffice.gov.uk/guide/weather/marine/beaufort-scale
  const t = [[0, 0, 0, 'Calm'], [1, 1, 3, 'Light air'], [2, 4, 6, 'Light breeze'], [3, 7, 10, 'Gentle breeze'], [4, 11, 16, 'Moderate breeze'], [5, 17, 21, 'Fresh breeze'],
    [6, 22, 27, 'Strong breeze'], [7, 28, 33, 'Near gale'], [8, 34, 40, 'Gale'], [9, 41, 47, 'Strong gale'], [10, 48, 55, 'Storm'], [11, 56, 63, 'Violent storm'], [12, 64, 120, 'Hurricane']];
  for (const [f, lo, hi, name] of t) for (let k = lo; k <= hi; k++) { assert.equal(C.beaufort(k).force, f, `${k} kn`); assert.equal(C.beaufort(k).desc, name); }
});

test('great circle (sphere): Bowditch 2019 chapter 12 and the AMS feature column', () => {
  // Bowditch art. 1208 ex. 1: 22S 116E to 20S 031E -> 4,693.8 nm, initial 253.0.
  // Ex. 3 prints the final course as 287.4. That figure does not agree with the book's own initial course:
  // Clairaut's relation (cos lat x sin course is constant along a great circle) gives 289.3, and PROJ on a
  // sphere gives 289.35. The tool is held to 289.35.
  let g = C.gcSphere(-22, 116, -20, 31); log('Bowditch 1208/1:', g.distNm.toFixed(1), g.initial.toFixed(2), g.final.toFixed(2));
  near(g.distNm, 4693.8, 0.6, 'distance'); ang(g.initial, 253.0, 0.06, 'initial course'); ang(g.final, 289.35, 0.01, 'final course');
  // Bowditch art. 1208 ex. 2: 28N 122W to 24S 151E -> 5,913.1 nm, initial 247.3
  g = C.gcSphere(28, -122, -24, 151); log('Bowditch 1208/2:', g.distNm.toFixed(1), g.initial.toFixed(2));
  near(g.distNm, 5913.1, 0.6, 'distance'); ang(g.initial, 247.3, 0.06, 'initial course');
  // AMS feature column (from Bowditch): 37-42N 123-04W to 34-50N 139-53E -> 4461.7 nm, N 57-46-15 W
  g = C.gcSphere(dm(37, 42), -dm(123, 4), dm(34, 50), dm(139, 53)); log('AMS:', g.distNm.toFixed(1), g.initial.toFixed(3));
  near(g.distNm, 4461.7, 0.6, 'distance'); ang(g.initial, 360 - dm(57, 46, 15), 0.02, 'initial course');
  // Bowditch art. 1211: from 28N 125W on N069W the vertex is 34-28.9N 164-15.9W. A point 2,500 nm along that track fixes the same great circle.
  const d = 2500 / 60 * Math.PI / 180, c = 291 * Math.PI / 180, p1 = 28 * Math.PI / 180;
  const p2 = Math.asin(Math.sin(p1) * Math.cos(d) + Math.cos(p1) * Math.sin(d) * Math.cos(c));
  const l2 = -125 + C.deg(Math.atan2(Math.sin(c) * Math.sin(d) * Math.cos(p1), Math.cos(d) - Math.sin(p1) * Math.sin(p2)));
  g = C.gcSphere(28, -125, C.deg(p2), l2); log('Bowditch vertex:', g.vertex.lat.toFixed(4), g.vertex.lon.toFixed(4));
  near(g.vertex.lat, dm(34, 28.9), 0.01, 'vertex latitude'); near(g.vertex.lon, -dm(164, 15.9), 0.01, 'vertex longitude'); ang(g.initial, 291, 1e-6, 'course');
});

test('rhumb line and meridional parts: Bowditch 2019 chapter 12 (Mercator sailing)', () => {
  // art. 1219 ex. 1: 32-14.7N 66-28.9W to 36-58.7N 75-42.2W -> M 2033.4 and 2377.1, C 301.8, D 538.9
  // Bowditch's printed meridional parts and the tool differ by up to 0.25 part in 7,000. That is the spheroid:
  // the same series with Clarke 1866 gives 7072.40 and 6226.07 (the printed 7072.4 and 6226.1), with WGS84 7072.65 and 6226.31.
  const series = (lat, e2) => { const a = 21600 / (2 * Math.PI), L = C.rad(lat), s = Math.sin(L);
    return a * Math.log(Math.tan(Math.PI / 4 + L / 2)) - a * (e2 * s + e2 * e2 * s ** 3 / 3 + e2 ** 3 * s ** 5 / 5); };
  for (const [lat, printed] of [[dm(32, 14.7), 2033.4], [dm(36, 58.7), 2377.1], [dm(75, 31.7), 7072.4], [dm(71, 32.9), 6226.1]]) {
    near(C.meridionalParts(lat), printed, 0.3, 'printed table'); near(C.meridionalParts(lat), series(lat, 0.00669437999014), 0.01, 'WGS84 series');
  }
  near(series(dm(75, 31.7), 0.006768658), 7072.4, 0.05, 'Clarke 1866'); near(series(dm(71, 32.9), 0.006768658), 6226.1, 0.05, 'Clarke 1866');
  let r = C.rhumb(dm(32, 14.7), -dm(66, 28.9), dm(36, 58.7), -dm(75, 42.2)); log('Bowditch 1219/1:', r.course.toFixed(2), r.distNm.toFixed(1), 'DMP', r.dmp.toFixed(1));
  ang(r.course, 301.8, 0.06, 'course'); near(r.dmp, 343.7, 0.15, 'meridional difference');
  // Distance: the book method takes one minute of latitude as one mile (D = l x sec C = 538.9). The tool measures the
  // real WGS84 meridian in 1,852 m miles, as ECDIS does, so it reads 537.3 here. Both are checked.
  near(284.0 / Math.cos(C.rad(r.course)), 538.9, 1.3, 'book method with the tool course'); near(r.distNm, 537.3, 0.1, 'WGS84 distance');
  near(r.distNm / 538.9, 1, 0.005, 'within half a percent of the book');
  // art. 1220: Cape Town 33-53.3S 018-23.1E to Ambrose Light 40-27.1N 073-49.4W -> 310.9, 6,811.5 nm
  r = C.rhumb(-dm(33, 53.3), dm(18, 23.1), dm(40, 27.1), -dm(73, 49.4)); log('Bowditch 1220:', r.course.toFixed(2), r.distNm.toFixed(1));
  ang(r.course, 310.9, 0.06, 'course'); near(r.distNm / 6811.5, 1, 0.005, 'within half a percent of the book');
});

test('WGS84 geodesic: Geoscience Australia test line Flinders Peak to Buninyong', () => {
  // 54,972.271 m, forward azimuth 306-52-05.37 (Vincenty test line used by Geoscience Australia / ICSM)
  const r = geodesic.Geodesic.WGS84.Inverse(-dm(37, 57, 3.7203), dm(144, 25, 29.5244), -dm(37, 39, 10.1561), dm(143, 55, 35.3839));
  log('Flinders-Buninyong:', r.s12.toFixed(3), 'm', C.norm360(r.azi1).toFixed(6));
  near(r.s12, 54972.271, 0.002, 'distance in metres'); ang(r.azi1, dm(306, 52, 5.37), 0.00001, 'azimuth');
});

test('amplitude and azimuth: published worked examples', () => {
  const amp = (lat, dec) => C.amplitude(lat, dec);
  near(Math.abs(amp(dm(50, 30), dm(20, 57.3)).amp), 34.2, 0.06, 'lat 50-30N dec 20-57.3N (E 34.2 N)');
  near(Math.abs(amp(-dm(48, 45), dm(10, 28.7)).amp), 16.0, 0.06, 'lat 48-45S dec 10-28.7N (E 16 N)');
  near(Math.abs(amp(-dm(30, 45), -dm(12, 15.6)).amp), 14.3, 0.06, 'lat 30-45S dec 12-15.6S (W 14.3 S)'); assert.equal(amp(-dm(30, 45), -dm(12, 15.6)).name, 'S');
  near(Math.abs(amp(7, dm(17, 24)).amp), 17.5, 0.06, 'lat 07N dec 17-24N (E 17.5 N)'); near(amp(7, dm(17, 24)).rise, 72.5, 0.06, 'true bearing 072.5');
  near(Math.abs(amp(39, -10).amp), 13, 0.5, 'lat 39 dec 10S (W 13 S)'); near(amp(39, -10).set, 257, 0.5, 'true bearing 257');
  near(amp(38, 18.23).set, 293.5, 0.15, 'lat 38N dec 18-14N: sunset 293.5 (Starpath)');
  // Bowditch art. 1704: lat 51-24.6N, dec N 19-40.4 -> table amplitude 32.7 (observed W 32.9 N, error 0.2)
  near(Math.abs(amp(dm(51, 24.6), dm(19, 40.4)).amp), 32.7, 0.06, 'Bowditch 1704');
  // Azimuth by the ABC formula: lat 47-30N, dec 10-42N, LHA 297-10.6 -> S 76.8 E = 103.2 T
  near(C.bodyAzAlt(dm(47, 30), dm(10, 42), dm(297, 10.6)).az, 103.2, 0.06, 'azimuth 103.2');
  // error naming from the same examples: true 103.2, compass 135.0 -> 31.8 W; rising 104 C and setting 243 C examples use the same rule
  near(C.compassError(103.2, 135.0), -31.8, 1e-9, 'compass error 31.8 W');
});

test('Sun position: one almanac-based exam question (found in search, source link not recorded)', () => {
  // 23 Sept 1992, 13h 50m 48s GMT, 00-00 120-27W: the Sun rose with true azimuth 090.3 (declination 0-18.6 S)
  const s = C.sunPosition(Date.UTC(1992, 8, 23, 13, 50, 48), 0, -dm(120, 27));
  log('1992 sunrise:', 'az', s.az.toFixed(2), 'dec', (s.dec * 60).toFixed(1) + "'", 'alt', s.alt.toFixed(2));
  near(s.az, 90.3, 0.06, 'azimuth'); near(s.dec * 60, -18.6, 0.3, 'declination in minutes'); near(s.alt, 0, 1.0, 'on the horizon');
});

test('CPA: published plotting examples', () => {
  // Crawford Nautical School radar plotting review: own 345 at 15 kn; 0830 329 x 9.0; 0836 326 x 6.0 -> CPA about one mile, relative speed about 30 kn
  const r = C.cpa(345, 15, 329, 9.0, 326, 6.0, 6); log('Crawford:', 'CPA', r.cpa.toFixed(2), 'SRM', r.relSpeed.toFixed(1));
  near(r.cpa, 1.0, 0.1, 'CPA'); near(r.relSpeed, 30, 0.5, 'relative speed');
  // Radar workbook arithmetic (not a full plot): relative speed 20 kn and 9.33 nm to run to the CPA -> 28 minutes
  const t = C.cpa(0, 0, 0, 11.33, 0, 9.33, 6); near(t.relSpeed, 20, 1e-9, 'relative speed'); near(t.tcpaMin, 28, 0.05, 'TCPA');
});

test('current triangle: published worked examples', () => {
  // Open Exam Prep (USCG OUPV): 6 kn boat, track 270, set 180 at 3 kn -> steer 300, make good about 5.2 kn
  let c = C.courseToSteer(270, 6, 180, 3); near(c.cts, 300, 0.01, 'course to steer'); near(c.smg, 5.2, 0.01, 'speed made good');
  // same source: steer 000 at 12 kn for an hour, fix 1.5 nm east of the DR -> CMG 007, set 090, drift 1.5
  let m = C.madeGood(0, 12, 90, 1.5); near(m.cmg, 7, 0.5, 'CMG 007');
  let s = C.setDrift(0, 12, 1, m.cmg, m.smg); ang(s.set, 90, 1e-6, 'set'); near(s.rate, 1.5, 1e-9, 'rate');
  // tdgil.com: 090 at 5 kn with a set of 323 at 0.7 kn -> CMG 083, 4.6 kn; to hold 090 steer 096 and make good 4.5 kn
  m = C.madeGood(90, 5, 323, 0.7); near(m.cmg, 83, 0.5, 'CMG 083'); near(m.smg, 4.6, 0.05, 'SMG 4.6');
  c = C.courseToSteer(90, 5, 323, 0.7); near(c.cts, 96, 0.5, 'CTS 096'); near(c.smg, 4.5, 0.05, 'SMG 4.5');
});

test('squat: Barrass formulas as published', () => {
  // Barrass, open water: Cb x Vk^2 / 100; confined channel: twice that. Derrett/Barrass style check values.
  near(C.squat(0.8, 10, false), 0.80, 1e-12, 'Cb 0.8, 10 kn, open'); near(C.squat(0.8, 10, true), 1.60, 1e-12, 'Cb 0.8, 10 kn, confined');
  near(C.squat(0.7, 12, false), 1.008, 1e-12, 'Cb 0.7, 12 kn, open');
});

test('propeller slip, fuel, FWA/DWA and list: published worked examples', () => {
  // engine distance sheet: 152 RPM x 97 h x 60 x 2.2958 m / 1852 = 1096.6 nm
  near(C.engineDistance(2.2958, 152 * 97 * 60), 1096.6, 0.05, 'engine distance');
  near(C.slipPercent(40, 34), 15, 1e-9, 'slip 15% (West Marine example)');
  // cube law exercise: 40 t/day at 12 kn -> 30.8 t/day at 11 kn; IMO rule of thumb: 10% slower = 27% less
  near(C.cubeLaw(40, 12, 11), 30.8, 0.05, 'cube law'); near(1 - C.cubeLaw(1, 10, 9), 0.27, 0.002, 'IMO 27%');
  // DWA: 153 x (1025-1013)/25 = 73 mm; 116 x (1025-1008)/25 = 78.88 mm; 150 x 15/25 = 90 mm; 254 at 1.009 -> 162.6 mm
  near(C.dwa(153, 1013), 73, 0.5, 'DWA 73'); near(C.dwa(116, 1008), 78.88, 0.005, 'DWA 78.88'); near(C.dwa(150, 1010), 90, 1e-9, 'DWA 90'); near(C.dwa(254, 1009), 162.56, 0.005, 'DWA 162.56');
  // list: 6000 t, KM 7.3, KG 6.7, 60 t moved 12 m -> GG1 0.12, GM 0.6, tan 0.2; and 12000 t, 60 t x 14 m -> 6.65 deg
  let s = C.stability(6000, 7.3, 6.7, 0, 60, 12); near(s.gg1, 0.12, 1e-12, 'GG1'); near(s.gmFluid, 0.6, 1e-9, 'GM'); near(Math.tan(C.rad(s.list)), 0.2, 1e-9, 'tan list');
  s = C.stability(12000, 7.3, 6.7, 0, 60, 14); near(s.gg1, 0.07, 1e-12, 'GG1'); near(s.list, 6.65, 0.01, 'list 6.65');
});

test('unit constants: NIST Handbook 44 and standard definitions', () => {
  near(C.convert('distance', 1, 'nm', 'm'), 1852, 0, 'nautical mile'); near(C.convert('distance', 1, 'nm', 'ft'), 6076.11549, 0.00001, 'nautical mile in feet');
  near(C.convert('speed', 1, 'kn', 'm/s'), 1852 / 3600, 1e-12, 'knot'); near(C.convert('depth', 1, 'fathom', 'ft'), 6, 1e-12, 'fathom');
  near(C.convert('mass', 1, 'long ton', 'kg'), 1016.047, 0.0005, 'long ton'); near(C.convert('mass', 1, 'short ton', 'kg'), 907.1848, 0.0005, 'short ton');
  near(C.convert('mass', 1, 'long ton', 'lb'), 2240, 1e-9, 'long ton in lb'); near(C.convertTemp(100, 'C', 'F'), 212, 1e-9, 'temperature');
});

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

// ---------------- second set of tools ----------------
test('Table 54B: Measurement Canada tables (API 2540, 1980) and a published bunker survey', () => {
  // https://ised-isde.canada.ca/site/measurement-canada/ : VCF_JetA.pdf (800 kg/m3), VCF_Gasoline_Ethanol-Blends.pdf (730), FCV_Diesel.pdf (840)
  const tables = { 800: [[-23, 1.0349], [-20, 1.0322], [-10, 1.0231], [-2, 1.0157], [0, 1.0139], [5, 1.0093], [10, 1.0046], [15, 1], [18, 0.9972], [20, 0.9953], [22.5, 0.9930], [25, 0.9907], [30, 0.9860], [35, 0.9813], [37.3, 0.9792], [40, 0.9766]],
    730: [[-20, 1.0432], [-10, 1.0310], [0, 1.0187], [5, 1.0125], [10, 1.0062], [15, 1], [20, 0.9937], [25, 0.9874], [30, 0.9811], [35, 0.9748], [40, 0.9684]],
    840: [[-30, 1.0375], [-25, 1.0334], [-20, 1.0293], [-10, 1.0210], [-6, 1.0176], [-5, 1.0168], [0, 1.0126], [5, 1.0084], [10, 1.0042], [15, 1], [20, 0.9958], [25, 0.9915], [27.5, 0.9894], [30, 0.9873], [33.3, 0.9845], [35, 0.9830], [40, 0.9788]] };
  let n = 0;
  for (const rho in tables) for (const [t, v] of tables[rho]) { near(Math.round(C.vcf54B(+rho, t).vcf * 1e4) / 1e4, v, 1e-9, `${rho} kg/m3 at ${t} C`); n++; }
  log(n, 'table values reproduced exactly');
  // Bunker survey example (Scribd 463110103): 161.68 m3 at 34 C, density 0.9903 -> VCF 0.9870, WCF 0.9892, 157.85 t
  const b = C.bunker(161.68, 34, 990.3); near(b.vcf, 0.9870, 1e-9, 'VCF'); near(b.wcf, 0.9892, 1e-9, 'WCF'); near(b.massAir, 157.85, 0.005, 'tonnes');
});

test('draught survey: UK P&I Club "Carefully to Carry" worked example and the Ocean Link guide', () => {
  // https://www.ukpandi.com/ ... UKPI_Carefully_to_Carry_2023_16.pdf
  let d = C.draftSurvey(4.61, 4.65, 4.93, 5.10, 5.58, 5.60, 181.8, 2.94, 1.44, 7.30);
  near(d.lbm, 171.56, 1e-9); near(d.fCorr, -0.0165, 0.00006); near(d.mCorr, -0.0081, 0.00006); near(d.aCorr, 0.0408, 0.00006);
  near(d.fc, 4.6135, 1e-9); near(d.mc, 5.0069, 1e-9); near(d.ac, 5.6308, 1e-9); near(d.trim, 1.0173, 1e-9); near(d.mmm, 5.0357, 0.00002);
  let r = C.draftSurveyDisp(d.trim, 181.8, 19894.37, 42.338, -4.331, 445.89, 435.26, 1.0185, 1.025);
  near(r.ftc, -102.61, 0.006, 'first trim correction'); near(r.stc, 3.03, 0.006, 'second trim correction'); near(r.dispTrim, 19794.79, 0.01); near(r.dispTrue, 19669.26, 0.01, 'true displacement');
  // Ocean Link guide "Draft survey basics": 20,931.6 t corrected, 20,788.7 t at 1.018, constant 303.7 t
  d = C.draftSurvey(5.62, 5.58, 6.47, 6.43, 7.33, 7.27, 180, 2.5, 0, 6);
  near(d.fc, 5.575, 0.0006); near(d.ac, 7.359, 0.0006); near(d.trim, 1.784, 0.0006); near(d.mmm, 6.454, 0.0006); near(d.deflection, -0.017, 0.0006);
  r = C.draftSurveyDisp(1.784, 180, 20861.4, 28.40, 2.10, 236.5, 224.0, 1.018, 1.025);
  near(r.ftc, 59.1, 0.05); near(r.stc, 11.1, 0.06); near(r.dispTrim, 20931.6, 0.06); near(r.dispTrue, 20788.7, 0.1); near(r.dispTrue - 11965 - 8520, 303.7, 0.1); // the guide rounds each step to 0.1 t
  // Scribd 456601441 sheet: trim -1.75 cm, LCF -2.934 (forward), TPC 32.37, LBP 150 -> +1.108 t; 18,988.11 t at 0.9960 -> 18,450.89 t
  r = C.draftSurveyDisp(-0.0175, 150, 18987, 32.37, -2.934, 0, 0, 0.9960, 1.025); near(r.ftc, 1.108, 0.001); near(r.dispTrue, 18450.89, 0.01);
  near(C.draftSurvey(2.470, 2.470, 3.980, 3.980, 5.495, 5.495, 150, 0, 0, 0).mmm, 3.981, 0.001);
});

test('LNG: International Gas Union conversion table and the S&P Global factor', () => {
  // IGU Natural Gas Conversion Guide (table reproduced by Gasgrid Finland, Annex 13): density 450 kg/m3, 1,300 Nm3 and 53.38 MMBtu per tonne
  let a = C.lng(1, 't', 450, 53.38, 1300); near(a.m3, 2.222, 0.0005); near(a.nm3, 1300, 1e-9); near(a.sm3, 1372, 0.5); near(a.mmbtu, 53.38, 1e-12);
  a = C.lng(1, 'm3', 450, 53.38, 1300); near(a.t, 0.450, 1e-12); near(a.nm3, 585, 1e-9); near(a.sm3, 617, 0.5); near(a.mmbtu, 24.02, 0.005);
  a = C.lng(1, 'nm3', 450, 53.38, 1300); near(a.t, 7.692e-4, 5e-8);
  // S&P Global conversion factors: 1 MMBtu = 0.019230769 mt LNG
  near(C.lng(1, 'mmbtu', 450, 52, 1300).t, 0.019230769, 5e-10);
  // a 174,000 m3 carrier at 0.1% a day boils off 174 m3, about 78 t, a day
  near(C.boilOff(174000, 173826, 24, 450).tDay, 78.3, 0.05);
});

test('dew point: US National Weather Service formula and published chart readings', () => {
  // https://www.weather.gov/media/epz/wxcalc/rhTdFromWetBulb.pdf worked by hand at 1013.25 hPa
  const f = x => (x - 32) / 1.8, F = c => c * 1.8 + 32;
  let p = C.psychro(f(78), f(65)); near(p.rh, 50, 1.0, 'Penn State: 78/65 F -> 50%'); near(F(p.dew), 58, 0.6, 'dew point 58 F');
  p = C.psychro(f(80), f(67)); near(p.rh, 50, 1.0, 'Nebraska: 80 F and 50% has a wet bulb of 67 F'); near(F(p.dew), 59, 1.0, 'dew point 59 F');
  p = C.psychro(25, 20, 1000); near(p.e, 6.112 * Math.exp(17.67 * 20 / 263.5) - 1000 * 0.00066 * 5 * 1.023, 1e-9, 'formula as printed');
});

test('sunrise, sunset and twilight: almanac worked examples', () => {
  const lmt = (ms, lon) => { const d = new Date(ms + lon / 15 * 3600000); return d.getUTCHours() * 60 + d.getUTCMinutes() + d.getUTCSeconds() / 60; };
  // US Navy Quartermaster course (NAVEDTRA 14220): 1 Sep 1994, 36-14N 069-26W, sunset LMT 1827 from the Nautical Almanac
  let lon = -(69 + 26 / 60), s = C.sunEvents(Date.UTC(1994, 8, 1, 5), 36 + 14 / 60, lon); log('1 Sep 1994 sunset LMT', (lmt(s.set, lon) / 60).toFixed(3));
  near(lmt(s.set, lon), 18 * 60 + 27, 1.6, 'sunset LMT 1827');
  // Ocean Navigator: evening civil twilight on 20 May at 16N is 1848 LMT
  for (const y of [2010, 2026]) { s = C.sunEvents(Date.UTC(y, 4, 20), 16, 0); near(lmt(s.civilEnd, 0), 18 * 60 + 48, 2.5, `civil twilight 1848 in ${y}`); }
});

test('rate of turn, horizon, rolling and encounter period: published figures', () => {
  // ROT = 57.3 V / (60 R): the bridge rule V/R gives 10 deg/min for 15 kn on 1.5 nm and 20 for 8 kn on 4 cables
  near(C.rateOfTurn(15, 1.5), 57.3 * 15 / (60 * 1.5), 0.001); near(C.rateOfTurn(15, 1.5) / 10, 1, 0.05); near(C.rateOfTurn(8, 0.4) / 20, 1, 0.05);
  near(C.rateOfTurn(12, 1), 0.955 * 12, 0.001, '0.955 x V / R'); near(C.turn(12, 1, 45).wheelOver, Math.tan(C.rad(22.5)), 1e-12, 'R tan(A/2)');
  // Bowditch Table 12, distance of the horizon (1.169 x square root of the height in feet = 2.1175 x square root of metres)
  const t12 = [[1.52, 2.6], [3.05, 3.7], [4.57, 4.5], [6.10, 5.2], [9.14, 6.4], [12.19, 7.4], [15.24, 8.3], [18.29, 9.1], [21.34, 9.8], [24.38, 10.5], [27.43, 11.1], [30.48, 11.7], [36.58, 12.8], [45.72, 14.3], [60.96, 16.5], [91.44, 20.3], [152.40, 26.2]];
  // The table's own formula: d = sqrt(2 R h / (6076.1 x 0.8279)), R = 3440.1 nm, h in feet -> 1.1695 x root(ft) = 2.118 x root(m)
  const kft = Math.sqrt(2 * 3440.1 / (6076.1 * 0.8279)), km = kft * Math.sqrt(3.28084);
  for (const [m, nm] of t12) near(C.horizon(m, km), nm, 0.051, `Table 12 at ${m} m`);
  near(km, C.HORIZON.high, 0.002, 'Bowditch table in metres is 2.12');
  // Bowditch appendix B: visible horizon 2.07 x root(m), radar horizon 2.21 x root(m); RYA and Reeds use 2.08; IALA 2.03
  near(C.HORIZON.visible, 2.07, 0.011); near(C.HORIZON.radar, 1.22 * Math.sqrt(3.28084), 0.002); near(C.horizon(9, C.HORIZON.radar), 6.63, 1e-9);
  // 2008 IS Code: C = 0.373 + 0.023 (B/d) - 0.043 (Lwl/100), T = 2 C B / sqrt(GM)
  near(C.rollCoeff(32.2, 12, 220), 0.373 + 0.023 * 32.2 / 12 - 0.043 * 2.2, 1e-15); near(C.rollPeriod(32.2, 12, 220, 2.5), 13.85, 0.005);
  // MSC.1/Circ.1228: TE = 3 TW^2 / (3 TW + V cos a); wave length 1.56 TW^2
  near(C.encounterPeriod(10, 15, 0), 300 / 45, 1e-12); near(C.encounterPeriod(8, 12, 180), 192 / 12, 1e-12); near(C.waveLength(8), 99.84, 1e-9);
});

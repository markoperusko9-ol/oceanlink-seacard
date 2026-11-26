// Second set of tools: sunrise and twilight, bunkers, draught survey, LNG, dew point, rate of turn, horizon, rolling.
// Run: node --test scripts/tools/tests/
const test = require('node:test');
const assert = require('node:assert');
const path = require('path');
const C = require(path.join(__dirname, '../../../tools/assets/calc.js'));
const SE = require('./fixtures_sun_events.json');
const near = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg || ''} got ${a}, want ${b} ±${tol}`);
let seed = 987654321;
const rnd = (a, b) => { seed = (seed * 1664525 + 1013904223) % 4294967296; return a + (b - a) * seed / 4294967296; };

test('sunrise, sunset, twilight and meridian passage against astropy (275 days, 2026-2039)', () => {
  const max = { transit: 0, rise: 0, civil: 0, naut: 0 }; let n = 0, missing = 0;
  for (const f of SE) {
    const s = C.sunEvents(f.start, f.lat, f.lon);
    assert.ok(s, 'meridian passage found');
    max.transit = Math.max(max.transit, Math.abs(s.transit - f.transit) / 1000);
    near(s.transitAlt, f.transitAlt, 0.01, 'altitude at meridian passage');
    for (const [key, am, pm] of [['rise', 'rise', 'set'], ['civil', 'civilBegin', 'civilEnd'], ['naut', 'nautBegin', 'nautEnd']]) {
      for (const [mine, ref] of [[s[am], f[key + 'AM']], [s[pm], f[key + 'PM']]]) {
        if (ref === null || mine === null) {
          // one says the limit is crossed and the other not: only allowed when the Sun grazes the limit
          if ((ref === null) !== (mine === null)) { missing++; const lim = C.SUN_LIMITS[key]; assert.ok(Math.abs(f.transitAlt - lim) < 0.03 || Math.abs(s.lowAlt - lim) < 0.03, `event presence differs away from a grazing case: ${JSON.stringify(f)}`); }
          continue;
        }
        const dt = Math.abs(mine - ref) / 1000; n++;
        if (Math.abs(f.lat) <= 62) { max[key] = Math.max(max[key], dt); }
        else assert.ok(dt < 240, `high latitude event within 4 minutes: ${dt}s ${JSON.stringify(f)}`);
      }
    }
  }
  console.log(`   max difference up to 62 degrees latitude: meridian passage ${max.transit.toFixed(1)} s, sunrise/sunset ${max.rise.toFixed(1)} s, civil twilight ${max.civil.toFixed(1)} s, nautical twilight ${max.naut.toFixed(1)} s (${n} events, ${missing} grazing)`);
  assert.ok(max.transit < 3 && max.rise < 20 && max.civil < 20 && max.naut < 30);
});

test('sun events: polar day and polar night, and the order of events', () => {
  const up = C.sunEvents(Date.UTC(2027, 5, 21, 0) - 3600000, 78, 15);       // Svalbard, midsummer
  assert.equal(up.rise, null); assert.equal(up.set, null); assert.ok(up.transitAlt > 0 && up.lowAlt > 0);
  const down = C.sunEvents(Date.UTC(2027, 11, 21, 0) - 3600000, 78, 15);    // Svalbard, midwinter
  assert.equal(down.rise, null); assert.equal(down.civilBegin, null); assert.ok(down.transitAlt < -6);
  for (let i = 0; i < 300; i++) {
    const lat = rnd(-60, 60), lon = rnd(-180, 180), start = Date.UTC(2026, 0, 1) + Math.floor(rnd(0, 5000)) * 86400000 - Math.round(lon / 15) * 3600000;
    const s = C.sunEvents(start, lat, lon);
    assert.ok(s.transit >= start - 1 && s.transit < start + 86400000 + 300000, 'meridian passage inside the day');
    const seq = [s.nautBegin, s.civilBegin, s.rise, s.transit, s.set, s.civilEnd, s.nautEnd].filter(x => x !== null);
    for (let k = 1; k < seq.length; k++) assert.ok(seq[k] > seq[k - 1], 'events in order');
    if (s.rise !== null) { near(C.sunPosition(s.rise, lat, lon).alt, -50 / 60, 0.0005, 'altitude at sunrise'); near(C.sunPosition(s.set, lat, lon).alt, -50 / 60, 0.0005, 'altitude at sunset'); }
    if (s.civilEnd !== null) near(C.sunPosition(s.civilEnd, lat, lon).alt, -6, 0.0005, 'altitude at end of civil twilight');
    near(Math.abs(C.norm180(C.sunPosition(s.transit, lat, lon).lha)), 0, 0.0005, 'LHA zero at meridian passage');
    // altitude at meridian passage = 90 - |lat - dec|
    near(s.transitAlt, 90 - Math.abs(lat - s.dec), 0.0005, 'meridian altitude');
  }
});

test('Table 54B: unity at 15 C, product groups, limits and the bunker sum', () => {
  for (const rho of [653, 700, 770, 771, 787.9, 788, 838.9, 839, 900, 991, 1075]) near(C.vcf54B(rho, 15).vcf, 1, 1e-15, 'VCF at 15 C');
  assert.equal(C.vcf54B(652.9, 20), null); assert.equal(C.vcf54B(1075.1, 20), null);
  assert.equal(C.vcf54B(991, 50).group, 'Fuel oils'); assert.equal(C.vcf54B(800, 50).group, 'Jet fuels and kerosenes');
  assert.equal(C.vcf54B(780, 50).group, 'Transition zone'); assert.equal(C.vcf54B(730, 50).group, 'Gasolines');
  assert.equal(C.vcf54B(991, 150).inRange, true); assert.equal(C.vcf54B(991, 150.1).inRange, false); assert.equal(C.vcf54B(991, -18.1).inRange, false);
  assert.equal(C.vcf54B(800, 125.1).inRange, false); assert.equal(C.vcf54B(730, 90.1).inRange, false);
  for (let i = 0; i < 500; i++) {
    const rho = rnd(653, 1075), t = rnd(-18, 90), f = C.vcf54B(rho, t);
    assert.ok((t > 15) === (f.vcf < 1), 'oil expands when warm');
    assert.ok(C.vcf54B(rho, t + 1).vcf < f.vcf, 'VCF falls as temperature rises');
    const b = C.bunker(1000, t, rho);
    near(b.vcf, f.vcf, 0.00005, 'four-decimal VCF'); near(b.gsv, 1000 * b.vcf, 0.0005 + 1e-9, 'standard volume to the litre'); near(b.massAir, b.gsv * (rho / 1000 - 0.0011), 1e-9); near(b.massVac - b.massAir, b.gsv * 0.0011, 1e-9);
  }
  // the groups meet without a jump larger than the table's own step at the class boundaries
  near(C.vcf54B(838.99, 40).vcf, C.vcf54B(839, 40).vcf, 0.0008, 'jet/fuel oil boundary'); near(C.vcf54B(770, 40).vcf, C.vcf54B(770.01, 40).vcf, 0.0003, 'gasoline/transition boundary');
});

test('draught survey: straight-line geometry, signs and the reverse problem', () => {
  for (let i = 0; i < 400; i++) {
    // build a ship with a known straight keel line plus hog or sag, then read the marks
    const lbp = rnd(90, 330), xf = rnd(-3, 8), xa = rnd(-3, 12), xm = rnd(-4, 4), dAP = rnd(4, 15), trim = rnd(-2, 4), sag = rnd(-0.15, 0.15), heel = rnd(-0.1, 0.1);
    const dFP = dAP - trim, at = x => dAP + (dFP - dAP) * x / lbp; // x from the AP
    const F = at(lbp - xf), A = at(xa), M = at(lbp / 2 - xm) + sag;
    const d = C.draftSurvey(F + heel, F - heel, M + heel, M - heel, A + heel, A - heel, lbp, xf, xm, xa);
    // the tool carries corrected draughts to 0.1 mm, so answers agree to that rounding
    near(d.fc, dFP, 5.1e-5, 'draught at FP'); near(d.ac, dAP, 5.1e-5, 'draught at AP'); near(d.mc, (dFP + dAP) / 2 + sag, 5.1e-5, 'draught at midships');
    near(d.trim, trim, 1.1e-4, 'true trim'); near(d.deflection, sag, 1.1e-4, 'hog or sag'); near(d.mmm, (dFP + dAP) / 2 + 0.75 * sag, 5.1e-5, 'mean of means');
  }
  const r = (trim, lcf) => C.draftSurveyDisp(trim, 180, 20000, 30, lcf, 240, 228, 1.025, 1.025);
  assert.ok(r(1, 2).ftc > 0 && r(1, -2).ftc < 0 && r(-1, 2).ftc < 0 && r(-1, -2).ftc > 0, 'first trim correction sign: plus when the LCF is toward the deeper end');
  assert.ok(r(1, 2).stc > 0 && r(-1, 2).stc > 0, 'second trim correction always added'); near(r(-1, 2).stc, r(1, 2).stc, 1e-12);
  near(r(0, 5).dispTrue, 20000, 1e-9, 'even keel, table density: no correction');
  near(C.draftSurveyDisp(0, 180, 20000, 30, 0, 240, 228, 1.000, 1.025).dispTrue, 20000 / 1.025, 0.005, 'fresh water');
  // the column adds up as written: displacement + the two corrections as printed, then the density line from that
  const col = C.draftSurveyDisp(-0.0313, 100, 19894.37, 42.338, -4.331, 445.89, 435.26, 1.0185, 1.025);
  assert.equal(col.ftc, 5.74); assert.equal(col.stc, 0.01); assert.equal(col.dispTrim, 19900.12); assert.equal(col.dispTrue, C.roundHalfUp(19900.12 * 1.0185 / 1.025, 2)); assert.equal(col.densityCorr, C.roundHalfUp(col.dispTrue - 19900.12, 2));
});

test('LNG conversions close the loop in every unit, boil-off arithmetic', () => {
  for (let i = 0; i < 300; i++) {
    const dens = rnd(420, 480), heat = rnd(50, 54), gas = rnd(1250, 1400), q = rnd(1, 200000);
    for (const u of ['m3', 't', 'mmbtu', 'nm3']) {
      const a = C.lng(q, u, dens, heat, gas), key = u;
      near(a[key], q, q * 1e-12, 'same unit back');
      for (const v of ['m3', 't', 'mmbtu', 'nm3']) near(C.lng(a[v], v, dens, heat, gas)[key], q, q * 1e-11, `${u} to ${v} and back`);
      near(a.t, a.m3 * dens / 1000, a.t * 1e-12); near(a.mmbtu, a.t * heat, a.mmbtu * 1e-12); near(a.sm3 * 0.9476, a.nm3, a.nm3 * 1e-12); near(a.gj, a.mmbtu * 1.05505585262, a.gj * 1e-12);
    }
  }
  const b = C.boilOff(170000, 169660, 48, 450); near(b.m3Day, 170, 1e-9); near(b.pctDay, 0.1, 1e-12); near(b.tDay, 76.5, 1e-9); near(b.lost, 340, 1e-9);
});

test('dew point: saturated air, physical limits and the definition of dew point', () => {
  for (let i = 0; i < 400; i++) {
    const dry = rnd(0, 45), wet = dry - rnd(0, Math.min(dry, 14)), p = C.psychro(dry, wet);
    if (!p) continue;
    assert.ok(p.dew <= wet + 1e-9 && wet <= dry, 'dew point <= wet bulb <= dry bulb'); assert.ok(p.rh > 0 && p.rh <= 100 + 1e-9);
    near(C.satVp(p.dew), p.e, 1e-9, 'vapour pressure at the dew point equals the actual vapour pressure');
    assert.ok(C.psychro(dry, wet - 0.5) === null || C.psychro(dry, wet - 0.5).dew < p.dew, 'bigger depression, drier air');
  }
  const s = C.psychro(20, 20); near(s.rh, 100, 1e-12); near(s.dew, 20, 1e-9);
  assert.equal(C.psychro(20, 20.1), null); assert.equal(C.psychro(40, 5), null);
});

test('dew point against the ASHRAE method (psychrolib), dew points at or above freezing', () => {
  const PS = require('./fixtures_psychro.json'); let maxDew = 0, maxRh = 0, n = 0;
  for (const f of PS) {
    const p = C.psychro(f.dry, f.wet); if (!p || f.dew < 0) continue;
    n++; maxDew = Math.max(maxDew, Math.abs(p.dew - f.dew)); maxRh = Math.max(maxRh, Math.abs(p.rh - f.rh));
  }
  console.log(`   max difference from ASHRAE: dew point ${maxDew.toFixed(2)} C, relative humidity ${maxRh.toFixed(2)} points (${n} cases)`);
  assert.ok(n > 500 && maxDew < 0.75 && maxRh < 1.1);
});

test('rate of turn, horizon and rolling: definitions hold', () => {
  for (let i = 0; i < 300; i++) {
    const v = rnd(2, 25), r = rnd(0.1, 5), a = rnd(5, 175), rot = C.rateOfTurn(v, r), t = C.turn(v, r, a);
    near(C.turnRadius(v, rot), r, 1e-12); near(t.minutes * rot, a, 1e-9, 'time x rate = course change'); near(t.arc, v * t.minutes / 60, 1e-12);
    // the wheel-over distance is the tangent length: the turn centre is r from both tracks
    near(Math.hypot(t.wheelOver, r) * Math.cos(Math.atan2(r, t.wheelOver) * 2 - C.rad(180 - a)), Math.hypot(t.wheelOver, r), 1e-9);
    const h = rnd(1, 80); near(C.horizon(h) ** 2 / h, 2.08 * 2.08, 1e-9); near(C.horizon(h, C.HORIZON.radar), 2.21 * Math.sqrt(h), 1e-12);
    const B = rnd(15, 60), d = rnd(5, 22), L = rnd(100, 400), gm = rnd(0.3, 8), T = C.rollPeriod(B, d, L, gm);
    near(C.gmFromRoll(B, d, L, T), gm, 1e-9); near(T, 2 * (0.373 + 0.023 * B / d - 0.043 * L / 100) * B / Math.sqrt(gm), 1e-12);
    // encounter period from first principles: crests 1.56 Tw^2 metres apart moving at 1.56 Tw m/s (deep water), ship speed in m/s
    const tw = rnd(4, 18), al = rnd(0, 180), vms = v * 1852 / 3600, lam = 1.56 * tw * tw, c = 1.56 * tw, te = lam / (c + vms * Math.cos(C.rad(al)));
    // IMO rounds the wave speed of 3.03 Tw knots to 3 Tw, so the two agree closely in head and beam seas only
    if (al <= 90) near(C.encounterPeriod(tw, v, al) / te, 1, 0.011, 'IMO rounded formula within 1.1 percent of first principles in head and beam seas');
    else if (v * -Math.cos(C.rad(al)) < 2.9 * tw) assert.ok(C.encounterPeriod(tw, v, al) >= te && te > tw - 1e-9, 'following sea: longer than the wave period, IMO figure on the long side');
  }
  near(C.encounterPeriod(10, 0, 0), 10, 1e-12); near(C.encounterPeriod(10, 20, 90), 10, 1e-9); assert.equal(C.encounterPeriod(10, 30, 180), Infinity); assert.ok(C.encounterPeriod(10, 35, 180) < 0);
  near(C.waveLength(10), 156, 1e-12);
});

test('Table 54B reproduces three official tables value for value (440 factors, Measurement Canada)', () => {
  const tables = require('./fixtures_vcf_tables.json'); let n = 0;
  for (const t of tables) for (const [temp, printed] of t.rows) {
    const got = C.bunker(1000, temp, t.rho15).vcf; n++;
    assert.ok(Math.abs(got - printed) < 1e-9, `${t.name} at ${temp} C: tool ${got}, printed ${printed}`);
  }
  assert.strictEqual(n, 440);
  // the three factors that sit on a rounding edge and need the coefficient carried to seven decimals, as the standard does
  assert.strictEqual(C.bunker(1, -38.5, 710).vcf, 1.0681); assert.strictEqual(C.bunker(1, -36, 710).vcf, 1.065); assert.strictEqual(C.bunker(1, -9.5, 710).vcf, 1.0316);
});

test('true wind: course over the ground moves the ship, heading aims the anemometer', () => {
  const a = C.trueWind(45, 14, 30, 25), b = C.trueWind(45, 14, 30, 25, 52);
  assert.ok(Math.abs(a.dir - 103.53) < 0.01 && Math.abs(a.speed - 14.656) < 0.001);
  assert.ok(Math.abs(b.dir - 99.31) < 0.01 && Math.abs(b.speed - 13.291) < 0.001);
  assert.strictEqual(b.apparentFrom, 75);
});

test('course to steer when the cross-track stream equals the ship\'s speed (boundary audit of 26 Nov 2026)', () => {
  // Track 000, 5 kn, stream 330 at 10 kn: the cross-track part is exactly 5 kn, so she steers 090 and makes 10 cos 30 along the track.
  // sin(330 deg) is -0.5000000000000004 in floating point, which used to read as "stream too strong".
  let c = C.courseToSteer(0, 5, 330, 10); assert.ok(c, 'track can be held'); assert.ok(Math.abs(c.cts - 90) < 1e-6); assert.ok(Math.abs(c.smg - 10 * Math.cos(Math.PI / 6)) < 1e-9);
  c = C.courseToSteer(330, 5, 0, 10); assert.ok(c, 'track can be held'); assert.ok(Math.abs(c.cts - 240) < 1e-6);
  c = C.courseToSteer(68.4, 18.5, 38.4, 37); assert.ok(c, 'track can be held'); assert.ok(Math.abs(c.cts - 158.4) < 1e-6);
  // Stream abeam and as fast as the ship: all her speed goes into holding the track, none along it.
  assert.equal(C.courseToSteer(0, 10, 90, 10), null); assert.equal(C.courseToSteer(0, 10, 270, 10), null); assert.equal(C.courseToSteer(43, 19.5, 133, 19.5), null);
  // A hair past the limit is still refused, a hair inside still works.
  assert.equal(C.courseToSteer(0, 5, 330, 10.1), null); assert.ok(C.courseToSteer(0, 5, 330, 9.9));
});

test('rounding half up on the decimal value, as on paper (boundary audit of 26 Nov 2026)', () => {
  const R = C.roundHalfUp;
  // decimal halves that binary numbers hold a hair low
  for (const [x, dp, want] of [[10.09875, 4, 10.0988], [1.005, 2, 1.01], [2.675, 2, 2.68], [0.615, 2, 0.62], [1.45, 1, 1.5], [0.15, 1, 0.2], [0.35, 1, 0.4], [10.15, 1, 10.2], [1.405, 2, 1.41], [1.095, 2, 1.1], [2.5, 0, 3], [0.5, 0, 1]]) assert.equal(R(x, dp), want, `${x} to ${dp} places`);
  // sums that come out a hair off a half: 5 mm net clearance, a GM of 5 mm, 50 kg of fuel short
  assert.equal(R(27.44 + 3.04 - 10.15 - 20.325, 2), 0.01); assert.equal(R(24.40 + 0.43 - 17.30 - 0.58 - 6.945, 2), 0.01); assert.equal(R(10.3 + 0.7 - 10.1 - 0.7 - 0.2, 2), 0);
  assert.equal(R(-0.05 - 1e-15, 1), -0.1); assert.equal(R(-0.004, 2), 0); assert.ok(Object.is(R(-0.004, 2), 0), 'no minus zero');
  // near misses stay where they are
  assert.equal(R(39103.992549996045, 4), 39103.9925); assert.equal(R(1.00499999, 2), 1); assert.equal(R(0.0049, 2), 0); assert.equal(R(109375.8577619615, 2), 109375.86);
  // away from halves it is ordinary rounding, for small, large, negative and odd figures alike
  let seed = 7; const rnd = () => { seed = (seed * 1664525 + 1013904223) % 4294967296; return seed / 4294967296; };
  for (let i = 0; i < 200000; i++) { const dp = Math.floor(rnd() * 5), x = (rnd() - 0.4) * Math.pow(10, Math.floor(rnd() * 9) - 2), k = Math.pow(10, dp); if (Math.abs(Math.abs(x * k) % 1 - 0.5) > 1e-4) assert.equal(R(x, dp), Math.round(Math.abs(x) * k) / k * (x < 0 && Math.round(Math.abs(x) * k) ? -1 : 1), `${x} to ${dp}`); }
  assert.equal(R(1e-7, 2), 0); assert.equal(R(1e21, 2), 1e21); assert.ok(Number.isNaN(R(NaN, 2))); assert.equal(R(Infinity, 1), Infinity); assert.equal(R(0, 3), 0);
});

test('draught survey: a corrected draught exactly on a half is rounded up, as on the surveyor\'s sheet', () => {
  // Marks 6 m abaft the FP, 2 m abaft the AP, 4 m forward of midships, LBP 100 m: midships comes to 10.10 - 0.00125 = 10.09875.
  const s = C.draftSurvey(10.02, 10.02, 10.10, 10.10, 9.99, 9.99, 100, 6, -4, -2);
  assert.equal(s.mc, 10.0988); assert.equal(s.fc, 10.0219); assert.equal(s.ac, 9.9906); near(s.mmm, 10.0756625, 1e-12, 'mean of means');
  // the UK P&I Club example is unchanged
  const u = C.draftSurvey(4.61, 4.65, 4.93, 5.10, 5.58, 5.60, 181.8, 2.94, 1.44, 7.30); assert.equal(u.fc, 4.6135); assert.equal(u.mc, 5.0069); assert.equal(u.ac, 5.6308);
});

test('bunker: each line is worked from the figure printed on the line above, as on paper', () => {
  const b = C.bunker(161.68, 34, 990.3);
  assert.equal(b.gsv, 159.578); near(b.wcf, 0.9892, 1e-12, 'weight factor'); assert.equal(C.roundHalfUp(b.massAir, 2), 157.85); near(b.massAir, 159.578 * 0.9892, 1e-9, 'weight in air');
  // whatever the factor, the litre figure is the product rounded half up, and the tonnes come from the litre figure
  const c = C.bunker(2743.21, 50, 985); assert.equal(c.gsv, C.roundHalfUp(2743.21 * c.vcf, 3)); near(c.massAir, c.gsv * (0.985 - 0.0011), 1e-9, 'weight in air from the litre figure');
  // a standard volume and a weight that fall exactly on a half are rounded up: 250 m3 at 15 C, density 0.9910, gives 250.000 x 0.9899 = 247.475
  const d = C.bunker(250, 15, 991); assert.equal(d.vcf, 1); assert.equal(d.gsv, 250); assert.equal(C.roundHalfUp(d.massAir, 2), 247.48);
});

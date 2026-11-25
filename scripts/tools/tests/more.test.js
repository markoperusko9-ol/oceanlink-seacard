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
    near(b.vcf, f.vcf, 0.00005, 'four-decimal VCF'); near(b.gsv, 1000 * b.vcf, 1e-9); near(b.massAir, b.gsv * (rho / 1000 - 0.0011), 1e-9); near(b.massVac - b.massAir, b.gsv * 0.0011, 1e-9);
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
  near(C.draftSurveyDisp(0, 180, 20000, 30, 0, 240, 228, 1.000, 1.025).dispTrue, 20000 / 1.025, 1e-9, 'fresh water');
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

/* Ocean Link seafarer tools: calculation library.
   Pure functions only (no DOM). Every function here is covered by
   scripts/tools/tests/calc.test.js. Angles in degrees, speeds in knots,
   distances in nautical miles unless a name says otherwise. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.OLCalc = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var D2R = Math.PI / 180, R2D = 180 / Math.PI;
  var NM = 1852; // metres in one international nautical mile
  function rad(d) { return d * D2R; }
  function deg(r) { return r * R2D; }
  function norm360(x) { x = x % 360; return x < 0 ? x + 360 : x; }
  function norm180(x) { x = norm360(x); return x > 180 ? x - 360 : x; }
  function clamp(x, a, b) { return x < a ? a : x > b ? b : x; }
  function hypot(x, y) { return Math.sqrt(x * x + y * y); }
  /* Direction (deg true) of a vector given as east (x) and north (y) parts. */
  function dirOf(x, y) { return norm360(deg(Math.atan2(x, y))); }

  /* ---------- Sun (Meeus, Astronomical Algorithms ch. 25 low-accuracy theory with sidereal time) ---------- */
  /* ms: UTC time in milliseconds since 1970. lat +N, lon +E.
     Returns declination, GHA, LHA, true altitude of the centre (no refraction) and true azimuth. */
  function sunPosition(ms, lat, lon) {
    var jd = ms / 86400000 + 2440587.5;
    var T = (jd - 2451545) / 36525;
    var L0 = norm360(280.46646 + T * (36000.76983 + 0.0003032 * T));
    var M = 357.52911 + T * (35999.05029 - 0.0001537 * T);
    var e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T);
    var C = Math.sin(rad(M)) * (1.914602 - T * (0.004817 + 0.000014 * T)) +
      Math.sin(rad(2 * M)) * (0.019993 - 0.000101 * T) +
      Math.sin(rad(3 * M)) * 0.000289;
    var om = 125.04 - 1934.136 * T;
    var lam = L0 + C - 0.00569 - 0.00478 * Math.sin(rad(om));
    var eps0 = 23 + (26 + (21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60) / 60;
    var eps = eps0 + 0.00256 * Math.cos(rad(om));
    var dec = deg(Math.asin(Math.sin(rad(eps)) * Math.sin(rad(lam))));
    // GHA = Greenwich apparent sidereal time minus the Sun's apparent right ascension.
    var ra = deg(Math.atan2(Math.cos(rad(eps)) * Math.sin(rad(lam)), Math.cos(rad(lam))));
    var gmst = 280.46061837 + 360.98564736629 * (jd - 2451545) + 0.000387933 * T * T - T * T * T / 38710000;
    var gast = gmst - 0.00478 * Math.sin(rad(om)) * Math.cos(rad(eps));
    var gha = norm360(gast - ra);
    var lha = norm360(gha + lon);
    var out = bodyAzAlt(lat, dec, lha);
    out.dec = dec; out.gha = gha; out.lha = lha;
    return out;
  }

  /* True azimuth and altitude of a body from latitude, declination and LHA (LHA measured west). */
  function bodyAzAlt(lat, dec, lha) {
    var p = rad(lat), d = rad(dec), h = rad(lha);
    var sinAlt = Math.sin(p) * Math.sin(d) + Math.cos(p) * Math.cos(d) * Math.cos(h);
    var alt = deg(Math.asin(clamp(sinAlt, -1, 1)));
    var az = norm360(deg(Math.atan2(-Math.cos(d) * Math.sin(h),
      Math.sin(d) * Math.cos(p) - Math.cos(d) * Math.sin(p) * Math.cos(h))));
    return { az: az, alt: alt };
  }

  /* Amplitude: sin A = sin dec / cos lat. Returns the angle from E (rising) or W (setting),
     positive towards north, and the true bearings at rising and setting. null if the body
     does not rise or set at this latitude. */
  function amplitude(lat, dec) {
    var s = Math.sin(rad(dec)) / Math.cos(rad(lat));
    if (!(Math.abs(s) <= 1) || Math.abs(lat) >= 90) return null;
    var a = deg(Math.asin(s));
    return { amp: a, name: a >= 0 ? 'N' : 'S', rise: norm360(90 - a), set: norm360(270 + a) };
  }

  /* Compass error = true minus compass. Positive = East (compass reads low), negative = West. */
  function compassError(trueBrg, compassBrg) { return norm180(trueBrg - compassBrg); }

  /* ---------- True wind ---------- */
  /* True wind as meteorologists define it (Smith, Bourassa and Sharp 1999): the wind over the fixed earth.
     heading deg true turns the anemometer's relative direction into a true bearing; the ship's movement
     is her course and speed over the ground. relDir = wind direction relative to the bow (0-360
     clockwise, where it comes FROM). course defaults to the heading when it is not given. */
  function trueWind(heading, shipSpeed, relDir, relSpeed, course) {
    if (course === undefined || course === null || isNaN(course)) course = heading;
    var af = rad(heading + relDir), c = rad(course);
    var x = relSpeed * Math.sin(af) - shipSpeed * Math.sin(c);
    var y = relSpeed * Math.cos(af) - shipSpeed * Math.cos(c);
    var sp = hypot(x, y);
    return { dir: sp < 1e-9 ? null : dirOf(x, y), speed: sp, apparentFrom: norm360(heading + relDir) };
  }

  var BEAUFORT = [
    [1, 'Calm'], [3, 'Light air'], [6, 'Light breeze'], [10, 'Gentle breeze'], [16, 'Moderate breeze'],
    [21, 'Fresh breeze'], [27, 'Strong breeze'], [33, 'Near gale'], [40, 'Gale'], [47, 'Strong gale'],
    [55, 'Storm'], [63, 'Violent storm'], [Infinity, 'Hurricane']
  ];
  /* Beaufort force from wind speed in knots (rounded to the whole knot, WMO table). */
  function beaufort(knots) {
    var k = Math.round(knots);
    if (k < 1) return { force: 0, desc: 'Calm' };
    for (var i = 1; i < BEAUFORT.length; i++) if (k <= BEAUFORT[i][0]) return { force: i, desc: BEAUFORT[i][1] };
  }

  /* ---------- Speed, distance, time ---------- */
  function steamingHours(distance, speed) { return distance / speed; }
  /* depLocalMs: departure clock time written as if it were UTC (ms). Offsets in hours, east +. */
  function eta(depLocalMs, depOffset, arrOffset, distance, speed) {
    var hours = distance / speed;
    var utc = depLocalMs - depOffset * 3600000 + hours * 3600000;
    return { hours: hours, utcMs: utc, arrLocalMs: utc + arrOffset * 3600000 };
  }
  function requiredSpeed(depLocalMs, depOffset, arrLocalMs, arrOffset, distance) {
    var hours = ((arrLocalMs - arrOffset * 3600000) - (depLocalMs - depOffset * 3600000)) / 3600000;
    return { hours: hours, speed: hours > 0 ? distance / hours : null };
  }

  /* ---------- Great circle on the sphere (exam method: 1 minute of arc = 1 nm) ---------- */
  function vec(lat, lon) {
    var p = rad(lat), l = rad(lon);
    return [Math.cos(p) * Math.cos(l), Math.cos(p) * Math.sin(l), Math.sin(p)];
  }
  function angBetween(a, b) {
    var cx = a[1] * b[2] - a[2] * b[1], cy = a[2] * b[0] - a[0] * b[2], cz = a[0] * b[1] - a[1] * b[0];
    return Math.atan2(Math.sqrt(cx * cx + cy * cy + cz * cz), a[0] * b[0] + a[1] * b[1] + a[2] * b[2]);
  }
  function gcSphere(lat1, lon1, lat2, lon2) {
    var p1 = rad(lat1), p2 = rad(lat2), dl = rad(norm180(lon2 - lon1));
    var a = vec(lat1, lon1), b = vec(lat2, lon2);
    var d = angBetween(a, b);
    var out = { distNm: deg(d) * 60, arcDeg: deg(d), initial: null, final: null, vertex: null };
    if (d < 1e-12) return out;
    out.initial = norm360(deg(Math.atan2(Math.sin(dl) * Math.cos(p2),
      Math.cos(p1) * Math.sin(p2) - Math.sin(p1) * Math.cos(p2) * Math.cos(dl))));
    out.final = norm360(deg(Math.atan2(Math.sin(dl) * Math.cos(p1),
      -Math.cos(p2) * Math.sin(p1) + Math.sin(p2) * Math.cos(p1) * Math.cos(dl))));
    // Vertex: the point of the great circle nearest a pole.
    var n = [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
    var nl = Math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]);
    if (nl < 1e-12) return out; // antipodal: track not defined
    n = [n[0] / nl, n[1] / nl, n[2] / nl];
    var v = [-n[2] * n[0], -n[2] * n[1], 1 - n[2] * n[2]];
    var vl = Math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
    if (vl < 1e-9) return out; // sailing along the equator: no vertex
    v = [v[0] / vl, v[1] / vl, v[2] / vl];
    var vs = [-v[0], -v[1], -v[2]];
    function onTrack(q) { return Math.abs(angBetween(a, q) + angBetween(q, b) - d) < 1e-9; }
    function pack(q, on) {
      return { lat: deg(Math.asin(clamp(q[2], -1, 1))), lon: deg(Math.atan2(q[1], q[0])), onTrack: on };
    }
    if (onTrack(v)) out.vertex = pack(v, true);
    else if (onTrack(vs)) out.vertex = pack(vs, true);
    else {
      var dn = Math.min(angBetween(a, v), angBetween(b, v)), ds = Math.min(angBetween(a, vs), angBetween(b, vs));
      out.vertex = pack(dn <= ds ? v : vs, false);
    }
    return out;
  }

  /* ---------- Rhumb line on the WGS84 ellipsoid (Mercator sailing) ---------- */
  var WGS_A = 6378137, WGS_F = 1 / 298.257223563;
  var WGS_E2 = WGS_F * (2 - WGS_F), WGS_E = Math.sqrt(WGS_E2), WGS_N = WGS_F / (2 - WGS_F);
  function atanh(x) { return 0.5 * Math.log((1 + x) / (1 - x)); }
  /* Isometric latitude in radians. */
  function isoLat(lat) {
    var s = Math.sin(rad(lat));
    return atanh(s) - WGS_E * atanh(WGS_E * s);
  }
  /* Meridional parts (minutes of longitude) for the WGS84 ellipsoid. */
  function meridionalParts(lat) { return isoLat(lat) * 10800 / Math.PI; }
  /* Meridian arc from the equator in metres (Helmert series in n). */
  function meridianArc(lat) {
    var p = rad(lat), n = WGS_N, n2 = n * n, n3 = n2 * n, n4 = n2 * n2;
    return WGS_A / (1 + n) * ((1 + n2 / 4 + n4 / 64) * p - 1.5 * (n - n3 / 8) * Math.sin(2 * p) +
      (15 / 16) * (n2 - n4 / 4) * Math.sin(4 * p) - (35 / 48) * n3 * Math.sin(6 * p) +
      (315 / 512) * n4 * Math.sin(8 * p));
  }
  function rhumb(lat1, lon1, lat2, lon2) {
    if (Math.abs(lat1) >= 90 || Math.abs(lat2) >= 90) return null;
    var dl = rad(norm180(lon2 - lon1));
    var dpsi = isoLat(lat2) - isoLat(lat1);
    var dphi = rad(lat2 - lat1);
    if (Math.abs(dl) < 1e-15 && Math.abs(dphi) < 1e-15) return { distNm: 0, course: null, dmp: 0 };
    var course = dirOf(dl, dpsi), distM;
    if (Math.abs(dphi) < 1e-10) {
      var s = Math.sin(rad(lat1));
      distM = Math.abs(dl) * WGS_A * Math.cos(rad(lat1)) / Math.sqrt(1 - WGS_E2 * s * s);
    } else {
      distM = Math.abs((meridianArc(lat2) - meridianArc(lat1)) / dpsi) * hypot(dl, dpsi);
    }
    return { distNm: distM / NM, course: course, dmp: dpsi * 10800 / Math.PI };
  }

  /* ---------- CPA / TCPA from two radar plots ---------- */
  /* Bearings true, ranges nm, dtMin = minutes between the plots. */
  function cpa(ownCourse, ownSpeed, brg1, rng1, brg2, rng2, dtMin) {
    var t = dtMin / 60;
    var x1 = rng1 * Math.sin(rad(brg1)), y1 = rng1 * Math.cos(rad(brg1));
    var x2 = rng2 * Math.sin(rad(brg2)), y2 = rng2 * Math.cos(rad(brg2));
    var rx = (x2 - x1) / t, ry = (y2 - y1) / t;
    var relSpeed = hypot(rx, ry);
    var out = { p1: [x1, y1], p2: [x2, y2], relSpeed: relSpeed, relCourse: relSpeed < 1e-9 ? null : dirOf(rx, ry) };
    if (relSpeed < 1e-9) { // no relative motion: range stays as it is
      out.cpa = rng2; out.tcpaMin = null; out.cpaBrg = norm360(brg2); out.cpaPoint = [x2, y2];
    } else {
      var tc = -(x2 * rx + y2 * ry) / (relSpeed * relSpeed); // hours after plot 2
      var cx = x2 + rx * tc, cy = y2 + ry * tc;
      out.cpa = hypot(cx, cy); out.tcpaMin = tc * 60; out.cpaPoint = [cx, cy];
      out.cpaBrg = out.cpa < 1e-9 ? null : dirOf(cx, cy);
    }
    var tx = rx + ownSpeed * Math.sin(rad(ownCourse)), ty = ry + ownSpeed * Math.cos(rad(ownCourse));
    out.targetSpeed = hypot(tx, ty);
    out.targetCourse = out.targetSpeed < 0.05 ? null : dirOf(tx, ty);
    // Aspect: relative bearing of own ship seen from the target, Red (port) negative, Green (starboard) positive.
    out.aspect = out.targetCourse === null ? null : norm180(norm360(brg2 + 180) - out.targetCourse);
    return out;
  }

  /* ---------- Current triangle ---------- */
  /* Course to steer to make good a track. set = direction the current flows TOWARDS. */
  function courseToSteer(track, stw, set, rate) {
    var a = rad(set - track);
    var cross = rate * Math.sin(a), along = rate * Math.cos(a);
    if (Math.abs(cross) > stw) return null; // current too strong to hold the track
    var corr = deg(Math.asin(cross / stw));
    var smg = stw * Math.cos(rad(corr)) + along;
    if (smg <= 0) return null;
    return { cts: norm360(track - corr), correction: -corr, smg: smg };
  }
  /* Course and speed made good from course steered, speed through water, set and rate. */
  function madeGood(course, stw, set, rate) {
    var x = stw * Math.sin(rad(course)) + rate * Math.sin(rad(set));
    var y = stw * Math.cos(rad(course)) + rate * Math.cos(rad(set));
    var s = hypot(x, y);
    return { cmg: s < 1e-9 ? null : dirOf(x, y), smg: s };
  }
  /* Set, drift and rate from what was steered and what was made good between two fixes. */
  function setDrift(course, stw, hours, cmg, distMadeGood) {
    var x = distMadeGood * Math.sin(rad(cmg)) - stw * hours * Math.sin(rad(course));
    var y = distMadeGood * Math.cos(rad(cmg)) - stw * hours * Math.cos(rad(course));
    var d = hypot(x, y);
    return { set: d < 1e-9 ? null : dirOf(x, y), drift: d, rate: d / hours };
  }

  /* ---------- Squat (Barrass simplified) and under keel clearance ---------- */
  function squat(cb, speedKn, confined) { return (confined ? 2 : 1) * cb * speedKn * speedKn / 100; }
  function ukc(chartedDepth, tide, draught, squatM, otherAllowances) {
    var depth = chartedDepth + tide;
    var stat = depth - draught;
    return { depth: depth, staticUkc: stat, afterSquat: stat - squatM, net: stat - squatM - (otherAllowances || 0) };
  }

  /* ---------- Propeller slip ---------- */
  function engineDistance(pitchM, revs) { return pitchM * revs / NM; }
  function engineSpeed(pitchM, rpm) { return pitchM * rpm * 60 / NM; }
  function slipPercent(engine, observed) { return (engine - observed) / engine * 100; }

  /* ---------- Fuel ---------- */
  function fuel(consumedT, periodHours, robT, speedKn, distanceToGo) {
    var daily = consumedT / periodHours * 24;
    var out = { daily: daily, perHour: daily / 24, daysLeft: robT / daily };
    if (speedKn > 0) {
      out.perNm = daily / (24 * speedKn);
      out.rangeNm = out.daysLeft * 24 * speedKn;
      if (distanceToGo >= 0) {
        out.voyageDays = distanceToGo / speedKn / 24;
        out.voyageFuel = out.voyageDays * daily;
        out.robArrival = robT - out.voyageFuel;
      }
    }
    return out;
  }
  /* Cube-law estimate of daily consumption at another speed. */
  function cubeLaw(daily, speed, newSpeed) { return daily * Math.pow(newSpeed / speed, 3); }

  /* ---------- Load line allowances ---------- */
  function fwa(displacementT, tpc) { return displacementT / (4 * tpc); } // mm
  function dwa(fwaMm, densityKgM3) { return fwaMm * (1025 - densityKgM3) / 25; } // mm

  /* ---------- Stability ---------- */
  function stability(displacement, km, kg, fsm, weight, distance) {
    var gmSolid = km - kg, fsc = (fsm || 0) / displacement, gm = gmSolid - fsc;
    var out = { gmSolid: gmSolid, fsc: fsc, gmFluid: gm, gg1: null, list: null };
    if (weight > 0 && distance > 0) {
      out.gg1 = weight * distance / displacement;
      if (gm > 0) out.list = deg(Math.atan(out.gg1 / gm));
    }
    return out;
  }

  /* ---------- Units ---------- */
  /* Each unit is its size in the base unit of its group. */
  var UNITS = {
    speed: { base: 'm/s', units: { kn: NM / 3600, 'm/s': 1, 'km/h': 1 / 3.6, mph: 1609.344 / 3600 } },
    distance: { base: 'm', units: { nm: NM, cable: NM / 10, km: 1000, m: 1, 'statute mile': 1609.344, ft: 0.3048 } },
    depth: { base: 'm', units: { m: 1, ft: 0.3048, fathom: 1.8288, 'shackle (27.5 m)': 27.5 } },
    pressure: { base: 'Pa', units: { bar: 100000, psi: 6894.757293168, kPa: 1000, MPa: 1000000, 'kgf/cm²': 98066.5, mmHg: 133.322387415, atm: 101325 } },
    volume: { base: 'm³', units: { 'm³': 1, litre: 0.001, 'US barrel': 0.158987294928, 'US gallon': 0.003785411784, 'Imperial gallon': 0.00454609, 'ft³': 0.028316846592 } },
    mass: { base: 'kg', units: { tonne: 1000, 'long ton': 1016.0469088, 'short ton': 907.18474, kg: 1, lb: 0.45359237 } },
    power: { base: 'W', units: { kW: 1000, 'hp (metric, PS)': 735.49875, 'hp (imperial, bhp)': 745.69987158227 } }
  };
  function convert(group, value, from, to) {
    var u = UNITS[group].units;
    return value * u[from] / u[to];
  }
  function convertTemp(value, from, to) {
    var k = from === 'C' ? value + 273.15 : from === 'F' ? (value - 32) * 5 / 9 + 273.15 : value;
    return to === 'C' ? k - 273.15 : to === 'F' ? (k - 273.15) * 9 / 5 + 32 : k;
  }

  return {
    NM: NM, rad: rad, deg: deg, norm360: norm360, norm180: norm180, dirOf: dirOf,
    sunPosition: sunPosition, bodyAzAlt: bodyAzAlt, amplitude: amplitude, compassError: compassError,
    trueWind: trueWind, beaufort: beaufort,
    steamingHours: steamingHours, eta: eta, requiredSpeed: requiredSpeed,
    gcSphere: gcSphere, rhumb: rhumb, meridionalParts: meridionalParts, meridianArc: meridianArc,
    cpa: cpa, courseToSteer: courseToSteer, madeGood: madeGood, setDrift: setDrift,
    squat: squat, ukc: ukc,
    engineDistance: engineDistance, engineSpeed: engineSpeed, slipPercent: slipPercent,
    fuel: fuel, cubeLaw: cubeLaw, fwa: fwa, dwa: dwa, stability: stability,
    UNITS: UNITS, convert: convert, convertTemp: convertTemp
  };
});

/* Exxon Valdez, Bligh Reef, 24 March 1989 — Incident Learnings, drawn in code.
   Scene timing follows the narration (assets/timing.js). draw(t) is a pure function of time. */
"use strict";
const NARR = window.NARR, LN = NARR.lines, END = window.FILM_END;
const ls = (i) => LN[i - 1].start, le = (i) => LN[i - 1].end;
const cut = (i) => (i <= 1 ? 0 : ls(i) - 0.2);
const key = (w) => w.toLowerCase().replace(/[^a-z0-9]/g, "");
function tok(line, word, nth) { let c = 0; for (const k of LN[line - 1].tokens) if (key(k.w) === word) { if (c === (nth || 0)) return k.s; c++; } return ls(line); }
const pop = (t, at, d) => back((t - at) / (d || 0.3));
const vis = (t, at, d) => clamp((t - at) / (d || 0.25));

// ================= chart =================
const KX = Math.cos((60.9 * Math.PI) / 180);
const P39 = [60.943, -146.852];
const U = [-0.588, -0.809], Q = [0.809, -0.588];                 // along the lanes (216°) and their south-east normal (east, north)
const nm2ll = (e, n, ref) => [ref[0] + n / 60, ref[1] + e / (60 * KX)];
const lane = (a, d) => nm2ll(U[0] * a + Q[0] * d, U[1] * a + Q[1] * d, P39);
const XY = (cam, ll) => [cam.x + (ll[1] - cam.lon) * 60 * KX * cam.s, cam.y - (ll[0] - cam.lat) * 60 * cam.s];
const TR = [[61.094, -146.4], [61.108, -146.55], [61.094, -146.628], [61.066, -146.676], [61.02, -146.745], [60.986, -146.803], [60.968, -146.833], [60.943, -146.852],
  [60.916, -146.852], [60.9, -146.852], [60.892, -146.852], [60.862, -146.852], [60.848, -146.856], [60.84, -146.8625]];
const BEAR = TR.slice(0, -1).map((a, i) => Math.atan2((TR[i + 1][1] - a[1]) * KX, TR[i + 1][0] - a[0]));
const angLerp = (a, b, u) => a + (((b - a + Math.PI * 3) % TAU) - Math.PI) * u;
function trackPos(k) {
  k = clamp(k, 0, TR.length - 1); const i = Math.min(TR.length - 2, Math.floor(k)), f = k - i;
  let h = angLerp(BEAR[i], BEAR[Math.min(BEAR.length - 1, i + 1)], ss(0.55, 1, f));
  if (k > 11) h = angLerp(Math.PI, (235 * Math.PI) / 180, ss(11, 13, k));        // heading swings right late; the track barely moves
  return { ll: [lerp(TR[i][0], TR[i + 1][0], f), lerp(TR[i][1], TR[i + 1][1], f)], h };
}
const G_POS = TR[TR.length - 1], BUOY = [60.842, -146.887], BUSBY = [60.892, -146.818], ICE_TIP = [60.854, -146.904];
const REEF = [[60.842, -146.889], [60.8427, -146.862], [60.839, -146.838], [60.829, -146.828], [60.824, -146.85], [60.829, -146.884]];
const PLAN = [[60.892, -146.852], [60.876, -146.857], [60.862, -146.874], [60.848, -146.8955], [60.836, -146.915], [60.822, -146.94]];
const ICE = [];
for (let i = 0; i < 44; i++) { const a = 0.9 + 4.5 * rnd(i * 3.7 + 1), dmax = 0.9 + 0.2 * a; ICE.push({ ll: lane(a, lerp(-1.4, dmax - 0.15, rnd(i * 5.3 + 2))), r: 0.1 + 0.17 * rnd(i * 7.9 + 3), seed: i }); }
ICE.push({ ll: ICE_TIP, r: 0.15, seed: 99 }, { ll: lane(4.6, 1.5), r: 0.2, seed: 98 });
const CAM = { wide: { lat: 60.955, lon: -146.63, s: 46 }, mid: { lat: 60.925, lon: -146.89, s: 120 }, reef: { lat: 60.868, lon: -146.875, s: 215 }, busby: { lat: 60.878, lon: -146.848, s: 250 },
  close: { lat: 60.8555, lon: -146.855, s: 1300 }, hit: { lat: 60.841, lon: -146.8615, s: 1900 }, spill: { lat: 60.8462, lon: -146.868, s: 560 } };
const camMix = (a, b, u) => ({ lat: lerp(a.lat, b.lat, u), lon: lerp(a.lon, b.lon, u), s: Math.exp(lerp(Math.log(a.s), Math.log(b.s), u)), x: 540, y: 860 });
const camOf = (a) => camMix(a, a, 0);

function poly(cam, pts, close) { pts.forEach((p, i) => { const [x, y] = XY(cam, p); if (i) g.lineTo(x, y); else g.moveTo(x, y); }); if (close) g.closePath(); }
function chartLabel(cam, ll, s, size, color, dx, dy, align) { const [x, y] = XY(cam, ll); font(size, 600, size * 0.12); g.textAlign = align || "center"; g.lineJoin = "round"; g.lineWidth = 6; g.strokeStyle = "rgba(255,255,255,.8)"; g.strokeText(s, x + (dx || 0), y + (dy || 0)); g.fillStyle = color; g.fillText(s, x + (dx || 0), y + (dy || 0)); }

function chart(cam, t, o) {
  // water
  g.fillStyle = lin(0, 0, 0, H, [[0, "#D6EFF8"], [1, "#BDE2F1"]]); g.fillRect(0, 0, W, H);
  g.strokeStyle = "rgba(60,110,150,.14)"; g.lineWidth = 2;
  const stepLat = cam.s > 400 ? 1 / 120 : cam.s > 100 ? 1 / 12 : 1 / 6, stepLon = stepLat * 2;
  for (let la = Math.floor((cam.lat - 1000 / (60 * cam.s)) / stepLat) * stepLat; la < cam.lat + 1000 / (60 * cam.s); la += stepLat) { const y = XY(cam, [la, cam.lon])[1]; g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke(); }
  for (let lo = Math.floor((cam.lon - 600 / (60 * KX * cam.s)) / stepLon) * stepLon; lo < cam.lon + 600 / (60 * KX * cam.s); lo += stepLon) { const x = XY(cam, [cam.lat, lo])[0]; g.beginPath(); g.moveTo(x, 0); g.lineTo(x, H); g.stroke(); }
  // traffic lanes
  if (cam.s < 500) {
    const la = o.lanes === undefined ? 1 : o.lanes;
    g.fillStyle = "rgba(196,62,170," + (0.2 * la).toFixed(3) + ")"; g.beginPath(); poly(cam, [lane(-9.6, -0.25), lane(13, -0.25), lane(13, 0.25), lane(-9.6, 0.25)], true); g.fill();
    g.strokeStyle = "rgba(176,52,150," + (0.6 * la).toFixed(3) + ")"; g.lineWidth = 3; g.setLineDash([16, 12]);
    for (const d of [-0.95, 0.95]) { g.beginPath(); poly(cam, [lane(-9.6, d), lane(13, d)]); g.stroke(); }
    g.setLineDash([]);
    for (const [d, dir] of [[-0.6, 1], [0.6, -1]]) for (let a = -8; a <= 11; a += cam.s < 80 ? 4 : 2) {         // lane arrows
      const [x, y] = XY(cam, lane(a, d)), ang = Math.atan2(-U[1], U[0]) + (dir < 0 ? Math.PI : 0), L = clamp(cam.s * 0.5, 22, 60);
      g.save(); g.translate(x, y); g.rotate(ang); g.strokeStyle = "rgba(176,52,150," + (0.7 * la).toFixed(3) + ")"; g.lineWidth = 3.5; g.lineCap = "round"; g.lineJoin = "round";
      g.beginPath(); g.moveTo(-L / 2, 0); g.lineTo(L / 2, 0); g.moveTo(L / 2 - 12, -9); g.lineTo(L / 2, 0); g.lineTo(L / 2 - 12, 9); g.stroke(); g.restore();
    }
  }
  // land
  g.fillStyle = "#EADFC2"; g.strokeStyle = "#B5A273"; g.lineWidth = 3; g.lineJoin = "round";
  for (const ring of window.GEO_LAND) {
    const closed = ring[0][0] === ring[ring.length - 1][0] && ring[0][1] === ring[ring.length - 1][1];
    if (!closed && ring.length < 200) continue;
    g.beginPath(); ring.forEach(([lo, la], i) => { const [x, y] = XY(cam, [la, lo]); if (i) g.lineTo(x, y); else g.moveTo(x, y); });
    if (!closed) { let p = XY(cam, [63.5, ring[ring.length - 1][0]]); g.lineTo(p[0], p[1]); p = XY(cam, [63.5, ring[0][0]]); g.lineTo(p[0], p[1]); }
    g.closePath(); g.fill(); g.stroke();
  }
  // reef
  const hot = o.reef || 0;
  g.save(); g.beginPath(); const rp = REEF.map((p) => XY(cam, p)); smoothPath(rp.concat([rp[0], rp[1]])); g.closePath();
  g.fillStyle = "rgba(242,85,90," + (0.16 + 0.2 * hot).toFixed(3) + ")"; g.fill();
  g.save(); g.clip(); g.strokeStyle = "rgba(210,50,60," + (0.35 + 0.3 * hot).toFixed(3) + ")"; g.lineWidth = 2.5;
  const hs = clamp(cam.s * 0.1, 14, 44); for (let x = -H; x < W + H; x += hs) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x + H, H); g.stroke(); }
  if (cam.s > 400) for (let i = 0; i < 60; i++) {                                                                // rocks, seen close
    const ll = [lerp(60.825, 60.8425, rnd(i * 3.1 + 7)), lerp(-146.888, -146.83, rnd(i * 5.7 + 9))], [x, y] = XY(cam, ll), r = (0.006 + 0.012 * rnd(i * 2.3)) * cam.s;
    g.fillStyle = "rgba(120,96,80,.55)"; g.beginPath(); g.ellipse(x, y, r * 1.3, r, rnd(i) * 3, 0, TAU); g.fill();
    g.fillStyle = "rgba(255,255,255,.45)"; g.beginPath(); g.ellipse(x - r * 0.2, y - r * 0.3, r * 0.5, r * 0.3, 0, 0, TAU); g.fill();
  }
  g.restore(); g.strokeStyle = "#E0434C"; g.lineWidth = 3 + 2 * hot; g.setLineDash([10, 8]); g.stroke(); g.setLineDash([]); g.restore();
  // ice
  if (o.ice > 0) for (const b of ICE) {
    const a = eo((o.ice * 1.6 - rnd(b.seed * 1.3) * 0.6)); if (a <= 0) continue;
    const [x, y] = XY(cam, b.ll), r = b.r * cam.s * a, rot = rnd(b.seed * 2.2) * 6 + Math.sin(t * 0.5 + b.seed) * 0.06;
    const dx = Math.sin(t * 0.6 + b.seed) * 0.012 * cam.s, dy = Math.cos(t * 0.5 + b.seed * 2) * 0.01 * cam.s;
    const shape = (ox, oy) => { g.beginPath(); for (let i = 0; i < 8; i++) { const an = rot + (i / 8) * TAU, rr2 = r * (0.72 + 0.5 * rnd(b.seed * 9 + i)); const px = x + dx + ox + Math.cos(an) * rr2, py = y + dy + oy + Math.sin(an) * rr2 * 0.85; if (i) g.lineTo(px, py); else g.moveTo(px, py); } g.closePath(); };
    shape(3, 5); g.fillStyle = "rgba(90,150,185,.45)"; g.fill();
    shape(0, 0); g.fillStyle = "#FFFFFF"; g.fill(); g.strokeStyle = "#8CC3DD"; g.lineWidth = 2; g.stroke();
  }
  // lights and marks
  { const [x, y] = XY(cam, BUSBY); g.fillStyle = "#B4329A"; g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + 26, y - 30, x + 8, y - 44); g.quadraticCurveTo(x + 2, y - 22, x, y); g.fill(); g.fillStyle = "#1C2B3A"; circle(x, y, 6); }
  { const [x, y] = XY(cam, BUOY), on = (t % 1.2) < 0.45; if (on) glow(x, y, 46, "255,60,60", 0.8); g.fillStyle = "#E0434C"; circle(x, y, 9); g.strokeStyle = "#FFFFFF"; g.lineWidth = 2.5; g.stroke(); }
  // labels
  const lab = o.labels || "";
  if (lab.includes("V")) { chartLabel(cam, [61.122, -146.42], "VALDEZ", 30, "#5A4A22"); const [x, y] = XY(cam, TR[0]); g.fillStyle = "#1C2B3A"; rr(x - 9, y - 9, 18, 18, 4); g.fill(); }
  if (lab.includes("N")) chartLabel(cam, [61.045, -146.6], "VALDEZ NARROWS", 22, "#5A4A22", 0, 0, "left");
  if (lab.includes("A")) chartLabel(cam, [60.99, -146.94], "VALDEZ ARM", 24, "#3B6C8F");
  if (lab.includes("P")) chartLabel(cam, [60.7, -146.76], "PRINCE WILLIAM SOUND", 26, "#3B6C8F");
  if (lab.includes("B")) chartLabel(cam, [60.848, -146.755], "BLIGH I.", cam.s > 150 ? 28 : 22, "#5A4A22");
  if (lab.includes("R")) chartLabel(cam, [60.8215, -146.86], "BLIGH REEF", cam.s > 150 ? 34 : 24, "#C22F3A", 0, cam.s > 150 ? 34 : 22);
  if (lab.includes("L")) chartLabel(cam, BUSBY, "BUSBY I. LIGHT", cam.s > 150 ? 26 : 20, "#8A2476", 30, -58);
  if (lab.includes("I") && o.ice > 0.5) chartLabel(cam, lane(2.6, -2.0), "GLACIER ICE", cam.s > 150 ? 34 : 28, "#2C7FA8");
  if (lab.includes("T")) chartLabel(cam, lane(1.5, -2.2), "SHIPPING LANES", 22, "#A0308A", 0, 0, "left");
  // planned turn
  if (o.plan > 0) { g.save(); g.strokeStyle = "rgba(0,150,190,.95)"; g.lineWidth = 6; g.setLineDash([18, 14]); g.lineCap = "round"; const pp = PLAN.map((p) => XY(cam, p)); const n = Math.max(2, Math.round(pp.length * o.plan)); g.beginPath(); smoothPath(pp.slice(0, n)); g.stroke(); g.restore(); }
  // track so far
  if (o.k !== undefined) {
    const pts = []; const k0 = o.k0 || 0; for (let i = Math.ceil(k0); i <= Math.floor(o.k); i++) pts.push(XY(cam, TR[i])); pts.push(XY(cam, trackPos(o.k).ll));
    if (pts.length > 1) { g.lineJoin = "round"; g.lineCap = "round"; for (const [c, w] of [["rgba(255,255,255,.9)", 10], ["#14293D", 5]]) { g.strokeStyle = c; g.lineWidth = w; g.beginPath(); pts.forEach((p, i) => (i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]))); g.stroke(); } }
  }
  // oil
  if (o.slick > 0) {
    const [x, y] = XY(cam, G_POS), R = (0.05 + 0.36 * o.slick) * cam.s;
    for (const [m, c] of [[1.22, "rgba(96,66,36,.42)"], [1, "rgba(34,24,16,.86)"]]) {
      g.beginPath(); const pts = []; for (let i = 0; i <= 18; i++) { const an = (i / 18) * TAU, rr2 = R * m * (0.74 + 0.3 * rnd(i * 3.3 + 4) + 0.06 * Math.sin(t * 0.9 + i)); pts.push([x - R * 0.42 * o.slick + Math.cos(an) * rr2 * 1.15, y + R * 0.36 * o.slick + Math.sin(an) * rr2]); }
      smoothPath(pts.concat([pts[1], pts[2]])); g.closePath(); g.fillStyle = c; g.fill();
    }
    g.fillStyle = "rgba(255,255,255,.10)"; for (let i = 0; i < 9; i++) { g.beginPath(); g.ellipse(x - R * 0.42 * o.slick + (rnd(i * 2.9) - 0.5) * R * 1.3, y + R * 0.36 * o.slick + (rnd(i * 4.1) - 0.5) * R * 1.1, R * 0.16, R * 0.05, rnd(i) * 3, 0, TAU); g.fill(); }
  }
  // ship
  if (o.k !== undefined) {
    const p = trackPos(o.k), [x, y] = XY(cam, p.ll), Lpx = Math.max(0.1625 * cam.s, o.minShip || 70), sc = Lpx / 520;
    if (cam.s < 400) { const pr = ((t * 0.9) % 1); g.strokeStyle = "rgba(0,170,210," + (0.8 * (1 - pr)).toFixed(2) + ")"; g.lineWidth = 4; g.beginPath(); g.arc(x, y, Lpx * 0.6 + pr * 40, 0, TAU); g.stroke(); }
    g.save(); g.translate(x, y); g.rotate(p.h); g.scale(sc, sc);
    const wk = o.wake === undefined ? 1 : o.wake;
    if (wk > 0.02 && cam.s > 400) {
      g.fillStyle = lin(0, 240, 0, 1300, [[0, "rgba(255,255,255," + (0.8 * wk).toFixed(2) + ")"], [1, "rgba(255,255,255,0)"]]);
      g.beginPath(); g.moveTo(-30, 244); g.lineTo(30, 244); for (let yy = 260; yy <= 1300; yy += 40) g.lineTo(30 + (yy - 244) * 0.075 + Math.sin(yy * 0.03 + t * 4) * 8, yy);
      for (let yy = 1300; yy >= 260; yy -= 40) g.lineTo(-30 - (yy - 244) * 0.075 + Math.sin(yy * 0.03 + t * 4 + 2) * 8, yy); g.closePath(); g.fill();
      for (const sd of [-1, 1]) for (let i = 0; i < 20; i++) { const ph = (((i / 20 + t * 0.5) % 1) + 1) % 1, d = 40 + 1300 * ph, len = 16 + 60 * ph;
        g.strokeStyle = "rgba(255,255,255," + (0.85 * (1 - ph) * wk).toFixed(3) + ")"; g.lineWidth = 3 + 6 * ph; g.lineCap = "round";
        g.beginPath(); g.moveTo(sd * (40 + d * 0.33) - sd * len * 0.2, -190 + d - len * 0.35); g.quadraticCurveTo(sd * (40 + d * 0.33) + sd * len * 0.5, -190 + d - len * 0.1, sd * (40 + d * 0.33) + sd * len * 0.9, -190 + d + len * 0.5); g.stroke(); }
      g.fillStyle = "rgba(255,255,255," + (0.9 * wk).toFixed(2) + ")"; g.beginPath(); g.ellipse(0, -258, 52, 26, 0, Math.PI, TAU); g.fill();
    }
    tankerTop(); g.restore();
  }
}

// ================= bridge, at night =================
function person(x, kind, alpha, hi, tag, t) {
  if (alpha <= 0.01) return;
  g.save(); g.globalAlpha = alpha;
  if (hi) { g.strokeStyle = "rgba(0,229,255,.9)"; g.lineWidth = 5; g.setLineDash([14, 10]); g.lineDashOffset = -t * 30; g.beginPath(); g.ellipse(x, 900, 138, 190, 0, 0, TAU); g.stroke(); g.setLineDash([]); }
  g.fillStyle = kind === "ab" ? "#E8792B" : "#EEF3F7";
  g.beginPath(); g.moveTo(x - 98, 1052); g.lineTo(x - 98, 914); g.quadraticCurveTo(x - 98, 872, x - 52, 866); g.lineTo(x + 52, 866); g.quadraticCurveTo(x + 98, 872, x + 98, 914); g.lineTo(x + 98, 1052); g.closePath(); g.fill();
  g.fillStyle = "rgba(20,44,90,.14)"; g.beginPath(); g.moveTo(x - 98, 1052); g.lineTo(x - 98, 914); g.quadraticCurveTo(x - 98, 872, x - 52, 866); g.lineTo(x - 30, 866); g.lineTo(x - 30, 1052); g.closePath(); g.fill();
  g.fillStyle = "#C79A78"; rr(x - 18, 842, 36, 34, 8); g.fill();
  g.beginPath(); g.ellipse(x - 46, 818, 8, 13, 0, 0, TAU); g.fill(); g.beginPath(); g.ellipse(x + 46, 818, 8, 13, 0, 0, TAU); g.fill();
  g.fillStyle = "#2A2F38"; circle(x, 812, 47);
  if (kind !== "ab") { const bars = kind === "master" ? 4 : 1; for (const sd of [-1, 1]) { g.fillStyle = "#16243A"; rr(x + sd * 66 - 24, 869, 48, 24, 5); g.fill(); g.fillStyle = "#F5C542"; for (let b = 0; b < bars; b++) g.fillRect(x + sd * 66 - 19 + b * 10, 873, 6, 16); } }
  if (tag) pill(x, 706, tag, { align: "center", size: 28, fill: hi ? "#00E5FF" : "rgba(7,10,15,.9)", color: hi ? "#06202A" : "#F2F4F7" });
  g.restore();
}
function screenCard(x, y, w, h, fill, stroke, lw) {
  rr(x - 8, y - 8, w + 16, h + 16, 20); g.fillStyle = "#70808C"; g.fill();
  rr(x, y, w, h, 14); g.fillStyle = "#0F1217"; g.fill();
  if (fill) { rr(x, y, w, h, 14); g.fillStyle = fill; g.fill(); }
  g.lineWidth = lw || 2; g.strokeStyle = stroke || "rgba(255,255,255,.10)"; rr(x, y, w, h, 14); g.stroke();
}
function bridge(t, lt, o) {
  const yH = 640, VPy = 632, yD = 1046, hw = (y) => (500 * (y - VPy)) / 368, z = 1 + 0.05 * (1 - eo(lt / 0.5)) + 0.004 * lt;
  g.save(); g.beginPath(); g.rect(0, 118, W, 926); g.clip(); g.translate(540, 700); g.scale(z, z); g.translate(-540, -700);
  sky(NIGHT, yH, 200, 330);
  clouds(NIGHT, t, [[820, 420, 0.7, 3], [520, 560, 0.34, 2]]);
  seaBase(NIGHT, yH, 1070); swell(yH, 1070, t, 0.5); glitter(t, 200, yH + 4, yH + 90, "225,235,255"); seaRows(yH, 1040, t, 0.16, 22, yH, 1100, 0.5);
  if (o.red) {                                                                    // the buoy light, broad on the starboard bow
    const on = ((t % 1.3) < 0.55) ? 1 : 0.12, x = 905, y = 674;
    glow(x, y, 150, "255,50,50", 0.75 * on); g.fillStyle = "rgba(255,90,90," + (0.4 + 0.6 * on) + ")"; circle(x, y, 9);
    for (let i = 0; i < 7; i++) { g.fillStyle = "rgba(255,70,70," + (0.5 * on * (1 - i / 7)).toFixed(2) + ")"; const w2 = 12 + i * 5 + 4 * Math.sin(t * 3 + i); rr(x - w2, y + 16 + i * 17, w2 * 2, 5, 3); g.fill(); }
  }
  const deck = () => { g.beginPath(); g.moveTo(540 - hw(yD), yD); g.lineTo(460, 689); g.quadraticCurveTo(508, 664, 540, 660); g.quadraticCurveTo(572, 664, 620, 689); g.lineTo(540 + hw(yD), yD); g.closePath(); };
  for (const sd of [-1, 1]) { g.fillStyle = "rgba(230,240,255,.8)"; g.beginPath(); g.moveTo(540 + sd * 26, 668); g.quadraticCurveTo(540 + sd * 160, 660 + Math.sin(t * 5 + sd) * 2, 540 + sd * 280, 704); g.quadraticCurveTo(540 + sd * 150, 686, 540 + sd * 62, 688); g.closePath(); g.fill(); }
  deck(); g.fillStyle = lin(0, 660, 0, yD, [[0, "#8F6276"], [1, "#7A3D46"]]); g.fill();
  g.save(); deck(); g.clip();
  for (let i = 1; i < 16; i++) { const y = VPy + 414 / (i * 0.72); if (y > yD) continue; g.fillStyle = "rgba(20,10,30,.2)"; g.fillRect(-40, y, W + 80, Math.max(1, (y - VPy) / 110)); }
  for (const oo of [-0.6, -0.4, -0.13, 0.13, 0.4, 0.6]) { const wide = Math.abs(oo) < 0.2 ? 22 : 13, ws = (y) => ((wide / 2) * (y - VPy)) / 414;
    g.fillStyle = Math.abs(oo) < 0.2 ? "#B9C6DA" : "#9DAEC8"; g.beginPath(); g.moveTo(540 + oo * hw(700) - ws(700), 700); g.lineTo(540 + oo * hw(700) + ws(700), 700); g.lineTo(540 + oo * hw(yD) + ws(yD), yD); g.lineTo(540 + oo * hw(yD) - ws(yD), yD); g.closePath(); g.fill(); }
  { const y = 812, h2 = hw(y); g.fillStyle = "#8795AC"; g.fillRect(540 - h2 * 0.93, y - 7, h2 * 1.86, 14);
    for (const sd of [-1, 1]) { g.strokeStyle = "#C9D4E6"; g.lineWidth = 7; g.lineCap = "butt"; g.beginPath(); g.moveTo(540 + sd * h2 * 0.34, y); g.lineTo(540 + sd * h2 * 0.34, y - 84); g.stroke(); glow(540 + sd * h2 * 0.34, y - 88, 70, "255,232,170", 0.7); } }
  glow(540, 940, 330, "255,232,170", 0.18);
  g.restore();
  deck(); g.strokeStyle = "#C9D4E6"; g.lineWidth = 3; g.stroke();
  g.strokeStyle = "#C9D4E6"; g.lineWidth = 3; g.beginPath(); g.moveTo(540, 662); g.lineTo(540, 606); g.stroke(); glow(540, 604, 52, "255,255,255", 0.95); g.fillStyle = "#FFFFFF"; circle(540, 604, 5);
  g.restore();
  // frame
  g.fillStyle = "#101826"; g.fillRect(0, 0, W, 122); g.fillStyle = "#2C3A50"; g.fillRect(0, 118, W, 4);
  for (const [x, w] of [[-2, 22], [292, 18], [770, 18], [1060, 22]]) { g.fillStyle = "#101826"; g.fillRect(x, 120, w, 926); g.fillStyle = "#34445C"; g.fillRect(x + w - 2, 122, 2, 922); }
  for (const [x0, w0] of [[20, 272], [310, 460], [788, 272]]) { g.save(); g.beginPath(); g.rect(x0, 122, w0, 922); g.clip(); g.fillStyle = "rgba(255,255,255,.05)";
    g.beginPath(); g.moveTo(x0 + w0 * 0.3, 122); g.lineTo(x0 + w0 * 0.55, 122); g.lineTo(x0 + w0 * 0.55 - 230, 1044); g.lineTo(x0 + w0 * 0.3 - 230, 1044); g.closePath(); g.fill(); g.restore(); }
  // people
  if (o.people) o.people();
  // console
  g.fillStyle = lin(0, 1044, 0, H, [[0, "#C6D1DC"], [0.5, "#A9B7C4"], [1, "#8B9AA8"]]); g.fillRect(0, 1044, W, H - 1044);
  g.fillStyle = "#5E6E7C"; g.fillRect(0, 1044, W, 6);
  g.fillStyle = lin(0, 1050, 0, 1084, [[0, "rgba(20,32,44,.22)"], [1, "rgba(20,32,44,0)"]]); g.fillRect(0, 1050, W, 34);
  if (o.cards) o.cards();
  for (let i = 0; i < 6; i++) { const x = 104 + i * 74; g.fillStyle = "#6B7A86"; circle(x, 1600, 24); g.fillStyle = "#1A2029"; circle(x, 1600, 18); g.fillStyle = i === 4 ? "#F5A524" : "#00B0D2"; circle(x, 1600, 10); }
}

// ================= overlays =================
const HOOK_OUT = 3.0;
function hook(t) {
  if (t > HOOK_OUT + 0.3) return;
  const u = clamp((t - HOOK_OUT) / 0.28), sc = (1 + 0.05 * (1 - eo(t / 0.5))) * (1 - 0.5 * u * u);
  g.save(); g.globalAlpha = 1 - u; g.translate(90, 560 - 180 * u * u); g.scale(sc, sc); g.translate(-90, -560);
  otxt("Everyone blames the", 90, 420, 72, "#FFFFFF", "left", 6);
  const k = 1 + 0.08 * (1 - back(t / 0.45));
  g.save(); g.translate(84, 560); g.scale(k, k); otxt("CAPTAIN", 0, 62, 186, "#F5A524", "left", 8); g.restore();
  otxt("…BUT", 90, 760, 124, "#FFFFFF", "left", 8);
  g.restore();
}
function pinned(t, t0, t1) {
  if (t < t0 || t > t1) return;
  const a = vis(t, t0, 0.3) * (1 - vis(t, t1 - 0.15, 0.15));
  g.save(); g.globalAlpha = a; g.translate(0, 26 * (1 - eo((t - t0) / 0.3)));
  const a1 = "Who put her on the ", w1 = tw(a1, 58, 600);
  otxt(a1, 90, 282, 58, "#FFFFFF", "left", 6); otxt("reef", 90 + w1, 282, 58, "#F5A524", "left", 6); otxt("?", 90 + w1 + tw("reef", 58, 600), 282, 58, "#FFFFFF", "left", 6);
  g.restore();
}
function reconLabel(night, y) { pill(90, y || 308, "ILLUSTRATED RECONSTRUCTION · positions approximate" + (night ? " · night brightened" : " · time compressed"), { size: 21, h: 40, padX: 14, fill: "rgba(7,10,15,.7)", color: "#D6DCE4", ls: 0.6, r: 8 }); }
function clockChip(t, at, big, small, x, y) {
  const a = vis(t, at, 0.25); if (a <= 0) return;
  g.save(); g.globalAlpha = a; const X = x || 90, Y = y || 366, wv = Math.max(tw(big, 54, 600, -1), tw(small, 22, 600, 2)) + 56;
  rr(X, Y, wv, 118, 14); g.fillStyle = "rgba(7,10,15,.92)"; g.fill(); g.lineWidth = 2; g.strokeStyle = "rgba(255,255,255,.16)"; g.stroke();
  txt(small, X + 28, Y + 38, 22, "#8B93A0", "left", 600, 2); txt(big, X + 26, Y + 96, 54, "#F2F4F7", "left", 600, -1);
  g.restore();
}
function chip(t, at, x, y, label, o) {
  const a = vis(t, at, 0.18); if (a <= 0) return 0; o = o || {};
  const k = lerp(1.25, 1, pop(t, at, 0.3));
  g.save(); g.globalAlpha *= a; g.translate(x, y + 30); g.scale(k, k); g.translate(-x, -(y + 30));
  const w = pill(x, y, label, Object.assign({ size: 34, h: 64, padX: 24 }, o)); g.restore(); return w;
}
// running captions: 3–5 words at a time, spoken word in amber
const CHUNKS = [];
for (const ln of LN) { let cur = [], n = 0; const flush = () => { if (cur.length) CHUNKS.push({ s: cur[0].s, e: cur[cur.length - 1].e, toks: cur }); cur = []; n = 0; };
  for (const k of ln.tokens) { if (cur.length && (cur.length >= 4 || n + k.w.length + 1 > 21)) flush(); cur.push(k); n += k.w.length + 1; if (/[.?!:]$/.test(k.w)) flush(); } flush(); }
for (let i = 0; i < CHUNKS.length; i++) CHUNKS[i].until = i + 1 < CHUNKS.length ? Math.min(CHUNKS[i + 1].s - 0.03, CHUNKS[i].e + 0.6) : CHUNKS[i].e + 0.6;
function captions(t, y) {
  const c = CHUNKS.find((c) => t >= c.s - 0.06 && t < c.until); if (!c) return;
  let size = 70; const text = c.toks.map((k) => k.w).join(" "); const wAll = tw(text, size, 600); if (wAll > 850) size = Math.floor((size * 850) / wAll);
  const sp = tw(" ", size, 600) + size * 0.2; let x = 510 - (c.toks.reduce((a, k) => a + tw(k.w, size, 600), 0) + sp * (c.toks.length - 1)) / 2;
  const a = vis(t, c.s - 0.06, 0.1); g.save(); g.globalAlpha = a; g.translate(0, 10 * (1 - a));
  for (const k of c.toks) { const on = t >= k.s - 0.03 && t < k.e + 0.05; otxt(k.w, x, y || 1318, size, on ? "#F5A524" : "#FFFFFF", "left", 7); x += tw(k.w, size, 600) + sp; }
  g.restore();
}
function infoCard(t, at, y, h, num, title, sub, accent) {
  const a = vis(t, at, 0.22); if (a <= 0) return;
  g.save(); g.globalAlpha = a; g.translate(60 * (1 - eo((t - at) / 0.35)), 0);
  rr(90, y, 840, h, 16); g.fillStyle = "rgba(8,10,13,.94)"; g.fill(); g.lineWidth = 2; g.strokeStyle = "rgba(255,255,255,.14)"; g.stroke();
  g.fillStyle = accent; rr(90, y, 10, h, [16, 0, 0, 16]); g.fill();
  g.fillStyle = accent; circle(160, y + h / 2, 34); txt(String(num), 160, y + h / 2 + 17, 46, "#0A0C10", "center", 600, 0);
  if (sub) { txt(title, 222, y + h / 2 - 8, 40, "#F2F4F7", "left", 600); txt(sub, 222, y + h / 2 + 36, 29, "#A3ACB9", "left", 500, 0); }
  else txt(title, 222, y + h / 2 + 14, 40, "#F2F4F7", "left", 600);
  g.restore();
}

// ================= scenes =================
function sHook(t) {
  bowScene(NIGHT, t, 0.86 + 0.012 * t, 1, 1100);
  if (t > HOOK_OUT + 0.15) reconLabel(true);
}
function sDeparture(t) {                                                         // L2
  const a = cut(2), b = cut(3), u = (t - a) / (b - a), z = 1 + 0.05 * (1 - eo((t - a) / 0.5));
  const cam = camOf(CAM.wide); cam.s *= z + 0.03 * u;
  chart(cam, t, { k: lerp(0, 5.3, eio(u * 1.02)), labels: "VNAPBRT", ice: 0, minShip: 74 });
  reconLabel(false);
  chip(t, ls(2), 90, 366, "23 MARCH 1989 · ALASKA", { size: 30, h: 58 });
  const c0 = tok(2, "loaded") - 0.1, av = vis(t, c0, 0.25);
  if (av > 0) { g.save(); g.globalAlpha = av; g.translate(0, 30 * (1 - eo((t - c0) / 0.35)));
    rr(90, 1000, 620, 172, 16); g.fillStyle = "rgba(8,10,13,.94)"; g.fill(); g.lineWidth = 2; g.strokeStyle = "rgba(255,255,255,.14)"; g.stroke();
    txt("VLCC EXXON VALDEZ", 122, 1054, 34, "#F2F4F7", "left", 600, 0.5);
    txt("214,861 dwt · 3 years old", 122, 1098, 28, "#A3ACB9", "left", 500, 0);
    txt("≈ 200,000 t", 122, 1146, 36, "#F5A524", "left", 600, 0); txt("crude oil", 122 + tw("≈ 200,000 t", 36, 600, 0) + 14, 1146, 28, "#A3ACB9", "left", 500, 0);
    g.restore(); }
}
function sIce(t) {                                                               // L3
  const a = cut(3), b = cut(4), u = (t - a) / (b - a);
  chart(camMix(CAM.wide, CAM.mid, eio((t - a) / 1.1)), t, { k: lerp(5.3, 6.0, u), labels: "ABRIT", ice: clamp((t - a - 0.2) / 1.6), minShip: 80 });
  reconLabel(false);
}
function sDivert(t) {                                                            // L4
  const a = cut(4), b = cut(5), u = (t - a) / (b - a), k = lerp(6.0, 8.5, u);
  const cam = camMix(CAM.mid, { lat: 60.915, lon: -146.875, s: 150 }, eio(u)); chart(cam, t, { k, k0: 4, labels: "BRIT", ice: 1, minShip: 84 });
  reconLabel(false);
  if (t < tok(4, "steers")) chip(t, tok(4, "leaves"), 90, 366, "LEAVES THE LANES", { size: 34, h: 64, fill: "#F5A524", color: "#0A0C10" });
  else { chip(t, tok(4, "steers"), 90, 500, "COURSE 180° · DUE SOUTH", { size: 32, h: 62 }); chip(t, tok(4, "autopilot") - 0.25, 90, 576, "AUTOPILOT ON", { size: 32, h: 62, dot: "#00E5FF" }); }
  clockChip(t, tok(4, "steers"), "23:39", "LOCAL TIME");
}
function sReef(t) {                                                              // L5
  const a = cut(5), b = cut(6), u = (t - a) / (b - a), cam = camMix({ lat: 60.915, lon: -146.875, s: 150 }, CAM.reef, eio((t - a) / 1.2));
  chart(cam, t, { k: lerp(8.5, 8.95, u), k0: 5, labels: "BRIL", ice: 1, reef: 0.5 + 0.5 * Math.sin(t * 6), minShip: 90 });
  reconLabel(false);
  const g0t = tok(5, "gap"), gv = eo((t - g0t) / 0.6);
  if (t > g0t) { const A = XY(cam, ICE_TIP), B = XY(cam, BUOY), E = [lerp(A[0], B[0], gv), lerp(A[1], B[1], gv)];
    g.strokeStyle = "#0A0C10"; g.lineWidth = 9; g.lineCap = "round"; g.beginPath(); g.moveTo(A[0], A[1]); g.lineTo(E[0], E[1]); g.stroke();
    g.strokeStyle = "#F5A524"; g.lineWidth = 5; g.beginPath(); g.moveTo(A[0], A[1]); g.lineTo(E[0], E[1]); g.stroke();
    g.fillStyle = "#F5A524"; circle(A[0], A[1], 9); circle(E[0], E[1], 9);
    chip(t, tok(5, "less") - 0.15, (A[0] + B[0]) / 2 - 300, (A[1] + B[1]) / 2 + 46, "GAP ≈ 0.9 mile", { size: 38, h: 70, fill: "#F5A524", color: "#0A0C10" }); }
}
function sOrder(t) {                                                             // L6
  const a = cut(6), lt = t - a, out = tok(6, "leaves"), mv = eio((t - out) / 1.5);
  bridge(t, lt, {
    people: () => { person(170, "mate", 1, false, "THIRD MATE", t); person(540, "ab", 1, false, "HELMSMAN", t); person(900 + 340 * mv, "master", 1 - ss(0.45, 1, mv), false, "MASTER", t); },
    cards: () => {
      screenCard(60, 1084, 410, 206); txt("LOCAL TIME", 94, 1136, 24, "#8B93A0", "left", 600, 2.5); txt("23:52", 90, 1250, 100, "#F2F4F7", "left", 600, -3);
      screenCard(500, 1084, 430, 206); txt("HEADING", 534, 1136, 24, "#8B93A0", "left", 600, 2.5); txt("180°", 530, 1250, 100, "#F2F4F7", "left", 600, -3); txt("AUTOPILOT", 762, 1246, 24, "#00E5FF", "left", 600, 2);
    },
  });
  reconLabel(true);
  const o0 = tok(6, "instruction") - 0.15, ov = vis(t, o0, 0.25);
  if (ov > 0) { g.save(); g.globalAlpha = ov; g.translate(0, 24 * (1 - eo((t - o0) / 0.35)));
    rr(90, 366, 840, 262, 16); g.fillStyle = "rgba(8,10,13,.94)"; g.fill(); g.lineWidth = 3; g.strokeStyle = "#F5A524"; g.stroke();
    txt("MASTER’S ORDER", 126, 420, 26, "#F5A524", "left", 600, 2.5);
    g.globalAlpha = ov * vis(t, tok(6, "turn") - 0.05, 0.2); txt("Turn back when Busby Island", 124, 504, 54, "#F2F4F7", "left", 600);
    g.globalAlpha = ov * vis(t, tok(6, "light") - 0.05, 0.2); txt("Light is", 124, 584, 54, "#F2F4F7", "left", 600); txt("abeam.", 124 + tw("Light is ", 54, 600), 584, 54, "#F5A524", "left", 600);
    g.restore(); }
  if (t > out) chip(t, out, 930, 648, "MASTER LEAVES THE BRIDGE", { size: 30, h: 58, align: "right", fill: "#F5A524", color: "#0A0C10" });
}
function sAlone(t) {                                                             // L7
  const a = cut(7), lt = t - a, f0 = tok(7, "tired") - 0.1, n = vis(t, tok(7, "needed") - 0.3, 0.25);
  bridge(t, lt, {
    people: () => { person(170, "mate", 1, t > tok(7, "third") - 0.1, "THIRD MATE", t); person(540, "ab", 1, false, "HELMSMAN", t); },
    cards: () => {
      screenCard(60, 1084, 410, 206); txt("OFFICERS ON WATCH", 94, 1136, 24, "#8B93A0", "left", 600, 2.5);
      txt("1", 92, 1264, 130, "#F2F4F7", "left", 600, -3); txt("of the 2", 190, 1212, 38, "#A3ACB9", "left", 500, 0); txt("needed", 190, 1258, 38, "#A3ACB9", "left", 500, 0);
      screenCard(500, 1084, 430, 206, null, "rgba(0,229,255," + (0.15 + 0.7 * n).toFixed(2) + ")", 3);
      g.save(); g.globalAlpha = 0.3 + 0.7 * n; txt("NTSB FINDING", 534, 1136, 24, "#8B93A0", "left", 600, 2.5); txt("Two officers", 532, 1204, 50, "#F2F4F7", "left", 600); txt("were needed here", 534, 1254, 32, "#A3ACB9", "left", 500, 0); g.restore();
    },
  });
  reconLabel(true);
  if (t > f0) chip(t, f0, 90, 366, "FATIGUE · EXCESSIVE WORKLOAD", { size: 34, h: 66, fill: "#F2555A", color: "#FFFFFF" });
  if (t > tok(7, "alone") - 0.1) chip(t, tok(7, "alone") - 0.1, 90, 446, "ALONE ON WATCH", { size: 34, h: 66 });
}
function sBusby(t) {                                                             // L8
  const a = cut(8), b = cut(9), ab = tok(8, "abeam"), fx = tok(8, "fix"), late = tok(8, "late") - 0.25;
  const k = t < ab ? lerp(9.0, 10, eio((t - a) / (ab - a))) : lerp(10, 10.75, (t - ab) / (b - ab));
  const cam = camMix(CAM.busby, { lat: 60.87, lon: -146.86, s: 290 }, eio((t - ab) / (b - ab)));
  chart(cam, t, { k, k0: 7, labels: "BRL", ice: 1, reef: 0.3, minShip: 100, plan: t > fx ? eo((t - fx) / 1.2) : 0 });
  reconLabel(false);
  if (t > ab - 0.2) { const A = XY(cam, TR[10]), B = XY(cam, BUSBY), v = eo((t - ab + 0.2) / 0.4);
    g.strokeStyle = "rgba(138,36,118,.95)"; g.lineWidth = 5; g.setLineDash([14, 10]); g.beginPath(); g.moveTo(A[0], A[1]); g.lineTo(lerp(A[0], B[0], v), lerp(A[1], B[1], v)); g.stroke(); g.setLineDash([]);
    g.strokeStyle = "#14293D"; g.lineWidth = 5; g.beginPath(); g.arc(A[0], A[1], 22, 0, TAU); g.stroke(); g.fillStyle = "#14293D"; circle(A[0], A[1], 6);
    g.save(); g.globalAlpha = 1 - vis(t, late - 0.45, 0.3);
    chip(t, ab, A[0] - 330, A[1] - 32, "LIGHT ABEAM", { size: 30, h: 58 });
    if (t > fx - 0.1) chip(t, fx - 0.1, A[0] - 330, A[1] + 38, "FIX PLOTTED  ✓", { size: 30, h: 58, color: "#06202A", fill: "#00E5FF" });
    g.restore(); }
  if (t > fx + 0.5) chartLabel(cam, PLAN[2], "PLANNED TURN", 26, "#007A9C", -120, 10);
  if (t > late) chip(t, late, 90, 500, "TURN STARTS LATE", { size: 38, h: 70, fill: "#F2555A", color: "#FFFFFF" });
  clockChip(t, ab - 0.1, "23:55", "LOCAL TIME");
}
function sLookout(t) {                                                           // L9
  const a = cut(9), lt = t - a, st = tok(9, "starboard") - 0.2, port = tok(9, "it") - 0.05;
  bridge(t, lt, {
    red: true,
    people: () => {
      const v = vis(t, st, 0.25);
      if (v > 0) { g.save(); g.globalAlpha = v; g.strokeStyle = "#FF6B6B"; g.lineWidth = 5; g.beginPath(); g.arc(905, 674, 62 + 6 * Math.sin(t * 6), 0, TAU); g.stroke(); g.restore(); chip(t, st, 930, 520, "RED LIGHT · STARBOARD", { size: 30, h: 60, align: "right", fill: "#F2555A", color: "#FFFFFF" }); }
      const pv = vis(t, port, 0.25);
      if (pv > 0) { g.save(); g.globalAlpha = pv; g.strokeStyle = "rgba(255,255,255,.9)"; g.lineWidth = 5; g.setLineDash([12, 10]); g.beginPath(); g.arc(190, 674, 56, 0, TAU); g.stroke(); g.setLineDash([]); g.restore(); chip(t, port, 60, 520, "SHOULD BE HERE · PORT", { size: 30, h: 60 }); }
    },
    cards: () => {
      screenCard(60, 1084, 870, 206); txt("LOOKOUT REPORTS", 96, 1136, 24, "#8B93A0", "left", 600, 2.5);
      const w1 = tw("Red light, ", 54, 600); txt("Red light,", 94, 1210, 54, "#F2F4F7", "left", 600); txt("starboard bow", 94 + w1, 1210, 54, "#F2555A", "left", 600);
      g.save(); g.globalAlpha = 0.3 + 0.7 * vis(t, port, 0.25); txt("Should be to port: she is on the wrong side of the buoy", 96, 1262, 27, "#A3ACB9", "left", 500, 0); g.restore();
    },
  });
  reconLabel(true);
}
function sRudder(t) {                                                            // L10 + L11
  const a = cut(10), hitT = tok(11, "reef"), b = cut(12);
  const k = t < hitT ? lerp(10.9, 13, Math.pow(clamp((t - a) / (hitT - a)), 0.95)) : 13;
  const cam = camMix(CAM.close, CAM.hit, eio((t - a) / (hitT - a + 0.4)));
  const shake = t > hitT && t < hitT + 0.7 ? Math.sin((t - hitT) * 60) * 9 * (1 - (t - hitT) / 0.7) : 0;
  g.save(); g.translate(shake, shake * 0.5);
  chart(cam, t, { k, k0: 9, labels: "", ice: 1, reef: t < hitT ? 0.5 + 0.5 * Math.sin(t * 8) : 1, wake: t < hitT ? 1 : 1 - vis(t, hitT, 0.8) });
  if (t > hitT) { const p = XY(cam, G_POS), r = (t - hitT) * 520; g.strokeStyle = "rgba(242,85,90," + (0.9 * (1 - clamp((t - hitT) / 1.1))).toFixed(2) + ")"; g.lineWidth = 10; g.beginPath(); g.arc(p[0], p[1], r, 0, TAU); g.stroke(); }
  g.restore();
  reconLabel(false);
  const y0 = 366, items = [[tok(10, "right", 0), "RIGHT 10°"], [tok(10, "right", 1), "RIGHT 20°"], [tok(10, "hard"), "HARD RIGHT"]];
  items.forEach(([at, lab], i) => { if (t > at - 0.05) { chip(t, at - 0.05, 90, y0 + i * 80, lab, { size: 36, h: 66 }); g.save(); g.globalAlpha = vis(t, at, 0.2); otxt("ordered", 90 + tw(lab, 36, 600, 0.5) + 66, y0 + i * 80 + 44, 28, "#FFFFFF", "left", 5); g.restore(); } });
  if (t > tok(10, "too") - 0.05 && t < cut(11) + 0.4) chip(t, tok(10, "too") - 0.05, 90, y0 + 250, "TOO LATE", { size: 48, h: 86, fill: "#F2555A", color: "#FFFFFF" });
  if (t > cut(11)) { clockChip(t, ls(11), "JUST AFTER MIDNIGHT", "24 MARCH 1989", 90, y0 + 250); chip(t, tok(11, "12") - 0.1, 90, y0 + 384, "≈ 12 knots", { size: 36, h: 66, fill: "#F5A524", color: "#0A0C10" }); }
  pill(930, 366, "BLIGH REEF", { align: "right", size: 34, h: 64, fill: "rgba(7,10,15,.9)", color: "#FF6B72", stroke: "#F2555A", padX: 24 });
  if (t > hitT) chip(t, hitT, 540, 1124, "AGROUND", { size: 60, h: 100, align: "center", fill: "#F2555A", color: "#FFFFFF", padX: 36 });
}
function sSpill(t) {                                                             // L12
  const a = cut(12), b = cut(13), u = (t - a) / (b - a);
  chart(camMix(CAM.hit, CAM.spill, eio((t - a) / 2.2)), t, { k: 13, k0: 10, labels: "", ice: 1, reef: 0.6, wake: 0, slick: eo(u * 1.05) });
  reconLabel(false);
  const c1 = tok(12, "8") - 0.1, v1 = vis(t, c1, 0.25);
  if (v1 > 0) { g.save(); g.globalAlpha = v1; rr(90, 366, 840, 200, 16); g.fillStyle = "rgba(8,10,13,.94)"; g.fill(); g.lineWidth = 2; g.strokeStyle = "rgba(255,255,255,.14)"; g.stroke();
    txt("CARGO TANKS HOLED", 124, 418, 26, "#8B93A0", "left", 600, 2.5); txt("8 of 11", 906, 422, 40, "#F2555A", "right", 600, 0);
    for (let i = 0; i < 11; i++) { const on = i < 8 && t > c1 + 0.25 + i * 0.12; rr(124 + i * 71, 452, 58, 84, 9); g.fillStyle = on ? "#F2555A" : "#2A313B"; g.fill(); if (on) { g.fillStyle = "rgba(255,255,255,.2)"; rr(124 + i * 71, 452, 58, 22, [9, 9, 0, 0]); g.fill(); } }
    g.restore(); }
  const c2 = tok(12, "nearly") - 0.1, v2 = vis(t, c2, 0.25);
  if (v2 > 0) { const n = 10.8 * eo((t - c2) / (tok(12, "gallons") - c2 + 0.3)); g.save(); g.globalAlpha = v2; rr(90, 590, 840, 222, 16); g.fillStyle = "rgba(8,10,13,.94)"; g.fill(); g.lineWidth = 2; g.strokeStyle = "rgba(255,255,255,.14)"; g.stroke();
    txt("OIL SPILLED", 124, 642, 26, "#8B93A0", "left", 600, 2.5); const s = n.toFixed(1); txt(s, 118, 772, 130, "#F5A524", "left", 600, -4); txt("million gallons", 118 + tw(s, 130, 600, -4) + 20, 772, 44, "#F2F4F7", "left", 600);
    g.restore(); }
}
function sWho(t) {                                                               // L13
  const a = cut(13), inv = tok(13, "investigators") - 0.1;
  chart(camMix(CAM.spill, CAM.reef, eio((t - a) / 2.6)), t, { k: 13, k0: 5, labels: "BRL", ice: 1, reef: 0.6, wake: 0, slick: 1, minShip: 90 });
  g.fillStyle = "rgba(255,255,255,.22)"; g.fillRect(0, 0, W, H);
  reconLabel(false);
  const k = lerp(1.3, 1, pop(t, ls(13), 0.35)), av = vis(t, ls(13) - 0.05, 0.2);
  g.save(); g.globalAlpha = av; g.translate(90, 560); g.scale(k, k); otxt("So who put", 0, -70, 104, "#FFFFFF", "left", 8); otxt("her THERE?", -4, 86, 150, "#F5A524", "left", 8); g.restore();
  if (t > inv) chip(t, inv, 90, 720, "NTSB: not one man", { size: 46, h: 86, padX: 30 });
}
const FIND = [["third", 0, "THIRD MATE", "Fatigue and excessive workload"], ["master", 0, "MASTER", "Impaired by alcohol · no proper watch"], ["company", 0, "COMPANY", "No fit master, no rested and sufficient crew"],
  ["traffic", 0, "TRAFFIC SERVICE (VTS)", "Not effective"], ["pilotage", 0, "PILOTAGE", "Not effective"]];
function sFindings(t) {                                                          // L14
  const a = cut(14);
  chart(camOf(CAM.reef), t, { k: 13, k0: 5, labels: "BR", ice: 1, reef: 0.5, wake: 0, slick: 1, minShip: 90 });
  g.fillStyle = "rgba(255,255,255,.42)"; g.fillRect(0, 0, W, H);
  const hv = vis(t, a, 0.3); g.save(); g.globalAlpha = hv; pill(90, 262, "NTSB · PROBABLE CAUSE", { size: 34, h: 66, fill: "#F5A524", color: "#0A0C10", padX: 26, ls: 1.5 }); g.restore();
  FIND.forEach(([w, n, title, sub], i) => infoCard(t, tok(14, w, n) - 0.35, 352 + i * 152, 138, i + 1, title, sub, i < 2 ? "#F2555A" : "#F5A524"));
  if (t > tok(14, "pilotage")) { g.save(); g.globalAlpha = vis(t, tok(14, "pilotage") + 0.4, 0.3); pill(90, 1120, "Source: NTSB Marine Accident Report MAR-90/04", { size: 24, h: 44, padX: 16, fill: "rgba(7,10,15,.75)", color: "#D6DCE4", r: 8 }); g.restore(); }
}
const LESS = [["rest", "Rest is safety equipment", "Fatigue is the first cause the NTSB names"], ["put", "Two officers in tight water", "One to con, one to fix the position"], ["and", "Off the plan? Fix your position", "Again and again, until you are back on it"]];
function sLessons(t) {                                                           // L15
  const a = cut(15), z = 1.05 - 0.05 * eo((t - a) / 3);
  g.save(); g.translate(540, 1400); g.scale(z, z); g.translate(-540, -1400); bowScene(DAY, t, 0.7, 0.25, 1480); g.restore();
  const hv = vis(t, a, 0.3); g.save(); g.globalAlpha = hv; pill(90, 262, "FOR EVERY WATCHKEEPER", { size: 34, h: 66, fill: "#00E5FF", color: "#06202A", padX: 26, ls: 1.5 }); g.restore();
  LESS.forEach(([w, title, sub], i) => infoCard(t, tok(15, w, i === 2 ? 0 : 0) - 0.2, 362 + i * 200, 180, i + 1, title, sub, "#00E5FF"));
}
function sClose(t) {                                                             // L16 + lockup
  const a = cut(16), l2 = tok(16, "a") - 0.05, lock = NARR.voice_end + 0.25;
  bowScene(NIGHT, t, 0.9 + 0.01 * (t - a), 1, 1100);
  reconLabel(true, 1448);
  g.save(); g.globalAlpha = vis(t, ls(16) - 0.05, 0.2); otxt("One ship hit the reef.", 90, 372, 74, "#FFFFFF", "left", 7); g.restore();
  if (t > l2) { const k = lerp(1.3, 1, pop(t, tok(16, "system") - 0.05, 0.35));
    g.save(); g.globalAlpha = vis(t, l2, 0.2); otxt("A whole", 90, 480, 96, "#FFFFFF", "left", 8); g.restore();
    if (t > tok(16, "system") - 0.05) { g.save(); g.translate(84, 620); g.scale(k, k); otxt("SYSTEM", 0, 40, 196, "#F5A524", "left", 8); g.restore(); }
    if (t > tok(16, "put") - 0.05) { g.save(); g.globalAlpha = vis(t, tok(16, "put") - 0.05, 0.2); otxt("put her there.", 90, 780, 96, "#FFFFFF", "left", 8); g.restore(); } }
  const lv = vis(t, lock, 0.3);
  if (lv > 0) { g.save(); g.globalAlpha = lv; g.translate(0, 24 * (1 - eo((t - lock) / 0.35)));
    rr(90, 1236, 560, 136, 14); g.fillStyle = "rgba(5,6,9,.92)"; g.fill(); g.lineWidth = 1.5; g.strokeStyle = "rgba(255,255,255,.14)"; g.stroke();
    olLogo(116, 1262, 84); const wO = tw("OCEAN", 54, 600, -1.2); txt("OCEAN", 222, 1310, 54, "#F2F4F7", "left", 600, -1.2); txt("LINK", 222 + wO, 1310, 54, "#00E5FF", "left", 600, -1.2);
    txt("Incident Learnings", 224, 1352, 32, "#8B93A0", "left", 500, 0);
    pill(90, 1392, "Sources: NTSB MAR-90/04 · Alaska Oil Spill Commission (1990)", { size: 22, h: 42, padX: 14, fill: "rgba(7,10,15,.7)", color: "#D6DCE4", r: 8 });
    g.restore(); }
}

// ================= master =================
const SCENES = [[cut(2), sHook], [cut(3), sDeparture], [cut(4), sIce], [cut(5), sDivert], [cut(6), sReef], [cut(7), sOrder], [cut(8), sAlone], [cut(9), sBusby], [cut(10), sLookout],
  [cut(12), sRudder], [cut(13), sSpill], [cut(14), sWho], [cut(15), sFindings], [cut(16), sLessons], [Infinity, sClose]];
function draw(t) {
  t = clamp(t, 0, END - 1e-4); g = g0;
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.setLineDash([]); g.lineJoin = "miter"; g.globalCompositeOperation = "source-over";
  g.clearRect(0, 0, W, H);
  for (const [until, fn] of SCENES) if (t < until) { g.save(); fn(t); g.restore(); break; }
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.setLineDash([]);
  hook(t);
  pinned(t, HOOK_OUT + 0.25, cut(13));
  if (t < cut(16)) captions(t, (t >= cut(6) && t < cut(8)) || (t >= cut(9) && t < cut(10)) ? 1396 : 1318);
}
window.__drawScene = draw;
draw(0);

/* Shared drawing kit for the Exxon Valdez film. Everything is a pure function of time. */
"use strict";
const W = 1080, H = 1920, TAU = Math.PI * 2;
const cv = document.getElementById("cv");
const g0 = cv.getContext("2d");
const oc = document.createElement("canvas"); oc.width = W; oc.height = H;
const g1 = oc.getContext("2d");
let g = g0;

const clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
const lerp = (a, b, t) => a + (b - a) * t;
const ss = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const eo = (t) => 1 - Math.pow(1 - clamp(t), 3);
const eio = (t) => { t = clamp(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
const back = (t) => { t = clamp(t); const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); };
const rnd = (n) => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
const circle = (x, y, r) => { g.beginPath(); g.arc(x, y, Math.max(0, r), 0, TAU); g.fill(); };
const rr = (x, y, w, h, r) => { g.beginPath(); g.roundRect(x, y, w, h, r); };
const lin = (x0, y0, x1, y1, stops) => { const gr = g.createLinearGradient(x0, y0, x1, y1); for (const [o, c] of stops) gr.addColorStop(o, c); return gr; };
function glow(x, y, r, rgb, a) {
  const gr = g.createRadialGradient(x, y, 0, x, y, r);
  gr.addColorStop(0, "rgba(" + rgb + "," + a + ")"); gr.addColorStop(0.35, "rgba(" + rgb + "," + a * 0.35 + ")"); gr.addColorStop(1, "rgba(" + rgb + ",0)");
  g.fillStyle = gr; g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill();
}
function font(size, weight, ls) { g.font = (weight || 600) + " " + size + "px Inter, sans-serif"; g.letterSpacing = (ls === undefined ? -0.02 * size : ls) + "px"; }
function txt(s, x, y, size, color, align, weight, ls) {
  font(size, weight, ls); g.fillStyle = color; g.textAlign = align || "left"; g.textBaseline = "alphabetic"; g.fillText(s, x, y);
}
function tw(s, size, weight, ls) { font(size, weight, ls); return g.measureText(s).width; }
/* caption text: fill over a hard dark outline at 80% (Ocean Link reel-hooks spec) */
function otxt(s, x, y, size, color, align, ring) {
  font(size, 600); g.textAlign = align || "left"; g.textBaseline = "alphabetic";
  g.lineJoin = "round"; g.lineWidth = (ring || 7) * 2; g.strokeStyle = "rgba(5,6,9,.8)"; g.strokeText(s, x, y);
  g.fillStyle = color; g.fillText(s, x, y);
}
function pill(x, y, label, o) {
  o = o || {};
  const size = o.size || 30, padX = o.padX || 22, h = o.h || size + 26, w = tw(label, size, 600, o.ls || 0.5) + padX * 2 + (o.dot ? 30 : 0);
  const x0 = o.align === "center" ? x - w / 2 : o.align === "right" ? x - w : x;
  rr(x0, y, w, h, o.r || 12); g.fillStyle = o.fill || "rgba(7,10,15,.9)"; g.fill();
  if (o.stroke) { g.lineWidth = 2; g.strokeStyle = o.stroke; g.stroke(); }
  if (o.dot) { g.fillStyle = o.dot; circle(x0 + padX + 8, y + h / 2, 8); }
  txt(label, x0 + padX + (o.dot ? 30 : 0), y + h / 2 + size * 0.36, size, o.color || "#F2F4F7", "left", 600, o.ls || 0.5);
  return w;
}

// ---------- palettes ----------
const DAY = { sky: [[0, "#3FAEE6"], [0.45, "#8FD6F4"], [1, "#E9F8FC"]], cA: "#CDE9F6", cB: "#FFFFFF", sea: [[0, "#5BCBE5"], [0.18, "#1FA3C6"], [0.55, "#0C7391"], [1, "#084C62"]], night: false };
const NIGHT = { sky: [[0, "#132B58"], [0.5, "#2B5898"], [1, "#78AADB"]], cA: "#35619E", cB: "#5683BE", sea: [[0, "#6FA4D6"], [0.18, "#3A78B4"], [0.55, "#205489"], [1, "#143A66"]], night: true };

function sky(P, yH, sx, sy) {
  g.fillStyle = lin(0, 0, 0, yH, P.sky); g.fillRect(0, 0, W, yH + 4);
  if (P.night) {
    for (let i = 0; i < 70; i++) { const x = rnd(i * 3.3) * W, y = rnd(i * 7.1) * yH * 0.8, a = 0.35 + 0.65 * rnd(i * 1.7); g.fillStyle = "rgba(255,255,255," + (a * 0.8).toFixed(2) + ")"; circle(x, y, 1.2 + 1.8 * rnd(i * 5.9)); }
    if (sx) { glow(sx, sy, 260, "210,228,255", 0.35); g.fillStyle = "#F2F6FF"; circle(sx, sy, 74); g.fillStyle = "rgba(190,205,235,.55)"; circle(sx - 22, sy - 14, 15); circle(sx + 20, sy + 22, 10); }
  } else if (sx) {
    g.fillStyle = "rgba(255,248,214,.20)"; circle(sx, sy, 250); g.fillStyle = "rgba(255,248,214,.34)"; circle(sx, sy, 165); g.fillStyle = "#FFF8D6"; circle(sx, sy, 100);
  }
}
function cloud(P, cx, cy, s) {
  g.save(); g.translate(cx, cy); g.scale(s, s);
  const B = [[-130, 6, 58], [-58, -34, 80], [36, -50, 96], [128, -8, 70], [196, 14, 44]];
  g.fillStyle = P.cA; g.beginPath(); for (const [x, y, r] of B) { g.moveTo(x + r, y + 16); g.arc(x, y + 16, r, 0, TAU); } g.roundRect(-188, 4, 428, 62, 31); g.fill();
  g.fillStyle = P.cB; g.beginPath(); for (const [x, y, r] of B) { g.moveTo(x + r, y); g.arc(x, y, r, 0, TAU); } g.roundRect(-188, -8, 428, 58, 29); g.fill();
  g.restore();
}
function clouds(P, t, list) { for (const [x, y, s, v] of list) cloud(P, x - v * t, y, s); }
function seaBase(P, yH, yB) {
  g.fillStyle = lin(0, yH, 0, yB, P.sea); g.fillRect(0, yH, W, yB - yH);
  g.fillStyle = "rgba(255,255,255,.45)"; g.fillRect(0, yH - 1, W, 3);
}
function swell(yH, yB, t, m) {
  for (let i = 0; i < 7; i++) {
    const u0 = (i + 0.3) / 7, u1 = (i + 0.85) / 7;
    const y0 = yH + (yB - yH) * Math.pow(u0, 1.7), y1 = yH + (yB - yH) * Math.pow(u1, 1.7);
    const A = (4 + 26 * u0) * m, k = (0.02 - 0.012 * u0) / m, w = 0.5 + 0.5 * u0;
    g.fillStyle = i % 2 === 0 ? "rgba(255,255,255,.055)" : "rgba(3,40,70,.09)"; g.beginPath();
    for (let x = -20; x <= W + 20; x += 30) { const y = y0 + A * Math.sin(x * k + t * w + i * 2.1) + A * 0.4 * Math.sin(x * k * 2.3 - t * w * 1.3 + i); if (x === -20) g.moveTo(x, y); else g.lineTo(x, y); }
    for (let x = W + 20; x >= -20; x -= 30) g.lineTo(x, y1 + A * Math.sin(x * k + t * w + i * 2.1 + 1.2) + A * 0.4 * Math.sin(x * k * 2.3 - t * w * 1.3 + i + 2));
    g.closePath(); g.fill();
  }
}
function seaRows(yH, yB, t, rate, N, yMin, yMax, m) {
  g.lineCap = "round";
  for (let i = 0; i < N; i++) {
    const u = (((i / N + t * rate) % 1) + 1) % 1, pu = Math.pow(u, 2.1), y = yH + 6 + (yB - yH + 60) * pu;
    if (y < yMin || y >= yMax) continue;
    const amp = (2 + 30 * pu) * m, lam = (70 + 560 * pu) * m, lw = (1.2 + 5.5 * pu) * m, fade = ss(0, 0.1, u) * (1 - ss(0.93, 1, u)), seed = i * 17.3;
    const off = rnd(seed) * lam + t * (10 + 26 * pu) * (rnd(seed + 1) < 0.5 ? -1 : 1), base = Math.floor(off / lam), om = off - base * lam;
    for (let k = -2; k * lam + om < W + lam; k++) {
      const id = k - base, r = rnd(seed + id * 3.7); if (r < 0.3) continue;
      const len = lam * (0.34 + 0.44 * rnd(seed + id * 5.1)), x0 = k * lam + om + lam * 0.12 * r;
      g.strokeStyle = "rgba(4,40,70," + (0.18 * fade).toFixed(3) + ")"; g.lineWidth = lw * 2.4;
      g.beginPath(); g.moveTo(x0, y + amp * 0.6); g.quadraticCurveTo(x0 + len / 2, y + amp * 0.6 - amp * 0.9, x0 + len, y + amp * 0.6); g.stroke();
      g.strokeStyle = "rgba(255,255,255," + ((0.24 + 0.4 * pu) * fade).toFixed(3) + ")"; g.lineWidth = lw;
      g.beginPath(); g.moveTo(x0, y); g.quadraticCurveTo(x0 + len / 2, y - amp, x0 + len, y); g.stroke();
    }
  }
}
function glitter(t, cx, y0, y1, rgb) {
  for (let i = 0; i < 46; i++) {
    const u = rnd(i * 2.9), y = lerp(y0, y1, u * u), spread = 40 + 190 * u, x = cx + (rnd(i * 7.7) - 0.5) * 2 * spread;
    const a = 0.5 + 0.5 * Math.sin(t * (3 + 4 * rnd(i * 1.1)) + i);
    g.fillStyle = "rgba(" + rgb + "," + (0.55 * a * a).toFixed(3) + ")"; rr(x, y, 10 + 34 * u, 2 + 3 * u, 2); g.fill();
  }
}

// ---------- tanker, bow-on ----------
function shipXf(cx, yW, s, t) { g.translate(cx, yW + Math.sin(t * 1.1 + 1) * 3); g.rotate(Math.sin(t * 0.9) * 0.006); g.scale(s, s); }
function hullPath() {
  g.beginPath(); g.moveTo(-250, 40); g.lineTo(-250, -84); g.quadraticCurveTo(-250, -98, -236, -102); g.quadraticCurveTo(-120, -128, 0, -138);
  g.quadraticCurveTo(120, -128, 236, -102); g.quadraticCurveTo(250, -98, 250, -84); g.lineTo(250, 40); g.closePath();
}
function anchor(x, y) {
  g.fillStyle = "#0B1724"; rr(x - 20, y - 24, 40, 48, 9); g.fill();
  g.strokeStyle = "#B4C1CB"; g.lineWidth = 4; g.lineCap = "round";
  g.beginPath(); g.moveTo(x, y - 14); g.lineTo(x, y + 12); g.stroke();
  g.beginPath(); g.arc(x, y + 1, 12, 0.12 * Math.PI, 0.88 * Math.PI); g.stroke();
  g.beginPath(); g.moveTo(x - 8, y - 8); g.lineTo(x + 8, y - 8); g.stroke();
}
function shipBody(t) {
  g.fillStyle = "#16324A"; rr(-36, -280, 72, 50, 7); g.fill(); g.fillStyle = "#F5A524"; g.fillRect(-36, -264, 72, 13);
  g.strokeStyle = "#AEBBC6"; g.lineCap = "butt"; g.lineWidth = 6; g.beginPath(); g.moveTo(0, -246); g.lineTo(0, -330); g.stroke();
  g.lineWidth = 4; g.beginPath(); g.moveTo(-26, -296); g.lineTo(26, -296); g.moveTo(-16, -314); g.lineTo(16, -314); g.stroke();
  g.fillStyle = "#EAF0F4"; const r1 = 8 + 34 * Math.abs(Math.cos(t * 2.6)), r2 = 6 + 22 * Math.abs(Math.cos(t * 3.4 + 1));
  rr(-r1, -284, r1 * 2, 7, 3); g.fill(); rr(-r2, -306, r2 * 2, 6, 3); g.fill();
  g.fillStyle = lin(0, -236, 0, -96, [[0, "#FFFFFF"], [1, "#E4ECF1"]]); g.fillRect(-108, -236, 216, 144);
  g.strokeStyle = "#C3D0D9"; g.lineWidth = 2; for (let y = -206; y <= -122; y += 28) { g.beginPath(); g.moveTo(-108, y); g.lineTo(108, y); g.stroke(); }
  g.fillStyle = "#2B4357"; for (let row = 0; row < 3; row++) for (let i = 0; i < 7; i++) g.fillRect(-90 + i * 28, -198 + row * 28, 12, 11);
  g.fillStyle = "#E3EBF0"; g.fillRect(-72, -256, 144, 12); g.fillStyle = "#FFFFFF"; g.fillRect(-178, -246, 356, 30);
  g.fillStyle = "#16303F"; g.fillRect(-124, -240, 248, 15); g.fillStyle = "#FFFFFF"; for (let x = -100; x <= 100; x += 25) g.fillRect(x - 1.5, -240, 3, 15);
  g.strokeStyle = "#B9C7D1"; g.lineWidth = 2.5;
  for (const sd of [-1, 1]) {
    g.beginPath(); g.moveTo(sd * 124, -254); g.lineTo(sd * 178, -254); g.stroke();
    for (let x = 132; x <= 178; x += 15) { g.beginPath(); g.moveTo(sd * x, -254); g.lineTo(sd * x, -246); g.stroke(); }
    g.fillStyle = "#D5E0E7"; g.beginPath(); g.moveTo(sd * 108, -216); g.lineTo(sd * 172, -216); g.lineTo(sd * 108, -190); g.closePath(); g.fill();
  }
  g.strokeStyle = "#5B6F7F"; g.lineWidth = 6; g.beginPath(); g.moveTo(0, -136); g.lineTo(0, -212); g.stroke();
  g.lineWidth = 4; g.beginPath(); g.moveTo(-17, -192); g.lineTo(17, -192); g.stroke();
  g.save(); g.beginPath(); g.rect(-420, -720, 840, 722); g.clip();
  hullPath(); g.fillStyle = "#14293D"; g.fill();
  g.save(); hullPath(); g.clip();
  g.fillStyle = "#1D3C58"; g.fillRect(0, -200, 300, 300);
  g.fillStyle = lin(0, -138, 0, -60, [[0, "rgba(255,255,255,.10)"], [1, "rgba(255,255,255,0)"]]); g.fillRect(-260, -140, 520, 90);
  g.fillStyle = "#C4402E"; g.fillRect(-260, -18, 520, 60); g.fillStyle = "rgba(255,255,255,.55)"; g.fillRect(-260, -20, 520, 3);
  g.restore();
  g.strokeStyle = "#2B5275"; g.lineWidth = 6; g.beginPath(); g.moveTo(0, -138); g.lineTo(0, 4); g.stroke();
  g.strokeStyle = "#E6EDF2"; g.lineWidth = 4; g.lineCap = "round"; g.beginPath(); g.moveTo(-236, -102); g.quadraticCurveTo(-120, -128, 0, -138); g.quadraticCurveTo(120, -128, 236, -102); g.stroke();
  anchor(-160, -66); anchor(160, -66);
  g.fillStyle = "rgba(255,255,255,.7)"; for (let y = -62; y <= -26; y += 9) { g.fillRect(-22, y, 9, 2.5); g.fillRect(13, y, 9, 2.5); }
  g.restore();
}
function tankerBow(P, cx, yW, s, t, smoke) {
  if (!P.night) { g.save(); shipXf(cx, yW, s, t); shipBody(t); g.restore(); }
  else {
    // draw the ship on its own layer, cool it down for night, then add her lights
    g1.setTransform(1, 0, 0, 1, 0, 0); g1.clearRect(0, 0, W, H);
    g = g1; g.save(); shipXf(cx, yW, s, t); shipBody(t); g.restore();
    g.globalCompositeOperation = "source-atop"; g.fillStyle = "rgba(16,36,86,.46)"; g.fillRect(0, 0, W, H); g.globalCompositeOperation = "source-over";
    g = g0; g.drawImage(oc, 0, 0);
    g.save(); shipXf(cx, yW, s, t);
    g.fillStyle = "#FFD98A"; for (let row = 0; row < 3; row++) for (let i = 0; i < 7; i++) if (rnd(row * 7 + i * 3.1) > 0.35) g.fillRect(-90 + i * 28, -198 + row * 28, 12, 11);
    glow(0, -226, 120, "255,220,150", 0.16);
    glow(0, -332, 54, "255,255,255", 0.95); g.fillStyle = "#FFFFFF"; circle(0, -332, 6);       // aft masthead light
    glow(0, -214, 46, "255,255,255", 0.9); circle(0, -214, 5);                                     // forward masthead light
    glow(-178, -232, 44, "60,230,120", 0.95); g.fillStyle = "#6CFFA0"; circle(-178, -232, 5);      // starboard (green) — on the viewer's left
    glow(178, -232, 44, "255,70,70", 0.95); g.fillStyle = "#FF8A8A"; circle(178, -232, 5);         // port (red) — on the viewer's right
    g.restore();
  }
  g.save(); shipXf(cx, yW, s, t);
  if (smoke) for (let j = 0; j < 60; j++) {
    const age = ((t * 0.9 + j * 0.11) % 2.3 + 2.3) % 2.3, a = age / 2.3;
    g.fillStyle = (P.night ? "rgba(150,170,205," : "rgba(84,98,110,") + (0.3 * (1 - a) * (1 - a * 0.3)).toFixed(3) + ")";
    circle(18 + 54 * age + Math.sin(j * 2.3 + age * 2.1) * 9, -280 - 62 * age - 12 * a * a, 12 + 36 * a);
  }
  g.fillStyle = lin(0, 0, 0, 200, [[0, "rgba(7,22,44,.58)"], [1, "rgba(7,22,44,0)"]]);
  g.beginPath(); g.moveTo(-250, 0);
  for (let y = 0; y <= 200; y += 10) g.lineTo(-250 + Math.sin(y * 0.09 + t * 2.2) * 7 * (y / 60 + 0.3), y);
  for (let y = 200; y >= 0; y -= 10) g.lineTo(250 + Math.sin(y * 0.09 + t * 2.2 + 2) * 7 * (y / 60 + 0.3), y);
  g.closePath(); g.fill();
  if (P.night) for (const [x, rgb] of [[0, "255,255,255"], [-178, "60,230,120"], [178, "255,70,70"]]) {   // light paths on the water
    for (let i = 0; i < 9; i++) { const y = 26 + i * 26, w = 10 + i * 3 + 6 * Math.sin(t * 3 + i + x); g.fillStyle = "rgba(" + rgb + "," + (0.5 * (1 - i / 9)).toFixed(2) + ")"; rr(x - w + 4 * Math.sin(t * 2 + i), y, w * 2, 5, 3); g.fill(); }
  }
  g.restore();
}
function smoothPath(pts) {
  g.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length - 1; i++) g.quadraticCurveTo(pts[i][0], pts[i][1], (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2);
  const l = pts[pts.length - 1]; g.lineTo(l[0], l[1]);
}
function foamShape(sd, t, k, sc, dy) {
  const pts = [];
  for (let x = 0; x <= 330; x += 22) {
    const f = Math.pow(Math.sin(Math.PI * Math.pow(x / 330, 0.55)), 1.25);
    pts.push([sd * x * sc, dy - (50 * k * f + (8 * Math.sin(x * 0.057 - t * 7 + sd) + 3 * Math.sin(x * 0.13 + t * 5 + sd * 2)) * (0.3 + f)) * sc]);
  }
  for (let x = 330; x >= 0; x -= 30) pts.push([sd * x * sc, dy + (14 + 12 * Math.sin((Math.PI * x) / 330) + 2 * Math.sin(x * 0.1 + t * 4)) * sc]);
  g.beginPath(); smoothPath(pts); g.closePath();
}
function bowFoam(P, cx, yW, s, t, k) {
  g.save(); shipXf(cx, yW, s, t); g.lineCap = "round";
  const A = P.night ? "rgba(170,205,245,.85)" : "rgba(176,234,249,.85)", Bc = P.night ? "#E6F0FF" : "#FFFFFF";
  for (const sd of [-1, 1]) for (let i = 0; i < 16; i++) {
    const ph = (((i / 16 + t * 0.32) % 1) + 1) % 1, x = sd * lerp(262, 720, ph), y = lerp(10, 700, ph * ph * 0.6 + ph * 0.4), len = 26 + 120 * ph;
    g.strokeStyle = "rgba(255,255,255," + (0.72 * (1 - ph) * k).toFixed(3) + ")"; g.lineWidth = 3 + 9 * ph;
    g.beginPath(); g.moveTo(x - sd * len * 0.3, y - 6 * ph); g.quadraticCurveTo(x + sd * len * 0.2, y - 14 - 10 * ph, x + sd * len * 0.7, y + 8 * ph); g.stroke();
  }
  for (const sd of [-1, 1]) {
    foamShape(sd, t, k, 1.1, 5); g.fillStyle = A; g.fill();
    foamShape(sd, t + 0.07, k, 1, 0); g.fillStyle = Bc; g.fill();
    for (let i = 0; i < 20; i++) {
      const ph = (((t * 1.6 + rnd(i * 9.1 + sd)) % 1) + 1) % 1, vx = sd * (40 + 170 * rnd(i * 3.3 + sd)), vy = -(130 + 170 * rnd(i * 5.7 + sd)) * k;
      g.fillStyle = "rgba(255,255,255," + (0.95 * (1 - ph)).toFixed(3) + ")";
      circle(sd * (16 + 70 * rnd(i * 2.1)) + vx * ph, -22 + vy * ph + 270 * ph * ph, (2 + 4.5 * rnd(i * 1.3)) * (1 - ph * 0.4));
    }
  }
  g.fillStyle = Bc; g.beginPath(); g.ellipse(0, 0, 34, 26 * k + 4, 0, 0, TAU); g.fill();
  g.restore();
}
const CL1 = [[200, 318, 0.95, 5], [860, 585, 0.62, 3.4], [330, 905, 0.5, 2.4], [985, 830, 0.42, 2], [640, 700, 0.36, 1.8]];
function bowScene(P, t, s, k, yW) {
  const yH = yW - 190;
  sky(P, yH, 850, 262);
  clouds(P, t, CL1.map(([x, y, sc, v]) => [x, y * (yH / 1000), sc, v]));
  seaBase(P, yH, H);
  swell(yH, H, t, 1);
  glitter(t, 850, yH + 6, yH + 150, P.night ? "225,235,255" : "255,252,235");
  seaRows(yH, H, t, 0.07, 26, yH, yW - 6, 1);
  tankerBow(P, 540, yW, s, t, true);
  seaRows(yH, H, t, 0.07, 26, yW - 6, H + 200, 1);
  bowFoam(P, 540, yW, s, t, k);
}

// ---------- tanker from above (bow up, 520 units long) ----------
function tankerTop() {
  const hb = 44;
  const hull = () => { g.beginPath(); g.moveTo(0, -260); g.bezierCurveTo(27, -256, hb, -214, hb, -164); g.lineTo(hb, 214);
    g.bezierCurveTo(hb, 246, 30, 260, 0, 260); g.bezierCurveTo(-30, 260, -hb, 246, -hb, 214); g.lineTo(-hb, -164); g.bezierCurveTo(-hb, -214, -27, -256, 0, -260); g.closePath(); };
  g.save(); g.translate(12, 14); hull(); g.fillStyle = "rgba(4,40,56,.28)"; g.fill(); g.restore();
  hull(); g.fillStyle = "#A5422F"; g.fill();
  g.save(); hull(); g.clip();
  g.fillStyle = "#B4513B"; g.fillRect(-50, -262, 100, 62); g.fillStyle = "rgba(255,255,255,.07)"; g.fillRect(0, -262, 50, 524);
  g.strokeStyle = "rgba(60,14,8,.28)"; g.lineWidth = 2; for (let y = -150; y <= 150; y += 50) { g.beginPath(); g.moveTo(-hb, y); g.lineTo(hb, y); g.stroke(); }
  g.restore();
  hull(); g.strokeStyle = "#14293D"; g.lineWidth = 6; g.stroke();
  g.strokeStyle = "#CBD4DA"; g.lineWidth = 3; g.lineCap = "butt"; for (const x of [-8, 0, 8]) { g.beginPath(); g.moveTo(x, -158); g.lineTo(x, 160); g.stroke(); }
  g.lineWidth = 3.5; for (const y of [-12, -4, 4, 12]) { g.beginPath(); g.moveTo(-hb + 7, y); g.lineTo(hb - 7, y); g.stroke(); }
  g.fillStyle = "#8E9AA3"; g.fillRect(-hb + 5, -18, 9, 36); g.fillRect(hb - 14, -18, 9, 36);
  g.fillStyle = "#EEF2F5"; circle(-24, -34, 6); circle(24, -34, 6);
  g.fillStyle = "#C96B55"; for (const y of [-128, -84, 62, 106, 148]) { circle(-25, y, 5); circle(25, y, 5); }
  g.fillStyle = "#8E9AA3"; g.fillRect(-22, -232, 14, 9); g.fillRect(8, -232, 14, 9); circle(0, -214, 4);
  g.fillStyle = "#F4F8FA"; rr(-34, 170, 68, 54, 4); g.fill(); g.strokeStyle = "#C3D0D9"; g.lineWidth = 2; g.strokeRect(-26, 180, 52, 36);
  g.fillStyle = "#FFFFFF"; g.fillRect(-hb - 3, 168, (hb + 3) * 2, 13); g.fillStyle = "#16303F"; g.fillRect(-28, 168, 56, 4);
  g.fillStyle = "#16324A"; rr(-13, 228, 26, 17, 5); g.fill(); g.fillStyle = "#F5A524"; circle(0, 236.5, 4.5);
  g.fillStyle = "#F07F2E"; rr(-6, 246, 12, 13, 4); g.fill();
}

// ---------- Ocean Link mark ----------
function olLogo(x, y, size) {
  const k = size / 32;
  for (const [rx, ry, s, r, c] of [[3.4, 21.6, 4.6, 1.4, "#0B5D75"], [8.2, 17.4, 5.2, 1.6, "#0E86A6"], [13.6, 12.4, 5.8, 1.8, "#00B0D2"], [19.6, 6.6, 6.6, 2, "#00E5FF"], [23.4, 13.8, 5.4, 1.7, "#00B0D2"], [18.4, 18.6, 4.8, 1.5, "#0E86A6"]]) {
    g.fillStyle = c; rr(x + rx * k, y + ry * k, s * k, s * k, r * k); g.fill();
  }
}

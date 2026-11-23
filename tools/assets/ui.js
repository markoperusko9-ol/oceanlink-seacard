/* Ocean Link seafarer tools: shared page helpers (inputs, formatting, drawing). */
(function () {
  'use strict';
  var C = window.OLCalc;
  var $ = function (id) { return document.getElementById(id); };

  // Inside the app the page is shown without its own header, and tool links keep that mode.
  if (/[?&]embed=1/.test(location.search)) {
    document.documentElement.classList.add('embed');
    document.addEventListener('DOMContentLoaded', function () {
      document.querySelectorAll('a[href^="/tools/"]').forEach(function (a) {
        a.setAttribute('href', a.getAttribute('href').split('?')[0] + '?embed=1');
      });
    });
  }

  /* Number from an input; accepts a decimal comma. NaN when empty or not a number. */
  function num(id) {
    var el = $(id); if (!el) return NaN;
    var s = String(el.value).trim().replace(',', '.');
    if (s === '' || !/^[-+]?(\d+\.?\d*|\.\d+)$/.test(s)) return NaN;
    return parseFloat(s);
  }
  function val(id) { return $(id).value; }
  /* Latitude or longitude from the three inputs <p>d, <p>m and <p>h. Decimal degrees, N and E positive. */
  function latlon(p, maxDeg) {
    var d = num(p + 'd'), m = num(p + 'm');
    if (isNaN(m) && String($(p + 'm').value).trim() === '') m = 0;
    if (isNaN(d) || isNaN(m) || d < 0 || m < 0 || m >= 60 || d % 1 !== 0) return NaN;
    var v = d + m / 60;
    if (v > maxDeg) return NaN;
    var h = val(p + 'h');
    return (h === 'S' || h === 'W') ? -v : v;
  }
  /* Segmented control: buttons with data-v inside the element. Returns {get,set}. */
  function seg(id, onChange) {
    var el = $(id), btns = el.querySelectorAll('button');
    function set(v) { btns.forEach(function (b) { b.classList.toggle('on', b.dataset.v === v); }); el.dataset.v = v; }
    btns.forEach(function (b) {
      b.type = 'button';
      b.addEventListener('click', function () { set(b.dataset.v); if (onChange) onChange(b.dataset.v); });
    });
    set(el.dataset.v || btns[0].dataset.v);
    return { get: function () { return el.dataset.v; }, set: set };
  }
  function show(id, on) { var el = $(id); if (el) el.style.display = on ? '' : 'none'; }
  /* Re-run fn whenever any input or select inside the calculator changes. */
  function live(fn) {
    document.querySelectorAll('.calc input, .calc select').forEach(function (el) {
      el.addEventListener('input', fn); el.addEventListener('change', fn);
      if (el.tagName === 'INPUT' && el.type === 'text') el.addEventListener('focus', function () { el.select(); });
    });
    fn();
  }

  /* ---------- formatting ---------- */
  function fx(x, dp) {
    var s = x.toFixed(dp);
    if (parseFloat(s) === 0) s = (0).toFixed(dp); // no "-0.0"
    return s;
  }
  /* Thousands separator for big numbers. */
  function big(x, dp) {
    var s = fx(x, dp).split('.');
    s[0] = s[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return s.join('.');
  }
  /* Bearing or course as three figures: 045.3° */
  function brg(x, dp) {
    dp = dp === undefined ? 1 : dp;
    var r = parseFloat(C.norm360(x).toFixed(dp)); if (r >= 360) r = 0;
    var s = r.toFixed(dp), i = s.split('.')[0];
    return ('000' + i).slice(-3) + (dp ? '.' + s.split('.')[1] : '') + '°';
  }
  /* 35°12.5'N style. kind 'lat' or 'lon'. */
  function dm(x, kind) {
    var h = kind === 'lat' ? (x < 0 ? 'S' : 'N') : (x < 0 ? 'W' : 'E');
    var a = Math.abs(x), d = Math.floor(a), m = (a - d) * 60;
    if (parseFloat(m.toFixed(1)) >= 60) { d += 1; m = 0; }
    var w = kind === 'lat' ? 2 : 3;
    return ('000' + d).slice(-w) + '°' + (m < 9.95 ? '0' : '') + m.toFixed(1) + "'" + h;
  }
  /* Hours as "4 d 04 h 00 min". */
  function dur(hours) {
    var mins = Math.round(hours * 60), d = Math.floor(mins / 1440), h = Math.floor((mins % 1440) / 60), m = mins % 60;
    var s = (d ? d + ' d ' : '') + (d ? ('0' + h).slice(-2) : h) + ' h ' + ('0' + m).slice(-2) + ' min';
    return s;
  }
  var DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  /* Clock time stored as UTC milliseconds, printed as it stands. */
  function stamp(ms) {
    var d = new Date(Math.round(ms / 60000) * 60000);
    return DAYS[d.getUTCDay()] + ' ' + d.getUTCDate() + ' ' + MONTHS[d.getUTCMonth()] + ' ' + d.getUTCFullYear() + ', ' +
      ('0' + d.getUTCHours()).slice(-2) + ':' + ('0' + d.getUTCMinutes()).slice(-2);
  }
  function zone(off) {
    if (!off) return 'UTC';
    var a = Math.abs(off), h = Math.floor(a), m = Math.round((a - h) * 60);
    return 'UTC' + (off > 0 ? '+' : '−') + h + (m ? ':' + ('0' + m).slice(-2) : '');
  }
  /* Date input (yyyy-mm-dd) and time parts to milliseconds, read as UTC. NaN if invalid. */
  function dateMs(dateStr, h, m, s) {
    var p = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateStr || '');
    if (!p || isNaN(h) || isNaN(m) || h < 0 || h > 23 || m < 0 || m > 59 || h % 1 || m % 1) return NaN;
    s = s || 0; if (isNaN(s) || s < 0 || s >= 60) return NaN;
    var ms = Date.UTC(+p[1], +p[2] - 1, +p[3], h, m, 0) + Math.round(s * 1000);
    var chk = new Date(Date.UTC(+p[1], +p[2] - 1, +p[3]));
    if (chk.getUTCDate() !== +p[3]) return NaN;
    return ms;
  }
  function timeParts(str) { // "hh:mm" from a time input
    var p = /^(\d{1,2}):(\d{2})/.exec(str || '');
    return p ? [parseInt(p[1], 10), parseInt(p[2], 10)] : [NaN, NaN];
  }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  /* Rows for a .kv list: [[label, value], ...]; rows with a null value are skipped. */
  function kv(rows) {
    return '<div class="kv">' + rows.filter(function (r) { return r && r[1] !== null && r[1] !== undefined; }).map(function (r) {
      return '<div><span class="k">' + r[0] + '</span><span class="v">' + r[1] + '</span></div>';
    }).join('') + '</div>';
  }
  function out(id, html) { $(id).innerHTML = html; }
  function need(id, text) { out(id, '<p class="empty">' + (text || 'Fill in the fields above to see the result.') + '</p>'); }

  /* ---------- drawing (inline SVG, north up) ---------- */
  var COL = { text: '#F2F4F7', dim: '#8B93A0', faint: '#4A505A', line: '#FFFFFF24', grid: '#FFFFFF14', cyan: '#00E5FF', mid: '#00B0D2', warn: '#F5A524', crit: '#F2555A' };
  function svgOpen(w, h, label) {
    return '<svg viewBox="0 0 ' + w + ' ' + h + '" role="img" aria-label="' + esc(label) + '" xmlns="http://www.w3.org/2000/svg" font-family="Inter,system-ui,sans-serif">';
  }
  /* Point at bearing b (deg true) and radius r from (cx, cy), north up. */
  function pt(cx, cy, b, r) { return [cx + r * Math.sin(C.rad(b)), cy - r * Math.cos(C.rad(b))]; }
  function line(x1, y1, x2, y2, col, w, dash) {
    return '<line x1="' + x1.toFixed(1) + '" y1="' + y1.toFixed(1) + '" x2="' + x2.toFixed(1) + '" y2="' + y2.toFixed(1) +
      '" stroke="' + col + '" stroke-width="' + (w || 1.8) + '" stroke-linecap="round"' + (dash ? ' stroke-dasharray="' + dash + '"' : '') + '/>';
  }
  function arrow(x1, y1, x2, y2, col, w, dash) {
    var a = Math.atan2(y2 - y1, x2 - x1), L = Math.sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1));
    if (L < 2) return '';
    var s = Math.min(10, L * 0.45), bx = x2 - s * Math.cos(a), by = y2 - s * Math.sin(a);
    var p1 = [bx + s * 0.5 * Math.cos(a + Math.PI / 2), by + s * 0.5 * Math.sin(a + Math.PI / 2)];
    var p2 = [bx - s * 0.5 * Math.cos(a + Math.PI / 2), by - s * 0.5 * Math.sin(a + Math.PI / 2)];
    return line(x1, y1, bx, by, col, w, dash) + '<polygon points="' + x2.toFixed(1) + ',' + y2.toFixed(1) + ' ' +
      p1[0].toFixed(1) + ',' + p1[1].toFixed(1) + ' ' + p2[0].toFixed(1) + ',' + p2[1].toFixed(1) + '" fill="' + col + '"/>';
  }
  function text(x, y, s, col, size, anchor, weight) {
    return '<text x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '" fill="' + (col || COL.dim) + '" font-size="' + (size || 13) +
      '" font-weight="' + (weight || 500) + '" text-anchor="' + (anchor || 'middle') + '">' + esc(s) + '</text>';
  }
  function circle(cx, cy, r, stroke, fill, w, dash) {
    return '<circle cx="' + cx.toFixed(1) + '" cy="' + cy.toFixed(1) + '" r="' + r.toFixed(1) + '" fill="' + (fill || 'none') + '" stroke="' +
      (stroke || 'none') + '" stroke-width="' + (w || 1) + '"' + (dash ? ' stroke-dasharray="' + dash + '"' : '') + '/>';
  }
  /* Compass ring with ticks every 30 degrees and N E S W. */
  function rose(cx, cy, r) {
    var s = circle(cx, cy, r, COL.line, 'none', 1);
    for (var b = 0; b < 360; b += 30) {
      var a = pt(cx, cy, b, r), c = pt(cx, cy, b, r - (b % 90 === 0 ? 9 : 5));
      s += line(a[0], a[1], c[0], c[1], b % 90 === 0 ? COL.dim : COL.faint, 1.2);
    }
    var L = { 0: 'N', 90: 'E', 180: 'S', 270: 'W' };
    for (var k in L) { var q = pt(cx, cy, +k, r + 14); s += text(q[0], q[1] + 4.5, L[k], +k === 0 ? COL.text : COL.dim, 12, 'middle', 600); }
    return s;
  }
  /* Small ship outline pointing along heading h. */
  function ship(cx, cy, h, len, col) {
    var w = len * 0.34, p = [[0, -len / 2], [w / 2, -len * 0.18], [w / 2, len / 2], [-w / 2, len / 2], [-w / 2, -len * 0.18]];
    var a = C.rad(h), d = p.map(function (q) {
      return (cx + q[0] * Math.cos(a) - q[1] * Math.sin(a)).toFixed(1) + ',' + (cy + q[0] * Math.sin(a) + q[1] * Math.cos(a)).toFixed(1);
    }).join(' ');
    return '<polygon points="' + d + '" fill="#0F1217" stroke="' + (col || COL.text) + '" stroke-width="1.6" stroke-linejoin="round"/>';
  }
  /* Label placed just beyond a point, away from the centre. */
  function tag(cx, cy, x, y, s, col, size) {
    var dx = x - cx, dy = y - cy, L = Math.sqrt(dx * dx + dy * dy) || 1;
    var tx = x + dx / L * 14, ty = y + dy / L * 14 + 4;
    return text(tx, ty, s, col, size || 12, Math.abs(dx / L) < 0.35 ? 'middle' : dx > 0 ? 'start' : 'end', 600);
  }

  window.OLUI = {
    $: $, num: num, val: val, latlon: latlon, seg: seg, show: show, live: live,
    fx: fx, big: big, brg: brg, dm: dm, dur: dur, stamp: stamp, zone: zone, dateMs: dateMs, timeParts: timeParts,
    esc: esc, kv: kv, out: out, need: need, COL: COL,
    svgOpen: svgOpen, pt: pt, line: line, arrow: arrow, text: text, circle: circle, rose: rose, ship: ship, tag: tag
  };
})();

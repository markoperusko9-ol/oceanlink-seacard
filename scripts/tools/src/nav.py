"""Tool definitions: navigation and bridge watch."""
from build import num, select, seg, segfield, latlon, date, time, zone

G = '/guides/'
TOOLS = []

# =====================================================================================
# 1. Compass error by the Sun
# =====================================================================================
TOOLS.append(dict(
    slug='sun-compass-error-calculator', cat='Navigation', diagram=True,
    name='Compass error by the Sun',
    blurb='Azimuth and amplitude without an almanac. Gyro error, compass error and deviation.',
    icon='<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2 5-5 2 2-5z"/>',
    title='Compass Error Calculator: Sun Azimuth and Amplitude | Ocean Link',
    h1='Compass error by the Sun: azimuth and amplitude calculator',
    desc='Free Sun azimuth and amplitude calculator. Enter date, UTC time, position and the compass bearing to get gyro error, compass error and deviation. No almanac needed.',
    lead='Enter the date, the UTC time, your position and the bearing you took. The tool gives the Sun\'s true azimuth and your gyro or compass error. No almanac needed.',
    form=(
        '<h2>When and where</h2><div class="fields">'
        + date('date', 'Date (UTC)')
        + '<div class="f"><span class="l">Time (UTC): h, min, s</span><div class="row">'
          '<input id="hh" type="text" inputmode="numeric" placeholder="hh" aria-label="Hours UTC" autocomplete="off">'
          '<input id="mm" type="text" inputmode="numeric" placeholder="mm" aria-label="Minutes" autocomplete="off">'
          '<input id="ss" type="text" inputmode="numeric" placeholder="ss" aria-label="Seconds" autocomplete="off"></div></div>'
        + latlon('lat', 'Latitude', '20', '00.0', 'N', 'lat')
        + latlon('lon', 'Longitude', '000', '00.0', 'E', 'lon')
        + '</div><h2>Bearing of the Sun by compass</h2><div class="fields">'
        + segfield('cmode', 'Compass', [('gyro', 'Gyro'), ('mag', 'Magnetic')], cls='full')
        + num('cb', 'Observed bearing (°)', '', ph='e.g. 287.0')
        + '<div class="f" id="varrow"><span class="l">Variation (°)</span><div class="row">'
          '<input id="var" type="text" inputmode="decimal" placeholder="e.g. 2.0" aria-label="Variation" autocomplete="off">'
          '<select id="varh" class="sm" aria-label="Variation east or west"><option>E</option><option>W</option></select></div>'
          '<small>Optional. Gives the deviation.</small></div>'
        + '</div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI, $ = U.$;
  var now = new Date();
  $('date').value = now.toISOString().slice(0, 10);
  $('hh').value = ('0' + now.getUTCHours()).slice(-2); $('mm').value = ('0' + now.getUTCMinutes()).slice(-2); $('ss').value = '00';
  var dl = Math.max(-180, Math.min(180, Math.round(-now.getTimezoneOffset() / 4))); // rough longitude from the device clock
  $('lond').value = ('00' + Math.abs(dl)).slice(-3); $('lonh').value = dl < 0 ? 'W' : 'E';
  var mode = U.seg('cmode', run);
  function degmin(x, w) {
    var a = Math.abs(x), d = Math.floor(a), m = (a - d) * 60;
    if (parseFloat(m.toFixed(1)) >= 60) { d += 1; m = 0; }
    return ('000' + d).slice(-w) + '°' + (m < 9.95 ? '0' : '') + m.toFixed(1) + "'";
  }
  function ew(e) { var r = parseFloat(Math.abs(e).toFixed(1)); return r === 0 ? 'Nil' : r.toFixed(1) + '° ' + (e > 0 ? 'E' : 'W'); }
  function run() {
    var mag = mode.get() === 'mag'; U.show('varrow', mag);
    var ss = $('ss').value.trim() === '' ? 0 : U.num('ss');
    var ms = U.dateMs(U.val('date'), U.num('hh'), U.num('mm'), ss), lat = U.latlon('lat', 90), lon = U.latlon('lon', 180);
    if (isNaN(ms) || isNaN(lat) || isNaN(lon)) { U.need('res', 'Enter the date, the UTC time and your position.'); U.out('dia', ''); return; }
    var s = C.sunPosition(ms, lat, lon), az = parseFloat(s.az.toFixed(1)) % 360, cb = U.num('cb');
    var h = '<div class="label">Sun\'s true azimuth</div><div class="big" id="r_az">' + U.brg(az) + 'T</div><p class="sub">Altitude ' + U.fx(s.alt, 1) + '°</p>';
    var hasCb = !isNaN(cb) && cb >= 0 && cb <= 360, msg = '';
    if (hasCb) {
      var err = C.compassError(az, cb), t = ew(err);
      h += '<div class="label" style="margin-top:14px">' + (mag ? 'Compass error' : 'Gyro error') + '</div><div class="big" id="r_err">' + t +
        (mag || t === 'Nil' ? '' : ' <small>gyro ' + (err > 0 ? 'low' : 'high') + '</small>') + '</div>';
      var v = U.num('var');
      if (mag && !isNaN(v) && v >= 0 && v <= 180) {
        var dev = err - (U.val('varh') === 'W' ? -v : v);
        h += '<div class="label" style="margin-top:14px">Deviation</div><div class="big" id="r_dev">' + ew(dev) + ' <small>for the present heading</small></div>';
      }
    } else if ($('cb').value.trim() !== '') msg += '<div class="msg crit">Enter the compass bearing as a number from 0 to 360.</div>';
    var amp = C.amplitude(lat, s.dec), rows = [
      ['Declination', degmin(s.dec, 2) + (s.dec < 0 ? 'S' : 'N')], ['GHA Sun', degmin(s.gha, 3)], ['LHA Sun', degmin(s.lha, 3)]];
    if (amp) {
      var a = Math.abs(amp.amp).toFixed(1) + '° ' + amp.name;
      rows.push(['Amplitude at sunrise', 'E ' + a + ' (' + U.brg(amp.rise) + 'T)'], ['Amplitude at sunset', 'W ' + a + ' (' + U.brg(amp.set) + 'T)']);
    } else rows.push(['Amplitude', 'The Sun does not rise or set here today']);
    if (s.alt < -0.9) msg += '<div class="msg crit">The Sun is below the horizon at this time and position. Check the date, the UTC time and the position.</div>';
    else if (s.alt > 70) msg += '<div class="msg warn">The Sun is very high (altitude ' + U.fx(s.alt, 0) + '°). The azimuth changes fast near the zenith. Take the bearing when the Sun is lower, ideally below 30°.</div>';
    U.out('res', h + U.kv(rows) + msg);
    var cx = 160, cy = 152, r = 98, g = U.svgOpen(320, 300, 'Compass rose showing the true bearing of the Sun') + U.rose(cx, cy, r);
    if (amp) [amp.rise, amp.set].forEach(function (b) { var p = U.pt(cx, cy, b, r - 10), q = U.pt(cx, cy, b, r); g += U.line(p[0], p[1], q[0], q[1], U.COL.mid, 2.4); });
    if (hasCb) { var c1 = U.pt(cx, cy, cb, r - 16); g += U.line(cx, cy, c1[0], c1[1], U.COL.warn, 1.6, '4 4'); }
    var p1 = U.pt(cx, cy, az, r - 18), sp = U.pt(cx, cy, az, r - 6);
    g += U.arrow(cx, cy, p1[0], p1[1], U.COL.cyan, 2) + U.circle(sp[0], sp[1], 5.5, 'none', U.COL.cyan) + U.circle(cx, cy, 3, 'none', U.COL.text) + '</svg>';
    U.out('dia', g + '<figcaption>Cyan: true bearing of the Sun. ' + (hasCb ? 'Amber dashed: your compass bearing. ' : '') +
      (amp ? 'Blue marks on the ring: where the Sun rises and sets today.' : '') + '</figcaption>');
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<p>The tool works out where the Sun is for your date and UTC time, so you do not need an almanac. From the Sun\'s declination and Greenwich hour angle and your position it finds the local hour angle, then solves the navigational triangle for the true azimuth:</p>'
        '<div class="formula">tan Z = sin LHA ÷ (cos Lat × tan Dec − sin Lat × cos LHA)</div>'
        '<p>Compass error is always <strong>true minus compass</strong>. If the true bearing is the larger, the error is East, and a gyro is reading low. If the true bearing is the smaller, the error is West, and a gyro is reading high. For a magnetic compass, deviation = compass error − variation. Deviation belongs to the heading you were on, so log the heading with it.</p>'
        '<h3>Amplitude</h3>'
        '<p>The amplitude lines give the Sun\'s true bearing at theoretical sunrise and sunset, when its centre is on the celestial horizon:</p>'
        '<div class="formula">sin Amplitude = sin Declination ÷ cos Latitude</div>'
        '<p>At that moment the Sun\'s lower limb is still about half a diameter above the visible horizon. If you enter the exact time of your observation instead, the azimuth at the top is already the true bearing for that instant.</p>'
        '<h3>Worked example</h3>'
        '<p>Latitude 20°00\'N, declination 15°00\'N. sin Amp = 0.2588 ÷ 0.9397 = 0.2754, so the amplitude at sunset is W 16.0° N and the true bearing is 286.0°. The gyro showed 287.0°. Error = 286.0 − 287.0 = 1.0° W, gyro high.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>The Sun position was compared with a reference astronomical ephemeris for 1,500 random times and positions between 2026 and 2040. With the Sun above the horizon and below 80° altitude, the azimuth always agreed within 0.02°. Declination agreed within 0.2′ and GHA within 0.6′. That is ample for compass error, which is logged to 0.1° or 0.5°. It is not almanac grade, so do not use these figures for sight reduction.</p></div>'
        '<h3>Limits</h3><ul><li>The time must be UTC. A one-minute clock error can move the azimuth by a quarter of a degree, and by more when the Sun is high.</li>'
        '<li>Take the bearing with the Sun low, ideally below 30° altitude.</li>'
        '<li>Sun only. Stars, planets and the Moon are not included.</li></ul>'),
    faq=[
        ('Do I need a nautical almanac for this calculator?',
         'No. The Sun\'s declination and GHA are computed from the date and UTC time you enter. They agree with reference ephemeris data to a fraction of a minute of arc, which is ample for compass error.'),
        ('How do I name the compass error?',
         'Subtract the compass bearing from the true bearing. If true is larger the error is East. If true is smaller the error is West. For a gyro, East means the gyro reads low and West means it reads high.'),
        ('When should I take an amplitude?',
         'When the Sun\'s centre is on the celestial horizon, which is when its lower limb is about half a diameter above the visible horizon. If you enter the exact time of the observation instead, the tool gives the true azimuth for that moment.'),
    ],
    guides=[(G + 'navigation/azimuth-and-amplitude-observations/', 'Azimuth and amplitude observations'),
            (G + 'navigation/compass-error-deviation-and-variation/', 'Compass error, deviation and variation'),
            (G + 'navigation/gyro-error-and-how-to-find-it/', 'Gyro error and how to find it')],
))

# =====================================================================================
# 2. Great circle and rhumb line
# =====================================================================================
TOOLS.append(dict(
    slug='great-circle-rhumb-line-calculator', cat='Navigation', diagram=True, scripts=['geodesic.min.js'],
    name='Great circle and rhumb line',
    blurb='Distance, initial and final course, vertex, and the rhumb line for comparison.',
    icon='<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c3 3.2 3 14.800 0 18"/><path d="M12 3c-3 3.2-3 14.800 0 18"/>',
    title='Great Circle and Rhumb Line Distance Calculator | Ocean Link',
    h1='Great circle and rhumb line calculator',
    desc='Free great circle and rhumb line calculator on WGS84: distance, initial and final course, vertex and the saving over the rhumb line, plus the spherical exam answer.',
    lead='Enter two positions. You get the great circle distance and courses on WGS84, as an ECDIS works them, the rhumb line for comparison, and the spherical answer used in exams.',
    form=(
        '<h2>From</h2><div class="fields">' + latlon('alat', 'Latitude', '35', '00.0', 'N', 'lat') + latlon('alon', 'Longitude', '140', '00.0', 'E', 'lon')
        + '</div><h2>To</h2><div class="fields">' + latlon('blat', 'Latitude', '37', '00.0', 'N', 'lat') + latlon('blon', 'Longitude', '123', '00.0', 'W', 'lon') + '</div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI, G = geodesic.Geodesic;
  function lonLabel(x) { x = C.norm180(x); var a = Math.round(Math.abs(x)); return a === 0 || a === 180 ? a + '°' : a + '°' + (x < 0 ? 'W' : 'E'); }
  function run() {
    var a = U.latlon('alat', 90), b = U.latlon('alon', 180), c = U.latlon('blat', 90), d = U.latlon('blon', 180);
    if ([a, b, c, d].some(isNaN)) { U.need('res', 'Enter both positions. Minutes must be less than 60.'); U.out('dia', ''); return; }
    var g = G.WGS84.Inverse(a, b, c, d), gc = g.s12 / 1852;
    if (gc < 0.005) { U.need('res', 'The two positions are the same.'); U.out('dia', ''); return; }
    var sp = C.gcSphere(a, b, c, d), rh = C.rhumb(a, b, c, d);
    var h = '<div class="two"><div><div class="label">Great circle</div><div class="big" id="r_gc">' + U.big(gc, 1) + ' <small>nm</small></div><p class="sub">Initial course ' +
      U.brg(g.azi1) + 'T<br>Final course ' + U.brg(g.azi2) + 'T</p></div>';
    if (rh) h += '<div><div class="label">Rhumb line</div><div class="big" id="r_rh">' + U.big(rh.distNm, 1) + ' <small>nm</small></div><p class="sub">Course ' + U.brg(rh.course) + 'T</p></div>';
    h += '</div>';
    var rows = [];
    if (rh) { var save = rh.distNm - gc; rows.push(['Great circle saves', save >= 0.05 ? U.big(save, 1) + ' nm (' + U.fx(save / rh.distNm * 100, 1) + '%)' : 'Nothing on this leg']); }
    if (sp.vertex) rows.push(['Vertex', Math.abs(sp.vertex.lat) > 89.99 ? 'At the pole (sailing along a meridian)' :
      U.dm(sp.vertex.lat, 'lat') + ' ' + U.dm(sp.vertex.lon, 'lon') + (sp.vertex.onTrack ? '' : ' (outside the track)')]);
    rows.push(['Exam method (sphere): distance', U.big(sp.distNm, 1) + ' nm']);
    if (sp.initial !== null) rows.push(['Exam method (sphere): initial course', U.brg(sp.initial) + 'T']);
    if (rh) rows.push(['Difference of meridional parts', U.big(Math.abs(rh.dmp), 1)]);
    U.out('res', h + U.kv(rows));
    draw(a, b, c, d, g, sp, rh);
  }
  function draw(a, b, c, d, g, sp, rh) {
    var n = 72, line = G.WGS84.InverseLine(a, b, c, d), pts = [], i, endLon = b + C.norm180(d - b);
    for (i = 0; i <= n; i++) { var p = line.Position(g.s12 * i / n, G.STANDARD | G.LONG_UNROLL); pts.push([p.lon2, p.lat2]); }
    if (!rh || Math.abs(pts[n][0] - endLon) > 1) { U.out('dia', ''); return; }
    function my(lat) { lat = Math.max(-84, Math.min(84, lat)); return Math.log(Math.tan(Math.PI / 4 + C.rad(lat) / 2)); }
    var xs = pts.map(function (q) { return C.rad(q[0]); }), ys = pts.map(function (q) { return my(q[1]); });
    var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs), y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
    var W = 360, H = 260, mL = 38, mR = 12, mT = 12, mB = 26;
    var dx = Math.max(x1 - x0, 0.02), dy = Math.max(y1 - y0, 0.02);
    var s = Math.min((W - mL - mR) / (dx * 1.16), (H - mT - mB) / (dy * 1.3));
    var mx = (x0 + x1) / 2, myc = (y0 + y1) / 2, pcx = mL + (W - mL - mR) / 2, pcy = mT + (H - mT - mB) / 2;
    function X(lon) { return pcx + (C.rad(lon) - mx) * s; }
    function Y(lat) { return pcy - (my(lat) - myc) * s; }
    var lonSpan = C.deg((W - mL - mR) / s), steps = [1, 2, 5, 10, 20, 30, 60], st = 60;
    for (i = 0; i < steps.length; i++) if (lonSpan / steps[i] <= 6) { st = steps[i]; break; }
    var v = U.svgOpen(W, H, 'Mercator plot of the great circle and rhumb line tracks') + '<clipPath id="cp"><rect x="' + mL + '" y="' + mT + '" width="' + (W - mL - mR) + '" height="' + (H - mT - mB) + '"/></clipPath>';
    var lonMin = C.deg(mx) - lonSpan / 2, lonMax = C.deg(mx) + lonSpan / 2;
    for (var L = Math.ceil(lonMin / st) * st; L <= lonMax; L += st) v += U.line(X(L), mT, X(L), H - mB, U.COL.grid, 1) + U.text(X(L), H - mB + 15, lonLabel(L), U.COL.faint, 10.5);
    for (var P = -80; P <= 80; P += st) { var yy = Y(P); if (yy > mT && yy < H - mB) v += U.line(mL, yy, W - mR, yy, U.COL.grid, 1) + U.text(mL - 6, yy + 4, Math.abs(P) + '°' + (P === 0 ? '' : P < 0 ? 'S' : 'N'), U.COL.faint, 10.5, 'end'); }
    v += '<rect x="' + mL + '" y="' + mT + '" width="' + (W - mL - mR) + '" height="' + (H - mT - mB) + '" fill="none" stroke="' + U.COL.line + '"/>';
    v += '<g clip-path="url(#cp)">' + U.line(X(b), Y(a), X(endLon), Y(c), U.COL.dim, 1.8, '6 5');
    v += '<polyline fill="none" stroke="' + U.COL.cyan + '" stroke-width="2.2" stroke-linejoin="round" points="' + pts.map(function (q) { return X(q[0]).toFixed(1) + ',' + Y(q[1]).toFixed(1); }).join(' ') + '"/></g>';
    v += U.circle(X(b), Y(a), 4, 'none', U.COL.text) + U.circle(X(endLon), Y(c), 4, 'none', U.COL.text);
    v += U.text(X(b), Y(a) + (a >= c ? -10 : 18), 'From', U.COL.text, 11, X(b) < X(endLon) ? 'start' : 'end', 600) + U.text(X(endLon), Y(c) + (c > a ? -10 : 18), 'To', U.COL.text, 11, X(b) < X(endLon) ? 'end' : 'start', 600);
    U.out('dia', v + '</svg><figcaption>Mercator projection, no coastline. Cyan: great circle. Grey dashed: rhumb line.</figcaption>');
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<p><strong>Great circle.</strong> The main figures are the shortest path on the WGS84 ellipsoid, the same model an ECDIS uses, so they should match your route check to a tenth of a mile. The spherical figures further down are what the textbook formula gives, with one minute of arc taken as one nautical mile:</p>'
        '<div class="formula">cos D = sin Lat₁ × sin Lat₂ + cos Lat₁ × cos Lat₂ × cos d.long</div>'
        '<p>The two differ by up to about half a percent because the Earth is not a perfect sphere. Use the spherical line to check your exam working, and the WGS84 line for the passage plan.</p>'
        '<p><strong>Rhumb line.</strong> Mercator sailing on WGS84: tan Course = d.long ÷ DMP, and the distance is the length of the meridian arc between the two latitudes divided by the cosine of the course. On an exact east–west course the tool switches to parallel sailing.</p>'
        '<p><strong>Vertex.</strong> The point of the great circle nearest the pole, from cos Lat(v) = cos Lat₁ × sin Course. If it is marked outside the track, the highest latitude you actually reach is at your departure or arrival point.</p>'
        '<h3>Worked example</h3>'
        '<p>From 35°00\'N 140°00\'E to 37°00\'N 123°00\'W. The spherical method gives 4,476 nm, initial course 055.3° and a vertex near 47°40\'N 169°38\'W. On WGS84 the great circle is 4,489.4 nm and the rhumb line is 4,723.4 nm on 088.5°, so the great circle saves about 234 nm, at the price of going up to nearly 48°N.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>The WGS84 distances and courses were compared with the PROJ geodesic library for 460 pairs of positions, including pairs almost exactly opposite each other on the globe. They agreed to better than 0.001 nm. The rhumb line was compared with direct numerical integration for 157 pairs and agreed to better than 0.001 nm. The spherical method reproduces the worked example in the Ocean Link guide.</p></div>'
        '<h3>Limits</h3><ul><li>The tool knows nothing about land, ice, load line zones or weather. A great circle often has to be limited by a maximum latitude (composite sailing).</li>'
        '<li>The vertex is computed on the sphere, so it can differ from an ECDIS by a few miles.</li></ul>'),
    faq=[
        ('Why is the great circle distance different from my textbook answer?',
         'Textbook working treats the Earth as a sphere and one minute of arc as one nautical mile. An ECDIS and this tool use the WGS84 ellipsoid for the main figure. The two can differ by up to about half a percent. The spherical answer is shown as well so you can check your exam working.'),
        ('When is a great circle worth it over a rhumb line?',
         'On long passages with a large change of longitude in middle or high latitudes. Near the equator, or on courses close to north–south, the saving is small.'),
    ],
    guides=[(G + 'navigation/great-circle-vs-rhumb-line-sailing/', 'Great circle vs rhumb line sailing'),
            (G + 'operations/passage-planning-appraisal-planning-execution-monitoring/', 'Passage planning')],
))

# =====================================================================================
# 3. Set and drift, course to steer
# =====================================================================================
TOOLS.append(dict(
    slug='set-and-drift-course-to-steer-calculator', cat='Navigation', diagram=True,
    name='Set and drift, course to steer',
    blurb='Course to steer in a stream, set and drift between two fixes, course made good.',
    icon='<path d="M3 20l8-16"/><path d="M11 4l9 13"/><path d="M3 20h17"/><path d="M17 17l3 3-3 1"/>',
    title='Set and Drift and Course to Steer Calculator | Ocean Link',
    h1='Set and drift and course to steer calculator',
    desc='Free current triangle calculator: course to steer to counter a tidal stream, set, drift and rate between two fixes, and course and speed made good.',
    lead='Solve the current triangle three ways: the course to steer to hold a track, the set and drift you actually experienced, or the course and speed you will make good.',
    form=(
        seg('mode', [('cts', 'Course to steer'), ('sd', 'Set and drift'), ('cmg', 'Made good')], cls='modes')
        + '<div id="g_cts"><div class="fields">'
        + num('ctrack', 'Track to make good (°T)', '090') + num('cstw', 'Speed through water (kn)', '10')
        + num('cset', 'Set of the stream (°T)', '000', hint='The direction it flows towards') + num('crate', 'Rate (kn)', '2')
        + '</div></div><div id="g_sd"><div class="fields">'
        + num('scourse', 'Course steered (°T)', '045') + num('sstw', 'Speed through water (kn)', '10')
        + '<div class="f full"><span class="l">Time between the two fixes</span><div class="row">'
          '<input id="sth" type="text" inputmode="numeric" value="2" placeholder="h" aria-label="Hours" autocomplete="off">'
          '<input id="stm" type="text" inputmode="numeric" value="00" placeholder="min" aria-label="Minutes" autocomplete="off"></div></div>'
        + num('scmg', 'Course made good (°T)', '053.5', hint='Fix to fix') + num('sdist', 'Distance made good (nm)', '20.2', hint='Fix to fix')
        + '</div></div><div id="g_cmg"><div class="fields">'
        + num('mcourse', 'Course steered (°T)', '101.5') + num('mstw', 'Speed through water (kn)', '10')
        + num('mset', 'Set of the stream (°T)', '000', hint='The direction it flows towards') + num('mrate', 'Rate (kn)', '2')
        + '</div></div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI, $ = U.$;
  var mode = U.seg('mode', run);
  function okB(x) { return !isNaN(x) && x >= 0 && x <= 360; }
  function tri(course, stw, set, rate) { // vectors for one hour
    var A = [0, 0], B = [stw * Math.sin(C.rad(course)), stw * Math.cos(C.rad(course))];
    var D = [B[0] + rate * Math.sin(C.rad(set)), B[1] + rate * Math.cos(C.rad(set))];
    var xs = [A[0], B[0], D[0]], ys = [A[1], B[1], D[1]];
    var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs), y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
    var W = 320, H = 250, m = 34, s = Math.min((W - 2 * m) / Math.max(x1 - x0, 0.01), (H - 2 * m) / Math.max(y1 - y0, 0.01));
    function P(q) { return [W / 2 + (q[0] - (x0 + x1) / 2) * s, H / 2 - (q[1] - (y0 + y1) / 2) * s]; }
    var a = P(A), b = P(B), d = P(D);
    var g = U.svgOpen(W, H, 'Current triangle') + U.arrow(22, 44, 22, 16, U.COL.dim, 1.4) + U.text(22, 58, 'N', U.COL.dim, 11, 'middle', 600);
    g += U.arrow(a[0], a[1], b[0], b[1], U.COL.dim, 2) + U.arrow(b[0], b[1], d[0], d[1], U.COL.warn, 2) + U.arrow(a[0], a[1], d[0], d[1], U.COL.cyan, 2.2);
    g += U.circle(a[0], a[1], 3.5, 'none', U.COL.text) + '</svg>';
    U.out('dia', g + '<figcaption>Grey: course steered and speed through the water. Amber: the stream. Cyan: course and speed made good. Drawn for one hour.</figcaption>');
  }
  function run() {
    var m = mode.get(); U.show('g_cts', m === 'cts'); U.show('g_sd', m === 'sd'); U.show('g_cmg', m === 'cmg');
    var h, r;
    if (m === 'cts') {
      var tr = U.num('ctrack'), v = U.num('cstw'), set = U.num('cset'), rate = U.num('crate');
      if (!okB(tr) || !(v > 0) || !okB(set) || !(rate >= 0)) { U.need('res', 'Enter the track, your speed and the stream. Directions are 0 to 360.'); U.out('dia', ''); return; }
      r = C.courseToSteer(tr, v, set, rate);
      if (!r) { U.out('res', '<div class="msg crit" style="margin-top:0">The stream is too strong for this speed. The track cannot be held.</div>'); U.out('dia', ''); return; }
      var cor = parseFloat(Math.abs(r.correction).toFixed(1));
      h = '<div class="label">Course to steer</div><div class="big" id="r_main">' + U.brg(r.cts) + 'T</div><p class="sub">' +
        (cor === 0 ? 'No allowance needed' : 'Allow ' + cor.toFixed(1) + '° to ' + (r.correction > 0 ? 'starboard' : 'port')) + '. Add leeway separately if there is wind.</p>' +
        U.kv([['Speed made good', '<span id="r_smg">' + U.fx(r.smg, 1) + ' kn</span>']]);
      U.out('res', h); tri(r.cts, v, set, rate);
    } else if (m === 'sd') {
      var c = U.num('scourse'), s = U.num('sstw'), th = $('sth').value.trim() === '' ? 0 : U.num('sth'), tm = $('stm').value.trim() === '' ? 0 : U.num('stm');
      var cmg = U.num('scmg'), dist = U.num('sdist'), hrs = th + tm / 60;
      if (!okB(c) || !(s >= 0) || !(hrs > 0) || !(tm >= 0 && tm < 60) || !(th >= 0) || !okB(cmg) || !(dist >= 0)) { U.need('res', 'Enter what you steered, the time between fixes and what you made good.'); U.out('dia', ''); return; }
      r = C.setDrift(c, s, hrs, cmg, dist);
      if (r.set === null) { U.out('res', '<div class="label">Set and drift</div><div class="big">Nil</div><p class="sub">The fix is on the DR position.</p>'); U.out('dia', ''); return; }
      h = '<div class="two"><div><div class="label">Set</div><div class="big" id="r_main">' + U.brg(r.set, 0) + 'T</div></div><div><div class="label">Rate</div><div class="big" id="r_rate">' + U.fx(r.rate, 1) + ' <small>kn</small></div></div></div>' +
        U.kv([['Drift', U.fx(r.drift, 1) + ' nm in ' + U.dur(hrs)], ['Speed made good', U.fx(dist / hrs, 1) + ' kn']]) +
        '<div class="msg">This figure holds everything you did not allow for: stream, leeway, log error and steering error.</div>';
      U.out('res', h); tri(c, s, r.set, r.rate);
    } else {
      var c2 = U.num('mcourse'), s2 = U.num('mstw'), set2 = U.num('mset'), rate2 = U.num('mrate');
      if (!okB(c2) || !(s2 >= 0) || !okB(set2) || !(rate2 >= 0)) { U.need('res', 'Enter the course steered, your speed and the stream. Directions are 0 to 360.'); U.out('dia', ''); return; }
      r = C.madeGood(c2, s2, set2, rate2);
      if (r.cmg === null) { U.out('res', '<div class="label">Made good</div><div class="big">Stopped</div><p class="sub">The stream cancels your speed exactly.</p>'); U.out('dia', ''); return; }
      h = '<div class="two"><div><div class="label">Course made good</div><div class="big" id="r_main">' + U.brg(r.cmg) + 'T</div></div><div><div class="label">Speed made good</div><div class="big" id="r_smg">' + U.fx(r.smg, 1) + ' <small>kn</small></div></div></div>';
      U.out('res', h); tri(c2, s2, set2, rate2);
    }
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<p>All three modes solve the same vector triangle: what you do through the water, plus what the water does, equals what you do over the ground. Every side must cover the same time, so the tool works in one-hour vectors.</p>'
        '<p><strong>Set</strong> is the direction the stream flows <em>towards</em>, in degrees true. <strong>Rate</strong> is its speed in knots. <strong>Drift</strong> is the distance it carried you.</p>'
        '<p><strong>Course to steer.</strong> The part of the stream that pushes you across the track has to be cancelled by pointing the ship the other way:</p>'
        '<div class="formula">sin (allowance) = rate × sin (set − track) ÷ speed through water</div>'
        '<p><strong>Set and drift.</strong> Lay off what you steered from the first fix to get the DR. The line from the DR to the second fix is the set and drift. Always measure from DR to fix, never the other way.</p>'
        '<h3>Worked example</h3>'
        '<p>You want to make good 090°T at 10 kn through the water. The stream sets 000°T at 2 kn, straight across the track. sin α = 2 ÷ 10 = 0.2, so α = 11.5°. Steer 101.5°T. Speed made good = 10 × cos 11.5° = 9.8 kn.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>The three modes were run against each other on 2,000 random cases: the course to steer was fed back into the made-good calculation and had to return the intended track, and the set and rate recovered from the result had to match the stream that went in. They also reproduce both worked examples in the Ocean Link guide.</p></div>'
        '<h3>Limits</h3><ul><li>Leeway is not included. Apply it separately, into the wind.</li><li>The stream is taken as constant over the leg. For a long leg, work it hour by hour from the tidal stream atlas or the chart diamonds.</li></ul>'),
    faq=[
        ('What is the difference between set, drift and rate?',
         'Set is the direction the stream or current flows towards, in degrees true. Rate is its speed in knots. Drift is the distance it moves you in a given time.'),
        ('Why can the calculator not find a course to steer?',
         'If the part of the stream across your track is stronger than your speed through the water, no heading can hold the track. The same happens if the stream against you is stronger than your speed along the track.'),
    ],
    guides=[(G + 'navigation/tidal-streams-and-set-and-drift/', 'Tidal streams and set and drift'),
            (G + 'navigation/dead-reckoning-and-estimated-position/', 'Dead reckoning and estimated position')],
))

# =====================================================================================
# 4. ETA, speed, distance, time
# =====================================================================================
TOOLS.append(dict(
    slug='eta-speed-distance-time-calculator', cat='Navigation',
    name='ETA, speed, distance and time',
    blurb='ETA across time zones, the speed needed to arrive on time, or any one of speed, distance and time.',
    icon='<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
    title='ETA Calculator for Ships: Speed, Distance, Time and Time Zones | Ocean Link',
    h1='ETA, speed, distance and time calculator',
    desc='Free ship ETA calculator with time zones. Find the ETA in ship\'s time and UTC, the speed required to arrive on time, or solve speed, distance and time.',
    lead='Work out an ETA across time zones, the speed you need to make a pilot station on time, or any one of speed, distance and time from the other two.',
    form=(
        seg('mode', [('eta', 'ETA'), ('spd', 'Required speed'), ('sdt', 'Speed · distance · time')], cls='modes')
        + '<div id="g_voy"><div class="fields">'
        + num('dist', 'Distance to go (nm)', '1200') + '<div id="f_speed">' + num('speed', 'Speed (kn)', '12') + '</div>'
        + date('ddate', 'Departure date') + time('dtime', 'Departure time', '08:00')
        + zone('dzone', 'Clock kept at departure', 0) + zone('azone', 'Clock kept at arrival', 0)
        + '</div><div id="g_arr"><div class="fields">' + date('adate', 'Required arrival date') + time('atime', 'Required arrival time', '06:00') + '</div></div></div>'
        + '<div id="g_sdt"><div class="fields three">'
        + num('d2', 'Distance (nm)', '100') + num('s2', 'Speed (kn)', '12')
        + '<div class="f"><span class="l">Time (h, min)</span><div class="row">'
          '<input id="th" type="text" inputmode="numeric" placeholder="h" aria-label="Hours" autocomplete="off">'
          '<input id="tm" type="text" inputmode="numeric" placeholder="min" aria-label="Minutes" autocomplete="off"></div></div>'
        + '</div><p class="cap">Fill in two. The tool works out the one you leave empty.</p></div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI, $ = U.$;
  var t = new Date(), today = t.getFullYear() + '-' + ('0' + (t.getMonth() + 1)).slice(-2) + '-' + ('0' + t.getDate()).slice(-2);
  $('ddate').value = today;
  var a5 = new Date(t.getTime() + 5 * 86400000); $('adate').value = a5.getFullYear() + '-' + ('0' + (a5.getMonth() + 1)).slice(-2) + '-' + ('0' + a5.getDate()).slice(-2);
  var mode = U.seg('mode', run);
  function clock(dateId, timeId) { var p = U.timeParts(U.val(timeId)); return U.dateMs(U.val(dateId), p[0], p[1], 0); }
  function run() {
    var m = mode.get();
    U.show('g_voy', m !== 'sdt'); U.show('g_sdt', m === 'sdt'); U.show('g_arr', m === 'spd'); U.show('f_speed', m === 'eta');
    if (m === 'sdt') return sdt();
    var dist = U.num('dist'), dep = clock('ddate', 'dtime'), dz = parseFloat(U.val('dzone')), az = parseFloat(U.val('azone'));
    if (!(dist > 0) || isNaN(dep)) { U.need('res', 'Enter the distance and the departure date and time.'); return; }
    if (m === 'eta') {
      var sp = U.num('speed');
      if (!(sp > 0)) { U.need('res', 'Enter the speed.'); return; }
      var e = C.eta(dep, dz, az, dist, sp);
      U.out('res', '<div class="label">ETA, ship\'s time (' + U.zone(az) + ')</div><div class="big" id="r_main">' + U.stamp(e.arrLocalMs) + '</div>' +
        U.kv([['ETA in UTC', '<span id="r_utc">' + U.stamp(e.utcMs) + '</span>'], ['Steaming time', '<span id="r_time">' + U.dur(e.hours) + '</span> (' + U.fx(e.hours, 1) + ' h)'],
          ['Departure in UTC', U.stamp(dep - dz * 3600000)]]));
    } else {
      var arr = clock('adate', 'atime');
      if (isNaN(arr)) { U.need('res', 'Enter the required arrival date and time.'); return; }
      var r = C.requiredSpeed(dep, dz, arr, az, dist);
      if (r.speed === null) { U.out('res', '<div class="msg crit" style="margin-top:0">The arrival time is not after the departure time. Check the dates and the time zones.</div>'); return; }
      U.out('res', '<div class="label">Speed required</div><div class="big" id="r_main">' + U.fx(r.speed, 1) + ' <small>kn</small></div>' +
        U.kv([['Time available', '<span id="r_time">' + U.dur(r.hours) + '</span> (' + U.fx(r.hours, 1) + ' h)'], ['Arrival in UTC', U.stamp(arr - az * 3600000)]]));
    }
  }
  function sdt() {
    var d = U.num('d2'), s = U.num('s2'), hs = $('th').value.trim(), ms = $('tm').value.trim();
    var noT = hs === '' && ms === '', th = hs === '' ? 0 : U.num('th'), tm = ms === '' ? 0 : U.num('tm'), hrs = th + tm / 60;
    var noD = $('d2').value.trim() === '', noS = $('s2').value.trim() === '';
    var empty = (noD ? 1 : 0) + (noS ? 1 : 0) + (noT ? 1 : 0);
    if (empty !== 1) { U.need('res', empty === 0 ? 'Clear one of the three. The tool works out the empty one.' : 'Fill in two of the three.'); return; }
    if (noT) {
      if (!(d >= 0) || !(s > 0)) { U.need('res', 'Enter the distance and a speed above zero.'); return; }
      U.out('res', '<div class="label">Time</div><div class="big" id="r_main">' + U.dur(d / s) + '</div><p class="sub">' + U.fx(d / s, 2) + ' hours</p>');
    } else if (!(hrs > 0) || !(th >= 0) || !(tm >= 0)) { U.need('res', 'Enter the time as hours and minutes.'); }
    else if (noS) {
      if (!(d >= 0)) { U.need('res', 'Enter the distance.'); return; }
      U.out('res', '<div class="label">Speed</div><div class="big" id="r_main">' + U.fx(d / hrs, 1) + ' <small>kn</small></div><p class="sub">' + U.fx(d / hrs, 2) + ' kn</p>');
    } else {
      if (!(s >= 0)) { U.need('res', 'Enter the speed.'); return; }
      U.out('res', '<div class="label">Distance</div><div class="big" id="r_main">' + U.big(s * hrs, 1) + ' <small>nm</small></div>');
    }
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<div class="formula">Time = Distance ÷ Speed &nbsp;·&nbsp; Speed = Distance ÷ Time &nbsp;·&nbsp; Distance = Speed × Time</div>'
        '<p>For an ETA the tool first turns your departure time into UTC, adds the steaming time, and then turns the result into the clock kept at the arrival port. That is the safe order: do the sums in UTC and convert to ship\'s time only at the end.</p>'
        '<p>Choose the clock by its offset from UTC. East of Greenwich is plus, west is minus. If the ship or the port keeps daylight saving time, pick the offset actually in use.</p>'
        '<h3>Worked example</h3>'
        '<p>You leave at 08:00 on the 23rd, keeping UTC+1, with 1,200 nm to go at 12 kn. Steaming time = 1,200 ÷ 12 = 100 hours, which is 4 days 4 hours. Departure is 07:00 UTC on the 23rd, so the ETA is 11:00 UTC on the 27th. The arrival port keeps UTC+8, so the ETA in local time is 19:00 on the 27th.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>The time arithmetic is tested on fixed cases, including a passage across the date line from UTC+12 to UTC−11, where the local arrival time comes out on the same calendar day you left.</p></div>'
        '<h3>Limits</h3><ul><li>The speed is the average you will make good over the ground. Allow for current, weather and slow steaming in pilotage yourself.</li><li>The tool does not know when clocks will be advanced or retarded on passage. It only needs the clock at each end.</li></ul>'),
    faq=[
        ('How do I calculate a ship\'s ETA across time zones?',
         'Convert the departure time to UTC, add the steaming time (distance divided by speed), then convert the result to the time kept at the arrival port. Doing the sums in UTC avoids mistakes with clock changes on passage.'),
        ('What speed do I need to arrive at a set time?',
         'Find the time available in UTC between departure and the required arrival, then divide the distance by that time. The Required speed tab does this, including the time zones at both ends.'),
    ],
    guides=[(G + 'operations/passage-planning-appraisal-planning-execution-monitoring/', 'Passage planning: appraisal, planning, execution, monitoring'),
            (G + 'navigation/dead-reckoning-and-estimated-position/', 'Dead reckoning and estimated position')],
))

# =====================================================================================
# 5. True wind
# =====================================================================================
TOOLS.append(dict(
    slug='true-wind-calculator', cat='Bridge watch', diagram=True,
    name='True wind',
    blurb='True wind direction, speed and Beaufort force from the anemometer and your own course and speed.',
    icon='<path d="M3 8h10a3 3 0 1 0-3-3"/><path d="M3 12h15a3 3 0 1 1-3 3"/><path d="M3 16h7"/>',
    title='True Wind Calculator for Ships (with Beaufort Force) | Ocean Link',
    h1='True wind calculator',
    desc='Free true wind calculator for ships. Enter heading, speed and the relative wind from the anemometer to get true wind direction, speed in knots and m/s, and Beaufort force.',
    lead='The anemometer shows the wind as it feels on a moving ship. Enter your heading and speed and the relative wind to get the true wind for the logbook and the weather report.',
    form=(
        '<h2>Own ship</h2><div class="fields">' + num('hdg', 'Heading (°T)', '000') + num('spd', 'Speed (kn)', '10')
        + '</div><h2>Relative wind from the anemometer</h2><div class="fields">'
        + num('rel', 'Angle off the bow (°)', '90', hint='0 to 180. A 0 to 360 display reading 270 is 90 to port.')
        + segfield('side', 'Side', [('stbd', 'Starboard'), ('port', 'Port')])
        + num('ws', 'Wind speed', '10') + segfield('unit', 'Unit', [('kn', 'kn'), ('ms', 'm/s')])
        + '</div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI;
  var side = U.seg('side', run), unit = U.seg('unit', run);
  function run() {
    var hdg = U.num('hdg'), spd = U.num('spd'), rel = U.num('rel'), ws = U.num('ws');
    if (!(hdg >= 0 && hdg <= 360) || !(spd >= 0) || !(rel >= 0 && rel <= 180) || !(ws >= 0)) {
      U.need('res', 'Enter heading (0 to 360), speed, and the relative wind (angle 0 to 180).'); U.out('dia', ''); return;
    }
    var wk = unit.get() === 'ms' ? C.convert('speed', ws, 'm/s', 'kn') : ws;
    var relDir = side.get() === 'port' ? 360 - rel : rel;
    var w = C.trueWind(hdg, spd, relDir, wk), bf = C.beaufort(w.speed), h;
    if (w.dir === null || w.speed < 0.05) {
      h = '<div class="label">True wind</div><div class="big" id="r_main">Calm</div><p class="sub">The wind you feel is all your own speed.</p>';
    } else {
      var off = C.norm180(w.dir - hdg), offR = Math.round(Math.abs(off));
      h = '<div class="two"><div><div class="label">True wind from</div><div class="big" id="r_main">' + U.brg(w.dir, 0) + 'T</div></div>' +
        '<div><div class="label">Speed</div><div class="big" id="r_spd">' + U.fx(w.speed, 1) + ' <small>kn</small></div></div></div>' +
        U.kv([['Beaufort', '<span id="r_bf">Force ' + bf.force + ', ' + bf.desc + '</span>'], ['Speed in m/s', U.fx(C.convert('speed', w.speed, 'kn', 'm/s'), 1) + ' m/s'],
          ['True wind off the bow', offR === 0 ? 'Dead ahead' : offR === 180 ? 'Dead astern' : offR + '° to ' + (off > 0 ? 'starboard' : 'port')],
          ['Relative wind from (true bearing)', U.brg(w.apparentFrom, 0) + 'T']]);
    }
    U.out('res', h);
    var cx = 160, cy = 152, r = 98, g = U.svgOpen(320, 300, 'Compass rose with relative and true wind') + U.rose(cx, cy, r);
    var mx = Math.max(wk, w.speed, spd, 1), k = (r - 34) / mx;
    function wind(from, sp, col, dash) { if (sp < 0.05) return ''; var a = U.pt(cx, cy, from, 22 + sp * k), b = U.pt(cx, cy, from, 22); return U.arrow(a[0], a[1], b[0], b[1], col, 2, dash); }
    g += wind(w.apparentFrom, wk, U.COL.dim, '5 4');
    if (w.dir !== null) g += wind(w.dir, w.speed, U.COL.cyan);
    g += U.ship(cx, cy, hdg, 34) + '</svg>';
    U.out('dia', g + '<figcaption>North up, ship at the centre on her heading. Grey dashed: relative wind. Cyan: true wind. Arrow length shows speed.</figcaption>');
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<p>The relative (apparent) wind is the true wind combined with the head wind made by the ship\'s own movement. Take the ship\'s movement back out and the true wind is left:</p>'
        '<div class="formula">True wind = Relative wind − Ship\'s head wind &nbsp;(as vectors)</div>'
        '<p>The tool first turns the relative angle into a true bearing (heading plus the angle, to starboard or port), then subtracts the ship\'s course and speed vector. The true wind is always further aft than the relative wind, unless you are stopped.</p>'
        '<p>Wind direction is where the wind comes <em>from</em>. The Beaufort force is read from the WMO table using the true wind speed in whole knots.</p>'
        '<h3>Worked example</h3>'
        '<p>Heading 000°T at 10 kn. The anemometer shows 10 kn on the starboard beam (090° relative). The ship makes 10 kn of head wind from the north. Remove it and the true wind is from 135°T at 14.1 kn, Force 4.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>The calculation was run on 2,000 random cases built the other way round: a known true wind and ship movement were combined into a relative wind, and the tool had to return the original true wind. It also passes head wind, following wind and calm cases worked by hand, and every boundary of the Beaufort table.</p></div>'
        '<h3>Limits</h3><ul><li>Heading and speed through the water give the wind over the water, which is what the sea state follows. For wind over the ground, enter course and speed over the ground.</li>'
        '<li>The anemometer reads at its own height and is disturbed by the ship\'s structure. Check the result against the look of the sea.</li></ul>'),
    faq=[
        ('What is the difference between true wind and relative wind?',
         'Relative, or apparent, wind is what the anemometer measures on a moving ship. True wind is the wind over the sea with the ship\'s own movement taken out. Weather reports and the logbook use true wind.'),
        ('Why is the true wind always further aft than the relative wind?',
         'The ship\'s movement adds a head wind from right ahead. That pulls the relative wind towards the bow. Taking it out moves the direction aft again.'),
    ],
    guides=[(G + 'meteorology/beaufort-scale-and-sea-state/', 'Beaufort scale and sea state'),
            (G + 'meteorology/swell-wind-waves-and-parametric-rolling/', 'Swell, wind waves and parametric rolling')],
))

# =====================================================================================
# 6. CPA / TCPA
# =====================================================================================
TOOLS.append(dict(
    slug='cpa-tcpa-calculator', cat='Bridge watch', diagram=True,
    name='CPA and TCPA from two plots',
    blurb='Two timed radar plots give CPA, TCPA, the target\'s true course and speed, and its aspect.',
    icon='<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.500"/><path d="M12 12l6.400-6.400"/><circle cx="16.500" cy="9" r="0.600"/>',
    title='CPA and TCPA Calculator from Two Radar Plots | Ocean Link',
    h1='CPA and TCPA calculator',
    desc='Free CPA and TCPA calculator. Enter two timed radar bearings and ranges and your own course and speed to get CPA, TCPA, target true course, speed and aspect, with a plot.',
    lead='Enter two timed bearings and ranges of a target and your own course and speed. You get the CPA, the TCPA, the target\'s true course and speed and its aspect, with the plot drawn.',
    form=(
        '<h2>Own ship</h2><div class="fields">' + num('oc', 'Course (°T)', '000') + num('os', 'Speed (kn)', '12')
        + '</div><h2>First plot</h2><div class="fields three">' + time('t1', 'Time', '12:00') + num('b1', 'Bearing (°T)', '037') + num('r1', 'Range (nm)', '10.0')
        + '</div><h2>Second plot</h2><div class="fields three">' + time('t2', 'Time', '12:12') + num('b2', 'Bearing (°T)', '045') + num('r2', 'Range (nm)', '5.7') + '</div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI;
  function rg(x) { var a = Math.round(Math.abs(x)); return a === 0 ? 'right ahead' : a === 180 ? 'right astern' : (x > 0 ? 'Green ' : 'Red ') + a + '°'; }
  function hhmm(min) { min = ((Math.round(min) % 1440) + 1440) % 1440; return ('0' + Math.floor(min / 60)).slice(-2) + ':' + ('0' + (min % 60)).slice(-2); }
  function run() {
    var oc = U.num('oc'), os = U.num('os'), b1 = U.num('b1'), r1 = U.num('r1'), b2 = U.num('b2'), r2 = U.num('r2');
    var p1 = U.timeParts(U.val('t1')), p2 = U.timeParts(U.val('t2'));
    var okB = function (x) { return x >= 0 && x <= 360; };
    if (!okB(oc) || !(os >= 0) || !okB(b1) || !okB(b2) || !(r1 > 0) || !(r2 > 0) || isNaN(p1[0]) || isNaN(p2[0])) {
      U.need('res', 'Enter your course and speed and both plots. Bearings are true, 0 to 360.'); U.out('dia', ''); return;
    }
    var m1 = p1[0] * 60 + p1[1], m2 = p2[0] * 60 + p2[1], dt = m2 - m1; if (dt < 0) dt += 1440;
    if (dt === 0) { U.need('res', 'The two plots need different times.'); U.out('dia', ''); return; }
    var r = C.cpa(oc, os, b1, r1, b2, r2, dt), msg = '', h;
    var tc = r.tcpaMin === null ? '–' : (r.tcpaMin < 0 ? 'Passed' : U.fx(r.tcpaMin, 0) + ' <small>min</small>');
    h = '<div class="two"><div><div class="label">CPA</div><div class="big" id="r_cpa">' + U.fx(r.cpa, 2) + ' <small>nm</small></div></div>' +
      '<div><div class="label">TCPA</div><div class="big" id="r_tcpa">' + tc + '</div>' + (r.tcpaMin !== null && r.tcpaMin >= 0 ? '<p class="sub">at <span id="r_at">' + hhmm(m2 + r.tcpaMin) + '</span></p>' : '') + '</div></div>';
    var rows = [];
    if (r.cpaBrg !== null && r.cpa >= 0.005) rows.push(['Bearing at CPA', U.brg(r.cpaBrg, 0) + 'T (' + rg(C.norm180(r.cpaBrg - oc)) + ')']);
    rows.push(['Target true course', r.targetCourse === null ? 'Stopped' : '<span id="r_tco">' + U.brg(r.targetCourse, 0) + 'T</span>'],
      ['Target true speed', '<span id="r_tsp">' + U.fx(r.targetSpeed, 1) + ' kn</span>']);
    if (r.aspect !== null) rows.push(['Aspect', '<span id="r_asp">' + rg(r.aspect).replace('right ahead', '0° (bow on)').replace('right astern', '180° (stern on)') + '</span>']);
    if (r.relCourse !== null) rows.push(['Relative track', U.brg(r.relCourse, 0) + ' at ' + U.fx(r.relSpeed, 1) + ' kn']);
    rows.push(['Plot interval', dt + ' min']);
    if (r.tcpaMin === null) msg = '<div class="msg">No relative movement between the plots. The target is on your course and speed and the range is steady.</div>';
    else if (r.tcpaMin < 0) msg = '<div class="msg warn">The CPA was ' + U.fx(-r.tcpaMin, 0) + ' min before the second plot. The range is now opening.</div>';
    else if (r.cpa < 0.05) msg = '<div class="msg crit">Steady bearing and closing range. On these plots the CPA is zero.</div>';
    U.out('res', h + U.kv(rows) + msg);
    // plot
    var W = 340, H = 340, cx = W / 2, cy = H / 2, R = 138;
    var w = [r.p1[0] - os * Math.sin(C.rad(oc)) * dt / 60, r.p1[1] - os * Math.cos(C.rad(oc)) * dt / 60];
    var far = Math.max(r1, r2, Math.sqrt(w[0] * w[0] + w[1] * w[1]));
    var steps = [0.5, 1, 2, 3, 5, 10, 20], ring = 20; for (var i = 0; i < steps.length; i++) if (far / steps[i] <= 4.2) { ring = steps[i]; break; }
    var maxR = Math.ceil(far / ring) * ring, k = R / maxR;
    function P(q) { return [cx + q[0] * k, cy - q[1] * k]; }
    var g = U.svgOpen(W, H, 'Relative motion plot') + '<clipPath id="cp"><circle cx="' + cx + '" cy="' + cy + '" r="' + R + '"/></clipPath>';
    for (var q = ring; q <= maxR + 1e-9; q += ring) g += U.circle(cx, cy, q * k, q + 1e-9 >= maxR ? U.COL.line : U.COL.grid, 'none', 1) + U.text(cx + 3, cy - q * k + 12, (ring < 1 ? q.toFixed(1) : q) + '', U.COL.faint, 10, 'start');
    g += U.text(cx, cy - R - 6, 'N', U.COL.dim, 11, 'middle', 600);
    var O = P(r.p1), A = P(r.p2), Wp = P(w), hd = U.pt(cx, cy, oc, R);
    g += U.line(cx, cy, hd[0], hd[1], U.COL.grid, 1.2, '2 4');
    if (r.relCourse !== null) {
      var e = [r.p2[0] + Math.sin(C.rad(r.relCourse)) * maxR * 3, r.p2[1] + Math.cos(C.rad(r.relCourse)) * maxR * 3], E = P(e);
      g += '<g clip-path="url(#cp)">' + U.line(A[0], A[1], E[0], E[1], U.COL.cyan, 1.4, '5 4') + '</g>';
      if (r.tcpaMin >= 0) { var Cp = P(r.cpaPoint); g += U.line(cx, cy, Cp[0], Cp[1], U.COL.warn, 1.6) + U.circle(Cp[0], Cp[1], 3.5, 'none', U.COL.warn) + U.tag(cx, cy, Cp[0], Cp[1], 'CPA', U.COL.warn); }
    }
    g += U.arrow(Wp[0], Wp[1], O[0], O[1], U.COL.dim, 1.6) + U.arrow(Wp[0], Wp[1], A[0], A[1], U.COL.text, 1.8) + U.arrow(O[0], O[1], A[0], A[1], U.COL.cyan, 2.2);
    g += U.circle(O[0], O[1], 3, 'none', U.COL.cyan) + U.tag(cx, cy, O[0], O[1], 'O ' + hhmm(m1), U.COL.dim, 11) + U.tag(cx, cy, A[0], A[1], 'A ' + hhmm(m2), U.COL.text, 11) + U.tag(cx, cy, Wp[0], Wp[1], 'W', U.COL.dim, 11);
    g += U.ship(cx, cy, oc, 18) + '</svg>';
    U.out('dia', g + '<figcaption>Relative motion, north up, own ship at the centre. O to A (cyan): relative track, extended to the CPA. W to O (grey): own ship. W to A (white): the target\'s true course and speed. Range rings in nm.</figcaption>');
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<p>This is the manual radar plot done with numbers. Two timed positions of the target, O and A, give its <strong>relative track</strong>. Extend that line past your own ship: the shortest distance from the centre to the line is the <strong>CPA</strong>, and the time it takes the target to run from A to that point at its relative speed is the <strong>TCPA</strong>.</p>'
        '<p>To find what the target is really doing, lay off your own course reversed from O for the distance you ran in the plot interval. That gives W. The line from W to A is the target\'s <strong>true course and speed</strong>. <strong>Aspect</strong> is the relative bearing of your own ship as seen from the target: Red if you see her port side, Green if you see her starboard side.</p>'
        '<h3>Worked example</h3>'
        '<p>Own ship 000°T at 12 kn. At 1200 the target bears 037°T at 10.0 nm. At 1212 it bears 045°T at 5.7 nm. The relative track runs about 207° at 22 kn. CPA is about 1.8 nm on a bearing of 117°T at about 1227. The target is steering about 232°T at 12.6 kn.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>The calculation was run on 1,500 simulated encounters with random courses, speeds and starting positions. The CPA and TCPA had to match a brute-force search of the range minute by minute, and the target\'s true course and speed had to match what the simulation started with. It also reproduces the worked example in the Ocean Link guide.</p></div>'
        '<h3>Limits</h3><ul><li>The answer assumes both ships hold course and speed. Two plots cannot show that the target is altering. Keep plotting.</li>'
        '<li>Small errors in bearing matter at long range. A longer plot interval gives a steadier result.</li>'
        '<li>CPA and TCPA tell you whether a close-quarters situation is developing. They do not tell you who gives way. That comes from the Rules.</li></ul>'),
    faq=[
        ('What do CPA and TCPA mean?',
         'CPA is the closest point of approach: the shortest distance the target will pass from your ship if neither alters course or speed. TCPA is the time remaining until that moment.'),
        ('Do I need true or relative bearings?',
         'This calculator uses true bearings. If your radar is head-up and you read relative bearings, add your heading to each bearing first.'),
        ('Does CPA depend on my own speed input?',
         'No. CPA and TCPA come only from the two plots and the time between them. Your own course and speed are needed to turn the relative track into the target\'s true course, speed and aspect.'),
    ],
    guides=[(G + 'navigation/cpa-and-tcpa-explained/', 'CPA and TCPA explained'),
            (G + 'navigation/radar-plotting-and-relative-motion/', 'Radar plotting and relative motion'),
            (G + 'colregs/colreg-rule-7-risk-of-collision/', 'COLREG Rule 7: Risk of collision')],
))

"""Tool definitions: squat, engine, stability and converters."""
from build import num, select, seg, segfield

G = '/guides/'
TOOLS = []

# =====================================================================================
# 7. Squat and UKC
# =====================================================================================
TOOLS.append(dict(
    slug='squat-ukc-calculator', cat='Bridge watch', diagram=True,
    name='Squat and UKC',
    blurb='Barrass squat in open or confined water and the under keel clearance left at your speed.',
    icon='<path d="M4 9h16l-2 5H6z"/><path d="M3 18c2-1.500 4-1.500 6 0s4 1.500 6 0 4-1.500 6 0"/><path d="M12 5v4"/>',
    title='Squat and UKC Calculator (Barrass Formula) | Ocean Link',
    h1='Squat and under keel clearance calculator',
    desc='Free ship squat and UKC calculator using the Barrass formula for open and confined water. Enter Cb, speed, depth, tide and draught to see the clearance left under the keel.',
    lead='Estimate squat with the Barrass formula and see how much water is left under the keel at your planned speed.',
    form=(
        '<h2>Squat</h2><div class="fields">' + num('cb', 'Block coefficient (Cb)', '0.80') + num('v', 'Speed through water (kn)', '8')
        + segfield('water', 'Water', [('conf', 'Confined channel'), ('open', 'Open shallow water')], cls='full')
        + '</div><h2>Under keel clearance</h2><div class="fields">'
        + num('depth', 'Charted depth (m)', '12.40') + num('tide', 'Height of tide (m)', '2.10', neg=True)
        + num('draught', 'Deepest static draught (m)', '11.20')
        + num('other', 'Other allowances (m)', '1.68', hint='Heel, waves, chart accuracy, pressure. Optional.')
        + '</div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI, $ = U.$;
  var water = U.seg('water', run);
  function run() {
    var cb = U.num('cb'), v = U.num('v');
    if (!(cb >= 0.3 && cb <= 1) || !(v >= 0 && v <= 40)) { U.need('res', 'Enter the block coefficient (0.30 to 1.00) and the speed in knots.'); U.out('dia', ''); return; }
    var conf = water.get() === 'conf', sq = C.squat(cb, v, conf);
    var h = '<div class="two"><div><div class="label">Squat, ' + (conf ? 'confined channel' : 'open water') + '</div><div class="big" id="r_squat">' + U.fx(sq, 2) + ' <small>m</small></div></div>';
    var depth = U.num('depth'), tide = U.num('tide'), dr = U.num('draught'), other = $('other').value.trim() === '' ? 0 : U.num('other');
    var blank = $('depth').value.trim() === '' && $('draught').value.trim() === '';
    var hasUkc = depth > 0 && !isNaN(tide) && dr > 0 && other >= 0, rows = [], msg = '', avail = null;
    if (hasUkc) {
      var u = C.ukc(depth, tide, dr, sq, other); avail = Math.round((u.staticUkc - other) * 1e6) / 1e6; // 5.24 + 3.64 - 7.59 - 1.29 is 0, not 9e-16
      h += '<div><div class="label">Net under keel clearance</div><div class="big" id="r_ukc">' + U.fx(u.net, 2) + ' <small>m</small></div><p class="sub">' + U.fx(u.net / dr * 100, 1) + '% of draught</p></div>';
      rows = [['Depth of water (charted + tide)', U.fx(u.depth, 2) + ' m'], ['Static UKC', '<span id="r_static">' + U.fx(u.staticUkc, 2) + ' m</span>'], ['Squat', '−' + U.fx(sq, 2) + ' m']];
      if (other > 0) rows.push(['Other allowances', '−' + U.fx(other, 2) + ' m']);
      if (avail > 0) rows.push(['Net UKC falls to zero at', U.fx(Math.sqrt(avail * 100 / ((conf ? 2 : 1) * cb)), 1) + ' kn']);
      var ratio = u.depth / dr, shown = parseFloat(U.fx(ratio, 2)); rows.push(['Depth to draught ratio', U.fx(ratio, 2)]);
      // The warnings go by the figures as printed, so the words never disagree with the numbers beside them.
      if (parseFloat(U.fx(u.net, 2)) <= 0) msg += '<div class="msg crit">No clearance. On these figures the ship touches bottom.</div>';
      if (ratio > 1 + 1e-9 && (shown < 1.1 || shown > 1.4)) msg += '<div class="msg">The quick Barrass formulas are meant for a depth to draught ratio of about 1.1 to 1.4. Here it is ' + U.fx(ratio, 2) + ', so treat the squat figure with extra care.</div>';
    } else if (!blank) msg += '<div class="msg">For the clearance, enter the charted depth, the height of tide and the draught.</div>';
    h += '</div>';
    rows.push(['Squat in open shallow water', U.fx(C.squat(cb, v, false), 2) + ' m'], ['Squat in a confined channel', U.fx(C.squat(cb, v, true), 2) + ' m']);
    U.out('res', h + U.kv(rows) + msg);
    // chart: squat against speed
    var W = 360, H = 240, mL = 34, mR = 10, mT = 20, mB = 36, vmax = Math.max(16, Math.ceil((v + 2) / 2) * 2);
    var top = Math.max(C.squat(cb, vmax, true), avail || 0) * 1.08, ystep = top > 3 ? 1 : top > 1.5 ? 0.5 : 0.25;
    while (top / ystep > 9) ystep *= String(ystep).charAt(0) === '2' ? 2.5 : 2; // a few grid lines however deep the water
    function X(s) { return mL + s / vmax * (W - mL - mR); }
    function Y(m) { return H - mB - m / top * (H - mT - mB); }
    var g = U.svgOpen(W, H, 'Squat against speed'), s;
    for (var yv = 0; yv <= top; yv += ystep) g += U.line(mL, Y(yv), W - mR, Y(yv), U.COL.grid, 1) + U.text(mL - 5, Y(yv) + 4, yv.toFixed(ystep < 0.5 ? 2 : 1), U.COL.faint, 10.5, 'end');
    for (s = 0; s <= vmax; s += 2) g += U.text(X(s), H - mB + 14, s + '', U.COL.faint, 10.5);
    g += U.text(W - mR, H - 6, 'Speed through water (kn)', U.COL.faint, 10.5, 'end') + U.text(4, 12, 'Squat (m)', U.COL.faint, 10.5, 'start');
    function curve(c, col, w, dash) { var p = []; for (var q = 0; q <= vmax + 1e-9; q += 0.25) p.push(X(q).toFixed(1) + ',' + Y(C.squat(cb, q, c)).toFixed(1)); return '<polyline fill="none" stroke="' + col + '" stroke-width="' + w + '"' + (dash ? ' stroke-dasharray="' + dash + '"' : '') + ' points="' + p.join(' ') + '"/>'; }
    g += curve(!conf, U.COL.dim, 1.6, '5 4') + curve(conf, U.COL.cyan, 2.4);
    if (avail !== null && avail > 0 && avail <= top) g += U.line(mL, Y(avail), W - mR, Y(avail), U.COL.warn, 1.6) + U.text(mL + 6, Y(avail) - 6, 'Clearance available ' + U.fx(avail, 2) + ' m', U.COL.warn, 11, 'start');
    g += U.line(X(v), Y(0), X(v), Y(sq), U.COL.line, 1.2, '3 3') + U.circle(X(v), Y(sq), 5, 'none', U.COL.cyan) + '</svg>';
    U.out('dia', g + '<figcaption>Cyan: squat for the water you selected. Grey dashed: the other case. ' + (avail !== null && avail > 0 ? 'Amber: the clearance you have before squat. Where the curve meets it, the keel meets the bottom.' : '') + '</figcaption>');
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<p>Squat is the extra sinkage and trim of a ship moving through shallow water. The tool uses the quick estimates from Dr Barrass that are taught for bridge planning and exams, with V in knots through the water:</p>'
        '<div class="formula">Open shallow water: squat (m) = Cb × V² ÷ 100<br>Confined channel: squat (m) = 2 × Cb × V² ÷ 100</div>'
        '<p>Then the clearance is built up in the usual order:</p>'
        '<div class="formula">Depth of water = charted depth + height of tide<br>Static UKC = depth of water − deepest static draught<br>Net UKC = static UKC − squat − other allowances</div>'
        '<p>Put everything your company UKC policy asks for into <strong>Other allowances</strong>: heel in the turns, wave response, chart and survey accuracy, and the effect of high pressure on the tide.</p>'
        '<h3>Worked example</h3>'
        '<p>Charted depth 12.40 m, tide 2.10 m, draught 11.20 m, Cb 0.80, 8 kn in a confined channel. Depth of water 14.50 m, static UKC 3.30 m. Squat = 2 × 0.80 × 8² ÷ 100 = 1.02 m. Other allowances are 0.28 m heel, 1.25 m chart accuracy and 0.15 m pressure, 1.68 m in all. Net UKC = 3.30 − 1.02 − 1.68 = 0.60 m. Slowing to 6 kn cuts the squat to 0.58 m.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>The squat and clearance figures reproduce every worked example in the Ocean Link squat and UKC guides, including the laden bulk carrier at 10 and 7 knots and the container ship at 16 knots.</p></div>'
        '<h3>Limits</h3><ul><li>The Barrass formulas are empirical estimates, not measurements. They are intended to lean to the safe side, and they are meant for a depth to draught ratio of roughly 1.1 to 1.4.</li>'
        '<li>The confined channel figure is for a channel in which the ship\'s midship section fills about a tenth to a quarter of the cross-section of the water (blockage factor 0.10 to 0.265). In a narrower canal the squat is greater than this.</li>'
        '<li>Squat depends on speed through the water, not over the ground. A following current hides a high water speed.</li>'
        '<li>Your company SMS and the port decide the method and the minimum UKC. Ports and pilots often use more detailed methods.</li></ul>'),
    faq=[
        ('How do you calculate ship squat quickly?',
         'The common bridge estimate is the Barrass approximation. Maximum squat in metres equals Cb × V² ÷ 100 in open shallow water and twice that in a confined channel, with V in knots through the water.'),
        ('What is the fastest way to gain under keel clearance?',
         'Slow down. Squat grows with the square of the speed, so going from 8 to 6 knots cuts it by almost half. Waiting for more tide is the other lever.'),
    ],
    guides=[(G + 'operations/squat-and-shallow-water-effect/', 'Squat and shallow-water effect'),
            (G + 'navigation/under-keel-clearance-ukc-calculation/', 'Under keel clearance (UKC) calculation')],
))

# =====================================================================================
# 8. Propeller slip
# =====================================================================================
TOOLS.append(dict(
    slug='propeller-slip-calculator', cat='Engine',
    name='Propeller slip',
    blurb='Apparent slip from pitch, RPM and the distance run, for the noon report.',
    icon='<circle cx="12" cy="12" r="2"/><path d="M12 10c-3-1.500-3-6 0-7 2 2 2 5 0 7z"/><path d="M13.700 13c2.800-1.800 6.700 0.500 6.100 3.600-2.700 0.700-5.300-0.800-6.100-3.600z"/><path d="M10.300 13c0.200 3.300-3.700 5.600-6.100 3.600 0.700-2.700 3.300-4.200 6.100-3.600z"/>',
    title='Propeller Slip Calculator for Ships | Ocean Link',
    h1='Propeller slip calculator',
    desc='Free propeller slip calculator. Enter pitch, RPM, time and observed distance to get engine distance and apparent slip percent for the noon report.',
    lead='Work out apparent slip for the noon report from the propeller pitch, the revolutions and the distance the ship actually ran.',
    form=(
        seg('mode', [('per', 'Over a period'), ('now', 'At this moment')], cls='modes')
        + '<div id="g_per"><div class="fields">'
        + num('pitch', 'Propeller pitch (m)', '6.0') + num('rpm', 'Average RPM', '95')
        + '<div class="f"><span class="l">Steaming time (h, min)</span><div class="row">'
          '<input id="ph" type="text" inputmode="numeric" value="24" placeholder="h" aria-label="Hours" autocomplete="off">'
          '<input id="pm" type="text" inputmode="numeric" value="00" placeholder="min" aria-label="Minutes" autocomplete="off"></div></div>'
        + num('od', 'Observed distance (nm)', '420')
        + '</div></div><div id="g_now"><div class="fields">'
        + num('pitch2', 'Propeller pitch (m)', '6.0') + num('rpm2', 'RPM', '95') + num('os', 'Ship\'s speed (kn)', '17.5')
        + '</div></div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI, $ = U.$;
  var mode = U.seg('mode', run);
  function show(slip, rows) {
    var msg = parseFloat(U.fx(slip, 2)) < 0 ? '<div class="msg">Negative slip. The ship covered more ground than the propeller advanced, usually from a following current, sea or wind.</div>' : '';
    U.out('res', '<div class="label">Apparent slip</div><div class="big" id="r_main">' + U.fx(slip, 2) + ' <small>%</small></div>' + U.kv(rows) + msg);
  }
  function run() {
    var m = mode.get(); U.show('g_per', m === 'per'); U.show('g_now', m === 'now');
    if (m === 'per') {
      var p = U.num('pitch'), rpm = U.num('rpm'), ph = $('ph').value.trim() === '' ? 0 : U.num('ph'), pm = $('pm').value.trim() === '' ? 0 : U.num('pm'), od = U.num('od');
      var hrs = ph + pm / 60;
      if (!(p > 0) || !(rpm > 0) || !(hrs > 0) || !(ph >= 0) || !(pm >= 0 && pm < 60) || !(od >= 0)) { U.need('res', 'Enter the pitch, the average RPM, the steaming time and the observed distance.'); return; }
      var revs = rpm * 60 * hrs, ed = C.engineDistance(p, revs);
      show(C.slipPercent(ed, od), [['Engine distance', '<span id="r_ed">' + U.big(ed, 1) + ' nm</span>'], ['Observed distance', U.big(od, 1) + ' nm'],
        ['Engine speed', U.fx(C.engineSpeed(p, rpm), 2) + ' kn'], ['Observed speed', U.fx(od / hrs, 2) + ' kn'], ['Revolutions', U.big(revs, 0)]]);
    } else {
      var p2 = U.num('pitch2'), rpm2 = U.num('rpm2'), os = U.num('os');
      if (!(p2 > 0) || !(rpm2 > 0) || !(os >= 0)) { U.need('res', 'Enter the pitch, the RPM and the ship\'s speed.'); return; }
      var es = C.engineSpeed(p2, rpm2);
      show(C.slipPercent(es, os), [['Engine speed', '<span id="r_ed">' + U.fx(es, 2) + ' kn</span>'], ['Ship\'s speed', U.fx(os, 2) + ' kn']]);
    }
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<p>If the propeller turned in something solid it would move the ship forward by one pitch every revolution. That theoretical run is the <strong>engine distance</strong>. Water gives way, so the ship covers less. The shortfall, as a percentage of the engine distance, is the slip.</p>'
        '<div class="formula">Engine distance (nm) = pitch (m) × revolutions ÷ 1,852<br>Slip (%) = (engine distance − observed distance) ÷ engine distance × 100</div>'
        '<p>Revolutions are average RPM × 60 × hours, or the difference in the revolution counter. Take the steaming time actually run between the two readings, which is 23 or 25 hours on a day the clocks were changed.</p>'
        '<h3>Worked example</h3>'
        '<p>Pitch 6.0 m, 95 RPM for 24 hours, observed distance 420 nm. Revolutions = 95 × 60 × 24 = 136,800. Engine distance = 6.0 × 136,800 ÷ 1,852 = 443.2 nm. Slip = (443.2 − 420) ÷ 443.2 × 100 = 5.23%.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>The formulas are tested against the worked example above, worked by hand, and against a negative-slip case.</p></div>'
        '<h3>Limits</h3><ul><li>This is apparent slip. It includes the effect of current, wind, sea, hull fouling and draught, not just the propeller.</li>'
        '<li>Use the pitch from the ship\'s propeller drawing. For a controllable pitch propeller, use the pitch at the setting actually in use.</li></ul>'),
    faq=[
        ('What is a normal propeller slip?',
         'It depends on the ship, her loading and the weather, so compare with your own ship\'s record. A rising trend at the same draught and weather points to hull or propeller fouling.'),
        ('Why is my slip negative?',
         'The ship covered more distance than the propeller\'s theoretical advance. A following current, sea or strong wind astern does this. Check the observed distance and the steaming time as well.'),
    ],
    guides=[(G + 'systems/main-engine-two-stroke-slow-speed-diesel/', 'Main engine: two-stroke slow-speed diesel'),
            (G + 'systems/controllable-pitch-propeller/', 'Controllable pitch propeller')],
))

# =====================================================================================
# 9. Fuel
# =====================================================================================
TOOLS.append(dict(
    slug='fuel-consumption-calculator', cat='Engine',
    name='Fuel consumption and ROB',
    blurb='Daily consumption, days of fuel left, range, and fuel remaining on arrival.',
    icon='<path d="M12 3s6 6.200 6 11a6 6 0 0 1-12 0c0-4.800 6-11 6-11z"/><path d="M9.500 14.500a2.500 2.500 0 0 0 2.500 2.500"/>',
    title='Ship Fuel Consumption and ROB Calculator | Ocean Link',
    h1='Fuel consumption and ROB calculator',
    desc='Free ship fuel calculator. Enter fuel consumed, ROB, speed and distance to get daily consumption, days of fuel left, range and the ROB on arrival.',
    lead='Turn a consumption figure into tonnes per day, see how many days and miles the fuel on board will last, and check what will be left on arrival.',
    form=(
        '<h2>Consumption</h2><div class="fields">' + num('cons', 'Fuel consumed (t)', '30') + num('hours', 'Over how many hours', '24')
        + '</div><h2>Fuel on board and voyage</h2><div class="fields">'
        + num('rob', 'ROB now (t)', '600') + num('speed', 'Speed (kn)', '14', hint='Optional. Gives the range.')
        + num('dist', 'Distance to go (nm)', '3000', hint='Optional. Gives the ROB on arrival.')
        + num('newspeed', 'Another speed to compare (kn)', '', hint='Optional. Cube-law estimate.', ph='e.g. 12')
        + '</div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI, $ = U.$;
  function run() {
    var cons = U.num('cons'), hours = U.num('hours'), rob = U.num('rob'), sp = U.num('speed'), dist = U.num('dist'), ns = U.num('newspeed');
    if (!(cons > 0) || !(hours > 0)) { U.need('res', 'Enter the fuel consumed and the number of hours it covers.'); return; }
    var hasRob = rob >= 0, f = C.fuel(cons, hours, hasRob ? rob : 0, sp > 0 ? sp : 0, dist >= 0 ? dist : -1), msg = '';
    var h = '<div class="two"><div><div class="label">Daily consumption</div><div class="big" id="r_daily">' + U.fx(f.daily, 1) + ' <small>t/day</small></div></div>';
    if (hasRob) h += '<div><div class="label">Fuel lasts</div><div class="big" id="r_days">' + U.fx(f.daysLeft, 1) + ' <small>days</small></div></div>';
    h += '</div>';
    var rows = [['Per hour', U.fx(f.perHour, 2) + ' t/h']];
    if (sp > 0) {
      rows.push(['Per nautical mile', U.fx(f.perNm * 1000, 1) + ' kg/nm']);
      if (hasRob) rows.push(['Range at ' + U.fx(sp, 1) + ' kn', '<span id="r_range">' + U.big(f.rangeNm, 0) + ' nm</span>']);
      if (dist >= 0) {
        rows.push(['Time for ' + U.big(dist, 0) + ' nm', U.dur(f.voyageDays * 24)], ['Fuel for the voyage', '<span id="r_voy">' + U.fx(f.voyageFuel, 1) + ' t</span>']);
        if (hasRob) {
          rows.push(['ROB on arrival', '<span id="r_arr">' + U.fx(f.robArrival, 1) + ' t</span>']);
          if (parseFloat(U.fx(f.robArrival, 1)) < 0) msg = '<div class="msg crit">Not enough fuel on these figures. Short by ' + U.fx(-f.robArrival, 1) + ' t.</div>';
        }
      }
      if (ns > 0) rows.push(['Estimate at ' + U.fx(ns, 1) + ' kn (cube law)', '<span id="r_cube">' + U.fx(C.cubeLaw(f.daily, sp, ns), 1) + ' t/day</span>']);
    }
    U.out('res', h + U.kv(rows) + msg);
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<div class="formula">Daily consumption = fuel consumed ÷ hours × 24<br>Days of fuel = ROB ÷ daily consumption<br>Range = days of fuel × 24 × speed<br>Fuel for the voyage = distance ÷ speed ÷ 24 × daily consumption</div>'
        '<p>The <strong>cube law</strong> estimate says that, for the same ship in the same condition, daily consumption changes roughly with the cube of the speed:</p>'
        '<div class="formula">New consumption ≈ consumption × (new speed ÷ speed)³</div>'
        '<h3>Worked example</h3>'
        '<p>30 t burned in 24 hours with 600 t on board at 14 kn. The fuel lasts 600 ÷ 30 = 20 days, a range of 20 × 24 × 14 = 6,720 nm. A 3,000 nm passage takes 3,000 ÷ 14 = 214.3 hours, 8 days 22 hours, and burns 267.9 t, leaving 332.1 t on arrival. At 12 kn the cube law gives about 30 × (12 ÷ 14)³ = 18.9 t/day.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>Every figure is tested against the worked example above, worked by hand.</p></div>'
        '<h3>Limits</h3><ul><li>No reserve is taken off. ROB includes fuel you cannot pump, and your company sets the safety margin to keep on arrival.</li>'
        '<li>Enter the main engine consumption or the total, but be consistent. Generators and boilers burn fuel in port as well.</li>'
        '<li>The cube law is a rough guide for small speed changes. Weather, draught, hull condition and engine load all move the real figure.</li></ul>'),
    faq=[
        ('How do I calculate a ship\'s daily fuel consumption?',
         'Divide the fuel consumed by the number of hours it covers and multiply by 24. For example 14.5 tonnes in 12 hours is 29 tonnes a day.'),
        ('How much fuel does slow steaming save?',
         'As a rough guide, daily consumption follows the cube of the speed. Dropping from 14 to 12 knots cuts daily consumption by about 37 percent, although the voyage takes longer, so the saving per mile is smaller.'),
    ],
    guides=[(G + 'engineering/marine-fuels-hfo-vlsfo-mgo-and-lng-as-fuel/', 'Marine fuels: HFO, VLSFO, MGO and LNG as fuel'),
            (G + 'operations/bunkering-operations/', 'Bunkering operations')],
))

# =====================================================================================
# 10. FWA and DWA
# =====================================================================================
TOOLS.append(dict(
    slug='fwa-dwa-calculator', cat='Stability and cargo',
    name='FWA and DWA',
    blurb='Fresh water and dock water allowance, and how far you may submerge the load line.',
    icon='<path d="M5 4v16"/><path d="M5 6h6"/><path d="M5 10h4"/><path d="M5 14h6"/><path d="M5 18h4"/><path d="M14 13c1.200-1 2.300-1 3.500 0s2.300 1 3.500 0"/><path d="M14 17c1.200-1 2.300-1 3.500 0s2.300 1 3.500 0"/>',
    title='FWA and DWA Calculator: Fresh and Dock Water Allowance | Ocean Link',
    h1='FWA and DWA calculator',
    desc='Free fresh water allowance and dock water allowance calculator. Enter displacement and TPC, or your FWA, and the dock water density to see how far the load line may be submerged.',
    lead='Find the fresh water allowance and the dock water allowance for the density at your berth, so you know how far you may submerge the load line.',
    form=(
        seg('mode', [('calc', 'Calculate FWA'), ('known', 'I know the FWA')], cls='modes')
        + '<div class="fields"><div id="f_disp">' + num('disp', 'Summer displacement (t)', '31500') + '</div><div id="f_tpc">' + num('tpc', 'TPC at summer draught (t/cm)', '42') + '</div>'
        + '<div id="f_fwa">' + num('fwa', 'FWA (mm)', '188', hint='From the load line certificate') + '</div>'
        + num('dens', 'Dock water density', '1.010', hint='By hydrometer, e.g. 1.010 or 1010')
        + num('draught', 'Summer draught (m)', '9.60', hint='Optional')
        + '</div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI, $ = U.$;
  var mode = U.seg('mode', run);
  function run() {
    var known = mode.get() === 'known'; U.show('f_disp', !known); U.show('f_tpc', !known); U.show('f_fwa', known);
    var fwa;
    if (known) { fwa = U.num('fwa'); if (!(fwa > 0)) { U.need('res', 'Enter the FWA in millimetres.'); return; } }
    else { var d = U.num('disp'), t = U.num('tpc'); if (!(d > 0) || !(t > 0)) { U.need('res', 'Enter the summer displacement and the TPC.'); return; } fwa = C.fwa(d, t); }
    var rho = U.num('dens');
    if (rho >= 0.99 && rho <= 1.04) rho *= 1000;
    if (!(rho >= 990 && rho <= 1040)) {
      U.out('res', '<div class="label">Fresh water allowance</div><div class="big" id="r_fwa">' + U.fx(fwa, 0) + ' <small>mm</small></div><p class="sub">Enter the dock water density, between 1.000 and 1.025, for the DWA.</p>'); return;
    }
    var dwa = C.dwa(fwa, rho), dr = U.num('draught'), rows = [['Fresh water allowance', '<span id="r_fwa">' + U.fx(fwa, 1) + ' mm</span>'], ['Dock water density', U.fx(rho / 1000, 3) + ' t/m³']], h, msg = '';
    if (dwa >= 0) {
      h = '<div class="label">Dock water allowance</div><div class="big" id="r_dwa">' + U.fx(dwa, 0) + ' <small>mm</small></div><p class="sub">You may submerge the load line by ' + U.fx(dwa / 10, 1) + ' cm at this berth.</p>';
      rows.push(['DWA, unrounded', U.fx(dwa, 1) + ' mm']);
    } else {
      h = '<div class="label">Dock water allowance</div><div class="big" id="r_dwa">None</div><p class="sub">This water is denser than 1.025.</p>';
      msg = '<div class="msg warn">Keep the load line ' + U.fx(-dwa, 0) + ' mm clear above the water. The ship will sink by that much when she reaches standard sea water.</div>';
    }
    if (dr > 0) rows.push(['Draught at the load line in this water', '<span id="r_dr">' + U.fx(dr + dwa / 1000, 3) + ' m</span>']);
    U.out('res', h + U.kv(rows) + msg);
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<p>A ship floats deeper in fresh water than in salt water. The <strong>fresh water allowance</strong> is the amount she rises going from water of density 1.000 to 1.025 t/m³. It is on the load line certificate, or it comes from:</p>'
        '<div class="formula">FWA (mm) = summer displacement (t) ÷ (4 × TPC)</div>'
        '<p>Dock water is usually somewhere in between. The <strong>dock water allowance</strong> is the matching share of the FWA:</p>'
        '<div class="formula">DWA = FWA × (1025 − dock water density) ÷ 25</div>'
        '<p>You may load until the load line for your zone is under water by the DWA. When the ship reaches sea water she rises to her proper mark.</p>'
        '<h3>Worked example</h3>'
        '<p>Summer displacement 31,500 t, TPC 42. FWA = 31,500 ÷ (4 × 42) = 187.5 mm, say 188 mm. Dock water 1.010. DWA = 188 × (1025 − 1010) ÷ 25 = 112.8 mm, say 113 mm. With a summer draught of 9.60 m, you may load to about 9.71 m at this berth.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>The formulas reproduce the worked example in the Ocean Link load lines guide, and are tested at fresh water (the DWA equals the FWA), at 1.025 (no allowance) and in denser water.</p></div>'
        '<h3>Limits</h3><ul><li>The allowance is for density only. Fuel, water and stores to be used before you reach the sea or the next zone are a separate allowance.</li>'
        '<li>Take the density with a calibrated hydrometer from a sample clear of the hull discharges, close to the time of completion.</li>'
        '<li>The draught line assumes the ship is on an even keel and upright. Hog, sag and trim need the full draught survey treatment.</li></ul>'),
    faq=[
        ('What is the formula for dock water allowance?',
         'DWA equals FWA multiplied by (1025 minus the dock water density in kg per cubic metre), divided by 25. In fresh water the DWA equals the FWA, and in sea water of 1.025 it is zero.'),
        ('How is the fresh water allowance calculated?',
         'FWA in millimetres equals the summer displacement in tonnes divided by four times the TPC at the summer waterline. It is also stated on the load line certificate.'),
    ],
    guides=[(G + 'stability-cargo/load-lines-and-freeboard-marks/', 'Load lines and freeboard marks'),
            (G + 'stability-cargo/draft-survey-basics/', 'Draft survey basics')],
))

# =====================================================================================
# 11. List and GM
# =====================================================================================
TOOLS.append(dict(
    slug='list-and-gm-calculator', cat='Stability and cargo', diagram=True,
    name='List and GM',
    blurb='Solid and fluid GM with free surface correction, and the list from a weight shifted across.',
    icon='<path d="M12 4v16"/><path d="M5 8l14-2"/><path d="M5 8l-2 6a3 3 0 0 0 4 0z"/><path d="M19 6l-2 6a3 3 0 0 0 4 0z"/><path d="M8 20h8"/>',
    title='List and GM Calculator with Free Surface Correction | Ocean Link',
    h1='List and GM calculator',
    desc='Free ship stability calculator: solid GM, free surface correction, fluid GM and the angle of list caused by shifting a weight transversely.',
    lead='Work out the fluid GM from KM, KG and free surface moments, and the list you will get from moving a weight across the ship.',
    form=(
        '<h2>GM</h2><div class="fields">' + num('disp', 'Displacement (t)', '13500') + num('km', 'KM (m)', '8.40')
        + num('kg', 'KG (m)', '7.193') + num('fsm', 'Free surface moments (t·m)', '5765.6', hint='Total for all slack tanks. Optional.')
        + '</div><h2>List from a weight shifted across</h2><div class="fields">'
        + num('w', 'Weight shifted (t)', '50') + num('d', 'Distance moved across (m)', '10')
        + segfield('side', 'Moved towards', [('stbd', 'Starboard'), ('port', 'Port')], cls='full')
        + '</div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI, $ = U.$;
  var side = U.seg('side', run);
  function run() {
    var disp = U.num('disp'), km = U.num('km'), kg = U.num('kg'), fsm = $('fsm').value.trim() === '' ? 0 : U.num('fsm');
    if (!(disp > 0) || !(km > 0) || !(kg > 0) || !(fsm >= 0)) { U.need('res', 'Enter the displacement, KM and KG.'); U.out('dia', ''); return; }
    var w = U.num('w'), d = U.num('d'), s = C.stability(disp, km, kg, fsm, w > 0 ? w : 0, d > 0 ? d : 0), msg = '', sd = side.get() === 'port' ? 'port' : 'starboard';
    // A GM that prints as 0.00 is treated as no GM: 7.62 - 7.193 - 0.427 is zero, not 4e-16 with a 90 degree list.
    var noGm = parseFloat(U.fx(s.gmFluid, 2)) <= 0; if (noGm) s.list = null;
    var h = '<div class="two"><div><div class="label">Fluid GM</div><div class="big" id="r_gm">' + U.fx(s.gmFluid, 2) + ' <small>m</small></div></div>';
    if (s.list !== null) h += '<div><div class="label">List</div><div class="big" id="r_list">' + U.fx(s.list, 1) + '° <small>to ' + sd + '</small></div></div>';
    h += '</div>';
    var rows = [['Solid GM (KM − KG)', '<span id="r_solid">' + U.fx(s.gmSolid, 3) + ' m</span>'], ['Free surface correction', '<span id="r_fsc">' + U.fx(s.fsc, 3) + ' m</span>']];
    if (s.gg1 !== null) rows.push(['Shift of G (GG₁)', U.fx(s.gg1, 3) + ' m']);
    if (noGm) msg = '<div class="msg crit">GM is zero or negative. The ship is unstable upright and will lie at an angle of loll, to either side. The list formula does not apply, and moving weight across will not cure it.</div>';
    else if (s.list !== null && s.list > 10) msg = '<div class="msg warn">Above about 10° the small-angle formula is no longer reliable. Use the ship\'s stability data.</div>';
    U.out('res', h + U.kv(rows) + msg);
    if (noGm) { U.out('dia', ''); return; }
    // cross-section seen from astern, starboard on the right
    var W = 320, H = 210, cx = 160, wl = 120, ang = (s.list || 0) * (sd === 'port' ? -1 : 1), a = C.rad(Math.min(Math.abs(ang), 30) * (ang < 0 ? -1 : 1));
    function R(x, y) { return [cx + x * Math.cos(a) - y * Math.sin(a), wl + x * Math.sin(a) + y * Math.cos(a)]; }
    var hull = [[-80, -52], [80, -52], [80, 30], [66, 44], [-66, 44], [-80, 30]].map(function (q) { var p = R(q[0], q[1]); return p[0].toFixed(1) + ',' + p[1].toFixed(1); }).join(' ');
    var g = U.svgOpen(W, H, 'Ship cross-section showing the list') + '<rect x="0" y="' + wl + '" width="' + W + '" height="' + (H - wl) + '" fill="#00B0D214"/>';
    g += '<polygon points="' + hull + '" fill="#0F1217" stroke="' + U.COL.text + '" stroke-width="1.8" stroke-linejoin="round"/>';
    var m1 = R(0, -52), m2 = R(0, -96), k1 = R(0, 44);
    g += U.line(m1[0], m1[1], m2[0], m2[1], U.COL.cyan, 2) + U.line(m1[0], m1[1], k1[0], k1[1], U.COL.grid, 1.2, '3 4') + U.line(cx, wl - 100, cx, wl + 50, U.COL.faint, 1.2, '2 5');
    g += U.line(0, wl, W, wl, U.COL.mid, 1.6) + U.text(12, 22, 'P', U.COL.dim, 12, 'start', 600) + U.text(W - 12, 22, 'S', U.COL.dim, 12, 'end', 600);
    g += U.text(cx, H - 10, s.list === null ? 'Upright' : U.fx(s.list, 1) + '° to ' + sd, U.COL.text, 13, 'middle', 600) + '</svg>';
    U.out('dia', g + '<figcaption>Seen from astern. The dotted line is upright, the cyan mast shows the list.' + (Math.abs(ang) > 30 ? ' Drawn at 30°.' : '') + '</figcaption>');
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<div class="formula">Solid GM = KM − KG<br>Free surface correction = free surface moments ÷ displacement<br>Fluid GM = solid GM − free surface correction</div>'
        '<p>KM comes from the hydrostatic tables for the present draught. KG comes from the loading computer or a moments calculation. The free surface moments for each slack tank are in the tank tables of the stability booklet. Add them up.</p>'
        '<p>When a weight already on board is moved across the ship, the centre of gravity moves with it and the ship lists until the centre of buoyancy is under the new G:</p>'
        '<div class="formula">GG₁ = weight × distance ÷ displacement<br>tan (list) = GG₁ ÷ fluid GM</div>'
        '<h3>Worked example</h3>'
        '<p>Displacement 13,500 t, KM 8.40 m, KG 7.193 m, one slack tank with a free surface moment of 5,765.6 t·m. Solid GM = 8.40 − 7.193 = 1.207 m. Free surface correction = 5,765.6 ÷ 13,500 = 0.427 m. Fluid GM = 0.78 m. Now 50 t is moved 10 m to starboard: GG₁ = 500 ÷ 13,500 = 0.037 m, tan θ = 0.037 ÷ 0.78 = 0.0475, so the list is 2.7° to starboard.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>The formulas reproduce the worked examples in the Ocean Link GM guide and the list and loll guide, and are tested with a negative GM, where no list is given.</p></div>'
        '<h3>Limits</h3><ul><li>The list formula is for small angles, up to about 10°, where the metacentre can be treated as fixed.</li>'
        '<li>It is for a weight already on board that is moved across. Loading or discharging a weight also changes the displacement, KG and KM.</li>'
        '<li>A negative GM gives an angle of loll, not a list. Treat it by lowering G, never by shifting weight to the high side.</li>'
        '<li>The loading computer and the approved stability booklet are the authority for the ship\'s actual condition.</li></ul>'),
    faq=[
        ('How do you calculate the angle of list?',
         'Find the shift of G: weight multiplied by the distance moved across, divided by displacement. Then tan of the list equals that shift divided by the fluid GM. The formula holds for small angles with positive GM.'),
        ('What is the free surface correction?',
         'It is the loss of GM caused by liquid moving in slack tanks. It equals the total free surface moments divided by the displacement, and it is subtracted from the solid GM to give the fluid GM.'),
    ],
    guides=[(G + 'stability-cargo/gm-and-metacentric-height-explained/', 'GM and metacentric height explained'),
            (G + 'stability-cargo/free-surface-effect/', 'Free surface effect'),
            (G + 'stability-cargo/angle-of-loll-vs-list/', 'Angle of loll vs list')],
))

# =====================================================================================
# 12. Unit converter
# =====================================================================================
TOOLS.append(dict(
    slug='marine-unit-converter', cat='Converters',
    name='Marine unit converter',
    blurb='Knots, m/s and Beaufort, nautical miles, fathoms, bar and psi, barrels, tonnes, and volume to mass by density.',
    icon='<path d="M4 8h14"/><path d="M15 5l3 3-3 3"/><path d="M20 16H6"/><path d="M9 13l-3 3 3 3"/>',
    title='Marine Unit Converter: Knots, Nautical Miles, Bar, Barrels | Ocean Link',
    h1='Marine unit converter',
    desc='Free marine unit converter: knots, m/s and Beaufort, nautical miles and cables, metres, feet and fathoms, bar and psi, cubic metres and barrels, tonnes and long tons, and volume to mass.',
    lead='Type a value once and read it in every unit used on board, from knots and Beaufort to barrels and long tons.',
    form=(
        '<div class="fields">'
        + select('group', 'What to convert', [('speed', 'Speed and wind'), ('distance', 'Distance'), ('depth', 'Depth and cable'), ('pressure', 'Pressure'),
                                             ('temp', 'Temperature'), ('volume', 'Volume'), ('mass', 'Mass'), ('power', 'Power'), ('vm', 'Volume to mass (density)')], 'speed', cls='full')
        + '</div><div id="g_std"><div class="fields">' + num('value', 'Value', '10', neg=True)
        + '<label class="f"><span>Unit</span><select id="unit"></select></label></div></div>'
        + '<div id="g_vm"><div class="fields">'
        + segfield('dir', 'Direction', [('v2m', 'Volume to mass'), ('m2v', 'Mass to volume')], cls='full')
        + num('q', 'Volume (m³)', '1000') + num('rho', 'Density (t/m³)', '0.450') + '</div></div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI, $ = U.$, last = null;
  var TEMP = { C: '°C', F: '°F', K: 'K' };
  var dir = U.seg('dir', run);
  function sig(x) {
    if (x === 0) return '0';
    var a = Math.abs(x), s = a >= 1e9 || a < 1e-4 ? x.toExponential(4) : parseFloat(x.toPrecision(6)).toString();
    if (s.indexOf('e') < 0) { var p = s.split('.'); p[0] = p[0].replace(/\B(?=(\d{3})+(?!\d))/g, ','); s = p.join('.'); }
    return s;
  }
  function fillUnits(g) {
    var names = g === 'temp' ? ['C', 'F', 'K'] : Object.keys(C.UNITS[g].units);
    $('unit').innerHTML = names.map(function (n) { return '<option value="' + n + '">' + (g === 'temp' ? TEMP[n] : n) + '</option>'; }).join('');
  }
  function run() {
    var g = U.val('group'); U.show('g_std', g !== 'vm'); U.show('g_vm', g === 'vm');
    if (g === 'vm') {
      var m2v = dir.get() === 'm2v', q = U.num('q'), rho = U.num('rho');
      $('q').previousElementSibling.textContent = m2v ? 'Mass (t)' : 'Volume (m³)';
      if (!(q >= 0) || !(rho > 0)) { U.need('res', 'Enter the quantity and the density.'); return; }
      U.out('res', '<div class="label">' + (m2v ? 'Volume' : 'Mass') + '</div><div class="big" id="r_main">' + sig(m2v ? q / rho : q * rho) + ' <small>' + (m2v ? 'm³' : 't') + '</small></div>' +
        '<div class="msg">Plain volume × density. Cargo figures for oil, gas and chemicals need the temperature and density corrections from the proper tables.</div>');
      return;
    }
    if (g !== last) { fillUnits(g); last = g; }
    var v = U.num('value'), from = U.val('unit'), rows;
    if (isNaN(v)) { U.need('res', 'Enter a value.'); return; }
    if (g === 'temp') {
      if (C.convertTemp(v, from, 'K') < 0) { U.need('res', 'That is below absolute zero.'); return; }
      rows = ['C', 'F', 'K'].map(function (n) { return [TEMP[n], '<span data-u="' + n + '">' + U.fx(C.convertTemp(v, from, n), 2) + '</span>']; });
    } else {
      if (v < 0) { U.need('res', 'Enter a value of zero or more.'); return; }
      rows = Object.keys(C.UNITS[g].units).map(function (n) { return [n, '<span data-u="' + n + '">' + sig(C.convert(g, v, from, n)) + '</span>']; });
      if (g === 'speed') { var b = C.beaufort(C.convert('speed', v, from, 'kn')); rows.push(['Beaufort', '<span data-u="bf">Force ' + b.force + ', ' + b.desc + '</span>']); }
    }
    U.out('res', '<div class="label plain">' + sig(v) + ' ' + (g === 'temp' ? TEMP[from] : from) + ' equals</div>' + U.kv(rows));
  }
  U.live(run);
})();''',
    how=(
        '<h2>The factors used</h2>'
        '<table><tr><th>Unit</th><th>Exact value</th></tr>'
        '<tr><td>1 nautical mile</td><td>1,852 m (10 cables)</td></tr><tr><td>1 knot</td><td>1,852 m per hour = 0.514444 m/s</td></tr>'
        '<tr><td>1 fathom</td><td>6 ft = 1.8288 m</td></tr><tr><td>1 shackle of cable</td><td>27.5 m (15 fathoms is 27.43 m)</td></tr>'
        '<tr><td>1 bar</td><td>100 kPa = 14.5038 psi</td></tr><tr><td>1 kgf/cm²</td><td>0.980665 bar</td></tr>'
        '<tr><td>1 US barrel</td><td>42 US gallons = 158.987 litres</td></tr><tr><td>1 long ton</td><td>2,240 lb = 1,016.05 kg</td></tr>'
        '<tr><td>1 short ton</td><td>2,000 lb = 907.185 kg</td></tr><tr><td>1 metric horsepower (PS)</td><td>735.499 W</td></tr></table>'
        '<p>The Beaufort force is read from the WMO table using the speed in whole knots. Results are shown to six significant figures.</p>'
        '<p><strong>Volume to mass</strong> multiplies cubic metres by the density in tonnes per cubic metre. That suits ballast, fresh water and quick estimates. It is not a cargo calculation: oil, gas and chemical quantities need the temperature and density corrections from the tables named in the charter party.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>Every group is tested against published conversion factors, for example 1 bar = 14.5038 psi, 1 m³ = 6.28981 US barrels and 100 °C = 212 °F, and against every boundary of the Beaufort table.</p></div>'),
    faq=[
        ('How many metres per second is one knot?',
         'One knot is 1,852 metres per hour, which is 0.514444 metres per second. To go the other way, 1 m/s is 1.94384 knots.'),
        ('How long is a shackle of anchor cable?',
         'A shackle is 27.5 metres in modern metric cable. The traditional length is 15 fathoms, which is 27.43 metres.'),
    ],
    guides=[(G + 'meteorology/beaufort-scale-and-sea-state/', 'Beaufort scale and sea state'),
            (G + 'systems/anchoring-equipment/', 'Anchoring equipment')],
))

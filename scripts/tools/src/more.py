"""Tool definitions, second set: bunkers, draught survey, LNG, dew point, sunrise and twilight,
rate of turn, horizon and rolling period."""
from build import num, select, seg, segfield, latlon, date, zone, e

G = '/guides/'
TOOLS = []


def numsel(id, label, value, opts, default, hint='', cls='', wide=False):
    """A number with a small choice beside it (direction or unit)."""
    o = ''.join('<option value="%s"%s>%s</option>' % (e(v), ' selected' if v == default else '', e(t)) for v, t in opts)
    return ('<div class="f %s"><span class="l">%s</span><div class="row"><input id="%s" type="text" inputmode="decimal" value="%s" autocomplete="off" aria-label="%s">'
            '<select id="%sd" class="%s" aria-label="%s: choice">%s</select></div>%s</div>'
            % (cls, label, id, e(value), e(label), id, 'md' if wide else 'sm', e(label), o, '<small>%s</small>' % hint if hint else ''))


# =====================================================================================
# 13. Bunker quantity
# =====================================================================================
TOOLS.append(dict(
    slug='bunker-quantity-calculator', cat='Engine',
    name='Bunker quantity',
    blurb='Sounded volume, temperature and density at 15°C to tonnes, with the Table 54B correction.',
    icon='<path d="M5 6c0-1.700 3.100-3 7-3s7 1.300 7 3v12c0 1.700-3.100 3-7 3s-7-1.300-7-3z"/><path d="M5 6c0 1.700 3.100 3 7 3s7-1.300 7-3"/><path d="M5 12c0 1.700 3.100 3 7 3s7-1.300 7-3"/>',
    title='Bunker Quantity Calculator (ASTM Table 54B VCF) | Ocean Link',
    h1='Bunker quantity calculator',
    desc='Free bunker calculator for ships. Enter the sounded volume, oil temperature and density at 15°C to get the VCF from ASTM Table 54B, the standard volume and the weight in tonnes.',
    lead='Turn a sounded volume into tonnes the way a bunker surveyor does: volume correction factor from Table 54B, standard volume at 15°C, then weight in air.',
    form=(
        '<div class="fields">'
        + num('vol', 'Observed volume (m³)', '161.68', hint='From the sounding table, after trim and list corrections', cls='full')
        + num('temp', 'Oil temperature (°C)', '34', neg=True)
        + num('dens', 'Density at 15°C', '0.9903', hint='From the BDN, e.g. 0.9903 or 990.3')
        + '</div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI;
  function run() {
    var v = U.num('vol'), t = U.num('temp'), d = U.num('dens');
    if (d > 0.5 && d < 1.2) d *= 1000;
    if (!(v > 0) || isNaN(t) || isNaN(d)) { U.need('res', 'Enter the volume, the oil temperature and the density at 15°C.'); return; }
    if (!(d >= 653 && d <= 1075)) { U.need('res', 'Table 54B covers densities from 0.6530 to 1.0750 at 15°C. Check the density.'); return; }
    var b = C.bunker(v, t, d);
    var h = '<div class="label">Weight in air</div><div class="big" id="r_main">' + U.big(b.massAir, 2) + ' <small>t</small></div>' +
      '<p class="sub">VCF <span id="r_vcf">' + U.fx(b.vcf, 4) + '</span>, standard volume ' + U.big(b.gsv, 3) + ' m³</p>';
    h += U.kv([['Product group in Table 54B', b.group], ['Volume correction factor', U.fx(b.vcf, 4)],
      ['Standard volume at 15°C', '<span id="r_gsv">' + U.big(b.gsv, 3) + ' m³</span>'],
      ['Weight factor (density − 0.0011)', '<span id="r_wcf">' + U.fx(b.wcf, 4) + '</span>'],
      ['Weight in air', U.big(b.massAir, 2) + ' t'], ['Mass in vacuum', '<span id="r_vac">' + U.big(b.massVac, 2) + ' t</span>'],
      ['Density at ' + U.fx(t, 1) + '°C', U.fx(d / 1000 * b.vcf, 4)]]);
    if (!b.inRange) h += '<div class="msg warn">Table 54B runs from −18°C to ' + b.tMax + '°C for this density. This temperature is outside it, so treat the factor as an extrapolation.</div>';
    U.out('res', h);
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<p>Oil expands as it warms, so a tank volume means nothing until it is brought back to 15°C. The supplier gives the density at 15°C on the bunker delivery note. Three steps turn your sounding into tonnes:</p>'
        '<div class="formula">Standard volume = observed volume × VCF<br>Weight in air (t) = standard volume × (density at 15°C − 0.0011)</div>'
        '<p>The <strong>volume correction factor</strong> comes from Petroleum Measurement Table 54B (ASTM D1250-80, API MPMS 11.1, IP 200), the table for fuel oils and other products. The tool works the table\'s own formula, carries the expansion coefficient α to seven decimals, which is what reproduces the published tables to the last figure, and rounds the factor to four decimals, as the printed table does:</p>'
        '<div class="formula">VCF = exp[ −α × ΔT × (1 + 0.8 × α × ΔT) ], ΔT = temperature − 15<br>α = 186.9696 ÷ ρ² + 0.4862 ÷ ρ for fuel oils (ρ = density at 15°C in kg/m³, 839 and above)</div>'
        '<p>Lighter products use the table\'s other constants: jet fuels and kerosenes from 788 to 838.5 kg/m³, gasolines up to 770 kg/m³ and a transition zone between them. Subtracting 0.0011 from the density is the short form of Table 56. It changes mass in vacuum to weight in air, which is what bunkers are bought in.</p>'
        '<h3>Worked example</h3>'
        '<p>Sounding gives 161.68 m³ at 34°C. Density at 15°C is 0.9903. Table 54B gives a VCF of 0.9870, so the standard volume is 161.68 × 0.9870 = 159.578 m³. The weight factor is 0.9903 − 0.0011 = 0.9892, so the tank holds 159.578 × 0.9892 = 157.85 t.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>The volume correction factor reproduces all 440 values checked in three tables published by Measurement Canada under API Standard 2540 (1980): aviation gasoline at 710 kg/m³, jet fuel at 800 kg/m³ and diesel at 840 kg/m³, from −40°C to 40°C, as well as 44 values from its gasoline table at 730 kg/m³. The whole calculation returns the 157.85 t of a published bunker survey example worked from the printed Table 54B.</p></div>'
        '<h3>Limits</h3><ul>'
        '<li>The volume must already be corrected for trim and list from your sounding tables, and free water must be taken off before you start.</li>'
        '<li>This is the 1980 edition of Table 54B (ASTM D1250-80). If your contract names the 2004 edition, the factor can differ in the fourth decimal.</li>'
        '<li>The density must be the density at 15°C in vacuum from the BDN or a laboratory. A density measured at tank temperature has to go through Table 53B first.</li>'
        '<li>The quick rule of 0.00064 per degree skips the weight-in-air step. In the example it gives 158.2 t, which is 0.3 t more.</li></ul>'),
    faq=[
        ('How do you calculate bunker quantity in tonnes?',
         'Multiply the observed volume by the volume correction factor from ASTM Table 54B to get the standard volume at 15 degrees Celsius. Then multiply by the density at 15 degrees minus 0.0011 to get the weight in air in tonnes.'),
        ('Which ASTM table is used for bunkers?',
         'Table 54B gives the volume correction factor for fuel oils from the density at 15 degrees Celsius and the oil temperature. Table 56 gives the weight factor, which in short form is the density minus 0.0011.'),
        ('What is the difference between weight in air and mass in vacuum?',
         'Weight in air allows for the buoyancy of air and is about 0.11 percent less than mass in vacuum. Bunkers are normally traded on weight in air, so the density in vacuum is reduced by 0.0011.'),
    ],
    guides=[(G + 'operations/bunkering-operations/', 'Bunkering operations'),
            (G + 'engineering/bunker-sampling-and-marpol-samples/', 'Bunker sampling and MARPOL samples'),
            (G + 'stability-cargo/tanker-cargo-calculations-astm-tables-vcf/', 'Tanker cargo calculations: ASTM tables and VCF')],
))

# =====================================================================================
# 14. Draught survey
# =====================================================================================
TOOLS.append(dict(
    slug='draft-survey-calculator', cat='Stability and cargo',
    name='Draft survey',
    blurb='Six draughts to mean of means, trim corrections, density correction and displacement.',
    icon='<path d="M3 13h18l-2.500 6h-13z"/><path d="M6 13V9"/><path d="M12 13V6"/><path d="M18 13V9"/>',
    title='Draft Survey Calculator: Mean of Means, Trim and Density Corrections | Ocean Link',
    h1='Draft survey calculator',
    desc='Free draft survey calculator. Enter six draughts and your hydrostatic data to get the corrected draughts, mean of means, first and second trim corrections, density correction and displacement.',
    lead='Enter the six draughts to get the mean of means. Read your hydrostatic tables at that draught, enter them, and the tool applies the trim and density corrections.',
    form=(
        '<h2>Draughts read at the marks (m)</h2><div class="fields">'
        + num('fp', 'Forward, port', '4.61') + num('fs', 'Forward, starboard', '4.65')
        + num('mp', 'Midship, port', '4.93') + num('ms', 'Midship, starboard', '5.10')
        + num('ap', 'Aft, port', '5.58') + num('as', 'Aft, starboard', '5.60')
        + '</div><h2>Ship</h2><div class="fields">'
        + num('lbp', 'LBP (m)', '181.8', cls='full')
        + numsel('xf', 'Forward marks from the FP (m)', '2.94', [('aft', 'Aft'), ('fwd', 'Fwd')], 'aft')
        + numsel('xa', 'Aft marks from the AP (m)', '7.30', [('fwd', 'Fwd'), ('aft', 'Aft')], 'fwd')
        + numsel('xm', 'Midship marks from midships (m)', '1.44', [('aft', 'Aft'), ('fwd', 'Fwd')], 'aft')
        + '</div><h2>Hydrostatics at the mean of means draught</h2><div class="fields">'
        + num('disp', 'Displacement (t)', '19894.37') + num('tpc', 'TPC (t/cm)', '42.338')
        + numsel('lcf', 'LCF from midships (m)', '4.331', [('aft', 'Aft'), ('fwd', 'Fwd')], 'fwd')
        + num('rhot', 'Density of the tables', '1.025')
        + num('mtcp', 'MTC at draught + 0.5 m', '445.89') + num('mtcm', 'MTC at draught − 0.5 m', '435.26')
        + '</div><h2>Water and weights</h2><div class="fields">'
        + num('rho', 'Dock water density', '1.0185', hint='By hydrometer, e.g. 1.0185', cls='full')
        + num('ded', 'Deductibles (t)', '', hint='Ballast, fresh water, fuel, lube oil, others. Optional')
        + num('ls', 'Light ship (t)', '', hint='Optional')
        + '</div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI;
  function signed(id, plus) { var v = U.num(id); if (isNaN(v) && U.val(id).trim() === '') v = 0; return U.val(id + 'd') === plus ? v : -v; }
  function sg(x, dp) { return (x > 0 ? '+' : x < 0 ? '−' : '') + U.fx(Math.abs(x), dp); }
  function tn(x) { return (x < 0 ? '−' : '+') + U.big(Math.abs(x), 2) + ' t'; }
  function dens(id) { var r = U.num(id); if (r > 900 && r < 1100) r /= 1000; return r; }
  function run() {
    var d = ['fp', 'fs', 'mp', 'ms', 'ap', 'as'].map(U.num), lbp = U.num('lbp');
    if (d.some(function (x) { return !(x > 0); }) || !(lbp > 0)) { U.need('res', 'Enter the six draughts and the LBP.'); return; }
    var xf = signed('xf', 'aft'), xm = signed('xm', 'aft'), xa = signed('xa', 'fwd');
    if (isNaN(xf) || isNaN(xm) || isNaN(xa) || !(lbp - xf - xa > lbp / 2)) { U.need('res', 'Check the distances of the draught marks from the perpendiculars.'); return; }
    var s = C.draftSurvey(d[0], d[1], d[2], d[3], d[4], d[5], lbp, xf, xm, xa);
    var trimTxt = Math.abs(s.trim) < 0.00005 ? 'Even keel' : U.fx(Math.abs(s.trim), 4) + ' m by the ' + (s.trim > 0 ? 'stern' : 'head');
    var defl = Math.abs(s.deflection) < 0.0005 ? 'None' : (s.deflection > 0 ? 'Sagged ' : 'Hogged ') + U.fx(Math.abs(s.deflection) * 100, 1) + ' cm';
    var rows = [['Forward, at the FP', '<span id="r_f">' + U.fx(s.fc, 4) + ' m</span> (' + sg(s.fCorr, 4) + ')'],
      ['Midships', '<span id="r_m">' + U.fx(s.mc, 4) + ' m</span> (' + sg(s.mCorr, 4) + ')'],
      ['Aft, at the AP', '<span id="r_a">' + U.fx(s.ac, 4) + ' m</span> (' + sg(s.aCorr, 4) + ')'],
      ['True trim', '<span id="r_trim">' + trimTxt + '</span>'], ['Hog or sag', '<span id="r_defl">' + defl + '</span>']];
    var mmm = '<div><div class="label">Mean of means draught</div><div class="big" id="r_mmm">' + U.fx(s.mmm, 4) + ' <small>m</small></div></div>';
    var disp = U.num('disp'), tpc = U.num('tpc'), lcf = signed('lcf', 'aft'), mp = U.num('mtcp'), mm = U.num('mtcm'), rt = dens('rhot'), rho = dens('rho');
    var blank = ['disp', 'tpc', 'mtcp', 'mtcm'].every(function (id) { return U.val(id).trim() === ''; });
    if (!(disp > 0) || !(tpc > 0) || isNaN(lcf) || !(mp > 0) || !(mm > 0) || !(rt >= 0.99 && rt <= 1.04)) {
      U.out('res', mmm + '<p class="sub">' + (blank ? 'Read the displacement, TPC, LCF and MTC from your hydrostatic tables at this draught and enter them above.' : 'Check the hydrostatic figures above.') + '</p>' + U.kv(rows)); return;
    }
    if (!(rho >= 0.99 && rho <= 1.04)) { U.out('res', mmm + '<p class="sub">Enter the dock water density, between 0.990 and 1.040.</p>' + U.kv(rows)); return; }
    var r = C.draftSurveyDisp(s.trim, lbp, disp, tpc, lcf, mp, mm, rho, rt);
    var h = '<div class="two">' + mmm + '<div><div class="label">Displacement</div><div class="big" id="r_disp">' + U.big(r.dispTrue, 1) + ' <small>t</small></div></div></div>';
    rows.push(['First trim correction', '<span id="r_ftc">' + tn(r.ftc) + '</span>'], ['Second trim correction', '<span id="r_stc">' + tn(r.stc) + '</span>'],
      ['Displacement corrected for trim', '<span id="r_dt">' + U.big(r.dispTrim, 2) + ' t</span>'], ['Density correction', tn(r.densityCorr)],
      ['Displacement in water of ' + U.fx(rho, 4), '<span id="r_true">' + U.big(r.dispTrue, 2) + ' t</span>']);
    var ded = U.num('ded'), ls = U.num('ls'), net = r.dispTrue;
    if (ded >= 0) { net -= ded; rows.push(['Less deductibles', '<span id="r_net">' + U.big(net, 2) + ' t</span>']); }
    if (ls > 0) { rows.push(['Less light ship', '<span id="r_ls">' + U.big(net - ls, 2) + ' t</span>']); }
    h += U.kv(rows);
    if (ls > 0) h += '<p class="sub" style="margin-top:10px">The last figure is the constant on an empty ship, or cargo plus constant on a loaded one.</p>';
    U.out('res', h);
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<p>A draft survey weighs the ship by her displacement. The tool follows the standard steps and shows each one.</p>'
        '<p><strong>1. Mean draughts.</strong> Port and starboard are averaged at each of the three positions.</p>'
        '<p><strong>2. Correction to the perpendiculars.</strong> The marks are rarely on the perpendiculars. With the apparent trim taken between the forward and aft marks:</p>'
        '<div class="formula">Correction = apparent trim × distance of the marks from the perpendicular ÷ length between the marks</div>'
        '<p>The tool treats the keel as a straight line through the forward and aft marks and reads it off at the FP, at midships and at the AP, so the signs take care of themselves. The corrected draughts are carried to 0.1 mm, as on a survey sheet.</p>'
        '<p><strong>3. Mean of means.</strong> Also called the quarter mean. It allows for hog or sag:</p>'
        '<div class="formula">Mean of means = (forward + aft + 6 × midships) ÷ 8</div>'
        '<p><strong>4. Hydrostatics.</strong> You read the displacement, TPC, LCF and the two MTC values from your own tables at this draught.</p>'
        '<p><strong>5. Trim corrections.</strong></p>'
        '<div class="formula">First trim correction (t) = trim (cm) × LCF from midships (m) × TPC ÷ LBP<br>Second trim correction (t) = trim² (m) × 50 × (MTC at +0.5 m − MTC at −0.5 m) ÷ LBP</div>'
        '<p>The first correction is added when the LCF lies toward the deeper end, and subtracted when it lies toward the shallower end. The second correction is always added.</p>'
        '<p><strong>6. Density.</strong> The tables are for 1.025 unless they say otherwise:</p>'
        '<div class="formula">Displacement in dock water = corrected displacement × dock water density ÷ density of the tables</div>'
        '<p><strong>7. Net weight.</strong> Take off the ballast, fresh water, fuel and other deductibles. The cargo is the difference between the net figures of the final and the initial survey.</p>'
        '<h3>Worked example</h3>'
        '<p>The figures shown when the page opens are the worked example in the UK P&amp;I Club\'s Carefully to Carry chapter on draught surveys. The mean of means is 5.0357 m, the first trim correction is −102.61 t because the LCF is forward and the ship is trimmed by the stern, the second is +3.03 t, and the displacement in water of 1.0185 is 19,669.26 t.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>The tool returns every figure of the UK P&amp;I Club worked example, from the perpendicular corrections to the final 19,669.26 t, and the worked example in the Ocean Link draft survey guide. The mark corrections were also tested on 400 made-up ships with known draughts, trim, hog and sag, with marks on either side of the perpendiculars.</p></div>'
        '<h3>Limits</h3><ul>'
        '<li>The LCF must be a distance from midships. If your tables give it from the AP, subtract half the LBP first.</li>'
        '<li>The ship is taken as upright. A heel correction, needed with a large list, is not included.</li>'
        '<li>With a very large trim, use the trimmed hydrostatic tables if the ship has them. The corrections here assume a moderate trim.</li>'
        '<li>The answer is only as good as the readings: six draughts read in a swell and one density sample are the usual weak points.</li></ul>'),
    faq=[
        ('What is the formula for the mean of means draught?',
         'Add the forward draught, the aft draught and six times the midship draught, all corrected to the perpendiculars and midships, and divide by eight. It is also called the quarter mean.'),
        ('When is the first trim correction positive?',
         'It is added when the LCF lies on the same side of midships as the deeper draught, for example LCF aft with the ship trimmed by the stern. It is subtracted when the LCF lies toward the shallower end.'),
        ('What is the second trim correction in a draft survey?',
         'It allows for the LCF moving as the ship trims. It equals the trim in metres squared, times 50, times the difference in MTC at 0.5 metres above and below the mean draught, divided by the LBP. It is always added.'),
    ],
    guides=[(G + 'stability-cargo/draft-survey-basics/', 'Draft survey basics'),
            (G + 'stability-cargo/trim-and-trim-calculations/', 'Trim and trim calculations'),
            (G + 'stability-cargo/hogging-and-sagging/', 'Hogging and sagging')],
))

# =====================================================================================
# 15. LNG conversion and boil-off
# =====================================================================================
TOOLS.append(dict(
    slug='lng-conversion-boil-off-calculator', cat='Stability and cargo',
    name='LNG converter and boil-off',
    blurb='Cubic metres of LNG to tonnes, MMBtu and gas volume, and the boil-off rate per day.',
    icon='<circle cx="8" cy="10" r="4"/><circle cx="16" cy="10" r="4"/><path d="M3 17h18l-1.500 3h-15z"/>',
    title='LNG Conversion Calculator: m³ to Tonnes and MMBtu, Boil-Off Rate | Ocean Link',
    h1='LNG converter and boil-off calculator',
    desc='Free LNG calculator. Convert cubic metres of LNG to tonnes, MMBtu and gas volume with your own density and heating value, and work out the boil-off rate in percent per day.',
    lead='Convert an LNG quantity between cubic metres, tonnes, MMBtu and gas volume using the figures from your cargo certificate, and find the boil-off rate between two gaugings.',
    form=(
        '<h2>Quantity</h2><div class="fields">'
        + num('qty', 'Quantity', '170000')
        + select('unit', 'Unit', [('m3', 'm³ of LNG'), ('t', 'Tonnes'), ('mmbtu', 'MMBtu'), ('nm3', 'Nm³ of gas')], 'm3')
        + '</div><h2>Cargo properties</h2><div class="fields">'
        + num('dens', 'LNG density (kg/m³)', '450') + num('gas', 'Gas per tonne (Nm³)', '1300')
        + numsel('heat', 'Heating value', '52', [('mmbtu', 'MMBtu/t'), ('mj', 'MJ/kg')], 'mmbtu', cls='full', wide=True,
                 hint='Typical values are shown. Use the figures from your cargo quality certificate.')
        + '</div><h2>Boil-off (optional)</h2><div class="fields">'
        + num('v0', 'Volume at the start (m³)', '') + num('v1', 'Volume at the end (m³)', '')
        + num('hrs', 'Hours between the two', '', cls='full')
        + '</div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI;
  var NAMES = { m3: 'm³ of LNG', t: 't', mmbtu: 'MMBtu', nm3: 'Nm³ of gas' };
  function run() {
    var q = U.num('qty'), unit = U.val('unit'), dens = U.num('dens'), heat = U.num('heat'), gas = U.num('gas'), h = '';
    if (U.val('heatd') === 'mj') heat = heat * 1000 / C.MJ_PER_MMBTU;
    if (!(dens >= 380 && dens <= 520)) { U.need('res', 'Enter the LNG density in kg/m³, between 380 and 520.'); return; }
    if (!(heat >= 45 && heat <= 57)) { U.need('res', 'Enter the heating value: 45 to 57 MMBtu per tonne, or 47.5 to 60.1 MJ/kg.'); return; }
    if (!(gas >= 1100 && gas <= 1500)) { U.need('res', 'Enter the gas volume per tonne, between 1,100 and 1,500 Nm³.'); return; }
    if (q > 0) {
      var a = C.lng(q, unit, dens, heat, gas), main = unit === 't' ? ['m³ of LNG', a.m3, 0] : ['t', a.t, 0];
      h += '<div class="label plain">' + U.big(q, q % 1 ? 2 : 0) + ' ' + NAMES[unit] + ' is</div><div class="big" id="r_main">' + U.big(main[1], main[2]) + ' <small>' + main[0] + '</small></div>';
      h += U.kv([['LNG volume', '<span id="r_m3">' + U.big(a.m3, 0) + ' m³</span>'], ['Mass', '<span id="r_t">' + U.big(a.t, 1) + ' t</span>'],
        ['Energy', '<span id="r_mmbtu">' + U.big(a.mmbtu, 0) + ' MMBtu</span>'], ['Energy in gigajoules', U.big(a.gj, 0) + ' GJ'],
        ['Gas at 0°C (Nm³)', '<span id="r_nm3">' + U.big(a.nm3, 0) + ' Nm³</span>'], ['Gas at 15°C (Sm³)', '<span id="r_sm3">' + U.big(a.sm3, 0) + ' Sm³</span>']]);
    } else h += '<p class="empty">Enter a quantity to convert.</p>';
    var v0 = U.num('v0'), v1 = U.num('v1'), hrs = U.num('hrs');
    if (v0 > 0 && v1 >= 0 && hrs > 0) {
      if (v1 > v0) h += '<div class="msg warn">The volume at the end is larger than at the start.</div>';
      else {
        var b = C.boilOff(v0, v1, hrs, dens), e = C.lng(b.m3Day, 'm3', dens, heat, gas);
        h += '<div class="label" style="margin-top:16px">Boil-off rate</div><div class="big" id="r_bor">' + U.fx(b.pctDay, 3) + ' <small>% per day</small></div>' +
          U.kv([['Boiled off', U.big(b.lost, 1) + ' m³ in ' + U.fx(hrs, hrs % 1 ? 1 : 0) + ' h'], ['Per day', '<span id="r_bm3">' + U.big(b.m3Day, 1) + ' m³</span>'],
            ['Per day, mass', '<span id="r_bt">' + U.big(b.tDay, 1) + ' t</span>'], ['Per day, energy', U.big(e.mmbtu, 0) + ' MMBtu']]);
      }
    }
    U.out('res', h);
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<p>Every conversion goes through the mass of the cargo. Three figures from the cargo quality certificate fix the rest:</p>'
        '<div class="formula">Mass (t) = volume (m³) × density (kg/m³) ÷ 1000<br>Energy (MMBtu) = mass × heating value per tonne<br>Gas volume (Nm³) = mass × gas per tonne</div>'
        '<p>A heating value in MJ/kg is changed to MMBtu per tonne with 1 MMBtu = 1,055.056 MJ. Nm³ is gas at 0°C and Sm³ is gas at 15°C, both at 1 atmosphere; 1 Sm³ = 0.9476 Nm³ (ISO 13443).</p>'
        '<p>The <strong>boil-off rate</strong> is the liquid that evaporates in a day as a percentage of the liquid volume:</p>'
        '<div class="formula">Boil-off (% per day) = (volume at start − volume at end) ÷ volume at start ÷ hours × 24 × 100</div>'
        '<h3>Worked example</h3>'
        '<p>With the International Gas Union\'s reference figures of 450 kg/m³, 1,300 Nm³ and 53.38 MMBtu per tonne, 1 m³ of LNG is 0.450 t, 585 Nm³ of gas and 24.02 MMBtu. For boil-off, a ship that gauges 170,000 m³ and 169,660 m³ 48 hours later has lost 340 m³: 170 m³ a day, or 0.100% per day, about 76.5 t a day at 450 kg/m³.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>With the International Gas Union\'s assumptions the tool reproduces its published LNG conversion table in every direction, and with 52 MMBtu per tonne it matches the S&amp;P Global factor of 0.01923 t per MMBtu. Each conversion was also run forwards and back through all four units for 300 random cargoes and returned the starting figure.</p></div>'
        '<h3>Limits</h3><ul>'
        '<li>The prefilled 450 kg/m³, 52 MMBtu per tonne and 1,300 Nm³ per tonne are typical values only. Real cargoes range from about 420 to 470 kg/m³. Use the certificate.</li>'
        '<li>This is a quantity conversion. The commercial figure comes from the custody transfer measurement: CTMS volumes before and after, density and heating value from the analysed composition, less the energy of the gas displaced.</li>'
        '<li>The boil-off rate here is a percentage of the volume at the first gauging. A builder\'s guaranteed boil-off rate is quoted against the full cargo capacity under set conditions, so the two are not the same number.</li>'
        '<li>Gauge at the same trim and list, or correct both volumes first.</li></ul>'),
    faq=[
        ('How many tonnes is one cubic metre of LNG?',
         'About 0.45 tonnes, because LNG density is typically 420 to 470 kilograms per cubic metre. Multiply the volume by the density from the cargo certificate and divide by 1000.'),
        ('How many MMBtu are in a tonne of LNG?',
         'Roughly 52 MMBtu per tonne for a typical cargo. The exact figure is the gross heating value on the cargo quality certificate; 54.86 megajoules per kilogram equals 52 MMBtu per tonne.'),
        ('How is the boil-off rate of an LNG carrier calculated?',
         'Divide the volume of liquid lost between two gaugings by the starting volume and by the time in days, then multiply by 100. Modern LNG carriers boil off roughly 0.08 to 0.15 percent of the cargo per day.'),
    ],
    guides=[(G + 'stability-cargo/gas-tanker-cargo-calculations-basics/', 'Gas tanker cargo calculations'),
            (G + 'engineering/marine-fuels-hfo-vlsfo-mgo-and-lng-as-fuel/', 'Marine fuels, including LNG as fuel')],
))

# =====================================================================================
# 16. Dew point
# =====================================================================================
TOOLS.append(dict(
    slug='dew-point-calculator', cat='Stability and cargo',
    name='Dew point and humidity',
    blurb='Dew point and relative humidity from wet and dry bulb, and the dew point rule for hold ventilation.',
    icon='<path d="M10 14.500V5a2 2 0 1 1 4 0v9.500a4 4 0 1 1-4 0z"/><path d="M18 6h2"/><path d="M18 10h2"/>',
    title='Dew Point Calculator from Wet and Dry Bulb (Cargo Ventilation) | Ocean Link',
    h1='Dew point calculator',
    desc='Free dew point calculator for ships. Enter wet and dry bulb readings to get the dew point and relative humidity, and compare outside air with hold air using the dew point rule.',
    lead='Enter the wet and dry bulb readings to get the dew point and relative humidity. Add the readings from the hold and the tool compares the two dew points.',
    form=(
        '<h2>Outside air</h2><div class="fields">'
        + num('dry', 'Dry bulb (°C)', '28', neg=True) + num('wet', 'Wet bulb (°C)', '25', neg=True)
        + '</div><h2>Air in the hold (optional)</h2><div class="fields">'
        + num('hdry', 'Dry bulb (°C)', '', neg=True) + num('hwet', 'Wet bulb (°C)', '', neg=True)
        + '</div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI;
  function read(a, b) {
    var d = U.num(a), w = U.num(b);
    if (isNaN(d) || isNaN(w)) return { empty: U.val(a).trim() === '' && U.val(b).trim() === '' };
    if (w > d) return { err: 'The wet bulb cannot read higher than the dry bulb.' };
    if (w < 0) return { err: 'Below 0°C the wet bulb may be coated in ice and this method does not apply.' };
    if (d > 55) return { err: 'Check the dry bulb reading.' };
    var p = C.psychro(d, w);
    if (!p) return { err: 'These two readings cannot occur together. Check the wet bulb.' };
    return { p: p };
  }
  function run() {
    var o = read('dry', 'wet'), i = read('hdry', 'hwet');
    if (!o.p) { U.need('res', o.err || 'Enter the dry and wet bulb readings.'); return; }
    var h = '<div class="two"><div><div class="label">Dew point outside</div><div class="big" id="r_dew">' + U.fx(o.p.dew, 1) + ' <small>°C</small></div></div>' +
      '<div><div class="label">Relative humidity</div><div class="big" id="r_rh">' + U.fx(o.p.rh, 0) + ' <small>%</small></div></div></div>';
    var rows = [['Vapour pressure', U.fx(o.p.e, 1) + ' hPa']], msg = '';
    if (o.p.dew < 0) msg += '<div class="msg warn">Very dry air. Below a dew point of 0°C a small reading error moves the answer by several degrees, so treat it as approximate.</div>';
    if (i.p) {
      rows.push(['Dew point in the hold', '<span id="r_hdew">' + U.fx(i.p.dew, 1) + ' °C</span>'], ['Relative humidity in the hold', U.fx(i.p.rh, 0) + ' %']);
      // The rule is read off the two dew points as printed, so the difference quoted is the one the reader can check.
      var tenths = Math.round((parseFloat(U.fx(o.p.dew, 1)) - parseFloat(U.fx(i.p.dew, 1))) * 10), diff = tenths / 10;
      if (Math.abs(tenths) < 5) msg += '<div class="msg" id="r_rule">The two dew points are within half a degree, which is inside the error of the readings. The dew point rule gives no clear answer.</div>';
      else if (tenths < 0) msg += '<div class="msg" id="r_rule">Outside dew point is lower than in the hold by ' + U.fx(-diff, 1) + '°C. By the dew point rule: ventilate.</div>';
      else msg += '<div class="msg warn" id="r_rule">Outside dew point is higher than in the hold by ' + U.fx(diff, 1) + '°C. By the dew point rule: do not ventilate.</div>';
    } else if (i.err) msg += '<div class="msg warn">Hold air: ' + i.err + '</div>';
    U.out('res', h + U.kv(rows) + msg);
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<p>A wet bulb reads lower than a dry bulb because water evaporating from the wick cools it. The drier the air, the bigger the difference. The tool uses the psychrometer formula in the form published by the US National Weather Service, at standard pressure of 1013.25 hPa:</p>'
        '<div class="formula">Saturation vapour pressure e<sub>s</sub>(T) = 6.112 × exp(17.67 × T ÷ (T + 243.5)) hPa<br>'
        'Vapour pressure e = e<sub>s</sub>(wet) − 1013.25 × 0.00066 × (dry − wet) × (1 + 0.00115 × wet)<br>'
        'Relative humidity = 100 × e ÷ e<sub>s</sub>(dry)<br>Dew point = 243.5 × ln(e ÷ 6.112) ÷ (17.67 − ln(e ÷ 6.112))</div>'
        '<p>The <strong>dew point rule</strong> for cargo holds compares two dew points. Ventilate when the dew point of the outside air is lower than the dew point of the air in the hold. Do not ventilate when it is higher, because the incoming air would give up its moisture on the cooler cargo or steel.</p>'
        '<h3>Worked example</h3>'
        '<p>Outside, the dry bulb reads 28°C and the wet bulb 25°C. The vapour pressure works out at 29.6 hPa, the relative humidity at 78% and the dew point at 23.9°C. In the hold the readings are 24°C and 20°C, a dew point of 18.0°C. The outside air is the wetter of the two, so the dew point rule says keep the hold closed.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>The formula was worked by hand from the National Weather Service document and matches two published psychrometric chart readings to within one percent of relative humidity and one degree Fahrenheit of dew point. It was also compared with the ASHRAE Handbook method for 856 pairs of readings: for dew points above freezing the two never differed by more than 0.7°C of dew point or 1 point of relative humidity.</p></div>'
        '<h3>Limits</h3><ul>'
        '<li>The wet bulb must be properly ventilated: a whirling (sling) or aspirated psychrometer, whirled until the reading stops falling. A still wet bulb in a screen reads high and makes the air look wetter than it is.</li>'
        '<li>Use clean fresh water and a clean wick. Salt on the wick spoils the reading.</li>'
        '<li>Pressure is taken as 1013.25 hPa. At sea level the barometer changes the dew point by a tenth of a degree or two at most.</li>'
        '<li>The dew point rule is one of two accepted methods. When you cannot get readings in the hold, the three degree rule is used instead: ventilate when the outside dry bulb is at least 3°C below the cargo temperature at loading. Follow the shipper\'s carrying instructions and your company procedures.</li></ul>'),
    faq=[
        ('How do you find the dew point from wet and dry bulb temperatures?',
         'Work out the vapour pressure from the wet bulb reading and the difference between the two thermometers, then find the temperature at which that vapour pressure is the saturation pressure. Dew point tables and this calculator do that for you.'),
        ('What is the dew point rule for cargo ventilation?',
         'Ventilate the hold when the dew point of the outside air is lower than the dew point of the air inside the hold. Do not ventilate when the outside dew point is higher.'),
        ('What is the three degree rule?',
         'Ventilate when the dry bulb temperature of the outside air is at least 3 degrees Celsius cooler than the average cargo temperature taken at loading. It is used when hold dew points cannot be measured.'),
    ],
    guides=[(G + 'stability-cargo/liquefaction-of-solid-bulk-cargoes-imsbc-code/', 'Solid bulk cargoes and the IMSBC Code'),
            (G + 'meteorology/fog-types-and-when-they-form/', 'Fog types and when they form')],
))

# =====================================================================================
# 17. Sunrise, sunset and twilight
# =====================================================================================
TOOLS.append(dict(
    slug='sunrise-sunset-twilight-calculator', cat='Navigation',
    name='Sunrise, sunset and twilight',
    blurb='Sunrise, sunset, civil and nautical twilight and meridian passage in ship\'s time.',
    icon='<path d="M12 3v3"/><path d="M5 9l2 2"/><path d="M19 9l-2 2"/><path d="M7 17a5 5 0 0 1 10 0"/><path d="M3 17h18"/><path d="M6 21h12"/>',
    title='Sunrise, Sunset and Twilight Calculator for Ships | Ocean Link',
    h1='Sunrise, sunset and twilight calculator',
    desc='Free sunrise and sunset calculator for ships. Enter date and position to get sunrise, sunset, civil and nautical twilight and the Sun\'s meridian passage in ship\'s time, without an almanac.',
    lead='Enter the date and your position to get sunrise, sunset, both twilights and the time of meridian passage in ship\'s time, for star sights, the noon sight and the log.',
    form=(
        '<div class="fields">'
        + date('date', "Date (ship's date)") + zone('zone', "Ship's time zone")
        + latlon('lat', 'Latitude', '20', '00.0', 'N', 'lat')
        + latlon('lon', 'Longitude', '000', '00.0', 'E', 'lon')
        + '</div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI, $ = U.$;
  var now = new Date(), off = -now.getTimezoneOffset() / 60;
  $('date').value = new Date(now.getTime() + off * 3600000).toISOString().slice(0, 10);
  if ([].some.call($('zone').options, function (o) { return parseFloat(o.value) === off; })) $('zone').value = String(off);
  var dl = Math.max(-180, Math.min(180, Math.round(off * 15)));
  $('lond').value = ('00' + Math.abs(dl)).slice(-3); $('lonh').value = dl < 0 ? 'W' : 'E';
  function dms(x) { var d = Math.floor(x), m = (x - d) * 60; if (parseFloat(m.toFixed(1)) >= 60) { d += 1; m = 0; } return d + '°' + (m < 9.95 ? '0' : '') + m.toFixed(1) + "'"; }
  function run() {
    var z = parseFloat(U.val('zone')), day = U.dateMs(U.val('date'), 0, 0), lat = U.latlon('lat', 90), lon = U.latlon('lon', 180);
    if (isNaN(day) || isNaN(lat) || isNaN(lon)) { U.need('res', 'Enter the date and your position.'); return; }
    var s = C.sunEvents(day - z * 3600000, lat, lon);
    if (!s) { U.need('res', 'No meridian passage was found on this date. Check the time zone against the longitude.'); return; }
    function clock(ms) { // ship's time, to the nearest minute, with a note when it falls on another date
      var t = Math.round((ms + z * 3600000) / 60000) * 60000, d = new Date(t), dd = Math.round((Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()) - day) / 86400000);
      return ('0' + d.getUTCHours()).slice(-2) + ':' + ('0' + d.getUTCMinutes()).slice(-2) + (dd > 0 ? ' next day' : dd < 0 ? ' previous day' : '');
    }
    function ev(ms, limit) { // a time, or why there is none
      if (ms !== null) return clock(ms);
      return s.transitAlt < limit ? 'Sun stays below' : 'Sun stays above';
    }
    var L = C.SUN_LIMITS, h, note = '';
    if (s.rise !== null || s.set !== null) { // on the day the midnight sun begins or ends there is only one of the two
      h = '<div class="two"><div><div class="label">Sunrise</div><div class="big" id="r_rise">' + (s.rise !== null ? clock(s.rise) : 'None') + '</div></div>' +
        '<div><div class="label">Sunset</div><div class="big" id="r_set">' + (s.set !== null ? clock(s.set) : 'None') + '</div></div></div>';
      if (s.rise === null) note = 'No sunrise on this date: the Sun was already above the horizon when the day began.';
      if (s.set === null) note = 'No sunset on this date: the Sun stays above the horizon into the next day.';
    } else {
      h = '<div class="label">Sun</div><div class="big" id="r_rise">' + (s.transitAlt < L.rise ? 'Does not rise' : 'Does not set') + '</div>';
    }
    h += '<p class="sub">Ship\'s time, ' + U.zone(z) + '</p>';
    var north = lat > s.dec;
    h += U.kv([['Nautical twilight begins', '<span id="r_nb">' + ev(s.nautBegin, L.naut) + '</span>'], ['Civil twilight begins', '<span id="r_cb">' + ev(s.civilBegin, L.civil) + '</span>'],
      s.rise !== null ? ['Sunrise', clock(s.rise) + ', bearing <span id="r_raz">' + U.brg(s.riseAz, 0) + 'T</span>'] : null,
      ['Meridian passage', '<span id="r_mp">' + clock(s.transit) + '</span>'],
      ['Altitude at meridian passage', '<span id="r_alt">' + (s.transitAlt >= 0 ? dms(s.transitAlt) + ', bearing ' + (north ? 'south' : 'north') : 'Below the horizon') + '</span>'],
      s.set !== null ? ['Sunset', clock(s.set) + ', bearing <span id="r_saz">' + U.brg(s.setAz, 0) + 'T</span>'] : null,
      ['Civil twilight ends', '<span id="r_ce">' + ev(s.civilEnd, L.civil) + '</span>'], ['Nautical twilight ends', '<span id="r_ne">' + ev(s.nautEnd, L.naut) + '</span>'],
      s.rise !== null && s.set !== null ? ['Sunrise to sunset', '<span id="r_len">' + U.dur((s.set - s.rise) / 3600000) + '</span>'] : null]);
    if (note) h += '<div class="msg" id="r_note">' + note + '</div>';
    if (Math.abs(lat) > 62) h += '<div class="msg">At this latitude the Sun crosses the horizon at a shallow angle, so the times can be a few minutes out and depend heavily on refraction.</div>';
    U.out('res', h);
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<p>The tool computes the Sun\'s position from the date and time, then finds the moments when its altitude crosses the limits the Nautical Almanac uses:</p>'
        '<table><tr><th>Event</th><th>Altitude of the Sun\'s centre</th></tr>'
        '<tr><td>Sunrise and sunset</td><td>−0°50′ (upper limb on the horizon, with 34′ of refraction and 16′ semi-diameter)</td></tr>'
        '<tr><td>Civil twilight</td><td>−6°</td></tr><tr><td>Nautical twilight</td><td>−12°</td></tr></table>'
        '<p><strong>Meridian passage</strong> is the moment the Sun is due north or south of you, when its local hour angle is zero. The altitude shown for it is the true altitude of the Sun\'s centre: 90° minus the difference between your latitude and the declination.</p>'
        '<p>Morning stars are taken between the start of nautical twilight and the start of civil twilight, when both the stars and the horizon are visible. Evening stars are taken between the end of civil twilight and the end of nautical twilight.</p>'
        '<h3>Worked example</h3>'
        '<p>On 1 September 1994 in 36°14′N 069°26′W, keeping UTC−5, the tool gives sunset at 18:06 ship\'s time. That is 23:06 UTC, or 18:28 local mean time at that longitude. A US Navy navigation course works the same case from the Nautical Almanac and gets a local mean time of 1827.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>Sunrise, sunset, both twilights and meridian passage were computed for 275 days between 2026 and 2039 with an independent astronomical library (astropy) and compared with the tool: 1,604 events. Up to 62° of latitude the largest difference was 3 seconds for sunrise and sunset, 10 seconds for civil twilight, 4 seconds for nautical twilight and 2 seconds for meridian passage. Two worked examples taken from the Nautical Almanac in published navigation courses agree within one minute. Against the Hong Kong Observatory Almanac 2026, an official printed table, the tool was checked on every day of March, June, September and December: of the 366 times of sunrise, meridian passage and sunset, 361 are the same to the minute and the other five are one minute apart, each within two seconds of the half minute.</p></div>'
        '<h3>Limits</h3><ul>'
        '<li>Times are for an observer at sea level. From a bridge 20 to 30 m up, sunrise is seen a minute or so earlier and sunset later, more in high latitudes.</li>'
        '<li>Refraction near the horizon varies with the weather. A minute or two of difference from what you observe is normal.</li>'
        '<li>Enter the position where the ship will be at the event, not where she is now. Every 15′ of longitude moves the times by one minute.</li>'
        '<li>Above the polar circles the Sun may stay up or down all day; the tool then says so. On the day the midnight sun begins or ends there is a sunrise without a sunset, or a sunset without a sunrise, and the tool shows the one that exists. Close to those dates the times are sensitive and should be treated as approximate.</li></ul>'),
    faq=[
        ('What is the difference between civil and nautical twilight?',
         'Civil twilight is the time when the Sun is between the horizon and 6 degrees below it. Nautical twilight is when it is between 6 and 12 degrees below. Star sights are taken between the two, when stars and the horizon can be seen together.'),
        ('How is the time of sunrise defined in the Nautical Almanac?',
         'Sunrise is when the upper limb of the Sun is on the visible horizon for an observer at sea level. Allowing for refraction and the semi-diameter, the centre of the Sun is then 50 minutes of arc below the horizon.'),
        ('What is meridian passage?',
         'Meridian passage is the moment the Sun crosses your meridian and reaches its highest altitude, bearing due north or south. It is the time of the noon sight for latitude.'),
    ],
    guides=[(G + 'navigation/celestial-navigation-basics-noon-sight/', 'Celestial navigation basics and the noon sight'),
            (G + 'navigation/azimuth-and-amplitude-observations/', 'Azimuth and amplitude observations')],
))

# =====================================================================================
# 18. Rate of turn
# =====================================================================================
TOOLS.append(dict(
    slug='rate-of-turn-calculator', cat='Bridge watch',
    name='Rate of turn and radius',
    blurb='Rate of turn for a planned radius, time to complete the turn and the wheel-over distance.',
    icon='<path d="M5 20V11a6 6 0 0 1 6-6h8"/><path d="M16 2l3 3-3 3"/>',
    title='Rate of Turn Calculator: ROT, Turn Radius and Wheel-Over Distance | Ocean Link',
    h1='Rate of turn calculator',
    desc='Free rate of turn calculator for ships. Enter speed and turn radius to get the rate of turn in degrees per minute, the time to complete the turn and the wheel-over distance.',
    lead='Find the rate of turn that holds a planned radius at your speed, or the radius you are turning on, with the time and wheel-over distance for a course change.',
    form=(
        seg('mode', [('rot', 'Find rate of turn'), ('rad', 'Find radius')], cls='modes')
        + '<div class="fields">' + num('spd', 'Speed over ground (kn)', '12')
        + '<div id="f_rad">' + num('rad', 'Turn radius (nm)', '1.0') + '</div>'
        + '<div id="f_rot">' + num('rot', 'Rate of turn (°/min)', '11.5') + '</div>'
        + num('ang', 'Course change (°)', '45', hint='Optional', cls='full')
        + '</div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI;
  var mode = U.seg('mode', run);
  function dist(nm) { return U.fx(nm, 2) + ' nm (' + U.fx(nm * 10, 1) + ' cables)'; }
  function run() {
    var findRot = mode.get() === 'rot'; U.show('f_rad', findRot); U.show('f_rot', !findRot);
    var v = U.num('spd'), r, rot, h;
    if (!(v > 0)) { U.need('res', 'Enter the speed over the ground.'); return; }
    if (findRot) {
      r = U.num('rad'); if (!(r > 0)) { U.need('res', 'Enter the turn radius in nautical miles.'); return; }
      rot = C.rateOfTurn(v, r);
      h = '<div class="label">Rate of turn</div><div class="big" id="r_main">' + U.fx(rot, 1) + ' <small>°/min</small></div><p class="sub">The bridge rule of speed ÷ radius gives ' + U.fx(v / r, 1) + '.</p>';
    } else {
      rot = U.num('rot'); if (!(rot > 0)) { U.need('res', 'Enter the rate of turn in degrees per minute.'); return; }
      r = C.turnRadius(v, rot);
      h = '<div class="label">Turn radius</div><div class="big" id="r_main">' + U.fx(r, 2) + ' <small>nm</small></div><p class="sub">' + U.fx(r * 10, 1) + ' cables, ' + U.big(r * 1852, 0) + ' m</p>';
    }
    var a = U.num('ang'), rows = [findRot ? ['Radius', dist(r)] : ['Rate of turn', U.fx(rot, 1) + ' °/min'], ['Rate of turn per second', U.fx(rot / 60, 2) + ' °/s']];
    if (a > 0 && a < 180) {
      var t = C.turn(v, r, a), sec = Math.round(t.minutes * 60);
      rows.push(['Time for ' + U.fx(a, a % 1 ? 1 : 0) + '°', '<span id="r_time">' + Math.floor(sec / 60) + ' min ' + ('0' + sec % 60).slice(-2) + ' s</span>'],
        ['Distance run on the arc', '<span id="r_arc">' + dist(t.arc) + '</span>'], ['Arc starts before the waypoint by', '<span id="r_wo">' + dist(t.wheelOver) + '</span>']);
    } else if (a >= 180) { h += ''; rows.push(['Course change', 'Enter less than 180°']); }
    h += U.kv(rows);
    if (a > 0 && a < 180) h += '<p class="sub" style="margin-top:10px">Put the wheel over earlier than the start of the arc by your ship\'s reaction distance.</p>';
    U.out('res', h);
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<p>On a turn of constant radius the ship moves along an arc. The angle she turns through each minute is her speed along the arc divided by the radius:</p>'
        '<div class="formula">Rate of turn (°/min) = speed (kn) ÷ radius (nm) × 57.3 ÷ 60 = 0.955 × speed ÷ radius</div>'
        '<p>On the bridge this is shortened to <strong>rate of turn = speed ÷ radius</strong>, which reads about 5% high. The tool gives the exact figure and shows the bridge rule beside it.</p>'
        '<p>For a planned course change the rest is geometry:</p>'
        '<div class="formula">Time = course change ÷ rate of turn<br>Distance on the arc = radius × course change (in radians)<br>Start of the arc before the waypoint = radius × tan(course change ÷ 2)</div>'
        '<h3>Worked example</h3>'
        '<p>At 12 knots on a 1.0 nm radius the rate of turn is 0.955 × 12 ÷ 1.0 = 11.5°/min. A 45° alteration takes 3 min 56 s and 0.79 nm along the arc. The arc begins 1.0 × tan 22.5° = 0.41 nm before the waypoint, and the wheel goes over earlier than that by the ship\'s reaction distance.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>The rate of turn matches the published formula 57.3 × V ÷ (60 × R) and the textbook examples worked with the bridge rule (15 knots on 1.5 nm, 8 knots on 4 cables) to within the 5% of that rule. Time, arc length and tangent distance were tested against the geometry of the turn for 300 random speeds, radii and course changes.</p></div>'
        '<h3>Limits</h3><ul>'
        '<li>Use speed over the ground. The ship slows in the turn, so the rate of turn has to come down with the speed to hold the radius. Plan with the mean of the speeds before and after.</li>'
        '<li>The start of the arc is not the wheel-over point. The ship needs time to answer the helm: add your reaction distance from the manoeuvring data, often about one ship\'s length.</li>'
        '<li>Wind, current and shallow water all change how the ship turns. Monitor the turn with a parallel index or the predictor, not the calculation alone.</li></ul>'),
    faq=[
        ('What is the formula for rate of turn?',
         'Rate of turn in degrees per minute equals 0.955 times the speed in knots divided by the turn radius in nautical miles. The common bridge rule is simply speed divided by radius, which reads about 5 percent high.'),
        ('How do you calculate the wheel-over point?',
         'The turning arc begins a distance of radius times the tangent of half the course change before the waypoint. The wheel-over point is earlier than that by the distance the ship runs before she starts to answer the helm.'),
        ('What rate of turn do I need for a 1 mile radius at 15 knots?',
         'About 14.3 degrees per minute, from 0.955 times 15 divided by 1. The bridge rule of speed divided by radius gives 15.'),
    ],
    guides=[(G + 'operations/passage-planning-appraisal-planning-execution-monitoring/', 'Passage planning'),
            (G + 'operations/parallel-indexing/', 'Parallel indexing'),
            (G + 'navigation/pilotage-master-pilot-information-exchange/', 'Pilotage and the master-pilot exchange')],
))

# =====================================================================================
# 19. Horizon and light range
# =====================================================================================
TOOLS.append(dict(
    slug='distance-to-horizon-calculator', cat='Navigation',
    name='Horizon and light range',
    blurb='Distance to the sea horizon, the range at which a light dips, and the radar horizon.',
    icon='<path d="M9.500 21l1.500-12h2l1.500 12"/><path d="M10 9V6h4v3"/><path d="M7 21h10"/><path d="M4 5l3 1.500"/><path d="M20 5l-3 1.500"/>',
    title='Distance to Horizon Calculator: Dipping Range of Lights and Radar Horizon | Ocean Link',
    h1='Horizon and light range calculator',
    desc='Free distance to horizon calculator for ships. Enter height of eye and the height of a light to get the sea horizon, the dipping range of the light and the radar horizon in nautical miles.',
    lead='Enter your height of eye to get the distance to the sea horizon. Add the height of a light for its dipping range, and the scanner height for the radar horizon.',
    form=(
        '<div class="fields">'
        + num('eye', 'Height of eye (m)', '25', cls='full')
        + num('obj', 'Height of light (m)', '40', hint='Optional. Elevation of the light or object from the chart or the List of Lights')
        + num('ant', 'Scanner height (m)', '', hint='Optional. For the radar horizon')
        + '</div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI, K = C.HORIZON;
  function run() {
    var eye = U.num('eye'), obj = U.num('obj'), ant = U.num('ant');
    if (!(eye > 0)) { U.need('res', 'Enter your height of eye in metres.'); return; }
    var d = C.horizon(eye), hasObj = obj > 0, rows = [], h;
    if (hasObj) {
      var dip = d + C.horizon(obj);
      h = '<div class="two"><div><div class="label">Sea horizon</div><div class="big" id="r_hor">' + U.fx(d, 1) + ' <small>nm</small></div></div>' +
        '<div><div class="label">Light dips at</div><div class="big" id="r_dip">' + U.fx(dip, 1) + ' <small>nm</small></div></div></div>';
      rows.push(['Horizon seen from the light', U.fx(C.horizon(obj), 1) + ' nm'],
        ['Dipping range in other tables', '<span id="r_span">' + U.fx(C.horizon(eye, K.low) + C.horizon(obj, K.low), 1) + ' to ' + U.fx(C.horizon(eye, K.high) + C.horizon(obj, K.high), 1) + ' nm</span>']);
    } else {
      h = '<div class="label">Sea horizon</div><div class="big" id="r_hor">' + U.fx(d, 1) + ' <small>nm</small></div>';
      rows.push(['In other tables', '<span id="r_span">' + U.fx(C.horizon(eye, K.low), 1) + ' to ' + U.fx(C.horizon(eye, K.high), 1) + ' nm</span>']);
    }
    if (ant > 0) {
      rows.push(['Radar horizon', '<span id="r_rad">' + U.fx(C.horizon(ant, K.radar), 1) + ' nm</span>']);
      if (hasObj) rows.push(['Radar range to the top of the object', '<span id="r_rado">' + U.fx(C.horizon(ant, K.radar) + C.horizon(obj, K.radar), 1) + ' nm</span>']);
    }
    U.out('res', h + U.kv(rows));
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<p>The Earth\'s curve hides the sea beyond a distance that depends on your height. Light bends slightly round the curve, so you see a little farther than the geometry alone allows. With heights in metres and distances in nautical miles:</p>'
        '<div class="formula">Sea horizon = 2.08 × √(height of eye)<br>Dipping range of a light = 2.08 × (√(height of eye) + √(height of light))<br>Radar horizon = 2.21 × √(scanner height)</div>'
        '<p>A light <strong>dips</strong> when it sinks below your horizon, or rises above it. That happens where your horizon and the light\'s horizon meet, so the two distances are added. Radar waves bend a little more than light, which is why the radar horizon is slightly farther.</p>'
        '<h3>Why tables disagree</h3>'
        '<p>The figure 2.08 depends on how much refraction is assumed, and publications do not agree. IALA uses 2.03. Bowditch gives 2.07 as a formula, while its Table 12 works out at 2.12. Reeds and the RYA use 2.08. The tool shows the range from 2.03 to 2.12 beside the answer so you can see the spread, which is about 2% either way.</p>'
        '<h3>Worked example</h3>'
        '<p>Height of eye 25 m: the horizon is 2.08 × 5 = 10.4 nm away. A light 40 m high has its own horizon at 2.08 × 6.32 = 13.2 nm, so it dips at about 23.6 nm. With the scanner at 30 m the radar horizon is 2.21 × 5.48 = 12.1 nm.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>Using the constant behind Bowditch Table 12, the same code reproduces 17 values of that table from 1.5 m to 152 m to the printed tenth of a mile. The constants 2.08 and 2.21 were checked against the formulas in Bowditch and the published dipping distance formula.</p></div>'
        '<h3>Limits</h3><ul>'
        '<li>Refraction changes with the weather. In abnormal conditions the true distance can differ by far more than the 2% spread between tables.</li>'
        '<li>Charted elevations of lights are above high water. At a lower tide the light is higher above the sea and dips a little farther off.</li>'
        '<li>The dipping range is a geographical limit. A weak light may not be seen that far: check its nominal range and the visibility.</li>'
        '<li>A dipping distance with a bearing gives an approximate position only. Confirm it with another fix.</li></ul>'),
    faq=[
        ('What is the formula for distance to the horizon at sea?',
         'In nautical miles it is about 2.08 times the square root of the height of eye in metres, or 1.17 times the square root of the height in feet. Different publications use constants from 2.03 to 2.12 because they assume different refraction.'),
        ('What is the dipping distance of a light?',
         'It is the distance at which a light just appears on or disappears below the horizon. Add the horizon distance for your height of eye to the horizon distance for the height of the light.'),
        ('Why is the radar horizon farther than the visible horizon?',
         'Radar waves are bent round the Earth slightly more than light. The radar horizon in nautical miles is about 2.21 times the square root of the scanner height in metres.'),
    ],
    guides=[(G + 'navigation/chartwork-basics-position-fixing-methods/', 'Chartwork basics and position fixing'),
            (G + 'navigation/admiralty-publications-every-bridge-carries/', 'Admiralty publications every bridge carries')],
))

# =====================================================================================
# 20. Rolling period and GM
# =====================================================================================
TOOLS.append(dict(
    slug='rolling-period-gm-calculator', cat='Stability and cargo',
    name='Rolling period and GM',
    blurb='Rolling period from GM or GM from a timed roll, and the wave encounter period.',
    icon='<path d="M3 18c2-1.500 4-1.500 6 0s4 1.500 6 0 4-1.500 6 0"/><path d="M6.500 13l11-3-1.500 4.500H8z"/><path d="M12 11V6"/>',
    title='Rolling Period and GM Calculator, Wave Encounter Period | Ocean Link',
    h1='Rolling period and GM calculator',
    desc='Free rolling period calculator for ships using the IMO Intact Stability Code formula. Find the rolling period from GM or GM from a timed roll, and the wave encounter period from MSC.1/Circ.1228.',
    lead='Estimate the rolling period from GM, or GM from a timed roll, with the Intact Stability Code formula. Add the waves to compare the encounter period with the rolling period.',
    form=(
        seg('mode', [('t', 'Period from GM'), ('gm', 'GM from period')], cls='modes')
        + '<div class="fields">' + num('beam', 'Beam (m)', '32.2') + num('dr', 'Mean draught (m)', '12.0')
        + num('lwl', 'Waterline length (m)', '220')
        + '<div id="f_gm">' + num('gm', 'GM, fluid (m)', '2.50') + '</div>'
        + '<div id="f_per">' + num('per', 'Rolling period (s)', '14.0', hint='One complete roll, side to side and back') + '</div>'
        + '</div><h2>Waves (optional)</h2><div class="fields three">'
        + num('tw', 'Wave period (s)', '') + num('spd', 'Ship speed (kn)', '')
        + num('wang', 'Waves off the bow (°)', '', hint='0 head sea, 180 following')
        + '</div>'),
    script=r'''
(function () {
  var C = OLCalc, U = OLUI;
  var mode = U.seg('mode', run);
  function run() {
    var fromGm = mode.get() === 't'; U.show('f_gm', fromGm); U.show('f_per', !fromGm);
    var B = U.num('beam'), d = U.num('dr'), L = U.num('lwl'), T, gm, h;
    if (!(B > 0) || !(d > 0) || !(L > 0)) { U.need('res', 'Enter the beam, the mean draught and the waterline length.'); return; }
    var c = C.rollCoeff(B, d, L);
    if (!(c > 0.2)) { U.need('res', 'These dimensions are outside the range of the formula. Check the beam, draught and length.'); return; }
    if (fromGm) {
      gm = U.num('gm'); if (isNaN(gm)) { U.need('res', 'Enter the fluid GM.'); return; }
      if (!(gm > 0)) { U.out('res', '<div class="msg crit">GM must be positive. With zero or negative GM the ship has no rolling period: she will loll.</div>'); return; }
      T = C.rollPeriod(B, d, L, gm);
      h = '<div class="label">Rolling period</div><div class="big" id="r_main">' + U.fx(T, 1) + ' <small>s</small></div>';
    } else {
      T = U.num('per'); if (!(T > 0)) { U.need('res', 'Enter the rolling period in seconds.'); return; }
      gm = C.gmFromRoll(B, d, L, T);
      h = '<div class="label">GM</div><div class="big" id="r_main">' + U.fx(gm, 2) + ' <small>m</small></div>';
    }
    var rows = [['Coefficient C', '<span id="r_c">' + U.fx(c, 3) + '</span>'], ['Same as T = f × B ÷ √GM with f', U.fx(2 * c, 2)]], msg = '';
    var tw = U.num('tw'), v = U.num('spd'), a = U.num('wang');
    if (tw > 0 && v >= 0 && a >= 0 && a <= 180) {
      rows.push(['Wave length', '<span id="r_wl">' + U.fx(C.waveLength(tw), 0) + ' m</span>']);
      var te = C.encounterPeriod(tw, v, a);
      if (!isFinite(te) || te < 0) {
        rows.push(['Encounter period', '<span id="r_te">None</span>']);
        msg = '<div class="msg warn">At this speed and heading the ship keeps pace with the waves or overtakes them (they travel at about ' + U.fx(3 * tw, 0) + ' kn), so there is no regular encounter period. This is the high-speed following sea case that MSC.1/Circ.1228 warns about.</div>';
      } else {
        var ratio = te / T;
        rows.push(['Encounter period', '<span id="r_te">' + U.fx(te, 1) + ' s</span>'], ['Encounter period ÷ rolling period', '<span id="r_ratio">' + U.fx(ratio, 2) + '</span>']);
        var pc = Math.round(parseFloat(U.fx(ratio, 2)) * 100); // the ratio as printed, in hundredths
        if (pc >= 90 && pc <= 110) msg = '<div class="msg warn" id="r_flag">The encounter period is within 10% of the rolling period. MSC.1/Circ.1228 names this as the condition for synchronous rolling, and for parametric rolling in head or following seas.</div>';
        else if (pc >= 45 && pc <= 55) msg = '<div class="msg warn" id="r_flag">The encounter period is within 10% of half the rolling period. MSC.1/Circ.1228 names this as a condition for parametric rolling in head or following seas.</div>';
        if (fromGm) msg += '<div class="msg" id="r_est">This comparison uses the rolling period estimated by the formula, which can be 10% or more out, mostly on the short side for large ships. For a decision, time the roll and enter it under GM from period.</div>';
      }
    }
    U.out('res', h + U.kv(rows) + msg);
  }
  U.live(run);
})();''',
    how=(
        '<h2>How it works</h2>'
        '<p>A stiff ship with a large GM snaps back quickly and has a short rolling period. A tender ship rolls slowly. The 2008 Intact Stability Code gives this approximate formula in its weather criterion:</p>'
        '<div class="formula">T = 2 × C × B ÷ √GM<br>C = 0.373 + 0.023 × (B ÷ d) − 0.043 × (L<sub>wl</sub> ÷ 100)</div>'
        '<p>T is the rolling period in seconds for one complete roll, B the moulded beam, d the mean draught, L<sub>wl</sub> the waterline length and GM the metacentric height corrected for free surface, all in metres. Turned round, it gives GM from a roll you have timed: GM = (2 × C × B ÷ T)².</p>'
        '<p>For waves, MSC.1/Circ.1228 gives the wave length and the period at which the ship meets the waves:</p>'
        '<div class="formula">Wave length (m) = 1.56 × T<sub>W</sub>²<br>Encounter period T<sub>E</sub> = 3 × T<sub>W</sub>² ÷ (3 × T<sub>W</sub> + V × cos α)</div>'
        '<p>T<sub>W</sub> is the wave period in seconds, V the speed in knots and α the angle between the keel and the wave direction, with 0° a head sea. The circular tells the master to avoid an encounter period close to the rolling period (synchronous rolling) and, in head or following seas, close to the rolling period or half of it (parametric rolling).</p>'
        '<h3>Worked example</h3>'
        '<p>Beam 32.2 m, draught 12.0 m, waterline length 220 m. C = 0.373 + 0.023 × 2.683 − 0.043 × 2.2 = 0.340. With a GM of 2.50 m the rolling period is 2 × 0.340 × 32.2 ÷ 1.581 = 13.9 s. Steaming at 15 knots into a head sea of 10 s period, the encounter period is 300 ÷ 45 = 6.7 s, which is 0.48 of the rolling period: close to half, the parametric rolling condition.</p>'
        '<div class="card checked"><div class="label">How this tool was checked</div><p>The rolling period formula and its coefficient were checked against the text of the 2008 IS Code as reproduced in the UK MCA instructions to surveyors, and the encounter period against MSC.1/Circ.1228. The encounter period was also derived from first principles for 300 cases: in head and beam seas the IMO formula agrees within 1.1%.</p></div>'
        '<h3>Limits</h3><ul>'
        '<li>The formula is an approximation. It was fitted to 71 ships measured in 1982, all within about 7.5% of it. A study presented at the International Marine Design Conference in 2024 found that it considerably underestimates the rolling period of large ships, and that errors of more than 10% are common with formulas of this kind. So a GM worked back from a timed roll can be 15% out or more, and for a large ship the period worked from GM is likely to be on the short side. It does not replace the loading computer.</li>'
        '<li>The best rolling period is the one you time yourself in calm water, as the circular recommends: several complete rolls, averaged.</li>'
        '<li>The encounter formula rounds the wave speed to 3 × T<sub>W</sub> knots. In following seas, when the ship\'s speed approaches the wave speed, it becomes very sensitive and should be read as a warning, not a number.</li>'
        '<li>Being outside the 10% bands shown here does not mean heavy rolling cannot happen. Real seas contain many periods at once.</li></ul>'),
    faq=[
        ('What is the formula for the rolling period of a ship?',
         'The 2008 Intact Stability Code gives T = 2 x C x B divided by the square root of GM, with C = 0.373 + 0.023 x (B/d) - 0.043 x (Lwl/100). T is in seconds and the dimensions and GM are in metres.'),
        ('How do you find GM from the rolling period?',
         'Time several complete rolls in calm water and take the average. Then GM equals the square of 2 x C x B divided by the rolling period. It is an estimate, within roughly 15 percent.'),
        ('What is synchronous rolling?',
         'Synchronous rolling happens when the period at which the ship meets the waves is close to her natural rolling period, so each wave adds to the roll. Altering course or speed changes the encounter period and breaks the match.'),
    ],
    guides=[(G + 'meteorology/swell-wind-waves-and-parametric-rolling/', 'Swell, wind waves and parametric rolling'),
            (G + 'stability-cargo/gm-and-metacentric-height-explained/', 'GM and metacentric height explained'),
            (G + 'operations/heavy-weather-precautions/', 'Heavy weather precautions')],
))

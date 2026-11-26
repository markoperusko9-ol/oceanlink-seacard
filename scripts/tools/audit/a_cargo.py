"""Independent end-to-end audit: bunker quantity (ASTM D1250-80 Table 54B), draught survey, LNG conversion and boil-off,
dew point. References: official printed tables, the 1980 procedure re-worked with exact decimals, the UK P&I Club and
MySeaTime worked examples, made-up ships with a known keel line, the IGU conversion table, psychrolib (ASHRAE) and the
WMO/JCOMM marine psychrometer formula."""
import math, random, sys
from decimal import Decimal as D, ROUND_HALF_UP, getcontext
from fractions import Fraction as F
import numpy as np, psychrolib
from common import *
from tables_mc import all_tables
getcontext().prec = 40
def q(x, places): return x.quantize(D(1).scaleb(-places), rounding=ROUND_HALF_UP)
def rs(rng, lo, hi, dp): return ('%.' + str(dp) + 'f') % rng.uniform(lo, hi)

def vcf_1980(rho, t):
    """Table 54B as the 1980 standard works it: alpha to seven decimals, VCF to four."""
    rho, t = D(str(rho)), D(str(t))
    if rho >= 839: a, grp = D('186.9696') / rho ** 2 + D('0.4862') / rho, 'Fuel oils'
    elif rho >= 788: a, grp = D('594.5418') / rho ** 2, 'Jet fuels and kerosenes'
    elif rho > 770: a, grp = D('-0.00336312') + D('2680.3206') / rho ** 2, 'Transition zone'
    else: a, grp = D('346.4228') / rho ** 2 + D('0.4388') / rho, 'Gasolines'
    a = q(a, 7); dt = t - 15
    return q((-a * dt * (1 + D('0.8') * a * dt)).exp(), 4), grp

def bunker_tables():
    T = Tally('bunker VCF (tool function) vs three official tables of Measurement Canada'); n = 0
    for name, rho, rw in all_tables():
        res = drive('bunker-quantity-calculator', [{'call': 'OLCalc.bunker(1000, %r, %d).vcf' % (t, rho)} for t, _ in rw], 'tab')
        for (t, v), r in zip(rw, res):
            T.close('%s: printed factor' % name, r['call'], v, 1e-9, 'T %.1f' % t); T.close('%s: my 1980 working equals the print' % name, float(vcf_1980(rho, t)[0]), v, 1e-9, 'T %.1f' % t)
    return T.report()

def bunker(n, rng):
    T = Tally('bunker quantity (page) vs the 1980 procedure in exact decimals'); cases = []; meta = []
    for i in range(n):
        rho = rng.choice([rng.uniform(653, 1075), rng.uniform(900, 1010), rng.uniform(820, 900), rng.choice([770.0, 770.5, 787.5, 788.0, 838.5, 839.0])])
        dens = ('%.4f' % (rho / 1000)) if rng.random() < 0.6 else ('%.1f' % rho); t = rs(rng, -18, 95, 1); vol = rs(rng, 0.5, 4000, 2)
        cases.append({'set': {'vol': vol, 'temp': t, 'dens': dens}}); d = D(dens); meta.append((D(vol), D(t), d * 1000 if d < 2 else d))
    for c, r, (vol, t, rho) in zip(cases, drive('bunker-quantity-calculator', cases), meta):
        ctx = str(c['set']); v, grp = vcf_1980(rho, t); gsv = q(vol * v, 3); wcf = rho / 1000 - D('0.0011')     # each line from the figure printed on the line above, as on paper
        T.close('VCF (4 dp) exactly as the standard rounds it', num(r['ids']['r_vcf']), float(v), 1e-9, ctx)
        T.eq('product group', r['kv']['Product group in Table 54B'], grp, ctx)
        T.close('standard volume (m3), rounded half up to the litre', num(r['ids']['r_gsv']), float(gsv), 1e-9, ctx); T.close('weight factor (4 dp)', num(r['ids']['r_wcf']), float(q(wcf, 4)), 1e-9, ctx)
        T.close('weight in air (t) = printed standard volume x weight factor, rounded half up', num(r['ids']['r_main']), float(q(gsv * wcf, 2)), 1e-9, ctx)
        T.close('mass in vacuum (t) = printed standard volume x density, rounded half up', num(r['ids']['r_vac']), float(q(gsv * rho / 1000, 2)), 1e-9, ctx)
        tmax = 150 if rho > 824 else 125 if rho > D('778.5') else 90
        T.eq('out-of-table warning shown exactly outside -18 to the table maximum', len(r['msg']) > 0, not (-18 <= t <= tmax), ctx)
    return T.report()

def survey_ref(fp, fs, mp, ms, ap, as_, lbp, xf, xm, xa):
    """A surveyor's sheet in exact decimals. xf: forward marks abaft the FP +, xa: aft marks forward of the AP +, xm: midship marks abaft midships +."""
    Fm, Mm, Am = (fp + fs) / 2, (mp + ms) / 2, (ap + as_) / 2; at = Am - Fm; lbm = lbp - xf - xa
    fc = q(Fm - at * xf / lbm, 4); ac = q(Am + at * xa / lbm, 4); mc = q(Mm - at * xm / lbm, 4)
    return fc, mc, ac, ac - fc, (fc + ac + 6 * mc) / 8, mc - (fc + ac) / 2
def draft(n, rng):
    T = Tally('draught survey (page) vs a surveyor\'s sheet in exact decimals and made-up ships'); cases = []; meta = []
    for i in range(n):
        lbp = D(rs(rng, 60, 330, 2)); xf = D(rs(rng, 0, 12, 2)); xa = D(rs(rng, 0, 14, 2)); xm = D(rs(rng, 0, 4, 2))
        sf, sa, sm = rng.choice([1, 1, 1, -1]), rng.choice([1, 1, 1, -1]), rng.choice([1, -1])
        t_fp = D(rs(rng, 2.5, 18, 3)); trim = D(rs(rng, -1.5, 4.5, 3)); defl = D(rs(rng, -0.12, 0.12, 3)) if i % 2 else D(0)
        line = lambda x: t_fp + trim * (lbp - x) / lbp + defl * (1 - ((2 * x - lbp) / lbp) ** 2)        # draught at x metres abaft the FP... x measured from the AP
        # positions measured from the AP: forward marks at lbp - xf*sf, aft marks at xa*sa, midship marks at lbp/2 - xm*sm
        true = lambda x_from_ap: t_fp + trim * (lbp - x_from_ap) / lbp + defl * (1 - ((2 * x_from_ap - lbp) / lbp) ** 2)
        Fr, Ar, Mr = true(lbp - xf * sf), true(xa * sa), true(lbp / 2 - xm * sm)
        heel = [D(rs(rng, -0.05, 0.05, 2)) for _ in range(3)]
        six = [q(Fr + heel[0], 2), q(Fr - heel[0], 2), q(Mr + heel[1], 2), q(Mr - heel[1], 2), q(Ar + heel[2], 2), q(Ar - heel[2], 2)]
        if min(six) <= 0.3: continue
        disp = D(rs(rng, 3000, 200000, 2)); tpc = D(rs(rng, 8, 130, 3)); lcf = D(rs(rng, 0, 9, 3)); sl = rng.choice([1, -1]); mtcp = D(rs(rng, 80, 2500, 2)); mtcm = mtcp - D(rs(rng, 1, 60, 2))
        rhot = rng.choice(['1.025', '1.025', '1.000', '1025']); rho = rng.choice([rs(rng, 0.995, 1.030, 4), rs(rng, 995, 1030, 1)]); ded = rng.choice(['', rs(rng, 100, 30000, 2)]); ls = rng.choice(['', rs(rng, 2000, 40000, 1)])
        cases.append({'sel': {'xfd': 'aft' if sf > 0 else 'fwd', 'xad': 'fwd' if sa > 0 else 'aft', 'xmd': 'aft' if sm > 0 else 'fwd', 'lcfd': 'aft' if sl > 0 else 'fwd'},
                      'set': dict(zip(['fp', 'fs', 'mp', 'ms', 'ap', 'as'], map(str, six)), lbp=str(lbp), xf=str(xf), xa=str(xa), xm=str(xm), disp=str(disp), tpc=str(tpc), lcf=str(lcf), rhot=rhot, mtcp=str(mtcp), mtcm=str(mtcm), rho=rho, ded=ded, ls=ls)})
        meta.append((six, lbp, xf * sf, xm * sm, xa * sa, disp, tpc, lcf * sl, mtcp, mtcm, D(rhot) / 1000 if D(rhot) > 2 else D(rhot), D(rho) / 1000 if D(rho) > 2 else D(rho), ded, ls, (true(lbp), true(lbp / 2), true(D(0)), defl, heel)))
    for c, r, (six, lbp, xf, xm, xa, disp, tpc, lcf, mtcp, mtcm, rhot, rho, ded, ls, truth) in zip(cases, drive('draft-survey-calculator', cases), meta):
        ctx = str(c)
        if not (lbp - xf - xa > lbp / 2): T.check('marks check message', r['empty'] is not None, ctx); continue
        fc, mc, ac, trim, mmm, dfl = survey_ref(*six, lbp, xf, xm, xa)
        T.close('forward draught at the FP (4 dp)', num(r['ids']['r_f']), float(fc), 1e-9, ctx); T.close('midship draught (4 dp)', num(r['ids']['r_m']), float(mc), 1e-9, ctx); T.close('aft draught at the AP (4 dp)', num(r['ids']['r_a']), float(ac), 1e-9, ctx)
        T.close('mean of means (4 dp)', num(r['ids']['r_mmm']), float(mmm), half(4), ctx)
        st = r['ids']['r_trim']
        if abs(trim) >= D('0.00005'): T.close('true trim (m)', num(st), float(abs(trim)), 1e-9, ctx); T.check('trim by the stern or by the head', st.endswith('stern' if trim > 0 else 'head'), st + ctx)
        sd = r['ids']['r_defl']
        if abs(dfl) >= D('0.0006'): T.close('hog or sag (cm, 1 dp)', num(sd), float(abs(dfl) * 100), half(1), ctx); T.check('sag when midships is deeper, hog when shallower', sd.startswith('Sagged' if dfl > 0 else 'Hogged'), sd + ctx)
        # made-up ship: with a straight keel the sheet must give back the draughts at the perpendiculars that the marks were read from
        tfp, tmid, tap, defl, heel = truth
        if defl == 0:
            T.close('straight keel: FP draught recovered (m)', float(fc), float(tfp), 0.0051 + 0.005 * float(abs(xf) + abs(xa)) / float(lbp - xf - xa) * 2, ctx)
            T.close('straight keel: AP draught recovered (m)', float(ac), float(tap), 0.0051 + 0.005 * float(abs(xf) + abs(xa)) / float(lbp - xf - xa) * 2, ctx)
            T.close('straight keel: midship draught recovered (m)', float(mc), float(tmid), 0.0061, ctx)
        # a survey sheet: every figure rounded half up to two decimals as it is written, every line taken from the line above as written
        ftc = q(trim * 100 * tpc * lcf / lbp, 2); stc = q(trim ** 2 * 50 * (mtcp - mtcm) / lbp, 2); dtr = q(disp + ftc + stc, 2); dtrue = q(dtr * rho / rhot, 2)
        T.close('first trim correction (t), as on the sheet', num(r['ids']['r_ftc']), float(ftc), 1e-9, ctx); T.close('second trim correction (t), as on the sheet', num(r['ids']['r_stc']), float(stc), 1e-9, ctx)
        T.check('first correction added when the LCF lies toward the deeper end', (num(r['ids']['r_ftc']) > 0) == ((lcf > 0) == (trim > 0)) or abs(ftc) < D('0.005'), r['ids']['r_ftc'] + ctx)
        T.check('second correction never negative', num(r['ids']['r_stc']) >= 0, ctx)
        T.close('displacement corrected for trim = displacement + the two corrections as printed', num(r['ids']['r_dt']), float(dtr), 1e-9, ctx); T.close('displacement in dock water, from the line above as printed', num(r['ids']['r_true']), float(dtrue), 1e-9, ctx)
        T.close('headline displacement (t, 1 dp)', num(r['ids']['r_disp']), float(q(dtrue, 1)), 1e-9, ctx); T.close('density correction = difference of the two printed displacements', num(r['kv']['Density correction']), float(dtrue - dtr), 1e-9, ctx)
        net = dtrue
        if ded: net -= D(ded); T.close('less deductibles (t), column adds up', num(r['ids']['r_net']), float(net), 1e-9, ctx)
        if ls: T.close('less light ship (t), column adds up', num(r['ids']['r_ls']), float(net - D(ls)), 1e-9, ctx)
    bad = T.report()
    # published examples
    P = Tally('draught survey: published worked examples')
    r = drive('draft-survey-calculator', [{'set': {}}, {'sel': {'xfd': 'aft', 'xad': 'fwd', 'xmd': 'fwd'}, 'set': {'fp': '6.43', 'fs': '6.43', 'mp': '7.42', 'ms': '7.42', 'ap': '8.53', 'as': '8.53', 'lbp': '174.03', 'xf': '9.95', 'xa': '9.08', 'xm': '2.29'}}], 'pub')
    d = r[0]['ids']
    for key, want, tol in (('r_mmm', 5.0357, 5e-5), ('r_ftc', -102.61, 0.005), ('r_stc', 3.03, 0.005), ('r_true', 19669.26, 0.005)): P.close('UK P&I Club example: ' + key, num(d[key]), want, tol + 1e-9)
    P.close('MySeaTime example: forward draught 6.295', num(r[1]['ids']['r_f']), 6.295, 0.0006); P.close('MySeaTime example: aft draught 8.653', num(r[1]['ids']['r_a']), 8.653, 0.0006); P.close('MySeaTime example: midship draught 7.451', num(r[1]['ids']['r_m']), 7.451, 0.0006)
    return bad + P.report()

MJ = D('1055.05585262'); NS = D('0.9476')
def lng(n, rng):
    T = Tally('LNG conversion and boil-off (page)'); cases = []; meta = []
    for i in range(n):
        unit = rng.choice(['m3', 't', 'mmbtu', 'nm3']); qty = {'m3': rs(rng, 100, 270000, 1), 't': rs(rng, 50, 125000, 1), 'mmbtu': rs(rng, 1000, 6500000, 0), 'nm3': rs(rng, 50000, 160000000, 0)}[unit]
        dens = rs(rng, 380, 520, 1); gas = rs(rng, 1100, 1500, 1); mj = rng.random() < 0.4; heat = rs(rng, 47.6, 60.0, 2) if mj else rs(rng, 45, 57, 2)
        bo = rng.random() < 0.5; v0 = rs(rng, 20000, 270000, 1) if bo else ''; v1 = ('%.1f' % (float(v0) - rng.uniform(0, 900))) if bo else ''; hrs = rs(rng, 1, 400, 1) if bo else ''
        cases.append({'sel': {'unit': unit, 'heatd': 'mj' if mj else 'mmbtu'}, 'set': {'qty': qty, 'dens': dens, 'gas': gas, 'heat': heat, 'v0': v0, 'v1': v1, 'hrs': hrs}})
        meta.append((unit, D(qty), D(dens), D(gas), D(heat) * 1000 / MJ if mj else D(heat), v0, v1, hrs))
    for c, r, (unit, qty, dens, gas, heat, v0, v1, hrs) in zip(cases, drive('lng-conversion-boil-off-calculator', cases), meta):
        ctx = str(c)
        if not (45 <= heat <= 57): T.check('heating value outside the accepted range', r['empty'] is not None, ctx); continue
        t = {'t': qty, 'm3': qty * dens / 1000, 'mmbtu': qty / heat, 'nm3': qty / gas}[unit]
        T.close('mass (t, 1 dp)', num(r['ids']['r_t']), float(t), half(1), ctx); T.close('liquid volume (m3, 0 dp)', num(r['ids']['r_m3']), float(t * 1000 / dens), half(0), ctx)
        T.close('energy (MMBtu, 0 dp)', num(r['ids']['r_mmbtu']), float(t * heat), half(0), ctx); T.close('energy (GJ, 0 dp)', num(r['kv']['Energy in gigajoules']), float(t * heat * MJ / 1000), half(0), ctx)
        T.close('gas at 0 C (Nm3)', num(r['ids']['r_nm3']), float(t * gas), half(0), ctx); T.close('gas at 15 C (Sm3)', num(r['ids']['r_sm3']), float(t * gas / NS), half(0), ctx)
        T.close('headline', num(r['ids']['r_main']), float(t * 1000 / dens if unit == 't' else t), half(0), ctx)
        if v0:
            a, b, h = D(v0), D(v1), D(hrs); day = (a - b) / h * 24
            T.close('boil-off (% per day, 3 dp)', num(r['ids']['r_bor']), float(day / a * 100), half(3), ctx); T.close('boil-off per day (m3)', num(r['ids']['r_bm3']), float(day), half(1), ctx); T.close('boil-off per day (t)', num(r['ids']['r_bt']), float(day * dens / 1000), half(1), ctx)
    bad = T.report()
    I = Tally('LNG: International Gas Union conversion table (450 kg/m3, 1,300 Nm3/t, 53.38 MMBtu/t)')
    base = {'dens': '450', 'gas': '1300', 'heat': '53.38', 'v0': '', 'v1': '', 'hrs': ''}
    res = drive('lng-conversion-boil-off-calculator', [{'sel': {'unit': 't', 'heatd': 'mmbtu'}, 'set': dict(base, qty='1000')}, {'sel': {'unit': 'm3', 'heatd': 'mmbtu'}, 'set': dict(base, qty='1000')},
                {'sel': {'unit': 'mmbtu', 'heatd': 'mmbtu'}, 'set': dict(base, qty='1000000')}, {'sel': {'unit': 'nm3', 'heatd': 'mmbtu'}, 'set': dict(base, qty='1000000')}], 'igu')
    for r, wants in zip(res, [{'r_m3': 2222, 'r_nm3': 1300000, 'r_mmbtu': 53380}, {'r_t': 450.0, 'r_nm3': 585000, 'r_mmbtu': 24021}, {'r_t': 18733.6, 'r_m3': 41630}, {'r_t': 769.2, 'r_m3': 1709, 'r_mmbtu': 41062}]):
        for k, w in wants.items(): I.close('IGU table value ' + k, num(r['ids'][k]), w, max(0.6, w * 6e-4))
    return bad + I.report()

def nws(dry, wet, p=1013.25):
    es = lambda t: 6.112 * math.exp(17.67 * t / (t + 243.5)); e = es(wet) - p * (dry - wet) * 0.00066 * (1 + 0.00115 * wet)
    if e <= 0: return None
    l = math.log(e / 6.112); return e, 100 * e / es(dry), 243.5 * l / (17.67 - l)
def jcomm(dry, wet, p=1013.25):
    """WMO/JCOMM marine formula as used for ship reports (ICOADS documentation)."""
    fp = 1.0016 + 0.00000315 * p - 0.074 / p; ew = 6.112 * math.exp(17.62 * wet / (243.12 + wet)); e = fp * ew - 0.000653 * (1 + 0.000944 * wet) * p * (dry - wet)
    if e <= 0: return None
    l = math.log(e / (6.112 * fp)); return 243.12 * l / (17.62 - l)
def ashrae(dry, wet, p=101325.0):
    psychrolib.SetUnitSystem(psychrolib.SI)
    try:
        w = psychrolib.GetHumRatioFromTWetBulb(dry, wet, p)
        if w <= 0: return None
        return psychrolib.GetTDewPointFromHumRatio(dry, w, p), psychrolib.GetRelHumFromHumRatio(dry, w, p) * 100
    except Exception: return None
def dew(n, rng):
    T = Tally('dew point and humidity (page) vs the NWS formula, ASHRAE (psychrolib) and WMO/JCOMM'); cases = []; meta = []
    for i in range(n):
        dry = round(rng.uniform(0, 45), 1); wet = round(dry - rng.choice([0, rng.uniform(0, 3), rng.uniform(0, 12)]), 1); wet = max(wet, 0.0)
        hold = rng.random() < 0.5; hd = round(rng.uniform(5, 40), 1); hw = max(0.0, round(hd - rng.uniform(0, 8), 1))
        cases.append({'set': {'dry': '%.1f' % dry, 'wet': '%.1f' % wet, 'hdry': ('%.1f' % hd) if hold else '', 'hwet': ('%.1f' % hw) if hold else ''}}); meta.append((dry, wet, hold, hd, hw))
    da, dj, ra = [], [], []; typical = []
    for c, r, (dry, wet, hold, hd, hw) in zip(cases, drive('dew-point-calculator', cases), meta):
        ctx = str(c['set']); x = nws(dry, wet)
        if x is None: T.check('impossible pair refused', r['empty'] is not None, ctx); continue
        e, rh, td = x
        T.close('dew point (C, 1 dp) vs NWS formula', num(r['ids']['r_dew']), td, half(1), ctx); T.close('relative humidity (%, 0 dp)', num(r['ids']['r_rh']), rh, half(0), ctx); T.close('vapour pressure (hPa, 1 dp)', num(r['kv']['Vapour pressure']), e, half(1), ctx)
        a = ashrae(dry, wet); j = jcomm(dry, wet)
        if a and td > 0: da.append(abs(td - a[0])); ra.append(abs(rh - a[1]))
        if j is not None and td > 0: dj.append(abs(td - j))
        if a and j is not None and rh >= 40 and dry >= 5: typical.append(max(abs(td - a[0]), abs(td - j)))
        if hold:
            y = nws(hd, hw)
            if y is None: continue
            T.close('hold dew point', num(r['ids']['r_hdew']), y[2], half(1), ctx); diff = td - y[2]; rule = r['ids'].get('r_rule', '')
            tenths = round((num(r['ids']['r_dew']) - num(r['ids']['r_hdew'])) * 10)   # the rule is read off the two dew points as printed
            want = 'no clear answer' if abs(tenths) < 5 else ('By the dew point rule: ventilate.' if tenths < 0 else 'do not ventilate')
            T.check('dew point rule follows the two printed dew points', want in rule and (('do not' in rule) == (tenths >= 5)), 'printed difference %.1f rule %r %s' % (tenths / 10, rule, ctx))
            if abs(tenths) >= 5: T.check('difference quoted is the difference of the printed dew points', ('by %.1f°C' % (abs(tenths) / 10)) in rule, 'printed difference %.1f rule %r %s' % (tenths / 10, rule, ctx))
            if abs(abs(diff) - 0.5) > 0.11: T.check('dew point rule by the independent formula, away from the half-degree edge', (abs(diff) < 0.5) == ('no clear answer' in rule) and (diff >= 0.5) == ('do not' in rule), 'diff %.3f rule %r %s' % (diff, rule, ctx))
    bad = T.report()
    for name, a in (('dew point vs ASHRAE (psychrolib)', da), ('dew point vs WMO/JCOMM marine formula', dj), ('RH vs ASHRAE (points)', ra), ('dew point, RH 40% or more: worst of the two', typical)):
        a = np.array(a); print('     %-44s n=%d  median %.2f  95%% %.2f  max %.2f' % (name, len(a), np.median(a), np.percentile(a, 95), a.max()))
    return bad

if __name__ == '__main__':
    rng = make_rng(31337); n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000; which = sys.argv[2:] or ['bunker_tables', 'bunker', 'draft', 'lng', 'dew']
    bad = sum(globals()[w]() if w == 'bunker_tables' else globals()[w](n, rng) for w in which); print('TOTAL FAILED', bad)

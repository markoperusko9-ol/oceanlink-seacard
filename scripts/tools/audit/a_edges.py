"""Exact-boundary audit of the seafarer tools.

Random cases almost never land exactly on a limit, but real users do, because they type round figures. Every case here
is built with exact decimal arithmetic to sit on a decision limit, or a hair either side of it, out of decimals that
binary floating point cannot hold exactly (10.3 + 0.7 - 10.1 - 0.7 - 0.2 is 0, not 4e-16). The page must decide as exact
arithmetic does, and its words must agree with the figures printed beside them."""
import math, random, sys, datetime as dt
from fractions import Fraction as F
from decimal import Decimal as D
import mpmath as mp
from common import *
mp.mp.dps = 40

def ds(x, dp):
    """Fraction -> plain decimal string with dp decimals. The value must be exact at that precision."""
    q = F(x) * 10 ** dp; assert q.denominator == 1, (x, dp)
    n = int(q); s = str(abs(n)).rjust(dp + 1, '0')
    return ('-' if n < 0 else '') + (s[:-dp] + '.' + s[-dp:] if dp else s)
def dmin(x, least=0):
    """Fewest decimals (at least `least`) that hold the fraction exactly. It must terminate."""
    for dp in range(least, 19):
        if (F(x) * 10 ** dp).denominator == 1: return ds(x, dp)
    raise ValueError(x)
def rnd(x, dp):
    """Exact value rounded half away from zero to dp decimals, printed the way the pages print (no minus zero)."""
    q = F(x) * 10 ** dp; n = int((abs(q) * 2 + 1) // 2) * (1 if q >= 0 else -1)
    return ds(F(n, 10 ** dp), dp)
def tie(x, dp): return ((F(x) * 10 ** dp) * 2).denominator == 1 and (F(x) * 10 ** dp).denominator != 1
crit = lambda r: any(m.startswith('crit') for m in r['msg'])
warn = lambda r: any(m.startswith('warn') for m in r['msg'])
def b3(x10):
    """Tenths of a degree -> 045.3° as the pages print a bearing."""
    x10 %= 3600; return '%03d.%d°' % (x10 // 10, x10 % 10)

def squat(n, rng):
    T = Tally('squat and UKC on the limits'); cases = []; meta = []
    while len(cases) < n:
        kind = len(cases) % 9; conf = rng.random() < 0.5; K = 2 if conf else 1; cb = F(rng.randrange(30, 101), 100)
        v = F(rng.choice([0, 10, 20])) if rng.random() < 0.5 else F(rng.randrange(0, 221), 10)   # half the cases have a squat of two decimals
        sq = K * cb * v * v / 100; dr = F(rng.randrange(300, 2300), 100); depth = F(rng.randrange(400, 4000), 100); tide = F(rng.randrange(-100, 600), 100); m = None
        if kind in (6, 7):                          # depth to draught ratio on and beside 1.10 and 1.40, and on the halves 1.095 and 1.405
            dr = F(rng.randrange(30, 230), 10) if kind == 6 else F(rng.randrange(3, 23))
            m = F(rng.choice([109, 110, 111, 139, 140, 141]), 100) if kind == 6 else F(rng.choice([1095, 1405, 1094, 1096, 1404, 1406]), 1000); depth = m * dr - tide; other = F(0)
        elif kind == 5: other = depth + tide - dr   # clearance before squat exactly nil
        else: other = depth + tide - dr - sq - [F(0), F(4, 1000), F(6, 1000), F(-4, 1000), F(-1, 100), None, None, None, F(5, 1000)][kind]   # net UKC exactly 0, +4 mm, +6 mm, -4 mm, -1 cm, +5 mm
        if depth <= 0 or other < 0: continue
        cases.append({'seg': {'water': 'conf' if conf else 'open'}, 'set': {'cb': ds(cb, 2), 'v': dmin(v, 1), 'depth': dmin(depth, 2), 'tide': ds(tide, 2), 'draught': dmin(dr, 2), 'other': dmin(other, 2)}})
        meta.append((kind, K, cb, sq, depth + tide, dr, other, m))
    for c, r, (kind, K, cb, sq, water, dr, other, m) in zip(cases, drive('squat-ukc-calculator', cases, 'edge'), meta):
        ctx = str(c); stat = water - dr; net = stat - sq - other; avail = stat - other; shown = num(r['ids']['r_ukc'])
        T.eq('net UKC printed, halves rounded up', r['ids']['r_ukc'], rnd(net, 2) + ' m', ctx)
        T.eq('grounding warning exactly when the net UKC is nil or prints as 0.00', crit(r), net < F(1, 200), ctx)
        T.eq('grounding warning agrees with the printed net UKC', crit(r), shown <= 0, ctx)
        row = r['kv'].get('Net UKC falls to zero at')
        if avail > 0: T.close('speed at which the clearance is used up', num(row), math.sqrt(float(avail) * 100 / (K * float(cb))), half(1), ctx)
        else: T.check('no zero-clearance speed when there is no clearance before squat', row is None, 'shown %r %s' % (row, ctx))
        note = any('1.1 to 1.4' in x for x in r['msg']); pr = num(r['kv']['Depth to draught ratio'])
        T.eq('range note agrees with the printed ratio', note, water / dr > 1 and (pr < 1.1 - 1e-9 or pr > 1.4 + 1e-9), ctx)
        if m is not None:
            T.eq('ratio printed, halves rounded up', r['kv']['Depth to draught ratio'], rnd(m, 2), ctx); T.eq('range note only when the ratio prints outside 1.10 to 1.40', note, m < F(1095, 1000) or m >= F(1405, 1000), ctx)
    return T.report()

def listgm(n, rng):
    T = Tally('list and GM on the limits'); cases = []; meta = []
    while len(cases) < n:
        g = [F(0), F(4, 1000), F(6, 1000), F(-4, 1000), F(1, 100), F(-1, 100), F(5, 1000), F(-5, 1000)][len(cases) % 8]      # fluid GM in exact arithmetic
        disp = F(rng.randrange(1, 400) * 500); km = F(rng.randrange(300, 2500), 100); fsc = F(rng.randrange(0, 900), 1000); kg = km - fsc - g
        if kg <= 0: continue
        w = F(rng.randrange(10, 2000)); d = F(rng.randrange(5, 400), 10); side = rng.choice(['stbd', 'port'])
        cases.append({'seg': {'side': side}, 'set': {'disp': dmin(disp), 'km': ds(km, 2), 'kg': ds(kg, 3), 'fsm': dmin(fsc * disp), 'w': dmin(w), 'd': ds(d, 1)}}); meta.append((g, disp, fsc, km - kg, w, d, side))
    for c, r, (g, disp, fsc, solid, w, d, side) in zip(cases, drive('list-and-gm-calculator', cases, 'edge'), meta):
        ctx = str(c); want = g < F(1, 200)
        T.eq('fluid GM printed', r['ids']['r_gm'], rnd(g, 2) + ' m', ctx); T.eq('solid GM printed', r['ids']['r_solid'], rnd(solid, 3) + ' m', ctx); T.eq('free surface correction printed', r['ids']['r_fsc'], rnd(fsc, 3) + ' m', ctx)
        T.eq('unstable warning exactly when GM is nil, negative or prints as 0.00', crit(r), want, ctx)
        if want: T.check('no list beside a GM of 0.00', 'r_list' not in r['ids'] and r['dia'] in (0, None), 'shown %r %s' % (r['ids'].get('r_list'), ctx))
        else:
            lst = math.degrees(math.atan(float(w * d / disp / g))); shown = r['ids']['r_list']
            T.close('list (deg, 1 dp)', num(shown), lst, half(1), ctx); T.check('list to the side the weight moved', shown.endswith('to ' + ('starboard' if side == 'stbd' else 'port')), shown + ctx)
    return T.report()

def fuel(n, rng):
    T = Tally('fuel on the limits'); cases = []; meta = []
    while len(cases) < n:
        delta = [F(0), F(1, 10), F(-1, 10), F(-4, 100), F(-6, 100), F(4, 100), F(-5, 100), F(5, 100)][len(cases) % 8]      # ROB on arrival in exact arithmetic
        hours = rng.choice([24, 24, 12, 6]); day = F(rng.randrange(50, 2000), 10); k = rng.randrange(1, 30); sp = F(rng.randrange(30, 250), 10); rob = day * k + delta
        if rob < 0: continue
        cases.append({'set': {'cons': dmin(day * hours / 24, 1), 'hours': str(hours), 'rob': dmin(rob, 1), 'speed': ds(sp, 1), 'dist': dmin(sp * 24 * k), 'newspeed': ''}}); meta.append((delta, day * k))
    for c, r, (delta, voy) in zip(cases, drive('fuel-consumption-calculator', cases, 'edge'), meta):
        ctx = str(c); msgs = ' '.join(r['msg'])
        T.eq('ROB on arrival printed', r['ids']['r_arr'], rnd(delta, 1) + ' t', ctx); T.eq('fuel for the voyage printed', r['ids']['r_voy'], rnd(voy, 1) + ' t', ctx)
        T.eq('shortfall warning exactly when the ROB on arrival prints below zero', crit(r), delta <= F(-1, 20), ctx)
        if crit(r): T.check('shortfall quoted', ('Short by %s t' % rnd(-delta, 1)) in msgs, msgs + ctx)
        T.check('never short by 0.0 t', 'Short by 0.0' not in msgs, msgs + ctx)
    return T.report()

def slip(n, rng):
    T = Tally('propeller slip on the limits'); cases = []; meta = []
    while len(cases) < n:
        s = [F(0), F(4, 1000), F(-4, 1000), F(-6, 1000), F(-1, 100), F(1, 100), F(-5, 1000), F(5, 1000)][len(cases) % 8]     # slip in percent, exact
        j = rng.randrange(3, 11); pitch = F(926 * j, 1000); rpm = F(rng.randrange(200, 2000), 10)       # pitch = j x 0.926 m, so the engine distance is a plain decimal
        if rng.random() < 0.5:
            ph = rng.randrange(0, 30); pm = rng.randrange(0, 60)
            if ph == 0 and pm == 0: pm = 30
            ed = pitch * rpm * (60 * ph + pm) / 1852
            cases.append({'seg': {'mode': 'per'}, 'set': {'pitch': ds(pitch, 3), 'rpm': ds(rpm, 1), 'ph': str(ph), 'pm': '%02d' % pm, 'od': dmin(ed * (1 - s / 100))}})
        else:
            cases.append({'seg': {'mode': 'now'}, 'set': {'pitch2': ds(pitch, 3), 'rpm2': ds(rpm, 1), 'os': dmin(pitch * rpm * 60 / 1852 * (1 - s / 100))}})
        meta.append(s)
    for c, r, s in zip(cases, drive('propeller-slip-calculator', cases, 'edge'), meta):
        ctx = str(c)
        T.eq('slip printed', r['ids']['r_main'], rnd(s, 2) + ' %', ctx); T.eq('negative-slip note exactly when the slip prints below zero', len(r['msg']) > 0, s <= F(-1, 200), ctx)
    return T.report()

def cts(n, rng):
    T = Tally('course to steer on the limits'); cases = []; meta = []
    while len(cases) < n:
        t10 = rng.randrange(0, 3600) if rng.random() < 0.5 else rng.randrange(0, 360) * 10; stw = F(rng.randrange(10, 250), 10); a = [30, 330, 150, 210, 90, 270][len(cases) % 6]
        tweak = rng.choice([F(0), F(0), F(-1, 10), F(1, 10)]); rate = stw * (1 if a in (90, 270) else 2) + tweak      # the cross-track part of the stream equals the ship's speed when tweak is 0
        cases.append({'seg': {'mode': 'cts'}, 'set': {'ctrack': '%05.1f' % (t10 / 10), 'cstw': ds(stw, 1), 'cset': '%05.1f' % ((t10 + a * 10) % 3600 / 10), 'crate': ds(rate, 1)}}); meta.append((t10, stw, a, tweak, rate))
    for c, r, (t10, stw, a, tweak, rate) in zip(cases, drive('set-and-drift-course-to-steer-calculator', cases, 'edge'), meta):
        ctx = str(c['set']); k = mp.mpf(rate.numerator) / rate.denominator * mp.sin(mp.radians(a)) / (mp.mpf(stw.numerator) / stw.denominator)
        if tweak == 0: k = mp.nint(k)                                         # exactly plus or minus one
        none = any('too strong' in m for m in r['msg'])
        if abs(k) > 1: T.check('track cannot be held', none, ctx); continue
        corr = mp.degrees(mp.asin(k)); smg = mp.mpf(stw.numerator) / stw.denominator * mp.cos(mp.radians(corr)) + mp.mpf(rate.numerator) / rate.denominator * mp.cos(mp.radians(a))
        if smg <= mp.mpf('1e-12'): T.check('no headway: track cannot be held', none, 'shown %r %s' % (r['ids'], ctx)); continue
        if none: T.check('track can be held', False, 'smg %s corr %s %s' % (mp.nstr(smg, 6), mp.nstr(corr, 8), ctx)); continue
        T.ang('course to steer', num(r['ids']['r_main']), float(t10 / 10 - corr), half(1), ctx); T.close('speed made good', num(r['ids']['r_smg']), float(smg), half(1), ctx)
        if tweak == 0:
            T.eq('course to steer printed, 90 degrees off the track', r['ids']['r_main'], b3(t10 - (900 if a == 30 else -900)) + 'T', ctx)
            T.check('allowance of 90 degrees to the side away from the stream', r['sub'][0].startswith('Allow 90.0° to ' + ('port' if a == 30 else 'starboard')), r['sub'][0] + ctx)
    return T.report()

def cpa(n, rng):
    T = Tally('CPA on the limits'); cases = []; meta = []
    for i in range(n):
        oc = rng.randrange(0, 360); os_ = F(rng.randrange(0, 250), 10); b10 = rng.randrange(0, 3600); r1 = F(rng.randrange(300, 1200), 100); r2 = F(rng.randrange(50, int(r1 * 100) - 20), 100)
        d10 = 0 if i % 3 == 0 else rng.choice([1, -1, 2, -2, 3, -3, 5, -5]); mins = rng.choice([3, 6, 12, 15])
        cases.append({'set': {'oc': '%03d' % oc, 'os': ds(os_, 1), 't1': '12:00', 'b1': '%05.1f' % (b10 / 10), 'r1': ds(r1, 2), 't2': '12:%02d' % mins, 'b2': '%05.1f' % ((b10 + d10) % 3600 / 10), 'r2': ds(r2, 2)}})
        meta.append((b10, d10, float(r1), float(r2), mins))
    for c, r, (b10, d10, r1, r2, mins) in zip(cases, drive('cpa-tcpa-calculator', cases, 'edge'), meta):
        ctx = str(c['set']); p1 = r1 * complex(math.sin(math.radians(b10 / 10)), math.cos(math.radians(b10 / 10))); b2 = (b10 + d10) / 10; p2 = r2 * complex(math.sin(math.radians(b2)), math.cos(math.radians(b2)))
        rel = p2 - p1; tau = -(p2.real * rel.real + p2.imag * rel.imag) / abs(rel) ** 2; dist = abs(p2 + rel * tau); shown = num(r['ids']['r_cpa'])
        T.close('CPA (nm, 2 dp)', shown, dist, half(2) + 1e-6, ctx); T.close('TCPA (min)', num(r['ids']['r_tcpa']), tau * mins, half(0) + 0.01, ctx)
        at = (12 * 60 + mins + int(num(r['ids']['r_tcpa']))) % 1440; T.eq('time of CPA is the second plot plus the TCPA shown', r['ids'].get('r_at'), '%02d:%02d' % (at // 60, at % 60), ctx)
        T.eq('collision warning exactly when the printed CPA is 0.05 nm or less', crit(r), shown < 0.05 + 1e-9, ctx)
        if crit(r): T.check('warning wording', 'CPA is 0.05 nm or less' in ' '.join(r['msg']), str(r['msg']) + ctx)
        if d10 == 0:
            T.eq('steady bearing: CPA printed as nil', r['ids']['r_cpa'], '0.00 nm', ctx); T.check('steady bearing: collision warning', crit(r), ctx); T.check('steady bearing: no bearing at CPA', 'Bearing at CPA' not in r['kv'], ctx)
    return T.report()

def dew(n, rng):
    from a_cargo import nws
    T = Tally('dew point rule on the limits'); cases = []; hits = {4: 0, 5: 0, 6: 0}
    while len(cases) < n:
        dry = rng.randrange(100, 350); wet = dry - rng.randrange(5, 60); x = nws(dry / 10, wet / 10)
        if x is None or wet < 0: continue
        target = x[2] + rng.choice([-0.6, -0.5, -0.4, 0.4, 0.5, 0.6]) * rng.choice([1, 1, 1, 0]); hd = rng.randrange(100, 350); best = None
        for hw in range(max(hd - 120, 0), hd + 1):                             # the hold wet bulb whose dew point comes nearest the target
            y = nws(hd / 10, hw / 10)
            if y is not None and (best is None or abs(y[2] - target) < best[0]): best = (abs(y[2] - target), hw)
        if best is None or best[0] > 0.15: continue
        cases.append({'set': {'dry': '%.1f' % (dry / 10), 'wet': '%.1f' % (wet / 10), 'hdry': '%.1f' % (hd / 10), 'hwet': '%.1f' % (best[1] / 10)}})
    for c, r in zip(cases, drive('dew-point-calculator', cases, 'edge')):
        ctx = str(c['set']); rule = r['ids'].get('r_rule', ''); tenths = round((num(r['ids']['r_dew']) - num(r['ids']['r_hdew'])) * 10)
        if abs(tenths) in hits: hits[abs(tenths)] += 1
        want = 'no clear answer' if abs(tenths) < 5 else ('By the dew point rule: ventilate.' if tenths < 0 else 'do not ventilate')
        T.check('rule follows the two printed dew points', want in rule and (('do not' in rule) == (tenths >= 5)), 'printed difference %.1f rule %r %s' % (tenths / 10, rule, ctx))
        if abs(tenths) >= 5: T.check('difference quoted is the difference of the printed dew points', ('by %.1f°C' % (abs(tenths) / 10)) in rule, 'printed difference %.1f rule %r %s' % (tenths / 10, rule, ctx))
        T.eq('"do not ventilate" is the amber one', warn(r) and 'do not' in rule, 'do not' in rule, ctx)
    bad = T.report(); print('     printed differences of 0.4, 0.5 and 0.6 in the set: %d, %d, %d' % (hits[4], hits[5], hits[6])); return bad

def rolling(n, rng):
    T = Tally('rolling: resonance flags on the limits'); cases = []; meta = []
    MS = [F(x, 10000) for x in (4400, 4449, 4451, 4500, 5000, 5500, 5549, 5551, 5600, 8900, 8949, 8951, 9000, 10000, 11000, 11049, 11051, 11100, 7000, 3000, 20000)]
    while len(cases) < n:
        m = MS[len(cases) % len(MS)]; tw = F(rng.randrange(40, 200), 10); v = F(rng.randrange(0, 250), 10); te = 3 * tw * tw / (3 * tw + v); per = te / m        # head sea, so the encounter period is a plain fraction
        if not 2 < per < 60: continue
        B = F(rng.randrange(150, 500), 10); d = F(rng.randrange(60, 160), 10); L = F(rng.randrange(100, 300))
        if 0.373 + 0.023 * float(B / d) - 0.043 * float(L) / 100 <= 0.21: continue
        cases.append({'seg': {'mode': 'gm'}, 'set': {'beam': ds(B, 1), 'dr': ds(d, 1), 'lwl': dmin(L), 'per': '%.12f' % float(per), 'tw': ds(tw, 1), 'spd': ds(v, 1), 'wang': '0'}}); meta.append((m, te))
    for c, r, (m, te) in zip(cases, drive('rolling-period-gm-calculator', cases, 'edge'), meta):
        ctx = str(c['set']); flag = r['ids'].get('r_flag', ''); pr = rnd(m, 2); p = float(pr)
        T.eq('ratio printed', r['ids']['r_ratio'], pr, ctx); T.close('encounter period', num(r['ids']['r_te']), float(te), half(1), ctx)
        T.eq('synchronous flag exactly when the ratio prints as 0.90 to 1.10', 'synchronous' in flag, 0.895 < p < 1.105, ctx)
        T.eq('parametric flag exactly when the ratio prints as 0.45 to 0.55', 'half the rolling period' in flag, 0.445 < p < 0.555, ctx)
        T.check('a timed roll gets no estimate note', 'r_est' not in r['ids'], ctx)
    return T.report()

def dwa(n, rng):
    T = Tally('dock water allowance on the limits'); cases = []; meta = []
    for i in range(n):
        fwa = rng.randrange(20, 420); rho = F(rng.choice([10250, 10250, 10250, 10255, 10245, 10260, 10240, 10000, 10400, 9900]), 10)       # kg/m3
        forms = [ds(rho / 1000, 4), ds(rho / 1000, 5), ds(rho, 1)] + ([ds(rho / 1000, 3), ds(rho, 0)] if rho.denominator == 1 else [])
        dr = F(rng.randrange(300, 2300), 100)
        cases.append({'seg': {'mode': 'known'}, 'set': {'fwa': str(fwa), 'dens': rng.choice(forms), 'draught': ds(dr, 2)}}); meta.append((F(fwa), rho, dr))
    for c, r, (fwa, rho, dr) in zip(cases, drive('fwa-dwa-calculator', cases, 'edge'), meta):
        ctx = str(c['set']); x = fwa * (1025 - rho) / 25; shown = r['ids']['r_dwa']
        if x >= 0:
            T.eq('DWA printed, halves rounded up', shown, rnd(x, 0) + ' mm', ctx)
            T.check('no warning in water of 1.025 or lighter', not warn(r) and 'denser' not in ' '.join(r['sub']), str(r['msg']) + ctx)
        else:
            T.eq('no allowance in water denser than 1.025', shown, 'None', ctx)
            T.check('load line kept clear by the right amount', ('Keep the load line %s mm clear' % rnd(-x, 0)) in ' '.join(r['msg']), str(r['msg']) + ctx)
        T.close('draught at the load line in this water', num(r['ids']['r_dr']), float(dr + x / 1000), half(3), ctx)
        if rho == 1025: T.eq('standard sea water: allowance exactly nil', shown, '0 mm', ctx)
    return T.report()

def bunker(n, rng):
    from a_cargo import vcf_1980
    T = Tally('bunker Table 54B on the limits'); cases = []; meta = []
    for b in (653, 770, 770.5, 778.5, 787.5, 788, 824, 838.5, 839, 1075):
        for off in (-0.5, -0.1, 0, 0.1, 0.5):
            rho = D(str(b)) + D(str(off))
            if not 653 <= rho <= 1075: continue
            tmax = 150 if rho > 824 else 125 if rho > D('778.5') else 90
            for typed in {'%.4f' % (rho / 1000), '%.1f' % rho} | ({'%d' % rho, '%.3f' % (rho / 1000)} if rho == rho.to_integral_value() else set()):
                for t in [D('-18.25'), D('-18'), D('-17.75'), D(tmax) - D('0.25'), D(tmax), D(tmax) + D('0.25'), D('15'), D(str(round(rng.uniform(-10, 80), 2)))]:
                    cases.append({'set': {'vol': '1000', 'temp': str(t), 'dens': typed}}); meta.append((rho, t, tmax))
    for c, r, (rho, t, tmax) in zip(cases, drive('bunker-quantity-calculator', cases, 'edge'), meta):
        ctx = str(c['set']); v, grp = vcf_1980(rho, t)
        T.close('VCF on a group boundary', num(r['ids']['r_vcf']), float(v), 1e-9, ctx); T.eq('product group on a boundary', r['kv']['Product group in Table 54B'], grp, ctx)
        T.eq('out-of-table warning exactly outside -18 to the table maximum', len(r['msg']) > 0, not (-18 <= t <= tmax), ctx)
        if r['msg']: T.check('the maximum quoted is the one for this density', ('to %d°C' % tmax) in r['msg'][0], r['msg'][0] + ctx)
    return T.report()

def truewind(n, rng):
    from a_vectors import beaufort, BF
    T = Tally('true wind: calm and Beaufort on the limits'); cases = []; meta = []
    for i in range(n):
        h10 = rng.randrange(0, 3600); kind = i % 4
        if kind == 0:   # ship stopped, wind exactly on a half knot: the force must not depend on the heading
            k = rng.randrange(0, 70); rel = rng.randrange(0, 181)
            cases.append({'seg': {'side': rng.choice(['stbd', 'port']), 'unit': 'kn'}, 'set': {'hdg': '%05.1f' % (h10 / 10), 'spd': '0', 'cog': '', 'rel': str(rel), 'ws': '%d.5' % k}}); meta.append(('bf', k))
        else:           # wind from right ahead at the ship's own speed, give or take
            sp = F(rng.randrange(10, 250), 10); d = [None, F(0), F(4, 100), F(6, 100)][kind] * rng.choice([1, -1])
            cases.append({'seg': {'side': 'stbd', 'unit': 'kn'}, 'set': {'hdg': '%05.1f' % (h10 / 10), 'spd': ds(sp, 1), 'cog': rng.choice(['', '%05.1f' % (h10 / 10)]), 'rel': '0', 'ws': dmin(sp + d, 1)}}); meta.append(('calm', d, h10))
    for c, r, m in zip(cases, drive('true-wind-calculator', cases, 'edge'), meta):
        ctx = str(c)
        if m[0] == 'bf':
            f = beaufort(m[1] + 1); T.eq('Beaufort force of a half knot rounds up on every heading', r['ids']['r_bf'], 'Force %d, %s' % (f, BF[f]), ctx); T.eq('speed printed', r['ids']['r_spd'], '%d.5 kn' % m[1], ctx)
        elif abs(m[1]) < F(5, 100): T.eq('calm when the wind felt is the ship\'s own speed', r['ids']['r_main'], 'Calm', ctx)
        else:
            want = (m[2] + (0 if m[1] > 0 else 1800)) % 3600 / 10   # from right ahead or right astern
            T.eq('speed printed', r['ids']['r_spd'], '0.1 kn', ctx); T.check('direction, to the nearest degree', r['ids']['r_main'] in {'%03d°T' % (math.floor(want + 0.5) % 360), '%03d°T' % (math.ceil(want - 0.5) % 360)}, 'shown %r want %.1f %s' % (r['ids']['r_main'], want, ctx))
            T.eq('off the bow', r['kv']['True wind off the bow'], 'Dead ahead' if m[1] > 0 else 'Dead astern', ctx)
    return T.report()

def compass(n, rng):
    T = Tally('compass error: nil and naming on the limits'); base = []
    for i in range(n):
        day = dt.date(2026, 1, 1) + dt.timedelta(days=rng.randrange(0, 1400)); lat = rng.randrange(0, 60); lon = rng.randrange(0, 180)
        base.append({'seg': {'cmode': 'gyro'}, 'sel': {'lath': rng.choice('NS'), 'lonh': rng.choice('EW')}, 'set': {'date': day.isoformat(), 'hh': '%02d' % rng.randrange(0, 24), 'mm': '%02d' % rng.randrange(0, 60), 'ss': '00', 'latd': '%02d' % lat, 'latm': '%04.1f' % (rng.randrange(0, 600) / 10), 'lond': '%03d' % lon, 'lonm': '%04.1f' % (rng.randrange(0, 600) / 10), 'cb': '', 'var': ''}})
    az = [int(round(num(r['ids']['r_az']) * 10)) for r in drive('sun-compass-error-calculator', base, 'edge0')]; cases = []; meta = []
    for i, (b, a10) in enumerate(zip(base, az)):
        d10 = [0, 1, -1, 2, -2, 15, -15, 0][i % 8]; cb10 = (a10 - d10) % 3600; c = {'seg': dict(b['seg']), 'sel': dict(b['sel']), 'set': dict(b['set'])}; c['set']['cb'] = '%05.1f' % (cb10 / 10); var = None
        if i % 8 == 7 or (i % 2 == 0 and d10):      # magnetic compass with a variation equal to the whole error: deviation nil
            c['seg']['cmode'] = 'mag'; var = abs(d10); c['set']['var'] = '%.1f' % (var / 10); c['sel']['varh'] = 'E' if d10 >= 0 else 'W'
        cases.append(c); meta.append((d10, var))
    for c, r, (d10, var) in zip(cases, drive('sun-compass-error-calculator', cases, 'edge1'), meta):
        ctx = str(c); name = 'Nil' if d10 == 0 else '%.1f° %s' % (abs(d10) / 10, 'E' if d10 > 0 else 'W')
        if var is None: T.eq('gyro error named', r['ids']['r_err'], name + ('' if d10 == 0 else ' gyro ' + ('low' if d10 > 0 else 'high')), ctx)
        else: T.eq('compass error named', r['ids']['r_err'], name, ctx); T.eq('deviation nil when the variation is the whole error', r['ids']['r_dev'], 'Nil for the present heading', ctx)
    return T.report()

def eta(n, rng):
    T = Tally('ETA: required speed on the limits'); cases = []; meta = []
    zones = drive('eta-speed-distance-time-calculator', [{'call': "[].map.call(document.getElementById('dzone').options, function (o) { return o.value; })"}], 'zones')[0]['call']
    for i in range(n):
        dz, az = rng.choice(zones), rng.choice(zones); dep = dt.datetime(2026, 1, 1) + dt.timedelta(minutes=rng.randrange(0, 1500000)); extra = [0, 1, -1, 60, -60, 1440][i % 6]; dist = rng.randrange(10, 5000)
        arr = dep + dt.timedelta(minutes=round((float(az) - float(dz)) * 60) + extra)
        cases.append({'seg': {'mode': 'spd'}, 'sel': {'dzone': dz, 'azone': az}, 'set': {'dist': str(dist), 'ddate': dep.date().isoformat(), 'dtime': dep.strftime('%H:%M'), 'adate': arr.date().isoformat(), 'atime': arr.strftime('%H:%M')}}); meta.append((extra, dist))
    for c, r, (extra, dist) in zip(cases, drive('eta-speed-distance-time-calculator', cases, 'edge'), meta):
        ctx = str(c)
        if extra <= 0: T.check('arrival not after departure is refused, across time zones', crit(r) and 'r_main' not in r['ids'], 'shown %r %s' % (r['ids'], ctx))
        else: T.eq('speed required', r['ids']['r_main'], rnd(F(dist * 60, extra), 1) + ' kn', ctx)
    return T.report()

def gc(n, rng):
    T = Tally('great circle: same point, meridian and equator'); cases = []; meta = []
    for i in range(n):
        kind = i % 3; la = rng.randrange(0, 80); lam = rng.randrange(0, 600); lo = rng.randrange(0, 180); lom = rng.randrange(0, 600); h, g = rng.choice('NS'), rng.choice('EW')
        A = {'alatd': '%02d' % la, 'alatm': '%04.1f' % (lam / 10), 'alond': '%03d' % lo, 'alonm': '%04.1f' % (lom / 10)}; sel = {'alath': h, 'alonh': g, 'blath': h, 'blonh': g}
        if kind == 0: B = {'blatd': A['alatd'], 'blatm': A['alatm'], 'blond': A['alond'], 'blonm': A['alonm']}
        elif kind == 1:
            lb = rng.randrange(0, 80); B = {'blatd': '%02d' % lb, 'blatm': '%04.1f' % (rng.randrange(0, 600) / 10), 'blond': A['alond'], 'blonm': A['alonm']}; sel['blath'] = rng.choice('NS')
            if B['blatd'] == A['alatd'] and sel['blath'] == h: B['blatd'] = '%02d' % ((lb + 7) % 80)
        else:
            A['alatd'], A['alatm'] = '00', '00.0'; lb = rng.randrange(0, 180); B = {'blatd': '00', 'blatm': '00.0', 'blond': '%03d' % lb, 'blonm': '%04.1f' % (rng.randrange(0, 600) / 10)}; sel['blonh'] = rng.choice('EW')
            if B['blond'] == A['alond'] and sel['blonh'] == g: B['blond'] = '%03d' % ((lb + 11) % 180)
        s = dict(A, **B); lon = lambda d, m, hh: (int(s[d]) + float(s[m]) / 60) * (1 if sel[hh] == 'E' else -1)
        cases.append({'sel': sel, 'set': s}); meta.append((kind, abs((lon('blond', 'blonm', 'blonh') - lon('alond', 'alonm', 'alonh') + 180) % 360 - 180), lon('alond', 'alonm', 'alonh'), lon('blond', 'blonm', 'blonh')))
    from pyproj import Geod
    WGS = Geod(ellps='WGS84')
    for c, r, (kind, dlon, lon1, lon2) in zip(cases, drive('great-circle-rhumb-line-calculator', cases, 'edge'), meta):
        ctx = str(c)
        if kind == 0: T.eq('same position refused', r['empty'], 'The two positions are the same.', ctx)
        elif kind == 1:
            T.eq('along a meridian: vertex at the pole', r['kv'].get('Vertex'), 'At the pole (sailing along a meridian)', ctx); T.eq('along a meridian: nothing saved', r['kv']['Great circle saves'], 'Nothing on this leg', ctx)
            T.check('along a meridian: course north or south', r['sub'][0].startswith('Initial course 000.0°T') or r['sub'][0].startswith('Initial course 180.0°T'), r['sub'][0] + ctx)
            T.close('along a meridian: rhumb line equals great circle', num(r['ids']['r_rh']), num(r['ids']['r_gc']), 0.11, ctx)
        elif dlon > 179.3:
            # On the ellipsoid the shortest way between two nearly opposite points of the equator leaves the equator and passes near a pole.
            # It does so once the difference of longitude is more than (1 - f) x 180 = 179.3965 degrees. PROJ is the reference here.
            T.close('nearly opposite points of the equator: WGS84 distance as PROJ', num(r['ids']['r_gc']), WGS.inv(lon1, 0, lon2, 0)[2] / 1852, half(1) + 0.01, ctx)
            if dlon > 179.5: T.check('nearly opposite points of the equator: the great circle is the shorter way', 'nm' in r['kv']['Great circle saves'], r['kv']['Great circle saves'] + ctx)
        else:
            T.check('along the equator: no vertex', 'Vertex' not in r['kv'], str(r['kv'].get('Vertex')) + ctx); T.eq('along the equator: nothing saved', r['kv']['Great circle saves'], 'Nothing on this leg', ctx)
            T.close('along the equator: WGS84 distance as PROJ', num(r['ids']['r_gc']), WGS.inv(lon1, 0, lon2, 0)[2] / 1852, half(1) + 0.01, ctx)
            T.check('along the equator: course east or west', r['sub'][0].startswith('Initial course 090.0°T') or r['sub'][0].startswith('Initial course 270.0°T'), r['sub'][0] + ctx)
    return T.report()

def setdrift(n, rng):
    T = Tally('set and drift: nil and stopped'); cases = []; meta = []
    for i in range(n):
        c10 = rng.randrange(0, 3600)
        if i % 2 == 0:   # the fix is exactly on the DR position, with a time that is not a round decimal of an hour
            k = rng.randrange(1, 80); m = rng.choice([10, 20, 40, 50, 15, 45, 30, 0, 5, 25]); th = rng.randrange(0 if m else 1, 6); s = F(3 * k, 10); dist = s * (F(th) + F(m, 60))
            cases.append({'seg': {'mode': 'sd'}, 'set': {'scourse': '%05.1f' % (c10 / 10), 'sstw': ds(s, 1), 'sth': str(th), 'stm': '%02d' % m, 'scmg': '%05.1f' % (c10 / 10), 'sdist': dmin(dist, 1)}}); meta.append('nil')
        else:            # the stream is equal and opposite to the ship
            s = F(rng.randrange(1, 250), 10)
            cases.append({'seg': {'mode': 'cmg'}, 'set': {'mcourse': '%05.1f' % (c10 / 10), 'mstw': ds(s, 1), 'mset': '%05.1f' % ((c10 + 1800) % 3600 / 10), 'mrate': ds(s, 1)}}); meta.append('stopped')
    for c, r, m in zip(cases, drive('set-and-drift-course-to-steer-calculator', cases, 'edge2'), meta):
        ctx = str(c['set'])
        if m == 'nil': T.check('fix on the DR position: nil set and drift', r['big'] and r['big'][0][1] == 'Nil', 'shown %r %s' % (r['big'], ctx))
        else: T.check('equal and opposite stream: stopped', r['big'] and r['big'][0][1] == 'Stopped', 'shown %r %s' % (r['big'], ctx))
    return T.report()

def survey(n, rng):
    T = Tally('draught survey: even keel and no deflection'); cases = []; meta = []
    for i in range(n):
        x = F(rng.randrange(3000, 150000), 10000) if i % 2 else F(rng.randrange(300, 1500), 100); lbp = F(rng.randrange(800, 3000), 10); rho = F(rng.randrange(10000, 10250), 10000); disp = F(rng.randrange(500000, 9000000), 100)
        s = {k: dmin(x, 2) for k in ('fp', 'fs', 'mp', 'ms', 'ap', 'as')}
        if i % 4 >= 2:   # trimmed, but midships exactly on the mean of the ends: no hog or sag only if the marks are on the perpendiculars
            e = F(rng.randrange(1, 200), 100); x += 3; s.update({k: dmin(x, 2) for k in ('mp', 'ms')}); s.update({'fp': dmin(x - e, 2), 'fs': dmin(x - e, 2), 'ap': dmin(x + e, 2), 'as': dmin(x + e, 2)})
        s.update({'lbp': ds(lbp, 1), 'xf': '0' if i % 4 >= 2 else ds(F(rng.randrange(0, 80), 10), 1), 'xa': '0' if i % 4 >= 2 else ds(F(rng.randrange(0, 120), 10), 1), 'xm': '0' if i % 4 >= 2 else ds(F(rng.randrange(0, 30), 10), 1),
                  'disp': dmin(disp, 2), 'tpc': '42.338', 'lcf': '4.331', 'rhot': '1.025', 'mtcp': '445.89', 'mtcm': '435.26', 'rho': ds(rho, 4), 'ded': '', 'ls': ''})
        cases.append({'set': s}); meta.append((i % 4 >= 2, x, disp, rho))
    for c, r, (trimmed, x, disp, rho) in zip(cases, drive('draft-survey-calculator', cases, 'edge'), meta):
        ctx = str(c['set'])
        T.eq('no hog or sag', r['ids']['r_defl'], 'None', ctx); T.eq('mean of means is the midship draught', r['ids']['r_mmm'], rnd(x, 4) + ' m', ctx)
        if not trimmed:
            T.eq('even keel', r['ids']['r_trim'], 'Even keel', ctx); T.eq('no first trim correction', r['ids']['r_ftc'], '+0.00 t', ctx); T.eq('no second trim correction', r['ids']['r_stc'], '+0.00 t', ctx)
            T.eq('displacement only corrected for density', r['ids']['r_true'].replace(',', ''), rnd(disp * rho / F(1025, 1000), 2) + ' t', ctx)
    return T.report()

def survey_halves(n, rng):
    """Round ship particulars make the corrections to the perpendiculars come out as plain decimals, and some land exactly on a half
    in the fifth decimal (10.09875). A surveyor rounds that up to 10.0988; so must the tool."""
    T = Tally('draught survey: corrected draughts exactly on a half'); cases = []; meta = []; tries = 0
    while len(cases) < n and tries < 400000:
        tries += 1; lbp = F(rng.choice([80, 96, 100, 120, 125, 128, 150, 160, 180, 192, 200, 220, 240, 250, 256, 320])); xf = F(rng.randrange(0, 9)) * rng.choice([1, -1]); xa = F(rng.randrange(0, 15)) * rng.choice([1, -1]); xm = F(rng.randrange(0, 5)) * rng.choice([1, -1])
        Fm, Mm, Am = (F(rng.randrange(300, 1500), 100) for _ in range(3)); lbm = lbp - xf - xa
        if not lbm > lbp / 2 or abs(Fm - Am) > 4: continue
        at = Am - Fm; raw = (Fm - at * xf / lbm, Mm - at * xm / lbm, Am + at * xa / lbm)      # a surveyor's sheet: xf abaft the FP +, xm abaft midships +, xa forward of the AP +
        if not any(tie(x, 4) for x in raw) or min(raw) <= 0: continue
        s = {'fp': ds(Fm, 2), 'fs': ds(Fm, 2), 'mp': ds(Mm, 2), 'ms': ds(Mm, 2), 'ap': ds(Am, 2), 'as': ds(Am, 2), 'lbp': dmin(lbp, 2), 'xf': dmin(abs(xf), 2), 'xa': dmin(abs(xa), 2), 'xm': dmin(abs(xm), 2),
             'disp': '', 'tpc': '', 'lcf': '', 'rhot': '1.025', 'mtcp': '', 'mtcm': '', 'rho': '1.025', 'ded': '', 'ls': ''}
        cases.append({'sel': {'xfd': 'aft' if xf >= 0 else 'fwd', 'xad': 'fwd' if xa >= 0 else 'aft', 'xmd': 'aft' if xm >= 0 else 'fwd', 'lcfd': 'aft'}, 'set': s}); meta.append(raw)
    for c, r, raw in zip(cases, drive('draft-survey-calculator', cases, 'edge3'), meta):
        ctx = str(c); fc, mc, ac = (F(rnd(x, 4)) for x in raw)
        T.eq('forward draught at the FP, half rounded up', r['ids']['r_f'], rnd(raw[0], 4) + ' m', ctx); T.eq('midship draught, half rounded up', r['ids']['r_m'], rnd(raw[1], 4) + ' m', ctx); T.eq('aft draught at the AP, half rounded up', r['ids']['r_a'], rnd(raw[2], 4) + ' m', ctx)
        T.eq('mean of means from the rounded draughts', r['ids']['r_mmm'], rnd((fc + 6 * mc + ac) / 8, 4) + ' m', ctx)
        tr = ac - fc; T.eq('true trim from the rounded draughts', r['ids']['r_trim'], 'Even keel' if tr == 0 else '%s m by the %s' % (rnd(abs(tr), 4), 'stern' if tr > 0 else 'head'), ctx)
    bad = T.report(); print('     sheets with a half in the fifth decimal: %d (from %d round-figure ships tried)' % (len(cases), tries)); return bad

def eta_halves(n, rng):
    """A steaming time that ends exactly on a half minute (0.7 nm at 12 kn is 3.5 minutes). The steaming time and the two ETA clocks
    must round it the same way, upwards, so that the ETA is the departure plus the steaming time shown."""
    T = Tally('ETA: steaming time exactly on a half minute'); cases = []; meta = []
    zones = drive('eta-speed-distance-time-calculator', [{'call': "[].map.call(document.getElementById('dzone').options, function (o) { return o.value; })"}], 'zones')[0]['call']
    def stamp(t): return '%s %d %s %d, %02d:%02d' % (t.strftime('%a'), t.day, t.strftime('%b'), t.year, t.hour, t.minute)
    def dur(mins): d, h, m = mins // 1440, mins % 1440 // 60, mins % 60; return ('%d d ' % d if d else '') + ('%02d' % h if d else '%d' % h) + ' h %02d min' % m
    for i in range(n):
        sp = rng.choice([6, 12, 24, 30, 15]); m = rng.randrange(0, 20000) if i % 3 else rng.randrange(0, 90); dist = F(sp * (2 * m + 1), 120)       # m and a half minutes under way
        dz, az = rng.choice(zones), rng.choice(zones); dep = dt.datetime(2026, 1, 1) + dt.timedelta(minutes=rng.randrange(0, 1500000))
        cases.append({'seg': {'mode': 'eta'}, 'sel': {'dzone': dz, 'azone': az}, 'set': {'dist': dmin(dist), 'speed': str(sp), 'ddate': dep.date().isoformat(), 'dtime': dep.strftime('%H:%M')}}); meta.append((m, dep, float(dz), float(az)))
    for c, r, (m, dep, dz, az) in zip(cases, drive('eta-speed-distance-time-calculator', cases, 'edge4'), meta):
        ctx = str(c); utc = dep - dt.timedelta(minutes=round(dz * 60)) + dt.timedelta(minutes=m + 1)
        T.eq('steaming time, half minute rounded up', r['ids']['r_time'], dur(m + 1), ctx); T.eq('ETA in UTC is the departure plus the steaming time shown', r['ids']['r_utc'], stamp(utc), ctx)
        T.eq('ETA in ship\'s time likewise', r['ids']['r_main'], stamp(utc + dt.timedelta(minutes=round(az * 60))), ctx)
    return T.report()

ALL = ['squat', 'listgm', 'fuel', 'slip', 'cts', 'cpa', 'dew', 'rolling', 'dwa', 'bunker', 'truewind', 'compass', 'eta', 'eta_halves', 'gc', 'setdrift', 'survey', 'survey_halves']
if __name__ == '__main__':
    rng = make_rng(1126); n = int(sys.argv[1]) if len(sys.argv) > 1 else 600; which = sys.argv[2:] or ALL
    bad = sum(globals()[w](n, rng) for w in which); print('TOTAL FAILED', bad); sys.exit(1 if bad else 0)

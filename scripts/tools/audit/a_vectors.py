"""Independent end-to-end audit: true wind, CPA/TCPA, set and drift. Expected values come from plain vector algebra
with complex numbers and from brute-force search, never from the site's code."""
import cmath, math, random, sys
from scipy.optimize import minimize_scalar, brentq
from common import *

def u(brg): t = math.radians(brg); return complex(math.cos(t), math.sin(t))      # real = north, imag = east
def brg(z): return math.degrees(math.atan2(z.imag, z.real)) % 360
BF = ['Calm', 'Light air', 'Light breeze', 'Gentle breeze', 'Moderate breeze', 'Fresh breeze', 'Strong breeze', 'Near gale', 'Gale', 'Strong gale', 'Storm', 'Violent storm', 'Hurricane']
BF_TOP = [0, 3, 6, 10, 16, 21, 27, 33, 40, 47, 55, 63]            # WMO: highest whole knot of forces 0..11
def beaufort(kn_whole):
    for f, top in enumerate(BF_TOP):
        if kn_whole <= top: return f
    return 12

def true_wind(n, rng):
    T = Tally('true wind (page)'); cases = []; exp = []
    for i in range(n):
        hdg = rng.choice([round(rng.uniform(0, 360), 1), float(rng.randrange(0, 361))])
        spd = rng.choice([0.0, round(rng.uniform(0, 26), 1)])
        cog = None if i % 5 < 3 else (round((hdg + rng.uniform(-30, 30)) % 360, 1) if i % 5 == 3 else round(rng.uniform(0, 360), 1))   # course over the ground, when it differs from the heading
        crs = hdg if cog is None else cog
        if i % 3 == 0:      # built the other way round: a known true wind and ship movement give the relative wind
            tdir, tspd = rng.uniform(0, 360), rng.uniform(0, 70)
            app_from = -(-tspd * u(tdir) - spd * u(crs))             # vector the apparent wind comes from
            ws = round(abs(app_from), 1); off = (brg(app_from) - hdg + 180) % 360 - 180
            rel = round(abs(off), 1); side = 'stbd' if off >= 0 else 'port'
        else:
            rel = rng.choice([round(rng.uniform(0, 180), 1), float(rng.choice([0, 45, 90, 135, 180]))]); side = rng.choice(['stbd', 'port']); ws = round(rng.uniform(0, 80), 1)
        unit = rng.choice(['kn', 'kn', 'ms'])
        if unit == 'ms': ws = round(ws / 2, 1)
        cases.append({'seg': {'side': side, 'unit': unit}, 'set': {'hdg': '%05.1f' % hdg, 'spd': '%.1f' % spd, 'cog': '' if cog is None else '%05.1f' % cog, 'rel': '%.1f' % rel, 'ws': '%.1f' % ws}})
        wk = ws * 3600 / 1852 if unit == 'ms' else ws
        A = hdg + rel if side == 'stbd' else hdg - rel
        tru_to = -wk * u(A) + spd * u(crs)                          # air over the ground = air relative to ship + ship (heading aims the anemometer, course moves the ship)
        exp.append((hdg, wk, A % 360, abs(tru_to), brg(-tru_to) if abs(tru_to) > 1e-12 else None))
    for c, r, (hdg, wk, A, sp, d) in zip(cases, drive('true-wind-calculator', cases), exp):
        ctx = str(c)
        if sp < 0.05:
            T.eq('calm', r['ids'].get('r_main'), 'Calm', ctx); continue
        if abs(sp - 0.05) < 1e-3: continue
        T.ang('direction (deg, 0 dp)', num(r['ids']['r_main']), d, half(0), ctx)
        T.close('speed (kn, 1 dp)', num(r['ids']['r_spd']), sp, half(1), ctx)
        T.close('speed (m/s, 1 dp)', num(r['kv']['Speed in m/s']), sp * 1852 / 3600, half(1), ctx)
        T.ang('relative wind as true bearing', num(r['kv']['Relative wind from (true bearing)']), A, half(0), ctx)
        fr = sp - math.floor(sp)
        forces = {beaufort(math.floor(sp + 0.5))} | ({beaufort(math.floor(sp)), beaufort(math.ceil(sp))} if abs(fr - 0.5) < 1e-6 else set())
        T.check('Beaufort', any(r['ids']['r_bf'] == 'Force %d, %s' % (f, BF[f]) for f in forces), 'shown %r speed %.4f %s' % (r['ids']['r_bf'], sp, ctx))
        off = (d - hdg + 180) % 360 - 180; ob = r['kv']['True wind off the bow']
        if abs(abs(off) % 1 - 0.5) > 1e-6 and 0.5 < abs(off) < 179.5 and abs(abs(off) - 180) > 0.51:
            T.eq('off the bow', ob, '%d° to %s' % (math.floor(abs(off) + 0.5), 'starboard' if off > 0 else 'port'), ctx)
        elif abs(off) < 0.49: T.eq('off the bow', ob, 'Dead ahead', ctx)
        elif abs(off) > 179.51: T.eq('off the bow', ob, 'Dead astern', ctx)
    return T.report()

def hhmm(m): m = int(m) % 1440; return '%02d:%02d' % (m // 60, m % 60)
def cpa(n, rng):
    T = Tally('CPA / TCPA (page)'); cases = []; exp = []
    while len(cases) < n:
        oc = rng.choice([round(rng.uniform(0, 360), 1), float(rng.randrange(0, 360))]); os_ = rng.choice([0.0, round(rng.uniform(0, 25), 1)])
        b1 = round(rng.uniform(0, 360), 1); r1 = round(rng.uniform(0.6, 24), 2); dt = rng.randrange(3, 31)
        tc, ts = rng.uniform(0, 360), rng.choice([0.0, rng.uniform(0, 30)])
        P1 = r1 * u(b1); P2t = P1 + (ts * u(tc) - os_ * u(oc)) * dt / 60
        if abs(P2t) < 0.1 or abs(P2t) > 48: continue
        b2 = round(brg(P2t), 1) % 360; r2 = round(abs(P2t), 2); m1 = rng.randrange(0, 1440); m2 = (m1 + dt) % 1440
        cases.append({'set': {'oc': '%05.1f' % oc, 'os': '%.1f' % os_, 't1': hhmm(m1), 'b1': '%05.1f' % b1, 'r1': '%.2f' % r1, 't2': hhmm(m2), 'b2': '%05.1f' % b2, 'r2': '%.2f' % r2}})
        Q1, Q2 = r1 * u(b1), r2 * u(b2); vrel = (Q2 - Q1) / (dt / 60); vt = vrel + os_ * u(oc)      # from the values as typed
        f = lambda tau: abs(Q2 + vrel * tau)
        if abs(vrel) > 1e-9:
            span = 4 * (abs(Q2) / abs(vrel) + 1)
            best = minimize_scalar(f, bounds=(-span, span), method='bounded', options={'xatol': 1e-12})
            grid = min((f(-span + 2 * span * k / 40000), -span + 2 * span * k / 40000) for k in range(40001))   # coarse brute force as a second opinion
            assert abs(best.fun - grid[0]) <= abs(vrel) * 2 * span / 40000 + 1e-6, (best.fun, grid)
            tau, dmin = best.x, best.fun
        else: tau, dmin = None, abs(Q2)
        exp.append((oc, os_, Q2, vrel, vt, tau, dmin, m2, dt))
    for c, r, (oc, os_, Q2, vrel, vt, tau, dmin, m2, dt) in zip(cases, drive('cpa-tcpa-calculator', cases), exp):
        ctx = str(c['set'])
        T.eq('plot interval', r['kv'].get('Plot interval'), '%d min' % dt, ctx)
        if abs(vrel) < 0.3: continue                               # nearly no relative motion: answers are numerically meaningless
        T.close('CPA (nm, 2 dp)', num(r['ids']['r_cpa']), dmin, half(2) + 2e-4, ctx)
        tm = tau * 60
        if abs(tm) > 0.02:
            if tm < 0: T.eq('TCPA passed', r['ids']['r_tcpa'], 'Passed', ctx)
            else:
                T.close('TCPA (min, 0 dp)', num(r['ids']['r_tcpa']), tm, half(0) + 0.01, ctx)
                want = {hhmm(math.floor(m2 + tm + 0.5 + e)) for e in (-0.012, 0, 0.012)}
                T.check('clock time of CPA', r['ids'].get('r_at') in want, 'shown %r want %r %s' % (r['ids'].get('r_at'), want, ctx))
        if dmin >= 0.02:
            cp = Q2 + vrel * tau; s = r['kv'].get('Bearing at CPA')
            T.ang('bearing at CPA', num(s), brg(cp), half(0) + 0.6 / max(dmin, 0.02) * 0.01, ctx)
        ts = abs(vt)
        T.close('target speed (kn, 1 dp)', num(r['ids']['r_tsp']), ts, half(1), ctx)
        if ts > 0.2:
            T.ang('target course', num(r['ids']['r_tco']), brg(vt), half(0) + 0.02 / ts, ctx)
            asp = (brg(-Q2) - brg(vt) + 180) % 360 - 180; shown = r['ids'].get('r_asp', '')
            if 1 < abs(asp) < 179 and abs(abs(asp) % 1 - 0.5) > 0.03 / ts + 1e-6:
                T.eq('aspect', shown, '%s %d°' % ('Green' if asp > 0 else 'Red', math.floor(abs(asp) + 0.5)), ctx)
        rt = r['kv'].get('Relative track'); a, s = nums(rt)[:2]
        T.ang('relative course', a, brg(vrel), half(0) + 0.01, ctx); T.close('relative speed', s, abs(vrel), half(1), ctx)
        if tm < -0.5: T.check('warning when CPA is past', any(m.startswith('warn') for m in r['msg']), ctx)
        if tm > 0.5 and dmin < 0.045: T.check('critical when CPA is zero', any(m.startswith('crit') for m in r['msg']), ctx)
        if r['ids']['r_tcpa'] not in ('Passed', '–'): T.eq('collision warning shown exactly when the printed CPA is 0.05 nm or less', any(m.startswith('crit') for m in r['msg']), num(r['ids']['r_cpa']) < 0.05 + 1e-9, ctx)
    return T.report()

def set_drift(n, rng):
    T = Tally('set and drift (page)'); cases = []; exp = []
    for i in range(n):
        mode = ['cts', 'sd', 'cmg'][i % 3]
        if mode == 'cts':
            tr = round(rng.uniform(0, 360), 1); v = round(rng.uniform(0.5, 25), 1); st = round(rng.uniform(0, 360), 1); rate = rng.choice([0.0, round(rng.uniform(0, 8), 1)])
            cases.append({'seg': {'mode': mode}, 'set': {'ctrack': '%05.1f' % tr, 'cstw': '%.1f' % v, 'cset': '%05.1f' % st, 'crate': '%.1f' % rate}})
            cross = lambda h: ((v * u(h) + rate * u(st)) * u(tr).conjugate()).imag     # component across the track
            need = -rate * math.sin(math.radians(st - tr))
            if abs(abs(need) - v) <= 1e-9: exp.append((mode, None, True))    # exactly on the limit: the boundary module covers it
            elif abs(need) > v: exp.append((mode, None))
            else:
                h = brentq(cross, tr - 90, tr + 90, xtol=1e-13)
                smg = ((v * u(h) + rate * u(st)) * u(tr).conjugate()).real
                exp.append((mode, None if smg <= 0 else (h % 360, smg, (h - tr + 180) % 360 - 180), abs(abs(need) - v) < 1e-6 or abs(smg) < 1e-6))
        elif mode == 'sd':
            c = round(rng.uniform(0, 360), 1); s = rng.choice([0.0, round(rng.uniform(0, 25), 1)]); th = rng.randrange(0, 7); tm = rng.randrange(0, 60)
            if th == 0 and tm == 0: tm = 30
            cmg = round(rng.uniform(0, 360), 1); dist = round(rng.uniform(0, 160), 1); hrs = th + tm / 60
            cases.append({'seg': {'mode': mode}, 'set': {'scourse': '%05.1f' % c, 'sstw': '%.1f' % s, 'sth': str(th), 'stm': '%02d' % tm, 'scmg': '%05.1f' % cmg, 'sdist': '%.1f' % dist}})
            d = dist * u(cmg) - s * hrs * u(c)
            exp.append((mode, (brg(d), abs(d), abs(d) / hrs, dist / hrs, hrs)))
        else:
            c = round(rng.uniform(0, 360), 1); s = rng.choice([0.0, round(rng.uniform(0, 25), 1)]); st = round(rng.uniform(0, 360), 1); rate = rng.choice([0.0, round(rng.uniform(0, 8), 1)])
            cases.append({'seg': {'mode': mode}, 'set': {'mcourse': '%05.1f' % c, 'mstw': '%.1f' % s, 'mset': '%05.1f' % st, 'mrate': '%.1f' % rate}})
            g = s * u(c) + rate * u(st); exp.append((mode, (brg(g), abs(g))))
    for c, r, e in zip(cases, drive('set-and-drift-course-to-steer-calculator', cases), exp):
        ctx = str(c['set']); mode, x = e[0], e[1]
        if mode == 'cts':
            if len(e) > 2 and e[2]: continue                      # exactly on the limit
            if x is None: T.check('no course possible', any('too strong' in m for m in r['msg']), 'shown %r %s' % (r, ctx)); continue
            h, smg, corr = x
            T.ang('course to steer (1 dp)', num(r['ids']['r_main']), h, half(1), ctx); T.close('speed made good', num(r['ids']['r_smg']), smg, half(1), ctx)
            sub = r['sub'][0]
            if abs(corr) < 0.049: T.check('no allowance', sub.startswith('No allowance needed'), sub + ctx)
            elif abs(corr) > 0.051 and abs(abs(corr) * 10 % 1 - 0.5) > 1e-4:
                T.check('allowance side and size', sub.startswith('Allow %.1f° to %s' % (math.floor(abs(corr) * 10 + 0.5) / 10, 'starboard' if corr > 0 else 'port')), 'shown %r corr %.4f %s' % (sub, corr, ctx))
        elif mode == 'sd':
            st, drift, rate, smg, hrs = x
            if drift < 1e-6: T.check('nil drift', r['big'][0][1] == 'Nil', ctx); continue
            T.ang('set (0 dp)', num(r['ids']['r_main']), st, half(0) + 0.006 / drift, ctx); T.close('rate (kn, 1 dp)', num(r['ids']['r_rate']), rate, half(1), ctx)
            T.close('drift (nm, 1 dp)', num(r['kv']['Drift']), drift, half(1), ctx); T.close('speed made good', num(r['kv']['Speed made good']), smg, half(1), ctx)
        else:
            cm, sm = x
            if sm < 1e-6: T.check('stopped', r['big'][0][1] == 'Stopped', ctx); continue
            T.ang('course made good (1 dp)', num(r['ids']['r_main']), cm, half(1) + 0.0006 / sm, ctx); T.close('speed made good (1 dp)', num(r['ids']['r_smg']), sm, half(1), ctx)
    return T.report()

if __name__ == '__main__':
    rng = make_rng(20261126); n = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    which = sys.argv[2:] or ['true_wind', 'cpa', 'set_drift']
    bad = sum(globals()[w](n, rng) for w in which)
    print('TOTAL FAILED', bad)

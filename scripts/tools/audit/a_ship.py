"""Independent end-to-end audit: squat and UKC, propeller slip, fuel, FWA/DWA, list and GM, unit converter,
rate of turn, horizon, rolling period. Expected values are worked from the published formulas with exact fractions,
from pint's unit registry, and from simple geometry or physics where a second route exists."""
import math, random, sys
from fractions import Fraction as F
import numpy as np, pint
from common import *
def fr(s): return F(s)
def rs(rng, lo, hi, dp): return ('%.' + str(dp) + 'f') % rng.uniform(lo, hi)

def squat(n, rng):
    T = Tally('squat and UKC (page) vs Barrass formulas'); cases = []; meta = []
    for i in range(n):
        cb = rs(rng, 0.30, 1.00, 2); v = rs(rng, 0, 22, 1); conf = rng.random() < 0.5
        depth = rs(rng, 4, 40, 2); tide = rs(rng, -1, 6, 2); dr = rs(rng, 3, 23, 2); other = rng.choice(['', '0', rs(rng, 0, 2.5, 2)])
        cases.append({'seg': {'water': 'conf' if conf else 'open'}, 'set': {'cb': cb, 'v': v, 'depth': depth, 'tide': tide, 'draught': dr, 'other': other}})
        meta.append((fr(cb), fr(v), conf, fr(depth), fr(tide), fr(dr), fr(other or '0')))
    for c, r, (cb, v, conf, depth, tide, dr, other) in zip(cases, drive('squat-ukc-calculator', cases), meta):
        ctx = str(c); K = 2 if conf else 1; sq = K * cb * v * v / 100
        T.close('squat (m, 2 dp)', num(r['ids']['r_squat']), float(sq), half(2), ctx)
        T.eq('water named', r['big'][0][0], 'Squat, ' + ('confined channel' if conf else 'open water'), ctx)
        T.close('open-water row', num(r['kv']['Squat in open shallow water']), float(cb * v * v / 100), half(2), ctx)
        T.close('confined row = twice open', num(r['kv']['Squat in a confined channel']), float(2 * cb * v * v / 100), half(2), ctx)
        water = depth + tide; stat = water - dr; net = stat - sq - other
        T.close('depth of water', num(r['kv']['Depth of water (charted + tide)']), float(water), half(2), ctx)
        T.close('static UKC', num(r['ids']['r_static']), float(stat), half(2), ctx)
        T.close('net UKC (m, 2 dp)', num(r['ids']['r_ukc']), float(net), half(2), ctx)
        T.close('net UKC as % of draught', num(r['sub'][0]), float(net / dr * 100), half(1), ctx)
        crit = any(m.startswith('crit') for m in r['msg'])
        T.eq('grounding warning shown exactly when the printed net UKC is 0.00 or less', crit, num(r['ids']['r_ukc']) <= 0, ctx)
        if net != F(1, 200): T.eq('grounding warning by exact arithmetic (net UKC rounds to 0.00 or less)', crit, net < F(1, 200), ctx)
        avail = stat - other; row = r['kv'].get('Net UKC falls to zero at')
        if avail > 0:
            v0 = math.sqrt(float(avail) * 100 / (K * float(cb))); T.close('speed at which UKC is zero', num(row), v0, half(1), ctx)
            sq0 = K * float(cb) * num(row) ** 2 / 100
            T.check('at that speed squat equals the clearance (within rounding)', abs(sq0 - float(avail)) <= K * float(cb) * ((v0 + 0.05) ** 2 - v0 ** 2) / 100 + 1e-6, ctx)
        else: T.check('no zero-UKC speed when none is left', row is None, ctx)
        ratio = water / dr; T.close('depth to draught ratio', num(r['kv']['Depth to draught ratio']), float(ratio), half(2), ctx)
        pr = num(r['kv']['Depth to draught ratio']); note = any('1.1 to 1.4' in m for m in r['msg'])
        T.eq('range note shown exactly when the printed ratio is outside 1.10 to 1.40', note, ratio > 1 and (pr < 1.1 - 1e-9 or pr > 1.4 + 1e-9), ctx)
        if ratio not in (F(1095, 1000), F(1405, 1000)): T.eq('range note by exact arithmetic', note, ratio > 1 and (ratio < F(1095, 1000) or ratio > F(1405, 1000)), ctx)
    return T.report()

def slip(n, rng):
    T = Tally('propeller slip (page)'); cases = []; meta = []
    for i in range(n):
        if i % 2 == 0:
            p = rs(rng, 2, 10, 2); rpm = rs(rng, 20, 200, 1); ph = rng.randrange(0, 30); pm = rng.randrange(0, 60); od = rs(rng, 0, 700, 1)
            if ph == 0 and pm == 0: pm = 30
            cases.append({'seg': {'mode': 'per'}, 'set': {'pitch': p, 'rpm': rpm, 'ph': str(ph), 'pm': '%02d' % pm, 'od': od}}); meta.append(('per', fr(p), fr(rpm), F(ph) + F(pm, 60), fr(od)))
        else:
            p = rs(rng, 2, 10, 2); rpm = rs(rng, 20, 200, 1); os_ = rs(rng, 0, 28, 1)
            cases.append({'seg': {'mode': 'now'}, 'set': {'pitch2': p, 'rpm2': rpm, 'os': os_}}); meta.append(('now', fr(p), fr(rpm), fr(os_)))
    for c, r, m in zip(cases, drive('propeller-slip-calculator', cases), meta):
        ctx = str(c)
        if m[0] == 'per':
            _, p, rpm, hrs, od = m; revs = rpm * 60 * hrs; ed = p * revs / 1852; s = (ed - od) / ed * 100
            T.close('slip % (2 dp)', num(r['ids']['r_main']), float(s), half(2), ctx); T.close('engine distance (nm)', num(r['ids']['r_ed']), float(ed), half(1), ctx)
            T.close('engine speed (kn)', num(r['kv']['Engine speed']), float(p * rpm * 60 / 1852), half(2), ctx); T.close('observed speed (kn)', num(r['kv']['Observed speed']), float(od / hrs), half(2), ctx)
            T.close('revolutions', num(r['kv']['Revolutions']), float(revs), half(0), ctx)
        else:
            _, p, rpm, os_ = m; es = p * rpm * 60 / 1852; s = (es - os_) / es * 100
            T.close('slip % (2 dp), instant', num(r['ids']['r_main']), float(s), half(2), ctx); T.close('engine speed (kn), instant', num(r['ids']['r_ed']), float(es), half(2), ctx)
        T.eq('negative-slip note shown exactly when the printed slip is below zero', len(r['msg']) > 0, num(r['ids']['r_main']) < 0, ctx)
        if s != F(-1, 200): T.eq('negative-slip note by exact arithmetic', len(r['msg']) > 0, s < F(-1, 200), ctx)
    return T.report()

def fuel(n, rng):
    T = Tally('fuel consumption and ROB (page)'); cases = []; meta = []
    for i in range(n):
        cons = rs(rng, 0.5, 200, 1); hours = rng.choice(['24', '12', rs(rng, 1, 48, 1)]); rob = rs(rng, 0, 6000, 1); sp = rng.choice(['', rs(rng, 3, 25, 1)])
        dist = rng.choice(['', str(rng.randrange(0, 9000))]); ns = rng.choice(['', rs(rng, 3, 25, 1)])
        cases.append({'set': {'cons': cons, 'hours': hours, 'rob': rob, 'speed': sp, 'dist': dist, 'newspeed': ns}}); meta.append((fr(cons), fr(hours), fr(rob), sp, dist, ns))
    for c, r, (cons, hours, rob, sp, dist, ns) in zip(cases, drive('fuel-consumption-calculator', cases), meta):
        ctx = str(c); daily = cons / hours * 24
        T.close('daily consumption (t/day, 1 dp)', num(r['ids']['r_daily']), float(daily), half(1), ctx); T.close('days of fuel (1 dp)', num(r['ids']['r_days']), float(rob / daily), half(1), ctx)
        T.close('per hour (t/h)', num(r['kv']['Per hour']), float(daily / 24), half(2), ctx)
        if sp:
            v = fr(sp); T.close('per nautical mile (kg)', num(r['kv']['Per nautical mile']), float(daily / (24 * v) * 1000), half(1), ctx)
            T.close('range (nm)', num(r['ids']['r_range']), float(rob / daily * 24 * v), half(0), ctx)
            if dist != '':
                d = fr(dist); vf = d / v / 24 * daily
                T.close('fuel for the voyage (t)', num(r['ids']['r_voy']), float(vf), half(1), ctx); T.close('ROB on arrival (t)', num(r['ids']['r_arr']), float(rob - vf), half(1), ctx)
                short = any(m.startswith('crit') for m in r['msg'])
                T.eq('shortfall warning shown exactly when the printed ROB on arrival is below zero', short, num(r['ids']['r_arr']) < 0, ctx)
                if rob - vf != F(-1, 20): T.eq('shortfall warning by exact arithmetic', short, rob - vf < F(-1, 20), ctx)
                if short: T.check('shortfall quoted is the printed ROB with its sign turned', ('Short by %.1f t' % -num(r['ids']['r_arr'])) in ' '.join(r['msg']), str(r['msg']) + ctx)
            if ns: T.close('cube-law estimate (t/day)', num(r['ids']['r_cube']), float(daily) * (float(fr(ns)) / float(v)) ** 3, half(1), ctx)
        else: T.check('no range without a speed', 'r_range' not in r['ids'] and 'r_voy' not in r['ids'], ctx)
    return T.report()

def fwa(n, rng):
    T = Tally('FWA and DWA (page)'); cases = []; meta = []
    for i in range(n):
        known = i % 2 == 1; rho = rng.uniform(0.996, 1.032); dens = ('%.3f' % rho) if rng.random() < 0.6 else ('%.1f' % (rho * 1000)); dr = rng.choice(['', rs(rng, 3, 23, 2)])
        if known:
            f = str(rng.randrange(20, 420)); cases.append({'seg': {'mode': 'known'}, 'set': {'fwa': f, 'dens': dens, 'draught': dr}}); meta.append((fr(f), dens, dr))
        else:
            disp = rs(rng, 800, 400000, 0); tpc = rs(rng, 4, 180, 1); cases.append({'seg': {'mode': 'calc'}, 'set': {'disp': disp, 'tpc': tpc, 'dens': dens, 'draught': dr}}); meta.append((fr(disp) / (4 * fr(tpc)), dens, dr))
    for c, r, (f, dens, dr) in zip(cases, drive('fwa-dwa-calculator', cases), meta):
        ctx = str(c); rho = fr(dens); rho = rho * 1000 if rho < 2 else rho; dwa = f * (1025 - rho) / 25
        T.close('FWA (mm, 1 dp)', num(r['ids']['r_fwa']), float(f), half(1), ctx)
        T.close('density echoed (t/m3)', num(r['kv']['Dock water density']), float(rho / 1000), half(3), ctx)
        if dwa >= 0:
            T.close('DWA (mm, 0 dp)', num(r['ids']['r_dwa']), float(dwa), half(0), ctx); T.close('DWA unrounded (mm, 1 dp)', num(r['kv']['DWA, unrounded']), float(dwa), half(1), ctx)
            T.close('allowance in cm', num(r['sub'][0]), float(dwa / 10), half(1), ctx)
        else:
            T.eq('no allowance in water denser than 1.025', r['ids']['r_dwa'], 'None', ctx); T.close('clearance to keep (mm)', num(r['msg'][0].split(':', 1)[1]), float(-dwa), half(0), ctx)
        if dr: T.close('draught at the load line in this water (m, 3 dp)', num(r['ids']['r_dr']), float(fr(dr) + dwa / 1000), half(3), ctx)
    return T.report()

def listgm(n, rng):
    T = Tally('list and GM (page)'); cases = []; meta = []
    for i in range(n):
        disp = rs(rng, 500, 300000, 0); km = rs(rng, 3, 25, 2); kg = '%.3f' % (float(km) - rng.uniform(-0.4, 4)); fsm = rng.choice(['', '0', rs(rng, 0, float(disp) * 0.8, 1)])
        w = rng.choice(['', rs(rng, 1, 2000, 1)]); d = rs(rng, 0.5, 40, 1); side = rng.choice(['stbd', 'port'])
        if float(kg) <= 0: continue
        cases.append({'seg': {'side': side}, 'set': {'disp': disp, 'km': km, 'kg': kg, 'fsm': fsm, 'w': w, 'd': d}}); meta.append((fr(disp), fr(km), fr(kg), fr(fsm or '0'), fr(w or '0'), fr(d), side))
    for c, r, (disp, km, kg, fsm, w, d, side) in zip(cases, drive('list-and-gm-calculator', cases), meta):
        ctx = str(c); solid = km - kg; fsc = fsm / disp; gm = solid - fsc
        T.close('fluid GM (m, 2 dp)', num(r['ids']['r_gm']), float(gm), half(2), ctx); T.close('solid GM (m, 3 dp)', num(r['ids']['r_solid']), float(solid), half(3), ctx)
        T.close('free surface correction (m, 3 dp)', num(r['ids']['r_fsc']), float(fsc), half(3), ctx)
        crit = any(m.startswith('crit') for m in r['msg'])
        T.eq('unstable warning shown exactly when the printed GM is 0.00 or less', crit, num(r['ids']['r_gm']) <= 0, ctx)
        if gm != F(1, 200): T.eq('unstable warning by exact arithmetic (GM rounds to 0.00 or less)', crit, gm < F(1, 200), ctx)
        if w > 0:
            gg1 = w * d / disp; T.close('shift of G (m, 3 dp)', num(r['kv']['Shift of G (GG₁)']), float(gg1), half(3), ctx)
            if not crit:
                lst = math.degrees(math.atan(float(gg1 / gm))); shown = r['ids']['r_list']
                T.close('list (deg, 1 dp)', num(shown), lst, half(1), ctx); T.check('list to the side the weight moved', shown.endswith('to ' + ('starboard' if side == 'stbd' else 'port')), shown + ctx)
                # second route: the heeling moment w*d must equal the righting moment disp*GM*tan(list)
                T.close('moments balance at the shown list (relative)', float(disp * gm) * math.tan(math.radians(num(shown))) / float(w * d), 1, math.radians(0.0501) / max(math.sin(math.radians(lst)) * math.cos(math.radians(lst)), 1e-9) * 1.05 + 1e-3 if 0.06 < lst < 89.9 else 1e9, ctx)
                T.eq('small-angle caution shown above 10 degrees', any(m.startswith('warn') for m in r['msg']), lst > 10, ctx)
            else: T.check('no list given with zero or negative GM', 'r_list' not in r['ids'], ctx)
    return T.report()

UREG = pint.UnitRegistry()
PINT = {'speed': {'kn': 'knot', 'm/s': 'meter/second', 'km/h': 'kilometer/hour', 'mph': 'mile/hour'},
        'distance': {'nm': 'nautical_mile', 'cable': 185.2, 'km': 'kilometer', 'm': 'meter', 'statute mile': 'mile', 'ft': 'foot'},
        'depth': {'m': 'meter', 'ft': 'foot', 'fathom': 'fathom', 'shackle (27.5 m)': 27.5},
        'pressure': {'bar': 'bar', 'psi': 'psi', 'kPa': 'kilopascal', 'MPa': 'megapascal', 'kgf/cm²': 'kilogram_force/centimeter**2', 'mmHg': 'mmHg', 'atm': 'atm'},
        'volume': {'m³': 'meter**3', 'litre': 'liter', 'US barrel': 'oil_barrel', 'US gallon': 'gallon', 'Imperial gallon': 'imperial_gallon', 'ft³': 'foot**3'},
        'mass': {'tonne': 'metric_ton', 'long ton': 'long_ton', 'short ton': 'short_ton', 'kg': 'kilogram', 'lb': 'pound'},
        'power': {'kW': 'kilowatt', 'hp (metric, PS)': 'metric_horsepower', 'hp (imperial, bhp)': 'horsepower'}}
def si(group, unit):
    x = PINT[group][unit]
    return x if isinstance(x, float) else (1 * UREG(x)).to_base_units().magnitude
BFN = ['Calm', 'Light air', 'Light breeze', 'Gentle breeze', 'Moderate breeze', 'Fresh breeze', 'Strong breeze', 'Near gale', 'Gale', 'Strong gale', 'Storm', 'Violent storm', 'Hurricane']
def bf(kn):
    k = math.floor(kn + 0.5)
    for f, top in enumerate([0, 3, 6, 10, 16, 21, 27, 33, 40, 47, 55, 63]):
        if k <= top: return f
    return 12
def units(n, rng):
    T = Tally('marine unit converter (page) vs pint'); cases = []; meta = []
    for i in range(n):
        g = rng.choice(list(PINT) + ['temp', 'vm'])
        if g == 'vm':
            m2v = rng.random() < 0.5; q = rs(rng, 0, 300000, 2); rho = rs(rng, 0.3, 1.9, 4)
            cases.append({'sel': {'group': 'vm'}, 'seg': {'dir': 'm2v' if m2v else 'v2m'}, 'set': {'q': q, 'rho': rho}}); meta.append((g, m2v, fr(q), fr(rho)))
        elif g == 'temp':
            f = rng.choice('CFK'); v = rs(rng, {'C': -60, 'F': -70, 'K': 200}[f], {'C': 400, 'F': 800, 'K': 700}[f], 1)
            cases.append({'sel': {'group': 'temp', 'unit': f}, 'set': {'value': v}}); meta.append((g, f, float(v)))
        else:
            f = rng.choice(list(PINT[g])); v = ('%.4g' % (10 ** rng.uniform(-3, 6)))
            v = '%f' % float(v); v = v.rstrip('0').rstrip('.') or '0'
            cases.append({'sel': {'group': g, 'unit': f}, 'set': {'value': v}}); meta.append((g, f, float(v)))
    for c, r, m in zip(cases, drive('marine-unit-converter', cases), meta):
        ctx = str(c)
        if m[0] == 'vm':
            _, m2v, q, rho = m; want = float(q / rho if m2v else q * rho); s = r['ids']['r_main']
            T.close('volume and mass by density (6 figures)', num(s), want, abs(want) * 6e-6 + 1e-9, ctx); T.check('unit shown', s.endswith('m³' if m2v else 't'), s + ctx)
        elif m[0] == 'temp':
            _, f, v = m; k = v + 273.15 if f == 'C' else (v - 32) * 5 / 9 + 273.15 if f == 'F' else v
            q = UREG.Quantity(v, {'C': 'degC', 'F': 'degF', 'K': 'kelvin'}[f])
            for name, pu in (('°C', 'degC'), ('°F', 'degF'), ('K', 'kelvin')):
                T.close('temperature to ' + name + ' (2 dp)', num(r['kv'][name]), q.to(pu).magnitude, half(2), ctx)
        else:
            g, f, v = m
            for name in PINT[g]:
                want = v * si(g, f) / si(g, name); s = r['kv'][name]
                rel = 6e-5 if 'e' in s else 6e-6
                T.close('%s: every unit pair (relative)' % g, num(s) / want if want else 1 + num(s), 1, rel, 'shown %r want %r %s' % (s, want, ctx))
            if g == 'speed':
                kn = v * si(g, f) / si(g, 'kn')
                if abs(kn - math.floor(kn) - 0.5) > 1e-6: T.eq('Beaufort row', r['kv']['Beaufort'], 'Force %d, %s' % (bf(kn), BFN[bf(kn)]), ctx)
    return T.report()

def rot(n, rng):
    T = Tally('rate of turn (page) vs geometry'); cases = []; meta = []
    for i in range(n):
        v = rs(rng, 1, 30, 1); ang = rng.choice(['', rs(rng, 1, 179, 1), str(rng.randrange(1, 180))])
        if i % 2 == 0:
            rad = rs(rng, 0.1, 5, 2); cases.append({'seg': {'mode': 'rot'}, 'set': {'spd': v, 'rad': rad, 'ang': ang}}); meta.append(('rot', float(v), float(rad), ang))
        else:
            ro = rs(rng, 2, 60, 1); cases.append({'seg': {'mode': 'rad'}, 'set': {'spd': v, 'rot': ro, 'ang': ang}}); meta.append(('rad', float(v), float(ro), ang))
    for c, r, (mode, v, x, ang) in zip(cases, drive('rate-of-turn-calculator', cases), meta):
        ctx = str(c)
        if mode == 'rot':
            R = x; rot_ = math.degrees(v / R) / 60                       # v/R radians per hour
            T.close('rate of turn (deg/min, 1 dp)', num(r['ids']['r_main']), rot_, half(1), ctx); T.close('bridge rule beside it', num(r['sub'][0]), v / R, half(1), ctx)
        else:
            rot_ = x; R = v / math.radians(rot_ * 60)
            T.close('radius (nm, 2 dp)', num(r['ids']['r_main']), R, half(2), ctx); m_ = nums(r['sub'][0]); T.close('radius in cables', m_[0], R * 10, half(1), ctx); T.close('radius in metres', m_[1], R * 1852, half(0), ctx)
        T.close('rate per second', num(r['kv']['Rate of turn per second']), rot_ / 60, half(2), ctx)
        if ang:
            a = float(ang); Rr = R                                              # geometry with the radius the page works with
            t = a / rot_ * 60; sec = math.floor(t + 0.5); shown = r['ids']['r_time']; mm, ss = nums(shown)[:2]
            T.close('time for the turn (s)', mm * 60 + ss, t, 0.5 + 1e-6, ctx)
            T.close('arc length (nm, 2 dp)', num(r['ids']['r_arc']), Rr * math.radians(a), half(2), ctx)
            # tangent length by construction: circle of radius R touching both legs; where it leaves the first leg
            d1 = np.array([0.0, 1.0]); th = math.radians(a); d2 = np.array([math.sin(th), math.cos(th)]); nrm1 = np.array([1.0, 0.0]); nrm2 = np.array([math.cos(th), -math.sin(th)])
            # centre c satisfies c.nrm1 = R and c.nrm2 = R (inside of a starboard turn); the waypoint is the origin
            cxy = np.linalg.solve(np.array([nrm1, nrm2]), np.array([Rr, Rr])); tang = -float(cxy @ d1)
            T.close('start of the arc before the waypoint (nm, 2 dp)', num(r['ids']['r_wo']), tang, half(2), ctx)
    return T.report()

def horizon(n, rng):
    T = Tally('horizon and light range (page)'); cases = []; meta = []
    for i in range(n):
        eye = rs(rng, 1, 70, 1); obj = rng.choice(['', rs(rng, 1, 300, 1)]); ant = rng.choice(['', rs(rng, 5, 70, 1)])
        cases.append({'set': {'eye': eye, 'obj': obj, 'ant': ant}}); meta.append((float(eye), obj, ant))
    for c, r, (eye, obj, ant) in zip(cases, drive('distance-to-horizon-calculator', cases), meta):
        ctx = str(c); T.close('sea horizon 2.08 x sqrt(h) (nm, 1 dp)', num(r['ids']['r_hor']), 2.08 * math.sqrt(eye), half(1), ctx)
        sp = nums(r['ids']['r_span'])
        if obj:
            o = float(obj); T.close('dipping range (nm, 1 dp)', num(r['ids']['r_dip']), 2.08 * (math.sqrt(eye) + math.sqrt(o)), half(1), ctx)
            T.close('range in other tables, low', sp[0], 2.03 * (math.sqrt(eye) + math.sqrt(o)), half(1), ctx); T.close('range in other tables, high', sp[1], 2.12 * (math.sqrt(eye) + math.sqrt(o)), half(1), ctx)
        else:
            T.close('horizon in other tables, low', sp[0], 2.03 * math.sqrt(eye), half(1), ctx); T.close('horizon in other tables, high', sp[1], 2.12 * math.sqrt(eye), half(1), ctx)
        if ant:
            T.close('radar horizon 2.21 x sqrt(h)', num(r['ids']['r_rad']), 2.21 * math.sqrt(float(ant)), half(1), ctx)
            if obj: T.close('radar range to the object', num(r['ids']['r_rado']), 2.21 * (math.sqrt(float(ant)) + math.sqrt(float(obj))), half(1), ctx)
    return T.report()

def rolling(n, rng):
    T = Tally('rolling period, GM and encounter period (page) vs IS Code and first principles'); cases = []; meta = []; fp = []
    for i in range(n):
        B = rs(rng, 8, 62, 1); d = rs(rng, 3, 23, 1); L = rs(rng, 40, 400, 0)
        waves = rng.random() < 0.6; tw = rs(rng, 3, 20, 1) if waves else ''; v = rs(rng, 0, 25, 1) if waves else ''; a = (str(rng.choice([0, 30, 45, 90, 135, 150, 180])) if rng.random() < 0.5 else rs(rng, 0, 180, 0)) if waves else ''
        if i % 2 == 0:
            gm = rs(rng, 0.15, 12, 2); cases.append({'seg': {'mode': 't'}, 'set': {'beam': B, 'dr': d, 'lwl': L, 'gm': gm, 'tw': tw, 'spd': v, 'wang': a}}); meta.append(('t', float(B), float(d), float(L), float(gm), tw, v, a))
        else:
            per = rs(rng, 4, 40, 1); cases.append({'seg': {'mode': 'gm'}, 'set': {'beam': B, 'dr': d, 'lwl': L, 'per': per, 'tw': tw, 'spd': v, 'wang': a}}); meta.append(('gm', float(B), float(d), float(L), float(per), tw, v, a))
    for c, r, (mode, B, d, L, x, tw, v, a) in zip(cases, drive('rolling-period-gm-calculator', cases), meta):
        ctx = str(c); C = 0.373 + 0.023 * (B / d) - 0.043 * (L / 100)
        if not C > 0.2: T.check('outside the formula', r['empty'] is not None, ctx); continue
        T.close('coefficient C (3 dp)', num(r['ids']['r_c']), C, half(3), ctx)
        if mode == 't': Tr = 2 * C * B / math.sqrt(x); T.close('rolling period (s, 1 dp)', num(r['ids']['r_main']), Tr, half(1), ctx)
        else: Tr = x; T.close('GM from the period (m, 2 dp)', num(r['ids']['r_main']), (2 * C * B / x) ** 2, half(2), ctx)
        if tw:
            tw, v, a = float(tw), float(v), float(a); T.close('wave length 1.56 Tw^2 (m)', num(r['ids']['r_wl']), 1.56 * tw * tw, half(0), ctx)
            den = 3 * tw + v * math.cos(math.radians(a)); te = 3 * tw * tw / den if abs(den) > 1e-9 else float('inf')
            if not math.isfinite(te) or te < 0: T.eq('no encounter period when overtaking the waves', r['ids']['r_te'], 'None', ctx)
            else:
                if te < 2000: T.close('encounter period, IMO formula (s, 1 dp)', num(r['ids']['r_te']), te, half(1) + te * 1e-9, ctx)
                ratio = te / Tr
                if te < 2000: T.close('ratio to rolling period (2 dp)', num(r['ids']['r_ratio']), ratio, half(2) + (0.006 * ratio / Tr if mode == 't' else 0), ctx)
                flag = r['ids'].get('r_flag', ''); pr = num(r['ids']['r_ratio'])   # the flags follow the ratio as printed
                T.eq('synchronous flag exactly when the printed ratio is 0.90 to 1.10', 'synchronous' in flag, 0.895 < pr < 1.105, ctx)
                T.eq('parametric flag exactly when the printed ratio is 0.45 to 0.55', 'half the rolling period' in flag, 0.445 < pr < 0.555, ctx)
                # first principles: deep-water wave of period Tw moves at g Tw / 2 pi; the ship closes at that plus her own speed along it
                cw = 9.80665 * tw / (2 * math.pi); lam = cw * tw; close = cw + v * 1852 / 3600 * math.cos(math.radians(a))
                if a <= 90 and close > 0: fp.append(abs(te / (lam / close) - 1))
    bad = T.report(); fp = np.array(fp); print('     IMO encounter formula vs first principles, head to beam seas: n=%d  median %.2f%%  max %.2f%%' % (len(fp), np.median(fp) * 100, fp.max() * 100))
    return bad

if __name__ == '__main__':
    rng = make_rng(909); n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000; which = sys.argv[2:] or ['squat', 'slip', 'fuel', 'fwa', 'listgm', 'units', 'rot', 'horizon', 'rolling']
    bad = sum(globals()[w](n, rng) for w in which); print('TOTAL FAILED', bad)

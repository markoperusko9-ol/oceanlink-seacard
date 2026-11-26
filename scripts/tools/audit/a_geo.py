"""Independent end-to-end audit: great circle and rhumb line (vs PROJ's geodesic and direct numerical integration on the
WGS84 ellipsoid) and the ETA tool (vs Python's own date arithmetic with exact fractions)."""
import math, random, sys, datetime as dt
from fractions import Fraction as F
import numpy as np
from pyproj import Geod
from scipy.integrate import quad
from scipy.optimize import minimize_scalar
from common import *
WGS = Geod(ellps='WGS84'); A_, F_ = 6378137.0, 1 / 298.257223563; E2 = F_ * (2 - F_)
RS = 1852 * 60 * 180 / math.pi; SPH = Geod(a=RS, b=RS)            # sphere on which 1 minute of arc is exactly 1 nm
def iso(lat): return quad(lambda t: (1 - E2) / ((1 - E2 * math.sin(t) ** 2) * math.cos(t)), 0, math.radians(lat), epsabs=1e-13, epsrel=1e-13, limit=200)[0]
def mer(lat): return A_ * quad(lambda t: (1 - E2) / (1 - E2 * math.sin(t) ** 2) ** 1.5, 0, math.radians(lat), epsabs=1e-13, epsrel=1e-13)[0]
def rhumb(lat1, lon1, lat2, lon2):
    dl = math.radians((lon2 - lon1 + 180) % 360 - 180); dpsi = iso(lat2) - iso(lat1)
    course = math.degrees(math.atan2(dl, dpsi)) % 360
    if abs(lat2 - lat1) < 1e-12: d = abs(dl) * A_ * math.cos(math.radians(lat1)) / math.sqrt(1 - E2 * math.sin(math.radians(lat1)) ** 2)
    else: d = abs(mer(lat2) - mer(lat1)) / abs(math.cos(math.atan2(dl, dpsi)))
    return d / 1852, course, abs(dpsi) * 10800 / math.pi
def sph_dist(lat1, lon1, lat2, lon2): return SPH.inv(lon1, lat1, lon2, lat2)[2] / 1852
def vertex(lat1, lon1, lat2, lon2):
    """Highest-latitude points of the whole great circle found by brute force along it, and which one the leg passes."""
    az, _, d = SPH.inv(lon1, lat1, lon2, lat2); C = 2 * math.pi * RS
    f = lambda s: SPH.fwd(lon1, lat1, az, s % C)[1]
    ss = np.linspace(0, C, 4001); lats = np.array([f(s) for s in ss]); out = []
    for sign in (1, -1):
        k = int(np.argmax(sign * lats)); step = C / 4000   # f() wraps, so the search may run past either end of the grid
        r = minimize_scalar(lambda s: -sign * f(s), bounds=(ss[k] - step, ss[k] + step), method='bounded', options={'xatol': 1e-4})
        s = r.x % C; lo, la, _ = SPH.fwd(lon1, lat1, az, s); out.append((la, lo, s <= d + 1.0 or s >= C - 1.0 and d > C - 2))
    return out, d
def pos(rng, maxlat=80):
    d = rng.randrange(0, maxlat); m = round(rng.uniform(0, 59.9), 1); h = rng.choice('NS'); D = rng.randrange(0, 180); M = round(rng.uniform(0, 59.9), 1); H = rng.choice('EW')
    return d, m, h, D, M, H
def val(d, m, h): return (d + m / 60) * (1 if h in 'NE' else -1)
def vparse(s):
    m = re.match(r"(\d+)°(\d+\.\d)'([NS]) (\d+)°(\d+\.\d)'([EW])", s)
    return val(int(m.group(1)), float(m.group(2)), m.group(3)), val(int(m.group(4)), float(m.group(5)), m.group(6))

def gc(n, rng):
    T = Tally('great circle and rhumb line (page) vs PROJ and numerical integration'); cases = []; meta = []
    for i in range(n):
        a = list(pos(rng)); b = list(pos(rng)); k = i % 12
        if k == 0: b[0], b[1], b[2] = a[0], a[1], a[2]                                   # same latitude: parallel sailing
        elif k == 1: b[3], b[4], b[5] = a[3], a[4], a[5]                                 # same meridian
        elif k == 2: a[0] = a[1] = b[0] = b[1] = 0; a[1] = b[1] = 0.0                     # along the equator
        elif k == 3: b = [a[0], a[1], 'S' if a[2] == 'N' else 'N', 179 - a[3], round(59.9 - a[4], 1), 'W' if a[5] == 'E' else 'E']   # nearly opposite points
        elif k == 4: b = [a[0], round(min(59.9, a[1] + rng.uniform(0, 8)), 1), a[2], a[3], round(min(59.9, a[4] + rng.uniform(0, 8)), 1), a[5]]   # short leg
        elif k == 5: a[3], a[5], b[3], b[5] = rng.randrange(150, 180), 'E', rng.randrange(150, 180), 'W'                              # across the date line
        A = (val(*a[:3]), val(*a[3:])); B = (val(*b[:3]), val(*b[3:]))
        if abs(A[0] - B[0]) < 1e-9 and abs(A[1] - B[1]) < 1e-9: continue
        if abs(abs((B[1] - A[1] + 180) % 360 - 180) - 180) < 1e-6: continue                 # exactly 180 of longitude apart: rhumb direction is a coin toss
        cases.append({'sel': {'alath': a[2], 'alonh': a[5], 'blath': b[2], 'blonh': b[5]}, 'set': {'alatd': str(a[0]), 'alatm': '%04.1f' % a[1], 'alond': '%03d' % a[3], 'alonm': '%04.1f' % a[4],
                      'blatd': str(b[0]), 'blatm': '%04.1f' % b[1], 'blond': '%03d' % b[3], 'blonm': '%04.1f' % b[4]}}); meta.append((A, B))
    res = drive('great-circle-rhumb-line-calculator', cases)
    for c, r, (A, B) in zip(cases, res, meta):
        ctx = '%r -> %r' % (A, B)
        az12, az21, s = WGS.inv(A[1], A[0], B[1], B[0]); g = s / 1852
        if g < 0.005: T.check('same position', r['empty'] is not None, ctx); continue
        T.close('great circle distance WGS84 (nm, 1 dp)', num(r['ids']['r_gc']), g, half(1) + 5e-4, ctx)
        anti = sph_dist(A[0], A[1], -B[0], B[1] + 180) < 40                     # within 40 nm of the antipode: courses are not unique
        co = nums(r['sub'][0])
        if not anti and g > 0.5:
            T.ang('initial course WGS84 (1 dp)', co[0], az12, half(1) + 0.002 + 0.03 / g, ctx); T.ang('final course WGS84 (1 dp)', co[1], az21 + 180, half(1) + 0.002 + 0.03 / g, ctx)
        rd, rc, dmp = rhumb(A[0], A[1], B[0], B[1])
        T.close('rhumb distance WGS84 (nm, 1 dp)', num(r['ids']['r_rh']), rd, half(1) + 5e-4, ctx)
        if rd > 0.5: T.ang('rhumb course (1 dp)', num(r['sub'][1]), rc, half(1) + 0.002 + 0.03 / rd, ctx)
        T.close('difference of meridional parts', num(r['kv']['Difference of meridional parts']), dmp, half(1) + 1e-3, ctx)
        T.check('rhumb is never shorter than the great circle', num(r['ids']['r_rh']) >= num(r['ids']['r_gc']) - 0.11, ctx)
        save = rd - g; sv = r['kv']['Great circle saves']
        if save >= 0.06: T.close('saving (nm)', num(sv), save, half(1) + 1e-3, ctx); T.close('saving (%)', nums(sv)[1], save / rd * 100, half(1) + 1e-3, ctx)
        elif save < 0.04: T.eq('no saving', sv, 'Nothing on this leg', ctx)
        sd = sph_dist(A[0], A[1], B[0], B[1])
        T.close('exam method distance (nm, 1 dp)', num(r['kv']['Exam method (sphere): distance']), sd, half(1) + 5e-4, ctx)
        if not anti and sd > 0.5:
            T.ang('exam method initial course', num(r['kv']['Exam method (sphere): initial course']), SPH.inv(A[1], A[0], B[1], B[0])[0], half(1) + 0.002 + 0.03 / sd, ctx)
        vs = r['kv'].get('Vertex')
        if vs and not anti and sd > 30:
            (vn, vso), d = vertex(A[0], A[1], B[0], B[1])
            if vs.startswith('At the pole'): T.check('the pole is named only when the vertex is within 0.6 nm of it', abs(vn[0]) > 89.99 - 1e-6, vs + ' true %r %s' % (vn, ctx))
            elif abs(vn[0]) > 89.99 + 1e-6: T.check('vertex at the pole', False, vs + ctx)
            elif abs(vn[0]) > 0.05:
                lat, lon = vparse(vs); outside = 'outside the track' in vs
                dN = sph_dist(lat, lon, vn[0], vn[1]); dS = sph_dist(lat, lon, vso[0], vso[1])
                T.check('vertex is a true highest-latitude point of the circle (within 0.25 nm)', min(dN, dS) < 0.25 + 0.3 / max(math.cos(math.radians(vn[0])), 0.02) * 0.05, 'shown %s north %r south %r %s' % (vs, vn, vso, ctx))
                near_edge = min(abs(sph_dist(A[0], A[1], *v[:2])) for v in (vn, vso)) < 0.3 or min(abs(sph_dist(B[0], B[1], *v[:2])) for v in (vn, vso)) < 0.3
                if not near_edge:
                    T.eq('vertex on or outside the leg', outside, not (vn[2] or vso[2]), 'shown %s north %r south %r %s' % (vs, vn, vso, ctx))
                    if vn[2] or vso[2]: T.check('the vertex shown is the one the leg passes', (dN < dS) == bool(vn[2]) or (vn[2] and vso[2]), vs + ctx)
    return T.report()

ZONES = [-12, -11, -10, -9.5, -9, -8, -7, -6, -5, -4, -3.5, -3, -2, -1, 0, 1, 2, 3, 3.5, 4, 4.5, 5, 5.5, 5.75, 6, 6.5, 7, 8, 8.75, 9, 9.5, 10, 10.5, 11, 12, 12.75, 13, 14]
def stamp(t): return t.strftime('%a ') + str(t.day) + t.strftime(' %b %Y, %H:%M')
def rmin(x):
    """Minutes rounded half up, plus whether x sits exactly on a half minute."""
    return math.floor(x + F(1, 2)), (x - math.floor(x)) == F(1, 2)
def dur(hours):
    mins, _ = rmin(hours * 60); d, h, m = mins // 1440, mins % 1440 // 60, mins % 60
    return ('%d d %02d h %02d min' % (d, h, m)) if d else ('%d h %02d min' % (h, m))
def fz(z): return F(str(z))
def eta(n, rng):
    T = Tally('ETA, required speed, speed-distance-time (page) vs exact date arithmetic'); cases = []; meta = []
    epoch = dt.datetime(2000, 1, 1)
    for i in range(n):
        mode = ['eta', 'spd', 'sdt'][i % 3]
        day = dt.date(2024, 1, 1) + dt.timedelta(days=rng.randrange(0, 365 * 12)); hh, mm = rng.randrange(24), rng.randrange(60); dz, az = rng.choice(ZONES), rng.choice(ZONES)
        dist = rng.choice(['%d' % rng.randrange(1, 9000), '%.1f' % rng.uniform(0.5, 6000)])
        if mode == 'eta':
            sp = '%.1f' % rng.uniform(0.5, 30)
            cases.append({'seg': {'mode': 'eta'}, 'sel': {'dzone': str(dz), 'azone': str(az)}, 'set': {'dist': dist, 'speed': sp, 'ddate': day.isoformat(), 'dtime': '%02d:%02d' % (hh, mm)}})
            meta.append((mode, day, hh, mm, dz, az, F(dist), F(sp)))
        elif mode == 'spd':
            aday = day + dt.timedelta(days=rng.randrange(0, 30)); ah, am = rng.randrange(24), rng.randrange(60)
            cases.append({'seg': {'mode': 'spd'}, 'sel': {'dzone': str(dz), 'azone': str(az)}, 'set': {'dist': dist, 'ddate': day.isoformat(), 'dtime': '%02d:%02d' % (hh, mm), 'adate': aday.isoformat(), 'atime': '%02d:%02d' % (ah, am)}})
            meta.append((mode, day, hh, mm, dz, az, F(dist), aday, ah, am))
        else:
            d2 = '%.1f' % rng.uniform(0, 5000); s2 = '%.1f' % rng.uniform(0.5, 30); th = rng.randrange(0, 400); tm = rng.randrange(0, 60); blank = rng.choice('dst')
            if blank != 't' and th == 0 and tm == 0: tm = 15
            cases.append({'seg': {'mode': 'sdt'}, 'set': {'d2': '' if blank == 'd' else d2, 's2': '' if blank == 's' else s2, 'th': '' if blank == 't' else str(th), 'tm': '' if blank == 't' else '%02d' % tm}})
            meta.append((mode, blank, F(d2), F(s2), F(th) + F(tm, 60)))
    for c, r, m in zip(cases, drive('eta-speed-distance-time-calculator', cases), meta):
        ctx = str(c.get('set')) + str(c.get('sel'))
        if m[0] == 'eta':
            _, day, hh, mm, dz, az, dist, sp = m; hours = dist / sp
            dep_utc_min = F((dt.datetime(day.year, day.month, day.day, hh, mm) - epoch).total_seconds() / 60).limit_denominator(1) - fz(dz) * 60
            utc_min, edge = rmin(dep_utc_min + hours * 60); loc_min, edge2 = rmin(dep_utc_min + hours * 60 + fz(az) * 60)
            ok = lambda shown, mins, e: shown in {stamp(epoch + dt.timedelta(minutes=int(mins) + k)) for k in ((0, -1) if e else (0,))}
            T.check('ETA in ship\'s time', ok(r['ids']['r_main'], loc_min, edge2), 'shown %r want %r %s' % (r['ids']['r_main'], stamp(epoch + dt.timedelta(minutes=int(loc_min))), ctx))
            T.check('ETA in UTC', ok(r['ids']['r_utc'], utc_min, edge), 'shown %r want %r %s' % (r['ids']['r_utc'], stamp(epoch + dt.timedelta(minutes=int(utc_min))), ctx))
            if (hours * 60 - math.floor(hours * 60)) != F(1, 2): T.eq('steaming time', r['ids']['r_time'], dur(hours), ctx)
            T.close('steaming hours (1 dp)', nums(r['kv']['Steaming time'])[-1], float(hours), half(1), ctx)
            T.eq('departure in UTC', r['kv']['Departure in UTC'], stamp(epoch + dt.timedelta(minutes=int(dep_utc_min))), ctx)
            T.check('zone named in the label', (r['big'][0][0] or '').endswith('(' + ('UTC' if az == 0 else 'UTC%s%d%s' % ('+' if az > 0 else '−', int(abs(az)), (':%02d' % round((abs(az) % 1) * 60)) if abs(az) % 1 else '')) + ')'), r['big'][0][0] + ctx)
        elif m[0] == 'spd':
            _, day, hh, mm, dz, az, dist, aday, ah, am = m
            hours = (F(int((dt.datetime(aday.year, aday.month, aday.day, ah, am) - dt.datetime(day.year, day.month, day.day, hh, mm)).total_seconds()), 3600) - fz(az) + fz(dz))
            if hours <= 0: T.check('arrival not after departure', any(x.startswith('crit') for x in r['msg']), ctx); continue
            T.close('required speed (kn, 1 dp)', num(r['ids']['r_main']), float(dist / hours), half(1), ctx); T.eq('time available', r['ids']['r_time'], dur(hours), ctx)
        else:
            _, blank, d2, s2, hrs = m
            if blank == 't':
                h = d2 / s2
                if (h * 60 - math.floor(h * 60)) != F(1, 2): T.eq('time from distance and speed', r['ids']['r_main'], dur(h), ctx)
                T.close('time in hours (2 dp)', num(r['sub'][0]), float(h), half(2), ctx)
            elif blank == 's': T.close('speed from distance and time (1 dp)', num(r['ids']['r_main']), float(d2 / hrs), half(1), ctx)
            else: T.close('distance from speed and time (1 dp)', num(r['ids']['r_main']), float(s2 * hrs), half(1), ctx)
    return T.report()

if __name__ == '__main__':
    rng = make_rng(4242); n = int(sys.argv[1]) if len(sys.argv) > 1 else 1500; which = sys.argv[2] if len(sys.argv) > 2 else 'both'
    bad = 0
    if which in ('both', 'gc'): bad += gc(n, rng)
    if which in ('both', 'eta'): bad += eta(max(n, 3000), rng)
    print('TOTAL FAILED', bad)

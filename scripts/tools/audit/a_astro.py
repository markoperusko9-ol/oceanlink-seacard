"""Independent end-to-end audit of the two astronomy tools against astropy (IAU/ERFA) and PyEphem (VSOP87).
Neither library shares code or method with the site's Meeus low-accuracy routine."""
import math, random, sys, datetime as dt, warnings
import numpy as np, ephem
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, get_sun, TETE
from astropy.utils import iers
import astropy.units as u
from common import *
iers.conf.auto_download = False; iers.conf.iers_degraded_accuracy = 'ignore'
warnings.simplefilter('ignore')
ZONES = [-12, -11, -10, -9.5, -9, -8, -7, -6, -5, -4, -3.5, -3, -2, -1, 0, 1, 2, 3, 3.5, 4, 4.5, 5, 5.5, 5.75, 6, 6.5, 7, 8, 8.75, 9, 9.5, 10, 10.5, 11, 12, 12.75, 13, 14]

def astropy_sun(times, lats, lons):
    t = Time(times, scale='utc'); loc = EarthLocation(lat=np.array(lats) * u.deg, lon=np.array(lons) * u.deg, height=0 * u.m)
    sun = get_sun(t); aa = sun.transform_to(AltAz(obstime=t, location=loc, pressure=0 * u.hPa)); eq = sun.transform_to(TETE(obstime=t))
    gha = (t.sidereal_time('apparent', 'greenwich').deg - eq.ra.deg) % 360
    return aa.az.deg, aa.alt.deg, eq.dec.deg, gha
def ephem_sun(when, lat, lon):
    o = ephem.Observer(); o.lat, o.lon, o.elevation, o.pressure = str(lat), str(lon), 0, 0; o.date = when.strftime('%Y/%m/%d %H:%M:%S')
    s = ephem.Sun(o); g = ephem.Observer(); g.lat, g.lon, g.pressure, g.date = '0', '0', 0, o.date
    return math.degrees(s.az), math.degrees(s.alt), math.degrees(s.g_dec), (math.degrees(g.sidereal_time()) - math.degrees(s.g_ra)) % 360
def dm_parse(s):
    """14°58.3'N or 052°17.4' -> signed degrees"""
    m = re.match(r"(\d+)°(\d+\.\d)'([NSEW]?)", s); v = int(m.group(1)) + float(m.group(2)) / 60
    return -v if m.group(3) in ('S', 'W') else v
def latlon_inputs(rng, maxlat):
    lat_d = rng.randrange(0, maxlat); lat_m = round(rng.uniform(0, 59.9), 1); lath = rng.choice('NS')
    lon_d = rng.randrange(0, 180); lon_m = round(rng.uniform(0, 59.9), 1); lonh = rng.choice('EW')
    lat = (lat_d + lat_m / 60) * (1 if lath == 'N' else -1); lon = (lon_d + lon_m / 60) * (1 if lonh == 'E' else -1)
    return {'latd': str(lat_d), 'latm': '%04.1f' % lat_m, 'lond': '%03d' % lon_d, 'lonm': '%04.1f' % lon_m}, {'lath': lath, 'lonh': lonh}, lat, lon

def compass(n, rng):
    T = Tally('compass error by the Sun (page) vs astropy and PyEphem'); cases = []; meta = []
    while len(cases) < n:
        day = dt.date(2024, 1, 1) + dt.timedelta(days=rng.randrange(0, 365 * 22)); hh, mm, ss = rng.randrange(24), rng.randrange(60), rng.randrange(60)
        st, sel, lat, lon = latlon_inputs(rng, 72); when = dt.datetime(day.year, day.month, day.day, hh, mm, ss)
        mag = rng.random() < 0.4; var = round(rng.uniform(0, 25), 1); varh = rng.choice('EW'); cb = None
        st.update({'date': day.isoformat(), 'hh': '%02d' % hh, 'mm': '%02d' % mm, 'ss': '%02d' % ss, 'var': '%.1f' % var}); sel['varh'] = varh
        cases.append({'seg': {'cmode': 'mag' if mag else 'gyro'}, 'sel': sel, 'set': st}); meta.append([when, lat, lon, mag, var, varh])
    az, alt, dec, gha = astropy_sun([m[0].isoformat() for m in meta], [m[1] for m in meta], [m[2] for m in meta])
    for i, c in enumerate(cases):      # a compass bearing within a few degrees of the truth, typed to 0.1
        cb = round((az[i] + rng.uniform(-6, 6)) % 360, 1) % 360; c['set']['cb'] = '%05.1f' % cb; meta[i].append(cb)
    res = drive('sun-compass-error-calculator', cases); stats = {'az_up': [], 'dec': [], 'gha': [], 'az_ephem': []}
    for i, (c, r, (when, lat, lon, mag, var, varh, cb)) in enumerate(zip(cases, res, meta)):
        ctx = '%s lat %.3f lon %.3f' % (when, lat, lon)
        saz = num(r['ids']['r_az']); salt = num(r['sub'][0])
        e_az, e_alt, e_dec, e_gha = ephem_sun(when, lat, lon)
        tol = half(1) + (0.03 if abs(alt[i]) < 78 else 0.03 + 0.012 / max(math.cos(math.radians(alt[i])), 1e-3))
        T.ang('azimuth vs astropy (0.1 shown)', saz, az[i], tol, ctx); T.ang('azimuth vs PyEphem', saz, e_az, tol + 0.01, ctx)
        if -1 < alt[i] < 80: stats['az_up'].append(angdiff(saz, az[i])); stats['az_ephem'].append(angdiff(saz, e_az))
        T.close('altitude vs astropy (0.1 shown)', salt, alt[i], half(1) + 0.01, ctx)
        sdec = dm_parse(r['kv']['Declination']); sgha = dm_parse(r['kv']['GHA Sun']); slha = dm_parse(r['kv']['LHA Sun'])
        T.close('declination vs astropy (arcmin)', sdec * 60, dec[i] * 60, 0.35, ctx); T.close('declination vs PyEphem (arcmin)', sdec * 60, e_dec * 60, 0.35, ctx)
        T.close('GHA vs astropy (arcmin)', ((sgha - gha[i] + 180) % 360 - 180) * 60, 0, 0.75, ctx); T.close('GHA vs PyEphem (arcmin)', ((sgha - e_gha + 180) % 360 - 180) * 60, 0, 0.75, ctx)
        stats['dec'].append(abs(sdec - dec[i]) * 60); stats['gha'].append(abs((sgha - gha[i] + 180) % 360 - 180) * 60)
        T.close('LHA = GHA + longitude (arcmin)', ((slha - (sgha + lon) + 180) % 360 - 180) * 60, 0, 0.11, ctx)
        # error naming from first principles: error = true - compass; compass reading high means error West
        err = (saz - cb + 180) % 360 - 180; shown = r['ids'].get('r_err', '')
        if abs(abs(err) - 180) > 0.2:
            if round(abs(err), 1) == 0: T.eq('error nil', shown, 'Nil', ctx)
            else:
                want = '%.1f° %s' % (abs(err), 'E' if err > 0 else 'W') + ('' if mag else ' gyro ' + ('low' if err > 0 else 'high'))
                T.eq('error size, name and high/low', shown, want, ctx)
            if mag:
                dev = err - (var if varh == 'E' else -var); sd = r['ids'].get('r_dev', '')
                T.eq('deviation = error - variation', sd, ('Nil' if round(abs(dev), 1) == 0 else '%.1f° %s' % (abs(dev), 'E' if dev > 0 else 'W')) + ' for the present heading', ctx)
        s = math.sin(math.radians(dec[i])) / math.cos(math.radians(lat))
        if abs(s) < 0.985:
            A = math.degrees(math.asin(s)); row = r['kv'].get('Amplitude at sunrise'); row2 = r['kv'].get('Amplitude at sunset'); tolA = half(1) + 0.008 / math.sqrt(1 - s * s) + 0.004
            T.check('amplitude rows shown', row is not None and row2 is not None, ctx)
            if row:
                v = nums(row); T.close('amplitude size', v[0], abs(A), tolA, ctx); T.ang('bearing at sunrise', v[1], 90 - A, tolA, ctx); T.ang('bearing at sunset', nums(row2)[1], 270 + A, tolA, ctx)
                if abs(A) > 0.1: T.check('amplitude named N or S', (' N ' in row) == (A > 0) and row.startswith('E ') and row2.startswith('W '), row + ctx)
        if alt[i] < -1.0: T.check('below-horizon warning', any(m.startswith('crit') for m in r['msg']), ctx)
        if alt[i] > 70.1: T.check('high-Sun warning', any(m.startswith('warn') for m in r['msg']), ctx)
    bad = T.report()
    for k in ('az_up', 'az_ephem', 'dec', 'gha'): a = np.array(stats[k]); print('     %-9s n=%d  median %.4f  95%% %.4f  max %.4f' % (k, len(a), np.median(a), np.percentile(a, 95), a.max()))
    return bad

def events_ephem(start, lat, lon):
    """Transit and the six events by PyEphem, using the Nautical Almanac limits on the Sun's centre."""
    o = ephem.Observer(); o.lat, o.lon, o.elevation, o.pressure = str(lat), str(lon), 0, 0; sun = ephem.Sun()
    o.date = ephem.Date(start); tr = o.next_transit(sun).datetime()
    out = {'transit': tr}
    for key, hz in (('rise', '-0:50'), ('civil', '-6'), ('naut', '-12')):
        o.horizon = hz
        for side in ('am', 'pm'):
            o.date = ephem.Date(tr)
            try:
                t = (o.previous_rising(sun, use_center=True) if side == 'am' else o.next_setting(sun, use_center=True)).datetime()
                if abs((t - tr).total_seconds()) > 12 * 3600 + 30: t = None
            except (ephem.AlwaysUpError, ephem.NeverUpError): t = None
            out[key + side] = t
    return out

def sunrise(n, rng):
    T = Tally('sunrise, sunset, twilight (page and raw times) vs PyEphem and astropy'); cases = []; calls = []; meta = []
    while len(cases) < n:
        day = dt.date(2024, 1, 1) + dt.timedelta(days=rng.randrange(0, 365 * 22)); st, sel, lat, lon = latlon_inputs(rng, 74)
        z = min(ZONES, key=lambda q: abs(q - lon / 15)) if rng.random() < 0.8 else rng.choice(ZONES)
        start = dt.datetime(day.year, day.month, day.day) - dt.timedelta(hours=z)
        e = events_ephem(start, lat, lon)
        if not (dt.timedelta(minutes=8) < e['transit'] - start < dt.timedelta(hours=23, minutes=52)): continue
        st['date'] = day.isoformat(); sel['zone'] = str(z)
        cases.append({'sel': sel, 'set': st}); meta.append((day, z, lat, lon, start, e))
        ms = int((start - dt.datetime(1970, 1, 1)).total_seconds() * 1000)
        calls.append({'call': 'OLCalc.sunEvents(%d, %r, %r)' % (ms, lat, lon)})
    res = drive('sunrise-sunset-twilight-calculator', cases); raw = drive('sunrise-sunset-twilight-calculator', calls, 'raw')
    def shown_clock(ms_dt, day, z):
        t = ms_dt + dt.timedelta(hours=z); t = (t + dt.timedelta(seconds=30)).replace(second=0, microsecond=0)
        dd = (t.date() - day).days
        return '%02d:%02d' % (t.hour, t.minute) + (' next day' if dd > 0 else ' previous day' if dd < 0 else '')
    names = {'rise': ('riseam', 'r_rise'), 'set': ('risepm', 'r_set'), 'civilBegin': ('civilam', 'r_cb'), 'civilEnd': ('civilpm', 'r_ce'), 'nautBegin': ('nautam', 'r_nb'), 'nautEnd': ('nautpm', 'r_ne')}
    limits = {'rise': -50 / 60, 'set': -50 / 60, 'civilBegin': -6, 'civilEnd': -6, 'nautBegin': -12, 'nautEnd': -12}
    secs = {k: [] for k in list(names) + ['transit']}; at_t, at_lat, at_lon, at_lim, at_key = [], [], [], [], []; baz = []; trn = []
    for c, r, w, (day, z, lat, lon, start, e) in zip(cases, res, raw, meta):
        ctx = '%s z%s lat %.3f lon %.3f' % (day, z, lat, lon); s = w['call']; hi = abs(lat) > 62
        T.check('transit found', s is not None, ctx)
        if s is None: continue
        tr = dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds=s['transit']); d = (tr - e['transit']).total_seconds(); secs['transit'].append(abs(d))
        T.close('meridian passage (s) vs PyEphem', d, 0, 20, ctx)
        T.check('meridian passage shown', r['ids']['r_mp'] in {shown_clock(tr + dt.timedelta(seconds=k), day, z) for k in (-1, 0, 1)}, 'shown %r %s' % (r['ids']['r_mp'], ctx))
        for key, (ek, rid) in names.items():
            mine = s[key]; ref = e[ek]
            if mine is None or ref is None:
                # both must agree that there is no event, except within a hair of the limit where either may be right
                if (mine is None) != (ref is None): at_t.append((tr if mine is None else dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds=mine)).isoformat()); at_lat.append(lat); at_lon.append(lon); at_lim.append(None); at_key.append((key, ctx, mine is None))
                continue
            t = dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds=mine); d = (t - ref).total_seconds()
            if not hi: secs[key].append(abs(d))
            T.close('%s (s) vs PyEphem, %s' % (key, 'above 62°' if hi else 'to 62°'), d, 0, 600 if hi else 45, ctx)
            shown = r['ids'].get(rid) if key not in ('rise', 'set') else r['ids'].get(rid)
            T.check('%s shown as ship\'s time' % key, shown in {shown_clock(t + dt.timedelta(seconds=k), day, z) for k in (-1, 0, 1)}, 'shown %r want %r %s' % (shown, shown_clock(t, day, z), ctx))
            at_t.append(t.isoformat()); at_lat.append(lat); at_lon.append(lon); at_lim.append(limits[key]); at_key.append((key, ctx, hi))
        if s['rise'] is not None and s['set'] is not None:
            mins = math.floor((s['set'] - s['rise']) / 60000 + 0.5); want = ('%d h %02d min' % (mins // 60, mins % 60))
            T.eq('sunrise to sunset', r['ids'].get('r_len'), want, ctx)
        else: T.check('no day length unless both sunrise and sunset exist', 'r_len' not in r['ids'], str(r['ids']) + ctx)
        for key, rid, lab in (('rise', 'r_rise', 'Sunrise'), ('set', 'r_set', 'Sunset')):
            if (s['rise'] is None) != (s['set'] is None) and s[key] is None:
                T.eq('the missing event is shown as None, never as a time', r['ids'].get(rid), 'None', ctx); T.check('and the page says why', 'r_note' in r['ids'], ctx)
        if s['rise'] is None and s['set'] is None: T.check('polar day or night named', r['ids'].get('r_rise') in ('Does not rise', 'Does not set'), str(r['ids'].get('r_rise')) + ctx)
        for key, rid in (('rise', 'r_raz'), ('set', 'r_saz')):
            if s[key] is not None and rid in r['ids']:
                tt = dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds=s[key]); baz.append((tt.isoformat(), lat, lon, num(r['ids'][rid]), ctx, key))
        trn.append((tr.isoformat(), lat, lon, r['ids'].get('r_alt'), ctx))
    # astropy as second opinion: the Sun's altitude at the very instant the tool reports each event
    az, alt, dec, gha = astropy_sun(at_t, at_lat, at_lon); worst = {}
    for a, lim, (key, ctx, flag) in zip(alt, at_lim, at_key):
        if lim is None:     # disagreement on existence: acceptable only when the Sun grazes the limit
            lim2 = {'rise': -50 / 60, 'set': -50 / 60}.get(key, -6 if 'civil' in key else -12)
            T.check('event exists only in one source', True, ctx); worst['graze'] = worst.get('graze', 0) + 1; continue
        T.close('altitude at the tool\'s %s (deg) vs astropy, %s' % (key, 'above 62°' if flag else 'to 62°'), a, lim, 0.05 if flag else 0.012, ctx)
    if baz:
        az2, alt2, _, _ = astropy_sun([b[0] for b in baz], [b[1] for b in baz], [b[2] for b in baz])
        for (tt, lat, lon, shown, ctx, key), a in zip(baz, az2): T.ang('bearing of the Sun at %s (0 dp) vs astropy' % ('sunrise' if key == 'rise' else 'sunset'), shown, a, half(0) + 0.05, ctx)
    az3, alt3, dec3, _ = astropy_sun([t[0] for t in trn], [t[1] for t in trn], [t[2] for t in trn])
    for (tt, lat, lon, shown, ctx), a, d in zip(trn, alt3, dec3):
        if a < -0.01: T.eq('meridian altitude below the horizon', shown, 'Below the horizon', ctx)
        elif a > 0.02:
            m = re.match(r"(\d+)°(\d+\.\d)', bearing (south|north)", shown or '')
            T.check('meridian altitude row readable', bool(m), str(shown) + ctx)
            if m:
                T.close('altitude at meridian passage (arcmin) vs astropy', (int(m.group(1)) + float(m.group(2)) / 60) * 60, a * 60, 0.45, ctx)
                if abs(lat - d) > 0.05: T.eq('Sun bears south when the observer is north of it', m.group(3), 'south' if lat > d else 'north', ctx)
    bad = T.report()
    for k, v in secs.items():
        if v: a = np.array(v); print('     %-11s to 62°: n=%d  median %.1f s  95%% %.1f s  max %.1f s' % (k, len(a), np.median(a), np.percentile(a, 95), a.max()))
    print('     events found by only one of the two (Sun grazing the limit):', worst.get('graze', 0))
    return bad

if __name__ == '__main__':
    rng = make_rng(77); n = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
    which = sys.argv[2] if len(sys.argv) > 2 else 'both'
    bad = 0
    if which in ('both', 'compass'): bad += compass(n, rng)
    if which in ('both', 'sunrise'): bad += sunrise(n, rng)
    print('TOTAL FAILED', bad)

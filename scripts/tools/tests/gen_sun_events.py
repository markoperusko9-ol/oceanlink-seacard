"""Builds fixtures_sun_events.json: sunrise, sunset, twilight and meridian passage times from astropy (ERFA),
found independently of the JavaScript: altitude on a one-minute grid for 12 hours either side of the meridian
passage, then linear interpolation inside the minute where a limit is crossed.
Run:  python3 gen_sun_events.py   (needs: pip install astropy)"""
import json, random, warnings
warnings.filterwarnings("ignore")
from datetime import datetime, timedelta, timezone
import numpy as np
from astropy.utils import iers
iers.conf.auto_download = False
iers.conf.iers_degraded_accuracy = "ignore"
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, get_sun
import astropy.units as u

random.seed(20261125)
LIMITS = {'rise': -50 / 60, 'civil': -6.0, 'naut': -12.0}

def alt_lha(ms, lat, lon):
    t = Time(np.asarray(ms) / 1000.0, format='unix')
    loc = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=0 * u.m)
    sun = get_sun(t)
    alt = sun.transform_to(AltAz(obstime=t, location=loc, pressure=0 * u.hPa)).alt.deg
    tete = sun.transform_to('tete')
    lha = ((t.sidereal_time('apparent', 'greenwich').deg - tete.ra.deg + lon + 180) % 360) - 180
    return alt, lha

def crossing(ts, ys):  # first index pair with a sign change, linear interpolation
    for i in range(len(ts) - 1):
        if (ys[i] < 0) != (ys[i + 1] < 0):
            return ts[i] + (ts[i + 1] - ts[i]) * (0 - ys[i]) / (ys[i + 1] - ys[i])
    return None

out = []
base = datetime(2026, 1, 1, tzinfo=timezone.utc)
cases = [(random.randint(0, 14 * 365), random.uniform(-62, 62), random.uniform(-180, 180)) for _ in range(260)]
cases += [(d, la, lo) for d in (171, 355, 80) for la, lo in ((68, 20), (-68, -60), (78, 15), (0, 0), (65.5, -150))]
for day, lat, lon in cases:
    zone = round(lon / 15)
    start = int((base + timedelta(days=day)).timestamp() * 1000) - zone * 3600000
    grid = np.arange(start - 60000, start + 86400000 + 120000, 60000)
    _, lha = alt_lha(grid, lat, lon)
    transit = None
    for i in range(len(grid) - 1):
        if lha[i] < 0 <= lha[i + 1] and lha[i + 1] - lha[i] < 90:
            transit = grid[i] + 60000 * (0 - lha[i]) / (lha[i + 1] - lha[i]); break
    if transit is None:
        continue
    g2 = transit + np.arange(-720, 721) * 60000.0
    alt, _ = alt_lha(g2, lat, lon)
    rec = dict(start=start, lat=lat, lon=lon, transit=float(transit), transitAlt=float(alt[720]))
    for name, lim in LIMITS.items():
        am_t, am_y = g2[720::-1], alt[720::-1] - lim      # going back from the passage
        pm_t, pm_y = g2[720:], alt[720:] - lim
        m = crossing(am_t, am_y) if am_y[0] >= 0 else None
        e = crossing(pm_t, pm_y) if pm_y[0] >= 0 else None
        rec[name + 'AM'] = None if m is None else float(m)
        rec[name + 'PM'] = None if e is None else float(e)
    out.append(rec)
json.dump(out, open('fixtures_sun_events.json', 'w'))
print(len(out), 'cases', sum(1 for r in out if r['riseAM'] is None), 'without a sunrise')

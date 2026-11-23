"""Builds fixtures.json: independent reference values the JavaScript maths is tested against.
Sun: astropy (ERFA). Geodesic: PROJ (pyproj). Rhumb line: numerical integration with mpmath.
Run:  python3 gen_fixtures.py   (needs: pip install astropy pyproj mpmath)"""
import json, math, random, warnings
warnings.filterwarnings("ignore")
from datetime import datetime, timedelta, timezone
import numpy as np
from astropy.utils import iers
iers.conf.auto_download = False
iers.conf.iers_degraded_accuracy = "ignore"
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, get_sun
import astropy.units as u
from pyproj import Geod
import mpmath as mp

random.seed(20261123)
out = {}

# ---- Sun: 1500 random times 2026-2040, positions 75S-75N, any altitude ----
start = datetime(2026, 1, 1, tzinfo=timezone.utc)
cases = []
for _ in range(1500):
    dt = start + timedelta(seconds=random.randint(0, int(15 * 365.25 * 86400)))
    cases.append((dt, random.uniform(-75, 75), random.uniform(-180, 180)))
t = Time([c[0] for c in cases])
loc = EarthLocation(lat=[c[1] for c in cases] * u.deg, lon=[c[2] for c in cases] * u.deg, height=0 * u.m)
sun = get_sun(t)
aa = sun.transform_to(AltAz(obstime=t, location=loc, pressure=0 * u.hPa))
tete = sun.transform_to('tete')
gast = t.sidereal_time('apparent', 'greenwich').deg
gha = (gast - tete.ra.deg) % 360
out['sun'] = [dict(ms=int(c[0].timestamp() * 1000), lat=c[1], lon=c[2], az=float(a), alt=float(al),
                   dec=float(d), gha=float(g))
              for c, a, al, d, g in zip(cases, aa.az.deg, aa.alt.deg, tete.dec.deg, gha)]

# ---- Geodesic on WGS84 (as ECDIS): random pairs plus hard near-antipodal ones ----
g = Geod(ellps='WGS84')
pairs = [(random.uniform(-80, 80), random.uniform(-180, 180), random.uniform(-80, 80), random.uniform(-180, 180))
         for _ in range(400)]
for _ in range(60):  # nearly antipodal
    la, lo = random.uniform(-60, 60), random.uniform(-180, 180)
    pairs.append((la, lo, -la + random.uniform(-0.4, 0.4), ((lo + 180 + random.uniform(-0.4, 0.4) + 180) % 360) - 180))
geo = []
for la1, lo1, la2, lo2 in pairs:
    az12, az21, d = g.inv(lo1, la1, lo2, la2)
    geo.append(dict(lat1=la1, lon1=lo1, lat2=la2, lon2=lo2, distNm=d / 1852.0,
                    initial=az12 % 360, final=(az21 + 180) % 360))
out['geodesic'] = geo

# ---- Rhumb line on WGS84 by direct numerical integration (30 significant figures) ----
mp.mp.dps = 30
a = mp.mpf(6378137); f = 1 / mp.mpf('298.257223563'); e2 = f * (2 - f)
def psi(lat):   # isometric latitude
    return mp.quad(lambda p: (1 - e2) / ((1 - e2 * mp.sin(p) ** 2) * mp.cos(p)), [0, mp.radians(lat)])
def marc(lat):  # meridian arc
    return mp.quad(lambda p: a * (1 - e2) / (1 - e2 * mp.sin(p) ** 2) ** mp.mpf(1.5), [0, mp.radians(lat)])
rh = []
rp = [(random.uniform(-75, 75), random.uniform(-180, 180), random.uniform(-75, 75), random.uniform(-180, 180))
      for _ in range(150)]
rp += [(35, 140, 37, -123), (50, -5, 50, -60), (0, 10, 0, 100), (-33.9, 18.4, -34.6, -58.4),
       (10, 20, 60, 20), (51.5, -0.1, 51.5000001, 3.0), (20, 179, 21, -179)]
for la1, lo1, la2, lo2 in rp:
    dl = mp.radians(((lo2 - lo1 + 180) % 360) - 180)
    dpsi = psi(la2) - psi(la1)
    course = mp.degrees(mp.atan2(dl, dpsi)) % 360
    if la1 == la2:
        s = mp.sin(mp.radians(la1))
        dist = abs(dl) * a * mp.cos(mp.radians(la1)) / mp.sqrt(1 - e2 * s * s)
    else:
        dist = abs(marc(la2) - marc(la1)) * mp.sqrt(dl ** 2 + dpsi ** 2) / abs(dpsi)
    rh.append(dict(lat1=la1, lon1=lo1, lat2=la2, lon2=lo2, distNm=float(dist / 1852), course=float(course),
                   dmp=float(dpsi * 10800 / mp.pi)))
out['rhumb'] = rh
out['mp'] = [dict(lat=l, mp=float(psi(l) * 10800 / mp.pi)) for l in (10, 35, 37, 45, 60, 75, -52.5)]

json.dump(out, open('fixtures.json', 'w'))
print({k: len(v) for k, v in out.items()})

"""Builds fixtures_psychro.json: dew point and relative humidity from wet and dry bulb readings worked by
psychrolib (the ASHRAE Handbook method), a different route from the psychrometer formula the tool uses.
Run:  python3 gen_psychro.py   (needs: pip install psychrolib)"""
import json
import psychrolib as ps
ps.SetUnitSystem(ps.SI)
out = []
for dry10 in range(20, 451, 5):
    dry = dry10 / 10
    for dep in (0, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 12):
        wet = dry - dep
        if wet < 0:
            continue
        try:
            td = ps.GetTDewPointFromTWetBulb(dry, wet, 101325)
            rh = ps.GetRelHumFromTWetBulb(dry, wet, 101325) * 100
        except Exception:
            continue
        out.append(dict(dry=dry, wet=wet, dew=td, rh=rh))
json.dump(out, open('fixtures_psychro.json', 'w'))
print(len(out), 'cases')

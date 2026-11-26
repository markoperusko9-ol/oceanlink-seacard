# Independent audit of the seafarer tools

Built on 26 Nov 2026 to answer one question: can a seafarer rely on the 20 calculators under `tools/`?

The audit does not read the site's maths. It opens each real page in headless Chrome, types figures in the way a user
would, reads back what the page prints, and compares that with references that share no code with the site.

## Run it

```
pip install astropy ephem pyproj pint psychrolib scipy mpmath numpy
NODE_PATH=<folder holding puppeteer-core>/node_modules python3 scripts/tools/audit/run_all.py
```

Exit code 0 means every check passed. A full run takes about three minutes and makes about 430,000 checks.

| Setting | What it does |
| --- | --- |
| `OL_AUDIT_SEED=<n>` | A fresh set of random cases. Without it the same cases run every time. |
| `OL_AUDIT_ROUND=1` | Round figures only: courses of 000, 045, 090, speeds of 5, 10, 15, minutes of 00, 10, 20. |
| `OL_AUDIT_PORT=<n>` | Port for the local copy of the site (default 8766). It is started if nothing answers there. |
| `CHROME_PATH=<path>` | Chrome to drive (default `/usr/bin/google-chrome`). |
| `TZ=<zone>` | Time zone of the device clock, to show the date tools do not depend on it. |

One module alone: `python3 scripts/tools/audit/a_ship.py 2000 squat` (number of cases, then the parts wanted).

## What each module checks

| Module | Tools | Reference |
| --- | --- | --- |
| `a_vectors.py` | True wind, CPA and TCPA, set and drift, course to steer | Vector arithmetic written separately, plus a brute-force search for the closest approach |
| `a_astro.py` | Compass error by the Sun, sunrise, sunset and twilight | astropy (IAU/ERFA) and PyEphem (VSOP87) |
| `a_geo.py` | Great circle and rhumb line, ETA and required speed | PROJ on WGS84, numerical integration of the meridian, exact date arithmetic |
| `a_ship.py` | Squat and UKC, slip, fuel, FWA and DWA, list and GM, unit converter, rate of turn, horizon, rolling period | Exact fractions, pint, geometry, first-principles wave encounter |
| `a_cargo.py` | Bunker quantity, draught survey, LNG, dew point | Three official Table 54B tables (440 printed factors), the 1980 procedure in exact decimals, a surveyor's sheet in exact decimals, the UK P&I Club example, the IGU table, ASHRAE and WMO formulas |
| `a_edges.py` | All of the above, on their limits | Exact decimal arithmetic. See below |
| `a_official.py` | Sunrise, meridian passage and sunset | The Hong Kong Observatory Almanac 2026, read off its printed monthly pages: 122 days, 366 times |
| `a_examples.py` | Every worked example printed on the pages | The page itself, and astropy for the Sun |
| `a_fuzz.py` | All 20 pages | Bad, empty and absurd input: a page may refuse it, but must never print NaN, hang or throw |

## Why there is a module for limits

Random figures almost never land exactly on a limit. People's figures do, because people type round numbers:
`10.3 + 0.7 - 10.1 - 0.7 - 0.2` is a net clearance of exactly nil, but binary arithmetic makes it `4e-16`.

The first audit passed 370,000 random checks and still missed these, because none of its cases sat on a limit. A
second set of random cases found the first one by chance. `a_edges.py` and the round-figures mode were then written
to look for the rest, and found:

- a net UKC of exactly 0.00 m printed without the grounding warning;
- a fluid GM of exactly 0.00 m printed beside a list of 90 degrees instead of the unstable warning;
- fuel running out exactly on arrival raising "Short by 0.0 t";
- a stream abeam as fast as the ship giving a course to steer with 0.0 kn made good;
- a rolling ratio of exactly 1.10 or 0.55 not flagged;
- a wind of exactly 3.5 kn coming out as Force 1 on some headings and Force 2 on others;
- a corrected draught of exactly 10.09875 m rounded down to 10.0987, not up as on a surveyor's sheet;
- a survey column that did not add up (19,894.37 + 5.74 + 0.01 printed as 19,900.11);
- a steaming time of 3.5 minutes shown as 3 while the ETA beside it moved on by 4.

Three rules came out of it, and the audit holds the pages to all three:

1. **Figures are rounded half up on the decimal value, as on paper** (`roundHalfUp` in `tools/assets/calc.js`).
2. **A warning follows the figure printed beside it.** If the page prints a net UKC of 0.00 m, it shows the
   grounding warning; if it prints a ratio of 1.40, it does not say the ratio is outside 1.1 to 1.4.
3. **Sheets are worked line by line from the figures as written.** The draught survey and the bunker calculation
   take each line from the line printed above it, so a surveyor with a calculator gets the same column.

## When a check fails

Read the case printed under `FAIL`, type it into the page, and work it by hand. Three times in the first audit the
page was right and the audit was wrong (a great-circle vertex just astern of the departure point, a vertex within a
mile of the pole, and two nearly opposite points on the equator, where the shortest way on the ellipsoid really does
leave the equator). Fix whichever is wrong, add the case to `scripts/tools/tests/`, and run the whole audit again.

"""Runs the whole independent audit of the 20 seafarer tools and prints one line per tool plus the totals.

    NODE_PATH=<dir holding puppeteer-core>/node_modules python3 scripts/tools/audit/run_all.py

Exit code 0 only when every check passes. OL_AUDIT_SEED=<n> runs a fresh set of random cases."""
import subprocess, sys, re, time, os
HERE = os.path.dirname(os.path.abspath(__file__))
JOBS = [('a_vectors.py', ['3000']), ('a_astro.py', ['1500']), ('a_geo.py', ['1500']), ('a_ship.py', ['2000']), ('a_cargo.py', ['2500']), ('a_edges.py', ['600']), ('a_examples.py', []), ('a_fuzz.py', ['1500'])]
tot = bad = 0; t0 = time.time(); lines = []
for f, args in JOBS:
    r = subprocess.run([sys.executable, os.path.join(HERE, f)] + args, capture_output=True, text=True, cwd=HERE)
    out = r.stdout + r.stderr; found = 0
    for m in re.finditer(r'== (.*?): (\d+) checks, (\d+) failed', out): lines.append('%-98s %7d checks  %d failed' % (m.group(1), int(m.group(2)), int(m.group(3)))); tot += int(m.group(2)); bad += int(m.group(3)); found += 1
    for m in re.finditer(r'^(\S+)\s+(\d+) odd inputs, (\d+) bad displays', out, re.M): lines.append('%-98s %7d odd inputs  %d bad' % ('fuzz ' + m.group(1), int(m.group(2)), int(m.group(3)))); found += 1
    m = re.search(r'TOTAL odd inputs (\d+) bad displays (\d+)', out)
    if m: tot += int(m.group(1)); bad += int(m.group(2))
    if 'Traceback' in out or 'HUNG' in out or not found: lines.append('!! problem in %s: %s' % (f, out[-900:])); bad += 1
    for m in re.finditer(r'^   FAIL .*$', out, re.M): lines.append('   ' + m.group(0).strip())
    for m in re.finditer(r'^     (az_up|dec|gha|rise|set|civilBegin|civilEnd|nautBegin|nautEnd|transit|dew point.*|RH vs.*|IMO encounter.*)$', out, re.M): lines.append('      ' + m.group(1).strip())
print('\n'.join(lines)); print('TOTAL %d checks, %d failed, %.0f s' % (tot, bad, time.time() - t0))
sys.exit(1 if bad else 0)

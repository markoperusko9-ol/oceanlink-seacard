"""Shared helpers for the independent audit of the Ocean Link seafarer tools.

The audit drives the real pages in headless Chrome, the way a user would, and compares what each page displays with
references that share no code with the site (astropy, PyEphem, PROJ, pint, psychrolib, exact decimal arithmetic,
official printed tables and published worked examples)."""
import json, math, re, subprocess, os, random, sys, tempfile, atexit, socket, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
PORT = int(os.environ.get('OL_AUDIT_PORT', '8766'))
BASE = 'http://127.0.0.1:%d' % PORT
TMP = os.path.join(tempfile.gettempdir(), 'ol-tools-audit'); os.makedirs(TMP, exist_ok=True)
_served = False
def seed(base):
    """Fixed by default so a run can be repeated exactly; OL_AUDIT_SEED=<n> gives a fresh set of cases."""
    return base + int(os.environ.get('OL_AUDIT_SEED', '0'))
class RoundRandom(random.Random):
    """Draws the round figures people actually type. uniform(a, b) gives a multiple of a round step inside the range
    (15 degrees on a full circle), so courses come out as 000, 045, 090, speeds as 5, 10, 15 and minutes as 00, 10, 20.
    Round figures are where sums land exactly on a limit and where a display figure sits exactly on a half."""
    STEPS = (10000, 5000, 1000, 500, 100, 50, 10, 5, 1, 0.5, 0.1)
    def uniform(self, a, b):
        lo, hi = min(a, b), max(a, b)
        step = 15 if (lo, hi) == (0, 360) else next((s for s in self.STEPS if (hi - lo) / s >= 4), 0.1)
        k0, k1 = math.ceil(lo / step - 1e-9), math.floor(hi / step + 1e-9)
        return random.Random.uniform(self, a, b) if k1 < k0 else self.randrange(k0, k1 + 1) * step
def make_rng(base):
    """The module's random source: plain by default, round figures with OL_AUDIT_ROUND=1."""
    return (RoundRandom if os.environ.get('OL_AUDIT_ROUND') else random.Random)(seed(base))

def _up():
    s = socket.socket(); s.settimeout(0.5)
    try: s.connect(('127.0.0.1', PORT)); return True
    except OSError: return False
    finally: s.close()
def serve():
    """Serve this checkout on 127.0.0.1 unless it is already being served there, and make sure the pages under test
    are the files in this checkout and not some other copy."""
    global _served
    if _served: return
    if not _up():
        p = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        atexit.register(p.terminate)
        for _ in range(100):
            if _up(): break
            time.sleep(0.1)
        else: raise RuntimeError('could not start a local server on port %d' % PORT)
    for rel in ('tools/assets/calc.js', 'tools/assets/ui.js', 'tools/true-wind-calculator/index.html'):
        got = urllib.request.urlopen(BASE + '/' + rel, timeout=10).read()
        if got != open(os.path.join(ROOT, rel), 'rb').read():
            raise RuntimeError('port %d serves a different copy of %s than this checkout; set OL_AUDIT_PORT to a free port' % (PORT, rel))
    _served = True

def drive(slug, cases, tag=''):
    """Run cases through the real page; returns the list of results."""
    serve()
    fin = os.path.join(TMP, '%s%s_in.json' % (slug, tag)); fout = os.path.join(TMP, '%s%s_out.json' % (slug, tag))
    json.dump({'cases': cases}, open(fin, 'w'))
    r = subprocess.run(['node', os.path.join(HERE, 'drive.cjs'), slug, fin, fout], capture_output=True, text=True, timeout=400, env=dict(os.environ, OL_AUDIT_BASE=BASE))
    if r.returncode != 0:
        raise RuntimeError('driver: ' + r.stderr[:800])
    out = json.load(open(fout))
    assert not out['pageErrors'], out['pageErrors'][:3]
    assert len(out['results']) == len(cases)
    return out['results']

NUM = re.compile(r'[-−+]?\d[\d,]*\.?\d*(?:e[-+]?\d+)?')
def num(s):
    """First number in a display string ('1,234.5 nm' -> 1234.5; '−0.68 m' -> -0.68)."""
    if s is None: return None
    m = NUM.search(s.replace('−', '-'))
    return float(m.group(0).replace(',', '')) if m else None
def nums(s):
    return [float(x.replace(',', '')) for x in NUM.findall((s or '').replace('−', '-'))]
def dp(s):
    """Decimals shown in the first number of a display string."""
    m = NUM.search((s or '').replace('−', '-'))
    if not m: return None
    t = m.group(0)
    return len(t.split('.')[1]) if '.' in t else 0
def angdiff(a, b):
    return abs((a - b + 180) % 360 - 180)
def half(decimals):
    """Largest honest difference between a correctly rounded display and the exact value."""
    return 0.5 * 10 ** (-decimals) + 1e-7

class Tally:
    def __init__(self, name): self.name = name; self.n = 0; self.bad = []; self.maxd = {}
    def check(self, label, ok, detail):
        self.n += 1
        if not ok and len(self.bad) < 400: self.bad.append((label, detail))
    def close(self, label, shown, expected, tol, ctx=''):
        d = abs(shown - expected)
        self.maxd[label] = max(self.maxd.get(label, 0), d)
        self.check(label, d <= tol, 'shown %r expected %r diff %.6g tol %.3g %s' % (shown, expected, d, tol, ctx))
    def ang(self, label, shown, expected, tol, ctx=''):
        d = angdiff(shown, expected)
        self.maxd[label] = max(self.maxd.get(label, 0), d)
        self.check(label, d <= tol, 'shown %r expected %r diff %.6g tol %.3g %s' % (shown, expected, d, tol, ctx))
    def eq(self, label, shown, expected, ctx=''):
        self.check(label, shown == expected, 'shown %r expected %r %s' % (shown, expected, ctx))
    def report(self):
        print('== %s: %d checks, %d failed' % (self.name, self.n, len(self.bad)))
        for k in sorted(self.maxd): print('     max diff %-34s %.6g' % (k, self.maxd[k]))
        seen = {}
        for lab, det in self.bad:
            seen.setdefault(lab, []).append(det)
        for lab, dets in seen.items():
            print('   FAIL %s x%d' % (lab, len(dets)))
            for d in dets[:4]: print('        ', d[:300])
        return len(self.bad)

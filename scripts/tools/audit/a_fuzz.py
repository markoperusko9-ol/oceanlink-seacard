"""Fuzz every tool page with bad, odd and extreme input. A page may refuse input or show a warning, but it must never
print NaN, Infinity, undefined, null or a nonsense figure, and must never throw."""
import random, sys, re, json
from common import *
ALL = ['sun-compass-error-calculator', 'great-circle-rhumb-line-calculator', 'set-and-drift-course-to-steer-calculator', 'eta-speed-distance-time-calculator', 'true-wind-calculator',
         'cpa-tcpa-calculator', 'squat-ukc-calculator', 'propeller-slip-calculator', 'fuel-consumption-calculator', 'fwa-dwa-calculator', 'list-and-gm-calculator', 'marine-unit-converter',
         'bunker-quantity-calculator', 'draft-survey-calculator', 'lng-conversion-boil-off-calculator', 'dew-point-calculator', 'sunrise-sunset-twilight-calculator', 'rate-of-turn-calculator',
         'distance-to-horizon-calculator', 'rolling-period-gm-calculator']
JUNK = ['', '0', '-1', '-0', '+5', '.5', '5.', '1e9', '1e-9', 'abc', '1,5', ' 12 ', '12..3', '999999999', '0.0001', '0,0001', '１２', '1 000', '12,345.6', '360', '359.99', '180', '90', '60', '59.99', '0.00', '00', '1000000', '--5', '5-', 'NaN', 'Infinity', '1/2', '٣', '12°', '1.5.5']
BAD = re.compile(r'NaN|Infinity|undefined|null|\[object|function|−−|--\d')
FORM = """(function () { var f = { text: [], date: [], time: [], sel: {}, seg: {} };
 document.querySelectorAll('.calc input').forEach(function (e) { (f[e.type] || f.text).push([e.id, e.value]); });
 document.querySelectorAll('.calc select').forEach(function (e) { f.sel[e.id] = [].map.call(e.options, function (o) { return o.value; }); });
 document.querySelectorAll('.calc .seg').forEach(function (e) { f.seg[e.id] = [].map.call(e.querySelectorAll('button'), function (b) { return b.dataset.v; }); });
 return f; })()"""
def run(n, rng, slugs=None):
    total_bad = 0; grand = 0
    for slug in (slugs or ALL):
        form = drive(slug, [{'call': FORM}], 'form')[0]['call']; cases = []
        for i in range(n):
            c = {'seg': {k: rng.choice(v) for k, v in form['seg'].items()}, 'sel': {}, 'set': {}}
            for k, opts in form['sel'].items():
                if k == 'unit' and slug == 'marine-unit-converter': continue        # options depend on the group just chosen
                if rng.random() < 0.6: c['sel'][k] = rng.choice(opts)
            style = i % 4
            for id_, default in form['text']:
                r = rng.random()
                if style == 0: v = rng.choice(JUNK) if r < 0.25 else default                 # one or two bad fields among good ones
                elif style == 1: v = rng.choice(JUNK)                                         # everything bad
                elif style == 2: v = ('%.3f' % (10 ** rng.uniform(-4, 7))) if r < 0.7 else default   # wild magnitudes
                else: v = rng.choice(['0', '', default, '-' + default if default else '-3', default.replace('.', ',')])
                c['set'][id_] = v
            for id_, default in form['date']: c['set'][id_] = rng.choice(['2026-12-01', '', '2027-02-29', '1900-01-01', '2100-12-31', '2028-02-29'])
            for id_, default in form['time']: c['set'][id_] = rng.choice([default or '12:00', '', '00:00', '23:59'])
            cases.append(c)
        try: res = drive(slug, cases, 'fuzz'); bad = []
        except Exception as ex:
            print('%-46s PAGE HUNG OR FAILED on odd input: %s' % (slug, str(ex)[:120])); total_bad += 1; continue
        for c, r in zip(cases, res):
            text = ' | '.join([x[1] or '' for x in r['big']] + ['%s: %s' % kv for kv in r['kv'].items()] + r['msg'] + r['sub'] + [r['empty'] or ''])
            m = BAD.search(text)
            if m: bad.append((m.group(0), text[:260], c))
            if not text.strip(): bad.append(('empty result', '', c))
        grand += len(cases); total_bad += len(bad)
        print('%-46s %5d odd inputs, %d bad displays' % (slug, len(cases), len(bad)))
        seen = set()
        for what, text, c in bad:
            if what in seen: continue
            seen.add(what); print('     %r in: %s' % (what, text)); print('       inputs: %s' % json.dumps({k: v for k, v in c['set'].items()})[:300], c['seg'], c['sel'])
    print('TOTAL odd inputs', grand, 'bad displays', total_bad); return total_bad
if __name__ == '__main__':
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 1500, make_rng(5), sys.argv[2:] or None)

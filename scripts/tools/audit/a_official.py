"""Official printed tables, read off the publisher's own pages and compared with what the tool pages print.

Hong Kong Observatory Almanac 2026: sunrise, sun transit and sunset for every day of March, June, September and December
(122 days, 366 times). The almanac is computed for the Observatory itself, upper limb, mean sea level, Hong Kong Time."""
import json, os, sys
from common import *
H = json.load(open(os.path.join(HERE, '..', 'tests', 'fixtures_hko_2026.json')))
def mins(s): s = s.replace(':', ''); return int(s[:2]) * 60 + int(s[2:4])
def hko():
    T = Tally('sunrise, meridian passage and sunset vs the Hong Kong Observatory almanac 2026 (official table)'); cases = []; meta = []
    for month, rows in sorted(H['months'].items(), key=lambda kv: int(kv[0])):
        for day, row in enumerate(rows, 1):
            cases.append({'sel': {'zone': '8', 'lath': 'N', 'lonh': 'E'}, 'set': {'date': '%d-%02d-%02d' % (H['year'], int(month), day), 'latd': '22', 'latm': '18.1', 'lond': '114', 'lonm': '10.5'}}); meta.append(row.split())
    same = n = 0
    for c, r, (rise, tr, st) in zip(cases, drive('sunrise-sunset-twilight-calculator', cases, 'hko'), meta):
        for name, shown, want in (('sunrise', r['ids']['r_rise'], rise), ('meridian passage', r['kv']['Meridian passage'], tr), ('sunset', r['ids']['r_set'], st)):
            d = abs(mins(shown[:5]) - mins(want)); n += 1; same += d == 0
            T.check('%s within one minute of the almanac' % name, d <= 1, '%s shown %s almanac %s' % (c['set']['date'], shown, want))
    T.check('at least 360 of the 366 times identical to the minute', same >= 360, 'identical: %d of %d' % (same, n))
    bad = T.report(); print('     identical to the minute: %d of %d; the rest one minute apart' % (same, n)); return bad
if __name__ == '__main__':
    bad = hko(); print('TOTAL FAILED', bad); sys.exit(1 if bad else 0)

"""Adds an 'Open jobs' block to every rank guide and ship-type guide, pointing at the matching
jobs pages on oceanlinkai.com, and writes sitemap-jobs.xml (the rank + ship jobs pages).
Safe to run again: pages that already carry the block are left alone.
python3 scripts/guides/link_jobs.py
"""
import html
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
APP = 'https://oceanlinkai.com'
MARK = '<!--ol-jobs-->'
ANCHOR = '<h2>Related guides</h2>'

# The rank + ship pages that exist in the app (option set "Rank vessel page"): (rank slug, ship slug)
SHIPS = {'bulk-carrier': 'bulk carriers', 'container-ship': 'container ships', 'oil-tanker': 'oil tankers',
         'chemical-tanker': 'chemical tankers', 'lpg-tanker': 'LPG tankers', 'lng-tanker': 'LNG tankers'}
RANKS = {'master': 'Master', 'chief-officer': 'Chief Officer', '2nd-officer': '2nd Officer', '3rd-officer': '3rd Officer',
         'chief-engineer': 'Chief Engineer', '2nd-engineer': '2nd Engineer', '3rd-engineer': '3rd Engineer',
         '4th-engineer': '4th Engineer', 'eto': 'ETO', 'fitter': 'Fitter', 'oiler': 'Oiler',
         'able-seaman': 'Able Seaman (AB)', 'chief-cook': 'Chief Cook'}
COMBOS = [
    ('master', 'chemical-tanker'), ('master', 'lpg-tanker'), ('master', 'bulk-carrier'), ('master', 'oil-tanker'),
    ('chief-officer', 'bulk-carrier'), ('chief-officer', 'container-ship'), ('chief-officer', 'oil-tanker'),
    ('chief-officer', 'chemical-tanker'), ('chief-officer', 'lpg-tanker'),
    ('2nd-officer', 'bulk-carrier'), ('2nd-officer', 'chemical-tanker'), ('2nd-officer', 'oil-tanker'),
    ('3rd-officer', 'chemical-tanker'), ('3rd-officer', 'container-ship'), ('3rd-officer', 'oil-tanker'),
    ('3rd-officer', 'bulk-carrier'),
    ('chief-engineer', 'chemical-tanker'), ('chief-engineer', 'oil-tanker'), ('chief-engineer', 'lpg-tanker'),
    ('chief-engineer', 'bulk-carrier'), ('chief-engineer', 'container-ship'),
    ('2nd-engineer', 'bulk-carrier'), ('2nd-engineer', 'chemical-tanker'), ('2nd-engineer', 'container-ship'),
    ('3rd-engineer', 'oil-tanker'), ('3rd-engineer', 'chemical-tanker'), ('3rd-engineer', 'bulk-carrier'),
    ('3rd-engineer', 'container-ship'),
    ('4th-engineer', 'chemical-tanker'), ('4th-engineer', 'oil-tanker'), ('4th-engineer', 'bulk-carrier'),
    ('eto', 'chemical-tanker'), ('eto', 'oil-tanker'), ('eto', 'bulk-carrier'), ('eto', 'container-ship'),
    ('eto', 'lpg-tanker'),
    ('fitter', 'chemical-tanker'), ('oiler', 'chemical-tanker'),
    ('able-seaman', 'chemical-tanker'), ('able-seaman', 'lpg-tanker'), ('chief-cook', 'chemical-tanker'),
    ('master', 'lng-tanker'), ('chief-officer', 'lng-tanker'), ('2nd-officer', 'lng-tanker'),
    ('3rd-officer', 'lng-tanker'), ('chief-engineer', 'lng-tanker'), ('2nd-engineer', 'lng-tanker'),
    ('3rd-engineer', 'lng-tanker'), ('4th-engineer', 'lng-tanker'), ('eto', 'lng-tanker'),
]

# rank guide folder -> (name shown, rank jobs page slug on /jobs_portal_main/, rank slug used in rank + ship pages)
RANK_GUIDES = {
    'master': ('Master', 'master', 'master'),
    'chief-officer': ('Chief Officer', 'chief-officer', 'chief-officer'),
    '2nd-officer': ('2nd Officer', '2nd-officer', '2nd-officer'),
    '3rd-officer': ('3rd Officer', '3rd-officer', '3rd-officer'),
    '4th-officer': ('4th Officer', '4th-officer', None),
    'deck-cadet': ('Deck Cadet', 'deck-cadet', None),
    'chief-engineer': ('Chief Engineer', 'chief-engineer', 'chief-engineer'),
    '2nd-engineer': ('2nd Engineer', '2nd-engineer', '2nd-engineer'),
    '3rd-engineer': ('3rd Engineer', '3rd-engineer', '3rd-engineer'),
    '4th-engineer': ('4th Engineer', '4th-engineer', '4th-engineer'),
    'engine-cadet': ('Engine Cadet', 'engine-cadet', None),
    'electrical-officer-eto': ('ETO', 'electro-technical-officer-eto', 'eto'),
    'pumpman': ('Pumpman', 'pumpman', None),
    'bosun': ('Bosun', 'bosun', None),
    'able-seaman-ab': ('Able Seaman (AB)', 'able-seaman-ab', 'able-seaman'),
    'ordinary-seaman-os': ('Ordinary Seaman (OS)', 'ordinary-seaman-os', None),
    'motorman': ('Motorman', 'motorman', None),
    'oiler': ('Oiler', 'oiler', 'oiler'),
    'wiper': ('Wiper', 'wiper', None),
    'crane-operator': ('Crane Operator', 'crane-operator', None),
    'cook': ('Chief Cook', 'chief-cook', 'chief-cook'),
    'messman': ('Messman', 'messman', None),
    'fitter': ('Fitter', 'fitter', 'fitter'),
    'welder': ('Welder', 'welder', None),
    'rigger': ('Rigger', 'rigger', None),
    'trainee': ('Trainee', 'trainee', None),
    'assistant-engineer': (None, None, None),
    'steward': (None, None, None),
}
GENERIC = [(APP + '/seafarer-jobs', 'Seafarer jobs by rank and ship type'), (APP + '/jobs_portal_main', 'All open seafarer jobs')]


def block(links):
    a = ''.join('<a href="%s">%s</a>' % (u, html.escape(t)) for u, t in links)
    return MARK + '<h2 id="jobs">Open jobs on Ocean Link</h2><div class="rel">' + a + '</div>'


def patch(path, links):
    s = open(path, encoding='utf-8').read()
    if MARK in s or ANCHOR not in s:
        return 0
    open(path, 'w', encoding='utf-8').write(s.replace(ANCHOR, block(links) + ANCHOR, 1))
    return 1


def main():
    n = 0
    for folder in sorted(os.listdir(os.path.join(ROOT, 'guides', 'ranks'))):
        key = folder.replace('-on-a-merchant-ship', '')
        if key not in RANK_GUIDES:
            continue
        name, portal, combo = RANK_GUIDES[key]
        links = []
        if portal:
            links.append(('%s/jobs_portal_main/%s' % (APP, portal), 'All open %s jobs' % name))
        if combo:
            links += [('%s/seafarer-jobs/%s-%s' % (APP, r, v), '%s jobs on %s' % (RANKS[r], SHIPS[v])) for r, v in COMBOS if r == combo]
        links += GENERIC if not combo else GENERIC[:1]
        n += patch(os.path.join(ROOT, 'guides', 'ranks', folder, 'index.html'), links)
    for folder in sorted(os.listdir(os.path.join(ROOT, 'guides', 'vessels'))):
        p = os.path.join(ROOT, 'guides', 'vessels', folder, 'index.html')
        if not os.path.isfile(p):
            continue
        ship = folder.replace('working-on-a-', '')
        links = [('%s/seafarer-jobs/%s-%s' % (APP, r, v), '%s jobs on %s' % (RANKS[r], SHIPS[v])) for r, v in COMBOS if v == ship]
        links += GENERIC if not links else GENERIC[:1]
        n += patch(p, links)
    urls = [APP + '/seafarer-jobs'] + ['%s/seafarer-jobs/%s-%s' % (APP, r, v) for r, v in COMBOS]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += ''.join('  <url><loc>%s</loc></url>\n' % u for u in urls) + '</urlset>\n'
    open(os.path.join(ROOT, 'sitemap-jobs.xml'), 'w', encoding='utf-8').write(sm)
    print('guides linked:', n, '| sitemap urls:', len(urls))


if __name__ == '__main__':
    main()

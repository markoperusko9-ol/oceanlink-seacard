"""Builds the Ocean Link seafarer tools pages into /tools.
Run from the repo root:  python3 scripts/tools/build.py
Tool definitions live in scripts/tools/src/*.py; the maths lives in tools/assets/calc.js
and is tested by scripts/tools/tests/calc.test.js."""
import html, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
SITE = 'https://card.oceanlinkai.com'
PLAY = 'https://play.google.com/store/apps/details?id=com.oceanlinkai.app'
V = '5'            # bump to refresh cached css/js
TODAY = '2026-11-23'

LOGO = ('<svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true"><rect x="3.4" y="21.6" width="4.6" height="4.6" rx="1.4" fill="#0B5D75"/>'
        '<rect x="8.2" y="17.4" width="5.2" height="5.2" rx="1.6" fill="#0E86A6"/><rect x="13.6" y="12.4" width="5.8" height="5.8" rx="1.8" fill="#00B0D2"/>'
        '<rect x="19.6" y="6.6" width="6.6" height="6.6" rx="2" fill="#00E5FF"/><rect x="23.4" y="13.8" width="5.4" height="5.4" rx="1.7" fill="#00B0D2"/>'
        '<rect x="18.4" y="18.6" width="4.8" height="4.8" rx="1.5" fill="#0E86A6"/></svg>')
ORG = {"@type": "Organization", "name": "Ocean Link", "url": "https://oceanlinkai.com",
       "sameAs": ["https://www.linkedin.com/company/oceanlinkapp", "https://www.instagram.com/oceanlink_ai", PLAY]}

CATEGORIES = ['Navigation', 'Bridge watch', 'Engine', 'Stability and cargo', 'Converters']


def e(s):
    return html.escape(str(s), quote=True)


# ---------- form helpers used by the tool definitions ----------
def num(id, label, value='', hint='', cls='', neg=False, ph=''):
    mode = 'text' if neg else 'decimal'
    return ('<label class="f %s"><span>%s</span><input id="%s" type="text" inputmode="%s" value="%s" placeholder="%s" autocomplete="off">%s</label>'
            % (cls, label, id, mode, e(value), e(ph), '<small>%s</small>' % hint if hint else ''))


def select(id, label, options, default=None, cls=''):
    opts = ''.join('<option value="%s"%s>%s</option>' % (e(v), ' selected' if str(v) == str(default) else '', e(t)) for v, t in options)
    return '<label class="f %s"><span>%s</span><select id="%s">%s</select></label>' % (cls, label, id, opts)


def seg(id, options, default=None, cls=''):
    default = default if default is not None else options[0][0]
    return '<div class="seg %s" id="%s" data-v="%s">%s</div>' % (
        cls, id, e(default), ''.join('<button data-v="%s">%s</button>' % (e(v), e(t)) for v, t in options))


def segfield(id, label, options, default=None, cls=''):
    return '<div class="f %s"><span class="l">%s</span>%s</div>' % (cls, label, seg(id, options, default))


def latlon(prefix, label, deg, minutes, hemi, kind):
    hs = ('N', 'S') if kind == 'lat' else ('E', 'W')
    opts = ''.join('<option%s>%s</option>' % (' selected' if h == hemi else '', h) for h in hs)
    return ('<div class="f full"><span class="l">%s</span><div class="row">'
            '<input id="%sd" type="text" inputmode="numeric" value="%s" placeholder="deg" aria-label="%s degrees" autocomplete="off">'
            '<input id="%sm" type="text" inputmode="decimal" value="%s" placeholder="min" aria-label="%s minutes" autocomplete="off">'
            '<select id="%sh" class="sm" aria-label="%s hemisphere">%s</select></div></div>'
            % (label, prefix, e(deg), e(label), prefix, e(minutes), e(label), prefix, e(label), opts))


def date(id, label, cls=''):
    return '<label class="f %s"><span>%s</span><input id="%s" type="date"></label>' % (cls, label, id)


def time(id, label, value='', cls=''):
    return '<label class="f %s"><span>%s</span><input id="%s" type="time" value="%s"></label>' % (cls, label, id, e(value))


ZONES = [-12, -11, -10, -9.5, -9, -8, -7, -6, -5, -4, -3.5, -3, -2, -1, 0, 1, 2, 3, 3.5, 4, 4.5, 5, 5.5, 5.75,
         6, 6.5, 7, 8, 8.75, 9, 9.5, 10, 10.5, 11, 12, 12.75, 13, 14]


def zone_label(z):
    if z == 0:
        return 'UTC'
    a = abs(z)
    h, m = int(a), int(round((a - int(a)) * 60))
    return 'UTC%s%d%s' % ('+' if z > 0 else '−', h, ':%02d' % m if m else '')


def zone(id, label, default=0, cls=''):
    return select(id, label, [(z, zone_label(z)) for z in ZONES], default, cls)


# ---------- page shell ----------
def head(title, desc, path, ld):
    url = SITE + path
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>%s</title><meta name="description" content="%s"><link rel="canonical" href="%s">\n'
            '<meta property="og:title" content="%s"><meta property="og:description" content="%s"><meta property="og:type" content="website"><meta property="og:url" content="%s"><meta property="og:site_name" content="Ocean Link">\n'
            '<meta property="og:image" content="%s/press/img/og.jpg"><meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#050609">\n'
            '<link rel="icon" type="image/svg+xml" href="/press/img/favicon.svg"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet"><link rel="stylesheet" href="/tools/assets/tools.css?v=%s">\n'
            '<script src="/tools/assets/embed.js?v=%s"></script>\n%s</head><body>\n'
            % (e(title), e(desc), url, e(title), e(desc), url, SITE, V, V,
               ''.join('<script type="application/ld+json">%s</script>' % json.dumps(x, ensure_ascii=False) for x in ld)))


BAR = ('<div class="bar"><div class="in"><a class="brand" href="/tools/">%s<span>OCEAN <b>LINK</b></span></a>'
       '<a class="btn" href="%s">Get the app</a></div></div>\n' % (LOGO, PLAY))

CTA = ('<div class="card cta"><div class="label">Ocean Link — free for seafarers</div><h3>Your career in one app</h3>'
       '<p>Keep your certificates, sea time and CV in one place, and apply for jobs for your rank with one tap. Built by a serving 2nd Officer.</p>'
       '<div class="feat">Certificate manager with expiry alerts · Sea time tracker · Free professional CV · Jobs for your rank · One-tap apply · Micro-lessons &amp; quizzes · Seafarer network (SeaFeed) · Crew messaging</div>'
       '<a class="btn" href="%s">Get it on Google Play</a> <a class="btn ghost" href="https://oceanlinkai.com">Open oceanlinkai.com</a></div>' % PLAY)

FOOT = ('</main>\n<footer>Ocean Link Seafarer Tools · <a href="/tools/">All tools</a><span class="out"> · <a href="/guides/">Seafarer guides</a> · <a href="https://oceanlinkai.com">oceanlinkai.com</a></span> · '
        '<a href="mailto:oceanlinksupport@gmail.com">oceanlinksupport@gmail.com</a><br>\n'
        'A planning and learning aid. Your ship\'s approved instruments, stability data, company SMS and the official publications always prevail.</footer>\n')


def tool_page(t, tools):
    path = '/tools/%s/' % t['slug']
    ld = [{"@context": "https://schema.org", "@type": "WebApplication", "name": t['h1'], "url": SITE + path,
           "description": t['desc'], "applicationCategory": "UtilitiesApplication", "operatingSystem": "Any",
           "isAccessibleForFree": True, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
           "dateModified": TODAY, "publisher": ORG},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Tools", "item": SITE + "/tools/"},
              {"@type": "ListItem", "position": 2, "name": t['h1'], "item": SITE + path}]}]
    if t.get('faq'):
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in t['faq']]})
    p = [head(t['title'], t['desc'], path, ld), BAR,
         '<main class="wrap"><a class="back" href="/tools/">‹ All tools</a><div class="crumbs"><a href="/tools/">Tools</a> › %s</div><h1>%s</h1><p class="lead">%s</p>\n' % (e(t['cat']), e(t['h1']), t['lead']),
         '<div class="card calc">%s<div class="res" id="res" aria-live="polite"></div>%s</div>\n' % (
             t['form'], '<figure class="dia" id="dia"></figure>' if t.get('diagram') else ''),
         t['how'], '\n']
    if t.get('faq'):
        p.append('<h2 id="faq">FAQ</h2>' + ''.join('<details><summary>%s</summary><p>%s</p></details>' % (e(q), e(a)) for q, a in t['faq']))
    p.append(CTA)
    rel = ''.join('<a href="%s">%s</a>' % (u, e(n)) for u, n in t.get('guides', []))
    if rel:
        p.append('<h2>Read the guide</h2><div class="rel">%s</div>' % rel)
    others = [o for o in tools if o['cat'] == t['cat'] and o['slug'] != t['slug']] + \
             [o for o in tools if o['cat'] != t['cat']]
    p.append('<h2>More tools</h2><div class="rel">%s<a href="/tools/">All seafarer tools</a></div>' % ''.join(
        '<a href="/tools/%s/">%s</a>' % (o['slug'], e(o['name'])) for o in others[:5]))
    p.append(FOOT)
    p.append('<script src="/tools/assets/calc.js?v=%s"></script><script src="/tools/assets/ui.js?v=%s"></script>' % (V, V))
    for s in t.get('scripts', []):
        p.append('<script src="/tools/assets/%s?v=%s"></script>' % (s, V))
    p.append('\n<script>\n%s\n</script>\n</body></html>\n' % t['script'].strip())
    return ''.join(p)


def hub_page(tools):
    desc = ('Free calculators for seafarers: compass error by the Sun, true wind, ETA, great circle, CPA and TCPA, set and drift, '
            'squat and UKC, propeller slip, fuel, FWA and DWA, list and GM, unit converter. Each one tested against reference data.')
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Seafarer Tools and Calculators",
           "url": SITE + "/tools/", "description": desc, "publisher": ORG},
          {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
              {"@type": "ListItem", "position": i + 1, "name": t['name'], "url": SITE + '/tools/%s/' % t['slug']}
              for i, t in enumerate(tools)]}]
    p = [head('Seafarer Tools: Free Marine Calculators | Ocean Link', desc, '/tools/', ld), BAR,
         '<main class="wrap wide"><h1 class="hubhead">Seafarer tools</h1><p class="lead hubhead">Free calculators for the bridge, the engine room and the cargo office. '
         'Every tool shows its formula and its limits, and its maths is tested against reference data before it goes live.</p>\n']
    for c in CATEGORIES:
        ts = [t for t in tools if t['cat'] == c]
        if not ts:
            continue
        p.append('<h2>%s</h2><div class="grid">' % e(c))
        for t in ts:
            p.append('<a class="tool" href="/tools/%s/"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" '
                     'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>'
                     '<span><b>%s</b><small>%s</small></span></a>' % (t['slug'], t['icon'], e(t['name']), e(t['blurb'])))
        p.append('</div>\n')
    p.append('<div class="card checked"><div class="label">How the tools are checked</div><p>Each calculation is written once and used by both the page and an automated test. '
             'The tests compare it with worked textbook examples and with an independent reference: an astronomical ephemeris for the Sun, '
             'a geodesic library for distances, and brute-force simulation for wind, current and radar plots. A tool is published only when every test passes.</p></div>\n')
    p.append(CTA)
    p.append('<h2>Seafarer guides</h2><div class="rel"><a href="/guides/">Browse all Ocean Link seafarer guides</a></div>')
    p.append(FOOT)
    p.append('</body></html>\n')
    return ''.join(p)


def main():
    import src.nav as nav
    import src.ship as ship
    tools = nav.TOOLS + ship.TOOLS
    order = {c: i for i, c in enumerate(CATEGORIES)}
    tools.sort(key=lambda t: order[t['cat']])
    for t in tools:
        for u, _ in t.get('guides', []):
            assert os.path.exists(os.path.join(ROOT, u.strip('/'), 'index.html')), 'missing guide ' + u
        d = os.path.join(ROOT, 'tools', t['slug'])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(tool_page(t, tools))
    open(os.path.join(ROOT, 'tools', 'index.html'), 'w', encoding='utf-8').write(hub_page(tools))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
          '  <url><loc>%s/tools/</loc><lastmod>%s</lastmod></url>' % (SITE, TODAY)]
    sm += ['  <url><loc>%s/tools/%s/</loc><lastmod>%s</lastmod></url>' % (SITE, t['slug'], TODAY) for t in tools]
    open(os.path.join(ROOT, 'tools', 'sitemap.xml'), 'w', encoding='utf-8').write('\n'.join(sm + ['</urlset>', '']))
    json.dump([{'slug': t['slug'], 'name': t['name'], 'guides': t.get('guides', [])} for t in tools],
              open(os.path.join(HERE, 'tools.json'), 'w'), indent=1)
    print('built', len(tools), 'tools')


if __name__ == '__main__':
    main()

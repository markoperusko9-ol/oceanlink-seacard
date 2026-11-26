"""Lets every guide page open inside the Ocean Link app (the same in-app mode the tools use).
Opened with ?embed=1 a guide drops its own top bar, app banner and footer, keeps guide and tool
links inside the app and tells the app how tall it is (/tools/assets/embed.js).
Safe to run again: pages that already carry the block are left alone.
python3 scripts/guides/embed_mode.py
"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
MARK = '<!--ol-embed-->'
BLOCK = (MARK + '<script src="/tools/assets/embed.js?v=9"></script><style>'
         '.embed .bar,.embed .cta,.embed footer{display:none}'
         'html.embed{scrollbar-width:none}html.embed::-webkit-scrollbar{display:none}'
         '.embed.framed .wrap{padding:4px 0 12px;max-width:none}'
         '</style>')

done = skipped = 0
for d, _, files in os.walk(os.path.join(ROOT, 'guides')):
    for f in files:
        if not f.endswith('.html'):
            continue
        p = os.path.join(d, f)
        s = open(p, encoding='utf-8').read()
        if MARK in s or '</head>' not in s:
            skipped += 1
            continue
        open(p, 'w', encoding='utf-8').write(s.replace('</head>', BLOCK + '</head>', 1))
        done += 1
print('embed block added to %d pages, %d left as they were' % (done, skipped))

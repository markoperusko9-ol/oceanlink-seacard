/* Drives one real tool page in Chrome: applies each case's inputs the way a user would (values typed, selects chosen,
   segment buttons clicked), then reads back what the page displays. No access to the page's maths other than through its UI,
   except for cases that carry an explicit `call` (a direct OLCalc function call, used only for precision statistics). */
const puppeteer = require('puppeteer-core');   // resolved through NODE_PATH
const BASE = process.env.OL_AUDIT_BASE || 'http://127.0.0.1:8766';
const CHROME = process.env.CHROME_PATH || '/usr/bin/google-chrome';
const fs = require('fs');
(async () => {
  const [slug, inFile, outFile] = process.argv.slice(2);
  const spec = JSON.parse(fs.readFileSync(inFile, 'utf8'));
  const b = await puppeteer.launch({ executablePath: CHROME, args: ['--no-sandbox'] });
  const p = await b.newPage();
  await p.setRequestInterception(true);
  p.on('request', (r) => { if (r.url().startsWith(BASE)) r.continue(); else r.abort(); });   // the page under test only, nothing from the network
  const errs = [];
  p.on('pageerror', (e) => errs.push(String(e)));
  await p.goto(BASE + '/tools/' + slug + '/' + (spec.query || ''), { waitUntil: 'load' });
  await p.waitForFunction(() => window.OLCalc && document.getElementById('res') && document.getElementById('res').innerHTML.length > 0, { timeout: 20000 });
  const out = await p.evaluate((spec) => {
    const fire = (el, type) => el.dispatchEvent(new Event(type, { bubbles: true }));
    const txt = (el) => (el ? el.textContent.replace(/\s+/g, ' ').trim() : null);
    const res = [];
    for (const c of spec.cases) {
      if (c.call) { res.push({ call: eval('(' + c.call + ')') }); continue; }
      for (const [id, v] of Object.entries(c.seg || {})) { const btn = document.querySelector('#' + id + ' button[data-v="' + v + '"]'); if (!btn) throw new Error('no segment ' + id + '=' + v); btn.click(); }
      for (const [id, v] of Object.entries(c.sel || {})) { const el = document.getElementById(id); if (!el) throw new Error('no select ' + id); el.value = String(v); if (el.value !== String(v)) throw new Error('select ' + id + ' has no option ' + v); fire(el, 'change'); }
      const ids = Object.keys(c.set || {});
      ids.forEach((id) => { const el = document.getElementById(id); if (!el) throw new Error('no input ' + id); el.value = String(c.set[id]); });
      if (ids.length) fire(document.getElementById(ids[ids.length - 1]), 'input');
      const root = document.getElementById('res'), r = { big: [], kv: {}, msg: [], sub: [], ids: {} };
      root.querySelectorAll('.big').forEach((el) => { const lab = el.previousElementSibling; r.big.push([txt(lab), txt(el)]); });
      root.querySelectorAll('.kv > div').forEach((d) => { r.kv[txt(d.querySelector('.k'))] = txt(d.querySelector('.v')); });
      root.querySelectorAll('.msg').forEach((el) => r.msg.push((el.className.replace('msg', '').trim() || 'info') + ': ' + txt(el)));
      root.querySelectorAll('p.sub').forEach((el) => r.sub.push(txt(el)));
      const em = root.querySelector('p.empty'); r.empty = em ? txt(em) : null;
      root.querySelectorAll('[id]').forEach((el) => { r.ids[el.id] = txt(el); });
      const dia = document.getElementById('dia'); r.dia = dia ? dia.innerHTML.length : null;
      res.push(r);
    }
    return res;
  }, spec);
  fs.writeFileSync(outFile, JSON.stringify({ results: out, pageErrors: errs }));
  await b.close();
  if (errs.length) { console.error('PAGE ERRORS', errs.slice(0, 3)); process.exit(2); }
})().catch((e) => { console.error('DRIVER FAILED', String(e).slice(0, 600)); process.exit(1); });

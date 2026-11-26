/* Ocean Link seafarer tools and guides: in-app mode. A page opened with ?embed=1 is shown inside the Ocean Link app,
   so it drops its own header, keeps tool and guide links in the same mode and tells the app how tall it is.
   Inside the app every page below a hub gets a Back button, and going back (button or phone back) returns
   to the spot in the list the reader left from. */
(function () {
  'use strict';
  if (!/[?&]embed=1/.test(location.search)) return;
  document.documentElement.classList.add('embed');
  try { if (window.self !== window.top) document.documentElement.classList.add('framed'); } catch (e) { document.documentElement.classList.add('framed'); } // opened directly, the page keeps its own margins
  var KEY_Y = 'olY:' + location.pathname, KEY_BACK = 'olBack';
  function store(k, v) { try { if (v === null) sessionStorage.removeItem(k); else sessionStorage.setItem(k, v); } catch (e) { /* storage blocked */ } }
  function read(k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } }
  function tell(extra) {
    var m = { olTools: 1, height: Math.ceil(document.documentElement.getBoundingClientRect().height) + 1 }; // whole document, including margins that sit outside the body box
    if (extra) for (var k in extra) m[k] = extra[k];
    try { window.parent.postMessage(m, '*'); } catch (e) { /* not framed */ }
  }
  function cameBack() {
    if (read(KEY_BACK)) { store(KEY_BACK, null); return true; }
    try { var n = performance.getEntriesByType('navigation')[0]; return !!n && n.type === 'back_forward'; } catch (e) { return false; }
  }
  function addBack() {
    var p = location.pathname;
    if (p === '/guides/' || p === '/tools/' || document.querySelector('.back')) return; // hubs need none; tools pages carry their own
    var main = document.querySelector('main');
    if (!main) return;
    var crumbs = main.querySelectorAll('.crumbs a'), up = crumbs.length ? crumbs[crumbs.length - 1].getAttribute('href') : '/guides/?embed=1';
    var a = document.createElement('a');
    a.className = 'back ol-back';
    a.href = up;
    a.textContent = '‹ Back';
    a.addEventListener('click', function (ev) {
      if (document.referrer.indexOf(location.origin + '/') === 0 && history.length > 1) { // came here from another page in the app frame: go back to it
        ev.preventDefault();
        store(KEY_BACK, '1');
        history.back();
      }
    });
    var st = document.createElement('style');
    st.textContent = '.ol-back{display:inline-flex;align-items:center;gap:6px;min-height:44px;font-size:14px;font-weight:500;color:#F2F4F7;background:#0F1217;border:1px solid #FFFFFF14;border-radius:10px;padding:0 14px 0 12px;margin:0 0 10px;letter-spacing:-.15px;text-decoration:none}.ol-back:hover{border-color:#FFFFFF24;text-decoration:none}';
    document.head.appendChild(st);
    main.insertBefore(a, main.firstChild);
  }
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('a[href]').forEach(function (a) {
      var h = a.getAttribute('href');
      if (h.indexOf('/tools/') === 0 || h.indexOf('/guides/') === 0) { // tools and guides stay inside the app
        var hash = h.indexOf('#') > -1 ? h.slice(h.indexOf('#')) : '';
        a.setAttribute('href', h.split('#')[0].split('?')[0] + '?embed=1' + hash);
        a.addEventListener('click', function () { // remember where in this page the reader was, for the way back
          store(KEY_Y, String(Math.max(0, Math.round(a.getBoundingClientRect().top + (window.scrollY || 0)) - 60)));
        });
      }
      else if (h.charAt(0) !== '#') { a.target = '_blank'; a.rel = 'noopener'; }
    });
    addBack();
    var y = read(KEY_Y);
    if (cameBack() && y !== null) tell({ y: +y }); // the app scrolls back to the link the reader opened
    else tell({ nav: 1 });
    if (window.ResizeObserver) new ResizeObserver(function () { tell(); }).observe(document.body);
  });
  window.addEventListener('load', function () { tell(); });
})();

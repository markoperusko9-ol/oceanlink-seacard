/* Ocean Link seafarer tools and guides: in-app mode. A page opened with ?embed=1 is shown inside the Ocean Link app,
   so it drops its own header, keeps tool links in the same mode and tells the app how tall it is. */
(function () {
  'use strict';
  if (!/[?&]embed=1/.test(location.search)) return;
  document.documentElement.classList.add('embed');
  try { if (window.self !== window.top) document.documentElement.classList.add('framed'); } catch (e) { document.documentElement.classList.add('framed'); } // opened directly, the page keeps its own margins
  function tell(extra) {
    var m = { olTools: 1, height: Math.ceil(document.documentElement.getBoundingClientRect().height) + 1 }; // whole document, including margins that sit outside the body box
    if (extra) m.nav = 1;
    try { window.parent.postMessage(m, '*'); } catch (e) { /* not framed */ }
  }
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('a[href]').forEach(function (a) {
      var h = a.getAttribute('href');
      if (h.indexOf('/tools/') === 0 || h.indexOf('/guides/') === 0) { // tools and guides stay inside the app
        var hash = h.indexOf('#') > -1 ? h.slice(h.indexOf('#')) : '';
        a.setAttribute('href', h.split('#')[0].split('?')[0] + '?embed=1' + hash);
      }
      else if (h.charAt(0) !== '#') { a.target = '_blank'; a.rel = 'noopener'; }
    });
    tell(true);
    if (window.ResizeObserver) new ResizeObserver(function () { tell(false); }).observe(document.body);
  });
  window.addEventListener('load', function () { tell(false); });
})();

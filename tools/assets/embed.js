/* Ocean Link seafarer tools: in-app mode. A page opened with ?embed=1 is shown inside the Ocean Link app,
   so it drops its own header, keeps tool links in the same mode and tells the app how tall it is. */
(function () {
  'use strict';
  if (!/[?&]embed=1/.test(location.search)) return;
  document.documentElement.classList.add('embed');
  function tell(extra) {
    var m = { olTools: 1, height: Math.ceil(document.documentElement.getBoundingClientRect().height) + 1 }; // whole document, including margins that sit outside the body box
    if (extra) m.nav = 1;
    try { window.parent.postMessage(m, '*'); } catch (e) { /* not framed */ }
  }
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('a[href]').forEach(function (a) {
      var h = a.getAttribute('href');
      if (h.indexOf('/tools/') === 0) a.setAttribute('href', h.split('?')[0] + '?embed=1');
      else if (h.charAt(0) !== '#') { a.target = '_blank'; a.rel = 'noopener'; }
    });
    tell(true);
    if (window.ResizeObserver) new ResizeObserver(function () { tell(false); }).observe(document.body);
  });
  window.addEventListener('load', function () { tell(false); });
})();

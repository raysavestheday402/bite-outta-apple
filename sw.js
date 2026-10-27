/* Offline support: keeps the app, the library and every poster on the device so TV Library opens without Wi-Fi.
   The page and data.js are fetched fresh when online (falling back to the saved copy); posters, icons and fonts
   come from the saved copy first and refresh in the background. Bump VERSION only to force-clear old caches. */
var VERSION = 'v3';
var SHELL = 'shell-' + VERSION, ART = 'art-' + VERSION, FONTS = 'fonts-' + VERSION;
var SHELL_FILES = [
  './', 'data.js', 'icons/icon-192.png', 'icons/apple-touch-icon.png',
  'icons/header-art.jpg', 'icons/favicon.ico', 'icons/favicon-32x32.png', 'icons/favicon-16x16.png', 'icons/manifest.webmanifest'
];

// every thumbnail and poster named in data.js, saved one at a time; a poster that fails is simply tried again next time
function savePosters() {
  return fetch('data.js', { cache: 'no-store' }).then(function (r) { return r.text(); }).then(function (js) {
    var paths = [], re = /"(?:thumb|poster)":\s*"((?:thumbs|posters)\/[^"]+)"/g, m;
    while ((m = re.exec(js))) paths.push(m[1]);
    return caches.open(ART).then(function (cache) {
      return paths.reduce(function (p, path) {
        return p.then(function () {
          return cache.match(path).then(function (hit) {
            if (hit) return;
            return fetch(path).then(function (res) { if (res.ok) return cache.put(path, res); }).catch(function () {});
          });
        });
      }, Promise.resolve());
    });
  }).catch(function () {});
}

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(SHELL).then(function (c) { return c.addAll(SHELL_FILES); }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener('activate', function (e) {
  var keep = [SHELL, ART, FONTS];
  e.waitUntil(caches.keys().then(function (names) {
    return Promise.all(names.filter(function (n) { return keep.indexOf(n) === -1; }).map(function (n) { return caches.delete(n); }));
  }).then(function () { return self.clients.claim(); }));
});

// the page asks for this once it has loaded, so new posters get saved after a library update too
self.addEventListener('message', function (e) {
  if (e.data === 'save-posters') e.waitUntil(savePosters());
});

function networkFirst(req, key) {
  return caches.open(SHELL).then(function (cache) {
    var net = fetch(req).then(function (res) { if (res.ok) cache.put(key, res.clone()); return res; });
    var saved = function () { return cache.match(key).then(function (hit) { return hit || net; }); };
    // a slow, flaky connection shouldn't leave the screen blank: after 4s use the saved copy if there is one
    var slow = new Promise(function (resolve) { setTimeout(resolve, 4000); }).then(saved);
    return Promise.race([net.catch(saved), slow]);
  });
}

function savedFirst(req, name) {
  return caches.open(name).then(function (cache) {
    return cache.match(req, { ignoreSearch: name === ART }).then(function (hit) {
      var net = fetch(req).then(function (res) { if (res.ok || res.type === 'opaque') cache.put(req, res.clone()); return res; });
      if (hit) { net.catch(function () {}); return hit; }
      return net;
    });
  });
}

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin === self.location.origin) {
    var path = url.pathname.replace(/^\//, '');
    if (req.mode === 'navigate' || path === '' || path === 'index.html') e.respondWith(networkFirst(req, './'));
    else if (path === 'data.js') e.respondWith(networkFirst(req, 'data.js'));
    else if (/^(posters|thumbs|icons)\//.test(path)) e.respondWith(savedFirst(req, /^(posters|thumbs)\//.test(path) ? ART : SHELL));
  } else if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    e.respondWith(savedFirst(req, FONTS));
  }
});

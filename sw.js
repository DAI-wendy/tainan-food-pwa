/* =========================================================
   府城新食代 Service Worker
   改版時只要改 CACHE_VERSION，舊快取會自動清掉
   ========================================================= */

const CACHE_VERSION = 'v1.0.0';
const SHELL_CACHE   = `tainan-food-shell-${CACHE_VERSION}`;
const RUNTIME_CACHE = `tainan-food-runtime-${CACHE_VERSION}`;

/* 安裝時就先抓下來的「應用外殼」——離線第一次開也看得到 */
const SHELL_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/maskable-192.png',
  './icons/maskable-512.png',
  './icons/apple-touch-icon.png',
  './icons/favicon.ico',
  './icons/icon.svg'
];

/* 這些 CDN 第一次載入後就快取起來（Tailwind、字型、Font Awesome） */
const CDN_HOSTS = [
  'cdn.tailwindcss.com',
  'cdnjs.cloudflare.com',
  'fonts.googleapis.com',
  'fonts.gstatic.com'
];

/* 圖片來源 */
const IMAGE_HOSTS = ['images.unsplash.com', 'placehold.co'];

/* 絕不快取（分析工具） */
const NEVER_CACHE = ['googletagmanager.com', 'google-analytics.com', 'analytics.google.com'];

/* 離線時圖片載不到的替代圖 */
const OFFLINE_IMAGE_SVG =
  `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
     <rect width="800" height="600" fill="#f3f4f6"/>
     <text x="400" y="300" font-family="sans-serif" font-size="34" fill="#9ca3af"
           text-anchor="middle" dominant-baseline="central">離線中，圖片暫時無法顯示</text>
   </svg>`;

function offlineImage() {
  return new Response(OFFLINE_IMAGE_SVG, {
    headers: { 'Content-Type': 'image/svg+xml; charset=utf-8', 'Cache-Control': 'no-store' }
  });
}

/* ------------------------------------------------- 安裝 */
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then((cache) => Promise.allSettled(
        SHELL_ASSETS.map((url) => cache.add(new Request(url, { cache: 'reload' })))
      ))
      .then(() => self.skipWaiting())
  );
});

/* ------------------------------------------------- 啟用：清舊快取 */
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== SHELL_CACHE && k !== RUNTIME_CACHE)
            .map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

/* ------------------------------------------------- 快取策略 */

// 網路優先（拿得到新的就用新的，拿不到再吃快取）
async function networkFirst(request, cacheName, fallback) {
  const cache = await caches.open(cacheName);
  try {
    const fresh = await fetch(request);
    if (fresh && fresh.ok) cache.put(request, fresh.clone());
    return fresh;
  } catch (err) {
    const cached = await cache.match(request) || await caches.match('./index.html');
    if (cached) return cached;
    if (fallback) return fallback();
    throw err;
  }
}

// 快取優先（自己網站的靜態檔）
async function cacheFirst(request, cacheName, fallback) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const fresh = await fetch(request);
    if (fresh && fresh.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, fresh.clone());
    }
    return fresh;
  } catch (err) {
    if (fallback) return fallback();
    throw err;
  }
}

// 先給快取、背景默默更新（CDN 與圖片最適合）
async function staleWhileRevalidate(request, cacheName, fallback) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);

  const network = fetch(request)
    .then((res) => {
      // 跨網域的 opaque 回應也存，才能離線顯示
      if (res && (res.ok || res.type === 'opaque')) cache.put(request, res.clone());
      return res;
    })
    .catch(() => null);

  if (cached) return cached;
  const fresh = await network;
  if (fresh) return fresh;
  if (fallback) return fallback();
  return Response.error();
}

/* ------------------------------------------------- 攔截請求 */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return;
  if (NEVER_CACHE.some((h) => url.hostname.includes(h))) return;   // 交給瀏覽器直接連

  // 1. 頁面導覽 → 網路優先，離線時給快取的 index.html
  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request, SHELL_CACHE));
    return;
  }

  // 2. 圖片 → 先快取後更新，全部失敗給離線替代圖
  if (request.destination === 'image' || IMAGE_HOSTS.some((h) => url.hostname.includes(h))) {
    event.respondWith(
      staleWhileRevalidate(request, RUNTIME_CACHE, offlineImage)
    );
    return;
  }

  // 3. CDN 樣式／腳本／字型 → 先快取後更新
  if (CDN_HOSTS.some((h) => url.hostname.includes(h))) {
    event.respondWith(staleWhileRevalidate(request, RUNTIME_CACHE));
    return;
  }

  // 4. 同網域的靜態資源 → 快取優先
  if (url.origin === self.location.origin) {
    event.respondWith(cacheFirst(request, SHELL_CACHE));
    return;
  }

  // 5. 其他跨網域 → 網路優先
  event.respondWith(staleWhileRevalidate(request, RUNTIME_CACHE));
});

/* ------------------------------------------------- 由頁面觸發立即更新 */
self.addEventListener('message', (event) => {
  if (event.data === 'SKIP_WAITING' || event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

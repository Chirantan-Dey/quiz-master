const CACHE_NAME = 'quiz-master-v1';
const OFFLINE_URL = '/offline.html';
const ASSETS_TO_CACHE = [
    '/',
    '/static/app.js',
    '/static/style.css',
    '/static/manifest.json',
    OFFLINE_URL,
    'https://cdn.jsdelivr.net/npm/vue@2.7.16/dist/vue.js',
    'https://unpkg.com/vue-router@3/dist/vue-router.js',
    'https://unpkg.com/vuex@3.6.2/dist/vuex.js',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        Promise.all([
            caches.open(CACHE_NAME)
                .then((cache) => cache.addAll(ASSETS_TO_CACHE)),
            fetch(OFFLINE_URL).catch(() => new Response(
                `<!DOCTYPE html>
                <html>
                <head>
                    <title>Offline - Quiz Master</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
                </head>
                <body class="p-4">
                    <div class="container text-center">
                        <h1>You're Offline</h1>
                        <p>Please check your internet connection and try again.</p>
                        <button class="btn btn-primary" onclick="window.location.reload()">Retry</button>
                    </div>
                </body>
                </html>`,
                { headers: { 'Content-Type': 'text/html' } }
            ))
        ])
    );
});

self.addEventListener('fetch', (event) => {
    if (event.request.url.includes('/api/')) {
        event.respondWith(
            fetch(event.request)
                .catch(() => new Response(
                    JSON.stringify({ error: 'You are offline' }),
                    { headers: { 'Content-Type': 'application/json' } }
                ))
        );
        return;
    }

    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request)
                .catch(() => caches.match(OFFLINE_URL) || caches.match('/'))
        );
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then((response) => response || fetch(event.request)
                .then((response) => {
                    if (response && response.status === 200) {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(event.request, responseClone);
                        });
                    }
                    return response;
                })
                .catch(() => {
                    if (event.request.headers.get('accept').includes('text/html')) {
                        return caches.match(OFFLINE_URL);
                    }
                    return new Response('Offline content not available');
                })
            )
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keyList) => {
            return Promise.all(keyList.map((key) => {
                if (key !== CACHE_NAME) {
                    return caches.delete(key);
                }
            }));
        })
    );
});
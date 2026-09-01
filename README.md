# Rive Bench

A single-page player for `.riv` files. It's a hand-written, dependency-free
web app that runs entirely client-side, deployed as a static site via GitHub
Pages, and installed on an iPad as a home-screen web app (offline-capable via
`sw.js`).

## Structure

- [src/template.html](src/template.html) — the actual source. Edit this.
  Everything is hand-written except for the Rive runtime, which is replaced
  by the placeholder `<!--RIVE_RUNTIME-->`.
- [build.py](build.py) — generates `index.html` from the template by
  downloading the two Rive runtimes (`@rive-app/webgl2` and
  `@rive-app/canvas`) from npm, base64-encoding their `rive.js`/`rive.wasm`
  payloads, and inlining them into the placeholder.
- `index.html` — **generated**. This is what GitHub Pages actually serves.
  Do not hand-edit it — edit `src/template.html` and rebuild instead.
- `sw.js`, `manifest.webmanifest`, `icon-*.png`, `can-it-run.html` — static
  assets served as-is, not touched by the build.

The two runtimes are embedded inline (rather than fetched at runtime) so the
app works fully offline once cached by the service worker.

## Building

Requires Node/npm (to fetch the runtime packages) and Python 3.

```bash
python build.py
```

This pulls the *latest* published versions of `@rive-app/webgl2` and
`@rive-app/canvas`. To pin exact versions instead:

```bash
python build.py --webgl2 2.41.0 --canvas 2.41.0
```

The script prints both runtime versions and the final `index.html` size, and
cleans up the downloaded tarballs/extracted packages when it's done. Commit
the regenerated `index.html` alongside any `src/template.html` changes.

## Deploying an update

1. Edit `src/template.html`.
2. **Bump `VERSION` in [sw.js](sw.js).** The service worker caches the app
   shell by that version string — if you don't bump it, the iPad home-screen
   app will keep serving the old cached `index.html` indefinitely, even
   after you push a fix.
3. Run `python build.py` (optionally pinning runtime versions) to regenerate
   `index.html`.
4. Commit and push `src/template.html`, `index.html`, and `sw.js` together.

GitHub Pages must stay configured to deploy from the `main` branch, root
(`/`) folder — that's where `index.html` and `sw.js` need to live for the
site and the service worker scope to work.

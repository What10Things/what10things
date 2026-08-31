# What10Things — Three.js + Flow video design preview

## What this is

A static, self-contained design preview in `preview/threejs/`. It is an
experiment: it takes **one existing Google Flow / Veo generated 8-second
sequence** and turns it into a scroll-driven knowledge surface with a restrained
Three.js spatial layer around it. It is not a live production feature and makes
no claim of finished functionality. The page is `noindex,nofollow,noarchive`
and carries the visible label **"Design preview · Three.js + Flow video"**.

## The Flow video is the frame source — confirmed

The only visual source on the page is the existing generated clip:

| Asset | Role |
| --- | --- |
| `media/source-flow-video.mp4` | The exact Google Flow / Veo clip. Used **only** by the "Play original Flow clip" control. Never fetched or seeked for the scroll interaction. |
| `media/frames/frame-001.webp … frame-096.webp` | 96 frames decoded once from that exact clip at 12&nbsp;fps. These drive the scroll-controlled visual. They are not replacement artwork. |
| `media/source-poster.jpg` | Poster for the `<video>` element in the play-original modal. |

There is **no synthetic/generated Three.js scene standing in for the video**.
The amber constellation you see on the plane is always a real decoded frame of
the generated clip.

## Architecture

### One offscreen 16:9 source canvas → CanvasTexture → plane

`src/main.js` creates a single `<canvas>` (640×360, 16:9) that is **never added
to the DOM**. The 96 WebP frames are loaded as `Image` objects. On every render
tick the frame that corresponds to the current scroll position is drawn into
that one canvas with `drawImage`, and the `THREE.CanvasTexture` wrapping the
canvas is marked `needsUpdate = true`.

That texture is applied to a `THREE.PlaneGeometry` with a `MeshBasicMaterial`
(no lighting, `toneMapped: false`, sRGB) so the generated footage is reproduced
faithfully. The plane is cover-fitted to the viewport every resize so the Flow
footage stays edge-to-edge and dominant. This is the persistent main visual on
every device, **including mobile Safari** — the scroll interaction never depends
on `HTMLVideoElement` seeking.

### Restrained genuine 3D treatment

Around the plane:

- A `PerspectiveCamera` that moves **through** the composition as chapters
  advance: `z` travels 4.7 → 3.2, with a gentle lateral arc and downward drift,
  plus a small clamped pointer parallax.
- Exactly **10** small additive light nodes (`SphereGeometry`, r&nbsp;=&nbsp;0.05)
  arranged on a shallow ring that hugs the outer edge of the frame, sitting in
  front of the plane with real depth so they parallax against the footage.
- A few relationship lines (`LineSegments`): the orbit ring plus a handful of
  spokes to the centre, faint amber, additive, `depthWrite: false`.
- The spatial group rotates ≤ 0.5&nbsp;rad and shifts slightly in `z` across the
  whole scroll.

Nothing is layered over the centre of the footage; the nodes/lines are additive
glints, not occluders. No post-processing.

### Scroll → frame mapping

- `progress = clamp(scrollY / (scrollHeight − innerHeight), 0, 1)`
- `frameIndex = Math.round(progress × 95)` — deterministic.
- A `requestAnimationFrame` loop lerps a smoothed progress toward the target
  (factor 0.16) and **snaps** to the exact target when within 0.0009, so the
  final drawn frame always corresponds exactly to scroll position.
- Scrolling **down advances** the frames; scrolling **up reverses** them.
- Frames load **coarse-to-fine** (stride 16 → 8 → 4 → 2 → 1) so a near-match
  frame exists for any scroll position within the first moment; the exact frame
  replaces it as loading completes.

## Performance / accessibility

- DPR capped: ≤ 1.5 on mobile (`pointer: coarse` or width &lt; 700), ≤ 2 desktop.
- Modest geometry (1 plane, 10 low-poly spheres, one `LineSegments`), no
  post-processing, `powerPreference: "low-power"`.
- Rendering pauses on `document.hidden` (`visibilitychange` → cancel rAF),
  resumes on return.
- **`prefers-reduced-motion` or `Save-Data`**: the interactive path is never
  started. Only `frame-001.webp` is loaded (no 96-frame download), shown as a
  static image; no continuous 3D animation; `mode === "static"`, `frame === 0`.
- **WebGL failure**: a pre-flight `hasWebGL()` probe (and a `try/catch` around
  renderer creation) falls back silently to the same static first-frame view
  (`mode === "fallback"`).
- HTML text is a separate layer (real `<h1>/<h2>/<p>`) over a fixed
  full-viewport stage, for legibility and SEO. 44&nbsp;px controls, no hover
  dependency, no horizontal overflow at 390&nbsp;px portrait.

## QA surface — `window.__W10_THREE__`

Created synchronously on script load (readable before `ready`). Getter-backed:

| Field | Meaning |
| --- | --- |
| `ready` | Interactive: first needed frame drawn + loop running. Static/fallback: first frame handled. |
| `mode` | `"interactive"` \| `"static"` \| `"fallback"`. |
| `progress` | Smoothed scroll progress 0–1. |
| `frame` | 0-based index of the video-derived frame currently drawn (deterministic target once settled). |
| `frameCount` | `96`. |
| `source` | Always `"flow-video-frames"`. |
| `signature` | Hash of sampled pixels read back from **the same source canvas** that feeds `CanvasTexture`. Recomputed whenever the drawn frame changes — automated proof that the displayed video texture is really moving. |
| `webgl` | `true` only when a real WebGL context/renderer was created. |

## Build

`src/main.js` imports `three` as an npm module. No CDN. The workflow bundles it
with esbuild:

```
esbuild preview/threejs/src/main.js --bundle --minify --format=iife --outfile=preview/threejs/app.js
```

`index.html` loads `./app.js` with `defer`.

## Files

```
preview/threejs/
  index.html                  # marker: W10_THREEJS_FLOW_VIDEO_PREVIEW
  style.css
  src/main.js                 # three import + CanvasTexture + QA surface
  app.js                      # esbuild bundle output (regenerated by CI)
  .htaccess                   # noindex headers, mime types, caching, CSP
  CLAUDE_THREEJS_REPORT.md    # this file
  media/source-flow-video.mp4 # exact Flow clip (play-original control only)
  media/source-poster.jpg
  media/frames/frame-001..096.webp
```

## Local verification performed

Bundled with esbuild + `node --check`, then Playwright (headless Chromium):

- iPhone (390×844, iOS UA) and desktop (1440×1000): `ready` within timeout,
  `source === "flow-video-frames"`, `webgl === true`, no console/page errors,
  no horizontal overflow. Scroll to 72–80% → `frame` 68–76; scroll back to
  10–18% → `frame` drops to ~9–17. `signature` changes on every move, and the
  `#three-stage canvas` screenshot hash changes forward and in reverse.
- Reduced motion: `mode === "static"`, `frame === 0`, no 96-frame load.
- WebGL disabled: `mode === "fallback"`, static first frame, `errs: []`.
- "Play original Flow clip": attaches `./media/source-flow-video.mp4` to the
  `<video>` only on click; that file is referenced nowhere else.

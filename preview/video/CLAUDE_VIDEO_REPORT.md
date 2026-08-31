# W10_FLOW_VIDEO_SCROLL_PREVIEW — implementation report

Isolated, `noindex` experimental preview proving that the Flow-generated clip
(`media/knowledge-constellation.mp4`) can be driven frame-by-frame by page scroll:
forward on scroll down, naturally backward on scroll up. Nothing here touches the
production site.

## Files

| File | Role |
|---|---|
| `index.html` | Semantic document: pinned video stage + four scrolling copy "beats" + outro CTA. Marker comment, `robots noindex,nofollow,noarchive`, `w10-preview` meta. |
| `style.css` | Knowledge Constellations visual system, mobile-first, desktop composition, static/reduced fallbacks. |
| `app.js` | Vanilla scroll-scrub controller with rAF smoothing. Exposes `window.__W10_SCROLL_PROGRESS__`. |
| `.htaccess` | `X-Robots-Tag: noindex, nofollow, noarchive`, MP4 MIME type, long cache for media, `-Indexes`. |

## How the scrub works

1. The stage is `position: sticky; top: 0; height: 100svh` inside `.scroll-track`.
   `.beats` uses `margin-top: -100svh` so the copy scrolls over the pinned stage.
2. On `scroll` / `resize`, `measure()` computes
   `target = clamp(-track.top / (track.height - viewport), 0, 1)`.
3. A single `requestAnimationFrame` loop eases a `shown` value toward `target`
   (`shown += (target - shown) * 0.16`) and snaps when within `0.0004`. The loop
   stops itself when `shown === target` and no seek is pending, and restarts on
   the next scroll — no permanent rAF churn.
4. Each frame, `shown` is written to `window.__W10_SCROLL_PROGRESS__` and mapped to
   `video.currentTime = shown * duration`.
5. `seekTo()` only issues a seek when the delta exceeds **half a frame**
   (`0.5 / 24 s`) and no seek is in flight (`seeking` flag set on `seeking`,
   cleared on `seeked`). This keeps a fast flick of the wheel to a handful of
   seeks instead of hundreds. `fastSeek()` is used when available.
6. Scroll direction is derived from the sign of `target − lastTarget` and shown in
   the header transport readout (`▼ FWD` / `▲ REV` / `■ HOLD`, HOLD after 550 ms
   of no movement). Scrolling up walks `currentTime` down, so the clip runs in
   reverse at the speed of the gesture.

The video is never played; `video.pause()` is asserted each frame. Audio is
irrelevant (`muted`), and nothing depends on it.

## Signature element

The page is treated as a piece of editing equipment. The **scrub rail** is a
diagrammatic transport: a hairline scale with a rotated-square playhead (the
constellation's diamond motif), per-beat tick marks, and a telecine readout
`FRAME 072 / 192 · 0:03.0` in amber. It sits along the bottom on mobile and
becomes a left-edge vertical instrument on desktop. It embodies the brief — the
page's whole job is to prove scroll-scrubbing, so the transport state is the hero.

## Editorial continuity

Continues `preview/site` (Knowledge Constellations):

- **Colour** — charcoal `#090b0e` / `#05070a`, paper `#f3f0e8`, muted `#9b9992`,
  hairline rules. Two restrained accents with distinct jobs: **lime `#b9ff3f`**
  for interactive state (progress fill, playhead, links, focus) and
  **amber `#ffd052`** reserved for the frame/timecode numerals and eyebrow index.
- **Type** — system sans (Inter stack, matching the existing preview; no web-font
  request, keeps within the site CSP `font-src 'self'`). Personality comes from
  the treatment: display at weight 650, `line-height .98`, `letter-spacing -.055em`,
  paired with a monospace utility face for eyebrows, the transport and the readout.
- **Structure** — numbering is real here (`01…04` are timecoded points along one
  8-second reel), so the numbered eyebrows carry information rather than decorate.
- No glass cards, no gradients, no bento. Copy sits on a solid charcoal panel with
  a single hairline top rule and a 34px lime tick — diagrammatic, not floating.

## Mobile (tested against 390×844 portrait in layout math)

- Stage is full-bleed and stays a full-viewport anchor; `object-position: 50% 34%`
  biases the focal content into the clear upper ~60%.
- Copy lives on a bottom panel (`max-width: 33rem`, full width minus gutter) that
  never covers more than the lower third — the focal area stays visible.
- Scrub rail is a fixed 52px bottom bar with `env(safe-area-inset-bottom)` padding;
  beats and outro carry matching bottom padding so nothing hides behind it.
- `overflow-x: hidden` on `body`; no element exceeds the viewport width.

## Desktop (≥ 900px)

- Deliberately composed, not an upscaled phone: the stage is full-bleed cinema,
  the scrub rail becomes a 66px left-edge instrument with a vertical
  `writing-mode` label and stacked readout, and the copy is locked to a ~30rem
  column at lower-left offset past the rail. Large intentional negative space
  upper-right.

## Performance

- `preload="metadata"` in markup; `app.js` upgrades to `preload="auto"` only in
  video mode, because scrubbing genuinely needs the media body buffered
  (clip is 1280×720, H.264, ~4.0 MB, 8 s).
- Seeks are throttled to the in-flight guard + half-frame threshold; a fast scroll
  produces on the order of 5–15 seeks, not one per scroll event.
- rAF loop is self-terminating; no work while the page is idle.
- Media is served with a 30-day cache header.

## Accessibility

- Semantic landmarks (`header` / `main` / `aside`), one `h1` then section `h2`s,
  eyebrows are plain text not headings.
- Decorative layers (`stage`, `scrub-rail`, transport) are `aria-hidden` and the
  `<video>` is `tabindex="-1"` — assistive tech reads the prose, which is the
  actual content and is complete without the video.
- Visible `:focus-visible` outline (2px lime, 3px offset). Skip link to the copy.
- Interactive targets ≥ 44px: brand link, skip link, the CTA (46px).
- Contrast: paper `#f3f0e8` on `#090b0e` (~17:1); body `#c7c4bc` (~11:1); muted
  mono labels `#9b9992` (~6:1). `prefers-contrast: more` lifts rules and muted text.
- No horizontal overflow at any width tested in the layout.

## Graceful degradation

| Condition | Behaviour |
|---|---|
| `prefers-reduced-motion: reduce` | `mode = static`: video hidden, poster shown, scrub controller disabled, rail collapses to a static note. All copy readable, sections stack normally. `__W10_SCROLL_PROGRESS__` still tracks scroll. |
| `Save-Data` header / `prefers-reduced-data: reduce` | Same static path; the `<source>` is removed and `video.load()` called so the 4 MB clip is never fetched (only the poster JPEG). |
| No `<video>` / MP4 support | Static path. |
| `loadedmetadata` never fires within 9 s | Falls back to static with an explanatory note. |
| `video` `error` event | Falls back to static with a note; poster `<img>` remains. |
| Repeated seek stalls (5 × 3 s watchdog with no `seeked`) | Falls back to static — the page never freezes waiting on a seek. |
| JavaScript disabled | `<noscript>` amber notice; CSS sticky still pins the poster while the copy scrolls; everything readable. |
| Before metadata is ready | `is-loading` state shows an indeterminate hairline bar and "Loading sequence…". |

## Limitations / notes

- **Seek granularity depends on the clip's GOP.** The supplied MP4 was not
  re-encoded (media files must not be altered). If keyframes are sparse, reverse
  scrubbing on some browsers can look slightly steppy. A keyframe-dense re-encode
  (`ffmpeg -g 6 -x264-params keyint=6:min-keyint=6`) or a fragmented MP4 would
  make it frame-accurate. This is noted rather than fixed by design constraint.
- **FPS is assumed to be 24** (verified with `ffprobe`: `24/1`, 192 frames, 8.0 s)
  and hard-coded as `FPS` for the frame counter. `duration` is read live from the
  element; the frame count adapts if it differs.
- Firefox has no `HTMLVideoElement.fastSeek`; it uses precise `currentTime`
  assignment, which is accurate but a touch heavier — the throttle keeps it smooth.
- iOS Safari decodes the first `currentTime` seek only after a load; the loading
  state covers that gap and the watchdog covers the pathological case.
- This is a **design preview only**. The single external link is the real
  What10Things homepage; no unfinished features are implied anywhere in the copy.

## Checks run locally

- `node --check app.js` → OK.
- CSS brace balance → balanced.
- HTML block-tag open/close parity (63/63); marker comment and `robots` meta present.
- Every `getElementById` in `app.js` resolves to an element in `index.html`.
- No inline `on*=` handlers, no `style=` attributes, no `<style>`/inline `<script>`
  bodies — stays within the site's `script-src 'self'` / `style-src 'self'` CSP.
- Asset paths (`media/*.mp4`, `media/*.jpg`, `style.css`, `app.js`) resolve; MP4
  serves `200`, 4,070,324 bytes over a local static server.
- `.htaccess` contains the marker and `X-Robots-Tag "noindex, nofollow, noarchive"`.

Not deployed. Media files untouched.

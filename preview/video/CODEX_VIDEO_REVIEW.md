# Codex independent video implementation review

## Scope and outcome

Reviewed `index.html`, `style.css`, `app.js`, `.htaccess`,
`CLAUDE_VIDEO_REPORT.md`, and the supplied MP4. Changes are confined to
`preview/video/`; the Knowledge Constellations presentation, visible copy,
media assets, and preview `noindex` controls remain intact.

The implementation is fit to proceed to hands-on browser QA. The deterministic
mapping remains `clamp(-track.top / (track.height - viewport.height), 0, 1)`:
downward scroll increases the target and upward scroll decreases it. Scroll
events only measure and schedule work; video seeks occur from the animation
frame controller.

## Findings and patches

- **Reduced motion/data media leak:** the parser-visible MP4 `src` could start a
  metadata request before deferred JavaScript detected reduced-motion,
  `prefers-reduced-data`, or Save-Data. The source is now held in `data-src`,
  `preload="none"` is the HTML default, and JavaScript attaches it only in video
  mode. Static mode therefore loads the poster, not the MP4.
- **iOS readiness:** retained declarative `muted` and `playsinline`, added the
  legacy `webkit-playsinline` hint, and asserts `muted`, `defaultMuted`, and
  `playsInline` before loading. Scrubbing becomes ready on `loadeddata` (a
  decoded first frame), while `loadedmetadata` is used to obtain duration.
- **Seek determinism and load:** removed approximate `fastSeek()`. Precise
  `currentTime` writes are serialized, with in-flight requests coalesced to the
  newest desired time. This avoids a backlog during rapid touch/wheel input and
  keeps forward/reverse endpoints deterministic.
- **rAF smoothing:** replaced frame-count-dependent easing with elapsed-time
  damping, giving comparable response on 60 Hz and 120 Hz displays. The loop no
  longer spins solely because a seek is in flight; `seeked` restarts it.
- **Failure behavior:** load/decode errors, timeout, and repeated seek stalls
  retain the poster and readable static layout. Source URLs are detached during
  fallback.
- **Width resilience:** horizontal clipping is applied at both root and body;
  fixed-header children may shrink; the tag cannot wrap; and the scrub scale has
  a safe minimum. The existing mobile and desktop layouts have no intrinsic
  width exceeding 390 px or 1440 px.
- **Accessibility/noindex:** semantic headings and landmarks, visible focus,
  skip link, decorative video UI exclusion, muted/no-audio operation, robots
  meta, and `X-Robots-Tag` are preserved.

## Media inspection and checks

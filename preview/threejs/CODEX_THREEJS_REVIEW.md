# Codex independent Three.js review

## Scope and result

Reviewed `index.html`, `style.css`, `src/main.js`,
`CLAUDE_THREEJS_REPORT.md`, and `ANTIGRAVITY_THREEJS_REVIEW.md` as a WebGL and
mobile-performance implementation. The preview is fit to proceed to browser QA
after the defects below were patched.

## Architecture verified

- The non-negotiable source pipeline remains intact: 96 WebP frames derived
  from the existing Flow/Veo MP4 are selected from scroll progress, drawn into
  one 640x360 source canvas, and that same canvas is wrapped by
  `THREE.CanvasTexture` and displayed on the dominant plane.
- Forward and reverse scroll use deterministic `round(progress * 95)` frame
  selection. No `HTMLVideoElement` seeking is used by the scroll path.
- The source MP4 remains attached only after the explicit original-clip button
  is activated. The modal video retains `controls`, `playsinline`, and
  `preload="none"`.
- Reduced-motion and Save-Data enter the static first-frame path before WebGL or
  the 96-frame loader starts. WebGL creation failure also retains the static
  fallback. Noindex metadata and response-header configuration remain present.
- GPU work is restrained: one unlit video plane, ten low-poly nodes, one line
  mesh, no post-processing, disabled mipmaps, low-power preference, and capped
  DPR. The 2.6 MB frame set has a bounded decoded-image cost (approximately 84
  MiB at 640x360 RGBA), appropriate for this explicit preview but worth
  observing on older physical iPhones during QA.

## Defects patched

- Stopped the requestAnimationFrame loop after scroll and pointer easing settle;
  scroll, pointer movement, resize, and visibility return wake it again. This
  removes the previous permanent full-screen GPU workload.
- Made readiness follow the first frame actually drawn, so failure of the
  initially prioritised request cannot leave a functioning nearest-frame render
  permanently reporting not ready.
- Added a WebGL context-loss handler that stops rendering and exposes the static
  fallback.
- Added modal background-scroll locking and keyboard focus containment while
  preserving Escape/backdrop close and focus restoration.

## Validation

Rebuilt `app.js` from the patched source with esbuild and passed `node --check`
on both source and bundle. The supplied first Playwright evidence already
establishes changing source signatures and WebGL canvas hashes on iPhone
simulation and desktop, reverse scrubbing, and a static reduced-motion path.
Physical Safari QA should additionally exercise context loss/memory pressure
and modal keyboard behavior.

VERDICT: PASS

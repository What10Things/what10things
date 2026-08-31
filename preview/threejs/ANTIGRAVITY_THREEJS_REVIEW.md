# Independent Architecture Review: Three.js + Flow Video Design Preview

### 1. Visual Source & Frame Pipeline Integrity
* **Source Fidelity:** The 96 WebP frames (`media/frames/frame-001.webp` through `frame-096.webp`) decoded from the original Google Flow / Veo 8-second MP4 serve as the visual substrate. No synthetic Three.js geometries replace the footage.
* **CanvasTexture Implementation:** The implementation creates a single offscreen 16:9 2D canvas (`640×360`), updates it via `CanvasRenderingContext2D.drawImage()`, and connects it directly to `THREE.CanvasTexture`. Setting `generateMipmaps = false`, `minFilter = LinearFilter`, `magFilter = LinearFilter`, and `colorSpace = SRGBColorSpace` ensures faithful color reproduction and prevents GPU mipmap generation overhead.
* **Scroll-to-Frame scrub mapping:** Scroll progress $p \in [0, 1]$ maps deterministically to `Math.round(p * 95)`. Forward and backward scrolling smoothly drives frame selection with snapping logic to guarantee precision at rest.

### 2. Mobile Safari & Spatial Rendering Suitability
* **Safari Video Scrubbing Mitigation:** By completely decoupling scroll interaction from `HTMLVideoElement.currentTime` seeking and relying on decoded WebP frames rendered to a 2D canvas texture, the implementation eliminates mobile Safari’s video seek stutter, keyframe lag, and black-frame flash.
* **Spatial Restraint:** The 3D layer remains strictly subservient to the Flow footage. Camera movement ($z$-axis transition from $4.7 \to 3.2$ with subtle yaw/drift) and the 10 additive spatial nodes (`SphereGeometry` with $r = 0.05$) hug the periphery without occluding central footage details.
* **Touch & Viewport Compliance:** Standard 44px minimum touch targets are enforced on controls (`.play-original` and `.flow-modal__close`), `overflow-x: hidden` prevents horizontal scroll jitter, and viewport-fit is accommodated.

### 3. Memory, Network & Render-Loop Strategy
* **Coarse-to-Fine Asset Loading:** Frame loading is intelligently prioritized: the frame at the current scroll position loads first, followed by frame 0, then a strided pyramid (`step = 16, 8, 4, 2, 1`). This provides immediate scrub feedback across the entire timeline before all 96 frames (~2.6MB) finish loading.
* **Jank Prevention:** Frames use `img.decoding = "async"`, and `nearestLoaded(want)` provides a stable fallback frame during rapid scrubbing while images buffer.
* **DPR & Render Loop Discipline:** Device pixel ratio is capped at `1.5` on mobile/coarse pointer devices and `2.0` on desktop. The `requestAnimationFrame` loop uses progressive lerping (factor 0.16) with a definite settling snap (`diff < 0.0009`), `powerPreference: "low-power"`, and halts on background tabs via `visibilitychange`.

### 4. Accessibility, Fallbacks & Media Isolation
* **Reduced Motion & Save-Data:** `prefers-reduced-motion: reduce` and `navigator.connection.saveData` bypass WebGL and 96-frame downloads entirely. They immediately invoke `enterStatic("static")`, fetching only `frame-001.webp` as a calm background.
* **WebGL Fallback & Noscript:** A pre-flight `hasWebGL()` probe and `try/catch` guard renderer creation, silently shifting to `stage-static` on failure. A `<noscript>` image handles disabled JavaScript.
* **DOM Accessibility:** The visual stage is isolated with `aria-hidden="true"`. All editorial content resides in a semantic HTML layer (`<main>`, `<header>`, `<section>`, `<h1>`, `<h2>`, `<p>`) with skip navigation. The video modal adheres to WAI-ARIA dialog practices (focus management, escape key listener, backdrop click dismiss).
* **Source MP4 Isolation:** `media/source-flow-video.mp4` is attached to the `<video>` element exclusively on user interaction inside `wirePlayOriginal()`, ensuring zero network or memory contention during scroll.

---

VERDICT: PASS

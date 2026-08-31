/*
 * What10Things — Three.js + Flow video design preview
 * ---------------------------------------------------
 * The ONLY visual source on this page is the existing Google Flow / Veo clip
 * (media/source-flow-video.mp4), decoded once into 96 WebP frames
 * (media/frames/frame-001.webp .. frame-096.webp).
 *
 * Scroll interaction:
 *   - scroll progress (0..1) is mapped deterministically to a frame index
 *   - the selected frame is drawn into ONE offscreen 16:9 2D canvas
 *   - a THREE.CanvasTexture wrapping that canvas is marked needsUpdate
 *   - the texture is shown on a plane that stays dominant in the composition
 *
 * The source MP4 is NEVER used for the scroll interaction. It is only attached
 * to the <video> element when the visitor presses "Play original Flow clip".
 *
 * Mobile Safari uses this exact CanvasTexture path — no HTMLVideoElement seeking.
 */

import * as THREE from "three";

/* -------------------------------------------------------------------------- */
/* Config                                                                     */
/* -------------------------------------------------------------------------- */

const FRAME_COUNT = 96;
const FRAME_DIR = "./media/frames/";
const SOURCE_W = 640; // offscreen source canvas — 16:9
const SOURCE_H = 360;
const PLANE_W = 3.556; // 16:9 base plane in world units
const PLANE_H = 2.0;
const NODE_COUNT = 10; // spec: no more than ten small spatial nodes

/* -------------------------------------------------------------------------- */
/* QA / proof surface — created synchronously so automation can read it early */
/* -------------------------------------------------------------------------- */

const state = {
  ready: false,
  mode: "interactive", // interactive | static | fallback
  progress: 0,
  frame: 0, // 0-based index into the video-derived frames
  frameCount: FRAME_COUNT,
  source: "flow-video-frames",
  signature: null, // hash of sampled pixels from the source canvas
  webgl: false,
};

window.__W10_THREE__ = {
  get ready() { return state.ready; },
  get mode() { return state.mode; },
  get progress() { return state.progress; },
  get frame() { return state.frame; },
  get frameCount() { return state.frameCount; },
  get source() { return state.source; },
  get signature() { return state.signature; },
  get webgl() { return state.webgl; },
};

/* -------------------------------------------------------------------------- */
/* One offscreen 16:9 source canvas — shared by CanvasTexture and signature   */
/* -------------------------------------------------------------------------- */

const sourceCanvas = document.createElement("canvas");
sourceCanvas.width = SOURCE_W;
sourceCanvas.height = SOURCE_H;
const sctx = sourceCanvas.getContext("2d", { willReadFrequently: true });
sctx.fillStyle = "#0a0a0d";
sctx.fillRect(0, 0, SOURCE_W, SOURCE_H);

let drawnFrame = -1;

function drawFrameToSource(img) {
  // cover-fit the frame into the 16:9 source canvas (frames are already 16:9)
  sctx.drawImage(img, 0, 0, SOURCE_W, SOURCE_H);
}

// Sparse deterministic hash of the source-canvas pixels. Changes whenever the
// drawn frame changes — this is the automated proof that the displayed texture
// is really moving through the generated video frames.
function computeSignature() {
  let data;
  try {
    data = sctx.getImageData(0, 0, SOURCE_W, SOURCE_H).data;
  } catch (e) {
    return null;
  }
  let h = 0x811c9dc5;
  let sum = 0;
  for (let i = 0; i < data.length; i += 997 * 4) {
    const v = data[i] + data[i + 1] * 3 + data[i + 2] * 7;
    sum += v;
    h ^= v;
    h = (h * 0x01000193) >>> 0;
  }
  return h.toString(16).padStart(8, "0") + "-" + (sum % 100000).toString(16);
}

function setDrawnFrame(index, img) {
  drawFrameToSource(img);
  drawnFrame = index;
  state.frame = index;
  state.signature = computeSignature();
  if (canvasTexture) canvasTexture.needsUpdate = true;
  state.ready = true;
}

/* -------------------------------------------------------------------------- */
/* Scroll progress                                                            */
/* -------------------------------------------------------------------------- */

function readScrollProgress() {
  const doc = document.documentElement;
  const max = doc.scrollHeight - window.innerHeight;
  if (max <= 0) return 0;
  return Math.min(1, Math.max(0, window.scrollY / max));
}

// Deterministic mapping: progress -> frame index (0 .. FRAME_COUNT-1)
function progressToFrame(p) {
  return Math.round(p * (FRAME_COUNT - 1));
}

/* -------------------------------------------------------------------------- */
/* Mode selection                                                             */
/* -------------------------------------------------------------------------- */

const prefersReducedMotion =
  window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const conn = navigator.connection || navigator.webkitConnection || navigator.mozConnection;
const saveData = !!(conn && conn.saveData);

const stageEl = document.getElementById("three-stage");
const canvasEl = document.getElementById("three-canvas");
const staticEl = document.getElementById("stage-static");
const staticImg = document.getElementById("stage-static-img");

/* -------------------------------------------------------------------------- */
/* Static path — reduced motion, Save-Data, or WebGL failure                  */
/* -------------------------------------------------------------------------- */

function enterStatic(mode) {
  state.mode = mode; // "static" or "fallback"
  state.webgl = false;
  state.progress = 0;
  state.frame = 0;
  if (canvasEl) canvasEl.hidden = true;
  if (staticEl) staticEl.hidden = false;

  // Load only the FIRST video-derived frame — no 96-frame download, no loop.
  const img = new Image();
  img.decoding = "async";
  img.onload = () => {
    drawFrameToSource(img);
    drawnFrame = 0;
    state.frame = 0;
    state.signature = computeSignature();
    state.ready = true;
  };
  img.onerror = () => { state.ready = true; };
  img.src = FRAME_DIR + "frame-001.webp";
}

/* -------------------------------------------------------------------------- */
/* Interactive Three.js path                                                  */
/* -------------------------------------------------------------------------- */

let renderer = null;
let scene = null;
let camera = null;
let canvasTexture = null;
let plane = null;
let spatialGroup = null;
let rafId = 0;
let running = false;
let settledTicks = 0;

const frames = new Array(FRAME_COUNT).fill(null); // HTMLImageElement per frame
let framesLoaded = 0;

let smoothProgress = 0;
let targetProgress = 0;
const pointer = { x: 0, y: 0 }; // -1..1 parallax input
const parallax = { x: 0, y: 0 };

function isMobileViewport() {
  return (
    (window.matchMedia && window.matchMedia("(pointer: coarse)").matches) ||
    window.innerWidth < 700
  );
}

// Probe WebGL support first so the fallback path stays silent (avoids
// three.js logging its own context-creation errors to the console).
function hasWebGL() {
  try {
    const c = document.createElement("canvas");
    return !!(
      window.WebGLRenderingContext &&
      (c.getContext("webgl2") || c.getContext("webgl") || c.getContext("experimental-webgl"))
    );
  } catch (e) {
    return false;
  }
}

function initThree() {
  if (!hasWebGL()) {
    enterStatic("fallback");
    return;
  }
  try {
    renderer = new THREE.WebGLRenderer({
      canvas: canvasEl,
      antialias: true,
      alpha: true,
      powerPreference: "low-power",
    });
  } catch (err) {
    console.warn("[w10] WebGL unavailable, using static fallback:", err && err.message);
    enterStatic("fallback");
    return;
  }
  if (!renderer.getContext()) {
    enterStatic("fallback");
    return;
  }

  const dprCap = isMobileViewport() ? 1.5 : 2;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, dprCap));
  renderer.setSize(window.innerWidth, window.innerHeight, false);
  if ("outputColorSpace" in renderer) renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.setClearColor(0x07070a, 0);

  state.webgl = true;

  canvasEl.addEventListener("webglcontextlost", (event) => {
    event.preventDefault();
    stop();
    enterStatic("fallback");
  }, { once: true });

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(
    42,
    window.innerWidth / window.innerHeight,
    0.1,
    100
  );
  camera.position.set(0, 0, 4.6);

  // --- The generated Flow footage: CanvasTexture on a plane (the main visual) ---
  canvasTexture = new THREE.CanvasTexture(sourceCanvas);
  canvasTexture.colorSpace = THREE.SRGBColorSpace;
  canvasTexture.minFilter = THREE.LinearFilter;
  canvasTexture.magFilter = THREE.LinearFilter;
  canvasTexture.generateMipmaps = false;
  canvasTexture.needsUpdate = true;

  const planeMat = new THREE.MeshBasicMaterial({
    map: canvasTexture,
    toneMapped: false,
  });
  plane = new THREE.Mesh(new THREE.PlaneGeometry(PLANE_W, PLANE_H), planeMat);
  scene.add(plane);

  // --- Restrained spatial layer: <=10 light nodes + a few relationship lines ---
  spatialGroup = new THREE.Group();
  const nodeGeo = new THREE.SphereGeometry(0.05, 16, 12);
  const nodeMat = new THREE.MeshBasicMaterial({
    color: 0xffcf8a,
    transparent: true,
    opacity: 0.55,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    toneMapped: false,
  });
  const nodePositions = [];
  for (let i = 0; i < NODE_COUNT; i++) {
    const a = (i / NODE_COUNT) * Math.PI * 2 + 0.35;
    // ring hugs the outer edge of the frame so the footage centre stays clear
    const rx = 2.15 + 0.12 * Math.sin(i * 1.7);
    const ry = 1.28 + 0.1 * Math.cos(i * 2.3);
    const p = new THREE.Vector3(
      Math.cos(a) * rx,
      Math.sin(a) * ry,
      0.35 + 0.5 * Math.sin(i * 1.3) // all in front of the plane, shallow depth
    );
    nodePositions.push(p);
    const m = new THREE.Mesh(nodeGeo, nodeMat);
    m.position.copy(p);
    spatialGroup.add(m);
  }

  const linePts = [];
  for (let i = 0; i < NODE_COUNT; i++) {
    linePts.push(nodePositions[i], nodePositions[(i + 1) % NODE_COUNT]); // orbit ring
    if (i % 3 === 0) linePts.push(nodePositions[i], new THREE.Vector3(0, 0, 0.2)); // spokes
  }
  const lineGeo = new THREE.BufferGeometry().setFromPoints(linePts);
  const lineMat = new THREE.LineBasicMaterial({
    color: 0xf6a63c,
    transparent: true,
    opacity: 0.22,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    toneMapped: false,
  });
  spatialGroup.add(new THREE.LineSegments(lineGeo, lineMat));
  scene.add(spatialGroup);

  fitPlaneToView();

  window.addEventListener("resize", onResize, { passive: true });
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("pointermove", onPointerMove, { passive: true });
  document.addEventListener("visibilitychange", onVisibility);

  // Kick off frame loading and the render loop.
  targetProgress = readScrollProgress();
  smoothProgress = targetProgress;
  loadFrames();
  start();
}

function fitPlaneToView() {
  if (!plane || !camera) return;
  const dist = 4.6; // nominal camera distance for cover fit
  const vFov = THREE.MathUtils.degToRad(camera.fov);
  const worldH = 2 * Math.tan(vFov / 2) * dist;
  const worldW = worldH * camera.aspect;
  const planeAspect = PLANE_W / PLANE_H;
  let w;
  let h;
  if (worldW / worldH > planeAspect) {
    w = worldW;
    h = worldW / planeAspect;
  } else {
    h = worldH;
    w = worldH * planeAspect;
  }
  const overscan = 1.08;
  plane.scale.set((w / PLANE_W) * overscan, (h / PLANE_H) * overscan, 1);
}

function onResize() {
  if (!renderer || !camera) return;
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  const dprCap = isMobileViewport() ? 1.5 : 2;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, dprCap));
  renderer.setSize(window.innerWidth, window.innerHeight, false);
  fitPlaneToView();
  start();
}

function onScroll() {
  targetProgress = readScrollProgress();
  if (!running) start(); // resume if we had paused
}

function onPointerMove(e) {
  pointer.x = (e.clientX / window.innerWidth) * 2 - 1;
  pointer.y = (e.clientY / window.innerHeight) * 2 - 1;
  start();
}

function onVisibility() {
  if (document.hidden) {
    stop();
  } else {
    start();
  }
}

/* ---- Frame loading ---- */

function frameUrl(i) {
  return FRAME_DIR + "frame-" + String(i + 1).padStart(3, "0") + ".webp";
}

function loadFrames() {
  // Load the frame we need first, then frame 0, then fill the whole range
  // coarse-to-fine so that after a moment there is a frame near ANY scroll
  // position (not just a contiguous block from the start).
  const first = progressToFrame(readScrollProgress());
  const order = [first];
  if (first !== 0) order.push(0);
  for (const step of [16, 8, 4, 2, 1]) {
    for (let i = 0; i < FRAME_COUNT; i += step) {
      if (order.indexOf(i) === -1) order.push(i);
    }
  }

  let cursor = 0;
  const CONCURRENCY = 8;

  function next() {
    if (cursor >= order.length) return;
    const idx = order[cursor++];
    const img = new Image();
    img.decoding = "async";
    img.onload = () => {
      frames[idx] = img;
      framesLoaded++;
      // If this is the frame we currently need and nothing better is drawn yet.
      const want = progressToFrame(smoothProgress);
      if (idx === want || (drawnFrame === -1 && idx === first)) {
        setDrawnFrame(idx, img);
      }
      next();
    };
    img.onerror = () => {
      framesLoaded++;
      next();
    };
    img.src = frameUrl(idx);
  }

  for (let c = 0; c < CONCURRENCY; c++) next();
}

// Pick the nearest already-loaded frame to a desired index.
function nearestLoaded(want) {
  if (frames[want]) return want;
  for (let d = 1; d < FRAME_COUNT; d++) {
    if (frames[want - d]) return want - d;
    if (frames[want + d]) return want + d;
  }
  return -1;
}

/* ---- Render loop ---- */

function start() {
  if (running || document.hidden || !renderer) return;
  running = true;
  settledTicks = 0;
  rafId = requestAnimationFrame(tick);
}

function stop() {
  running = false;
  if (rafId) cancelAnimationFrame(rafId);
  rafId = 0;
}

function tick() {
  if (!running) return;
  rafId = requestAnimationFrame(tick);

  // rAF smoothing toward the scroll target; snap when close so the final
  // frame deterministically corresponds to scroll progress.
  const diff = targetProgress - smoothProgress;
  if (Math.abs(diff) < 0.0009) {
    smoothProgress = targetProgress;
  } else {
    smoothProgress += diff * 0.16;
  }
  state.progress = smoothProgress;

  // Select and draw the video-derived frame for this progress.
  const want = progressToFrame(smoothProgress);
  if (want !== drawnFrame) {
    const use = nearestLoaded(want);
    if (use !== -1 && use !== drawnFrame) {
      setDrawnFrame(use, frames[use]);
      // keep the reported index aligned with the deterministic target
      state.frame = frames[want] ? want : use;
    } else if (frames[want]) {
      setDrawnFrame(want, frames[want]);
    }
  } else if (state.frame !== want && frames[want]) {
    state.frame = want;
  }

  // Camera moves subtly through the composition as chapters advance.
  const p = smoothProgress;
  parallax.x += (pointer.x * 0.16 - parallax.x) * 0.05;
  parallax.y += (pointer.y * 0.12 - parallax.y) * 0.05;
  const camZ = 4.7 - p * 1.5;
  const camX = Math.sin(p * Math.PI * 1.15) * 0.5 + parallax.x;
  const camY = 0.22 - p * 0.5 - parallax.y;
  camera.position.set(camX, camY, camZ);
  camera.lookAt(0, -0.04 + p * 0.12, 0);

  if (spatialGroup) {
    spatialGroup.rotation.z = p * 0.5;
    spatialGroup.position.z = -0.2 + p * 0.15;
  }

  renderer.render(scene, camera);

  // Nothing animates independently. Sleep once scroll and pointer easing
  // settle; input, resize and visibility events wake the loop again.
  const progressSettled = Math.abs(targetProgress - smoothProgress) < 0.0009;
  const parallaxSettled =
    Math.abs(pointer.x * 0.16 - parallax.x) < 0.0005 &&
    Math.abs(pointer.y * 0.12 - parallax.y) < 0.0005;
  settledTicks = progressSettled && parallaxSettled ? settledTicks + 1 : 0;
  if (settledTicks >= 2) stop();
}

/* -------------------------------------------------------------------------- */
/* "Play original Flow clip" — the ONLY use of the source MP4                  */
/* -------------------------------------------------------------------------- */

function wirePlayOriginal() {
  const btn = document.getElementById("play-original");
  const modal = document.getElementById("flow-modal");
  const video = document.getElementById("flow-video");
  if (!btn || !modal || !video) return;

  let lastFocus = null;

  function focusableElements() {
    return Array.from(modal.querySelectorAll(
      'button:not([disabled]), video[controls], [href], [tabindex]:not([tabindex="-1"])'
    )).filter((element) => element.getClientRects().length > 0);
  }

  function open() {
    lastFocus = document.activeElement;
    if (!video.getAttribute("src")) {
      // Attach the source MP4 here and nowhere else.
      video.setAttribute("src", "./media/source-flow-video.mp4");
    }
    modal.hidden = false;
    document.body.classList.add("modal-open");
    const closeBtn = modal.querySelector(".flow-modal__close");
    if (closeBtn) closeBtn.focus();
    video.play().catch(() => {});
  }

  function close() {
    video.pause();
    modal.hidden = true;
    document.body.classList.remove("modal-open");
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  btn.addEventListener("click", open);
  modal.addEventListener("click", (e) => {
    const t = e.target;
    if (t instanceof Element && t.hasAttribute("data-close")) close();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !modal.hidden) close();
    if (e.key === "Tab" && !modal.hidden) {
      const focusable = focusableElements();
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  });
}

/* -------------------------------------------------------------------------- */
/* Boot                                                                       */
/* -------------------------------------------------------------------------- */

wirePlayOriginal();

if (prefersReducedMotion || saveData) {
  enterStatic("static");
} else {
  initThree();
}

#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
preview = root / "preview" / "video"
app = preview / "app.js"
css = preview / "style.css"
ht = preview / ".htaccess"
deploy = root / ".github" / "workflows" / "deploy-w10-flow-video-preview.yml"

s = app.read_text()

if "const poster    =" not in s:
    s = s.replace(
        "  const video     = document.getElementById('video');\n",
        "  const video     = document.getElementById('video');\n"
        "  const poster    = stage ? stage.querySelector('.stage-poster') : null;\n"
        "  const staticPoster = poster ? poster.getAttribute('src') : '';\n",
    )

old_mode = """  const canPlayVideo    = !!video.canPlayType && (video.canPlayType('video/webm; codecs=\"vp8\"') !== '' || video.canPlayType('video/mp4') !== '');

  let mode = (prefersReduced || prefersLessData || saveData || !canPlayVideo) ? 'static' : 'video';
"""
new_mode = """  const canPlayVideo    = !!video.canPlayType && (video.canPlayType('video/webm; codecs=\"vp8\"') !== '' || video.canPlayType('video/mp4') !== '');
  const appleTouch = /iPad|iPhone|iPod/.test(navigator.userAgent) ||
                     (/Macintosh/.test(navigator.userAgent) && navigator.maxTouchPoints > 1);
  const FRAME_COUNT = 96;

  let mode = (prefersReduced || prefersLessData || saveData)
    ? 'static'
    : (appleTouch ? 'frames' : (canPlayVideo ? 'video' : 'frames'));
"""
if "const FRAME_COUNT = 96;" not in s:
    if old_mode not in s:
        raise SystemExit("mode block not found")
    s = s.replace(old_mode, new_mode)

if "const frameCache = new Array(96);" not in s:
    s = s.replace(
        "  let stalls = 0, watchdog = 0, metaTimer = 0;\n",
        "  let stalls = 0, watchdog = 0, metaTimer = 0;\n"
        "  let frameIndex = -1;\n"
        "  const frameCache = new Array(96);\n",
    )

s = s.replace(
    "  function totalFrames() {\n    return Math.max(1, Math.round(duration * FPS));\n  }",
    "  function totalFrames() {\n"
    "    return mode === 'frames' ? FRAME_COUNT : Math.max(1, Math.round(duration * FPS));\n"
    "  }",
)

old_tick = """    if (mode === 'video' && ready) {
      if (!video.paused) video.pause();
      seekTo(shown);
    }
    if (shown !== target) schedule();
"""
new_tick = """    if (mode === 'video' && ready) {
      if (!video.paused) video.pause();
      seekTo(shown);
    } else if (mode === 'frames' && ready) {
      renderFrame(shown);
    }
    if (shown !== target) schedule();
"""
if "mode === 'frames' && ready" not in s:
    if old_tick not in s:
        raise SystemExit("tick block not found")
    s = s.replace(old_tick, new_tick)

if "is-frame-mode');" not in s:
    s = s.replace(
        "    stage.classList.remove('is-loading', 'is-ready');\n",
        "    stage.classList.remove('is-loading', 'is-ready', 'is-frame-mode');\n"
        "    if (poster && staticPoster) poster.src = staticPoster;\n",
    )

helpers = r'''  function frameUrl(index) {
    return './media/frames/frame-' + String(index + 1).padStart(3, '0') + '.webp';
  }

  function renderFrame(p) {
    if (!poster) return;
    const index = clamp(Math.round(p * (FRAME_COUNT - 1)), 0, FRAME_COUNT - 1);
    if (index === frameIndex) return;
    frameIndex = index;
    const cached = frameCache[index];
    poster.src = (cached && cached.complete && cached.naturalWidth) ? cached.src : frameUrl(index);
  }

  function preloadFrameBatches(start) {
    let next = start;
    function batch() {
      const end = Math.min(next + 8, FRAME_COUNT);
      for (; next < end; next += 1) {
        if (frameCache[next]) continue;
        const image = new Image();
        image.decoding = 'async';
        image.src = frameUrl(next);
        frameCache[next] = image;
      }
      if (next < FRAME_COUNT) setTimeout(batch, 90);
    }
    batch();
  }

  function startFrameMode() {
    if (!poster) {
      failToStatic('The mobile frame sequence is unavailable, so a single still frame is shown instead.');
      return;
    }
    stage.classList.add('is-frame-mode', 'is-loading');
    video.querySelectorAll('source').forEach((src) => src.removeAttribute('src'));
    video.preload = 'none';

    const first = new Image();
    first.decoding = 'async';
    frameCache[0] = first;
    first.onload = () => {
      ready = true;
      poster.src = first.src;
      frameIndex = 0;
      stage.classList.remove('is-loading');
      stage.classList.add('is-ready');
      buildTicks();
      measure();
      renderFrame(shown);
      schedule();
      preloadFrameBatches(1);
    };
    first.onerror = () => failToStatic('The mobile sequence could not be loaded, so a single still frame is shown instead.');
    first.src = frameUrl(0);
  }

'''
if "function startFrameMode()" not in s:
    marker = "  function startVideoMode() {\n"
    if marker not in s:
        raise SystemExit("startVideoMode marker not found")
    s = s.replace(marker, helpers + marker)

old_start = """  if (mode === 'static') {
    document.body.classList.add('is-static');
    if (railNote) railNote.hidden = false;
    try {
      video.querySelectorAll('source').forEach((src) => src.removeAttribute('src'));
      video.preload = "none";
    } catch (err) { /* ignore */ }
  } else {
    startVideoMode();
  }
"""
new_start = """  if (mode === 'static') {
    document.body.classList.add('is-static');
    if (railNote) railNote.hidden = false;
    try {
      video.querySelectorAll('source').forEach((src) => src.removeAttribute('src'));
      video.preload = "none";
    } catch (err) { /* ignore */ }
  } else if (mode === 'frames') {
    startFrameMode();
  } else {
    startVideoMode();
  }
"""
if "else if (mode === 'frames')" not in s:
    if old_start not in s:
        raise SystemExit("startup block not found")
    s = s.replace(old_start, new_start)

s = s.replace(
    "    get currentTime() { return video ? video.currentTime : 0; }",
    "    get currentTime() { return mode === 'frames' ? shown * duration : (video ? video.currentTime : 0); }",
)
app.write_text(s)

c = css.read_text()
if ".stage.is-frame-mode .stage-video" not in c:
    c += """

/* Apple touch devices use a frame sequence instead of HTML video seeking. */
.stage.is-frame-mode .stage-video{display:none}
.stage.is-frame-mode .stage-poster{display:block;opacity:1}
"""
css.write_text(c)

h = ht.read_text()
if "image/webp" not in h:
    h += "\nAddType image/webp .webp\n"
ht.write_text(h)

# Keep future preview deployments aware of the iPhone sequence.
d = deploy.read_text()
if "media/frames/frame-001.webp" not in d:
    d = d.replace(
        "          test -s preview/video/media/knowledge-constellation-scroll.webm\n",
        "          test -s preview/video/media/knowledge-constellation-scroll.webm\n"
        "          test -s preview/video/media/frames/frame-001.webp\n"
        "          test -s preview/video/media/frames/frame-096.webp\n",
    )

# Replace the old inline browser QA with the reusable QA script.
start = "      - name: Browser QA mobile, desktop and reduced motion\n"
if start in d:
    before = d.split(start, 1)[0]
    d = before + """      - name: Browser QA desktop video, iPhone frames and reduced motion
        shell: bash
        run: |
          set -euo pipefail
          export NODE_PATH="$HOME/agents/flow-browser-automation/node_modules"
          node .github/scripts/w10_scroll_qa.js https://what10things.co.uk/w10-video-preview/
"""
deploy.write_text(d)

print("IOS_SCROLL_PATCH_OK=yes")

/* W10_FLOW_VIDEO_SCROLL_PREVIEW
 * Scroll-driven video scrub controller. Vanilla JS, no dependencies.
 *
 * Scroll position through the pinned track maps to a target progress 0..1.
 * A requestAnimationFrame loop eases a "shown" progress toward that target and
 * drives HTMLVideoElement.currentTime, so normal wheel/touch scrolling feels
 * smooth without firing a seek on every pixel. Scrolling up walks currentTime
 * backwards for a natural reverse.
 *
 * window.__W10_SCROLL_PROGRESS__ is updated every frame for automated QA.
 */
(() => {
  'use strict';

  window.__W10_SCROLL_PROGRESS__ = 0;

  const FPS = 24; // knowledge-constellation.mp4: 24fps, ~192 frames, 8s

  const root      = document.documentElement;
  const track     = document.getElementById('track');
  const stage     = document.getElementById('stage');
  const video     = document.getElementById('video');
  const beats     = Array.prototype.slice.call(document.querySelectorAll('.beat'));
  const railTicks  = document.getElementById('railTicks');
  const railFrame  = document.getElementById('railFrame');
  const railTotal  = document.getElementById('railTotal');
  const railTc     = document.getElementById('railTc');
  const railNote   = document.getElementById('railNote');
  const transport  = document.getElementById('transport');
  const tGlyph     = document.getElementById('transportGlyph');
  const tWord      = document.getElementById('transportWord');

  root.classList.remove('no-js');
  root.classList.add('js');

  if (!track || !stage || !video) return;

  const prefersReduced  = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const prefersLessData = matchMedia('(prefers-reduced-data: reduce)').matches;
  const saveData        = !!(navigator.connection && navigator.connection.saveData);
  const canPlayVideo    = !!video.canPlayType && (video.canPlayType('video/webm; codecs="vp8"') !== '' || video.canPlayType('video/mp4') !== '');

  let mode = (prefersReduced || prefersLessData || saveData || !canPlayVideo) ? 'static' : 'video';

  let duration = 8;
  let target = 0, shown = 0, lastTarget = 0, lastTick = 0;
  let dir = 0, dirTimer = 0;
  let rafId = 0;
  let seeking = false, ready = false, pendingTime = null;
  let stalls = 0, watchdog = 0, metaTimer = 0;

  const clamp = (n, a, b) => (n < a ? a : n > b ? b : n);
  const pad3  = (n) => String(n).padStart(3, '0');

  function timecode(sec) {
    const whole = Math.floor(sec);
    const tenths = clamp(Math.floor((sec - whole) * 10), 0, 9);
    return Math.floor(whole / 60) + ':' + String(whole % 60).padStart(2, '0') + '.' + tenths;
  }

  function measure() {
    const total = track.offsetHeight - window.innerHeight;
    const passed = -track.getBoundingClientRect().top;
    target = total > 0 ? clamp(passed / total, 0, 1) : 0;
  }

  function totalFrames() {
    return Math.max(1, Math.round(duration * FPS));
  }

  function paint(p) {
    root.style.setProperty('--p', p.toFixed(4));
    const frames = totalFrames();
    if (railFrame) railFrame.textContent = pad3(clamp(Math.round(p * (frames - 1)), 0, frames - 1));
    if (railTotal) railTotal.textContent = String(frames);
    if (railTc) railTc.textContent = timecode(p * duration);
  }

  function paintDir() {
    if (!transport) return;
    const name = dir > 0 ? 'fwd' : dir < 0 ? 'rev' : 'hold';
    if (transport.dataset.dir === name) return;
    transport.dataset.dir = name;
    if (tGlyph) tGlyph.textContent = dir > 0 ? '▼' : dir < 0 ? '▲' : '■';
    if (tWord) tWord.textContent = name.toUpperCase();
  }

  function schedule() {
    if (!rafId) rafId = requestAnimationFrame(tick);
  }

  function tick(now) {
    rafId = 0;
    const elapsed = lastTick ? Math.min(64, now - lastTick) : 16.7;
    lastTick = now;
    shown += (target - shown) * (1 - Math.exp(-elapsed / 92));
    if (Math.abs(target - shown) < 0.0004) shown = target;

    window.__W10_SCROLL_PROGRESS__ = shown;
    paint(shown);

    if (mode === 'video' && ready) {
      if (!video.paused) video.pause();
      seekTo(shown);
    }
    if (shown !== target) schedule();
  }

  function seekTo(p) {
    const t = clamp(p * duration, 0, Math.max(0, duration - 1 / FPS));
    if (Math.abs(t - video.currentTime) < 0.5 / FPS) return;
    if (seeking) {
      pendingTime = t;
      return;
    }
    seeking = true;
    try {
      video.currentTime = t;
    } catch (err) {
      seeking = false;
      return;
    }
    clearTimeout(watchdog);
    watchdog = setTimeout(onStall, 3000);
  }

  function onStall() {
    // Release the lock and keep trying; only give up after repeated stalls.
    seeking = false;
    pendingTime = null;
    stalls += 1;
    if (stalls >= 5) failToStatic('Scrubbing stalled on this device, so a single still frame is shown instead.');
    else schedule();
  }

  function onSeeked() {
    seeking = false;
    stalls = 0;
    clearTimeout(watchdog);
    if (pendingTime !== null) {
      const next = pendingTime;
      pendingTime = null;
      if (Math.abs(next - video.currentTime) >= 0.5 / FPS) seekTo(next / duration);
    }
    schedule();
  }

  function failToStatic(message) {
    if (mode === 'static') return;
    mode = 'static';
    ready = false;
    pendingTime = null;
    clearTimeout(watchdog);
    clearTimeout(metaTimer);
    document.body.classList.add('is-static');
    stage.classList.remove('is-loading', 'is-ready');
    if (railNote) {
      if (message) railNote.textContent = message;
      railNote.hidden = false;
    }
    try {
      video.querySelectorAll('source').forEach((src) => src.removeAttribute('src'));
      video.removeAttribute('src');
      video.load();
    } catch (err) { /* poster <img> remains as the fallback */ }
    schedule();
  }

  function setDir(d) {
    dir = d;
    paintDir();
    clearTimeout(dirTimer);
    dirTimer = setTimeout(() => { dir = 0; paintDir(); }, 550);
  }

  function onScroll() {
    measure();
    if (target > lastTarget + 1e-4) setDir(1);
    else if (target < lastTarget - 1e-4) setDir(-1);
    lastTarget = target;
    schedule();
  }

  function buildTicks() {
    if (!railTicks) return;
    const total = track.offsetHeight - window.innerHeight;
    railTicks.textContent = '';
    if (total <= 0) return;
    const trackTop = track.getBoundingClientRect().top;
    beats.forEach((beat, i) => {
      const rect = beat.getBoundingClientRect();
      const centre = rect.top - trackTop + beat.offsetHeight * 0.5 - window.innerHeight * 0.5;
      const pos = clamp(centre / total, 0, 1);
      const tick = document.createElement('span');
      tick.className = 'rail-tick';
      tick.style.setProperty('--tp', pos.toFixed(4));
      const num = document.createElement('i');
      num.textContent = String(i + 1).padStart(2, '0');
      tick.appendChild(num);
      railTicks.appendChild(tick);
    });
  }

  function startVideoMode() {
    stage.classList.add("is-loading");
    const sources = Array.from(video.querySelectorAll("source[data-src]"));
    if (!sources.length) {
      failToStatic("The sequence source is unavailable, so a single still frame is shown instead.");
      return;
    }
    video.muted = true;
    video.defaultMuted = true;
    video.playsInline = true;
    video.preload = "auto";
    sources.forEach((source) => { source.src = source.dataset.src; });
    try { video.load(); } catch (err) {
      failToStatic("The sequence could not be started here, so a single still frame is shown instead.");
      return;
    }

    metaTimer = setTimeout(() => {
      if (!ready) failToStatic('The sequence did not load in time, so a single still frame is shown instead.');
    }, 9000);

    video.addEventListener('loadedmetadata', () => {
      if (isFinite(video.duration) && video.duration > 0) duration = video.duration;
    }, { once: true });

    video.addEventListener("loadeddata", () => {
      ready = true;
      clearTimeout(metaTimer);
      stage.classList.remove('is-loading');
      stage.classList.add('is-ready');
      try { video.pause(); } catch (err) { /* ignore */ }
      buildTicks();
      measure();
      schedule();
    }, { once: true });

    video.addEventListener('seeked', onSeeked);
    video.addEventListener('error', () => {
      failToStatic('The sequence could not be decoded here, so a single still frame is shown instead.');
    });
  }

  if (mode === 'static') {
    document.body.classList.add('is-static');
    if (railNote) railNote.hidden = false;
    try {
      video.querySelectorAll('source').forEach((src) => src.removeAttribute('src'));
      video.preload = "none";
    } catch (err) { /* ignore */ }
  } else {
    startVideoMode();
  }

  addEventListener('scroll', onScroll, { passive: true });
  addEventListener("resize", () => { lastTick = 0; measure(); buildTicks(); schedule(); }, { passive: true });
  addEventListener('orientationchange', () => {
    setTimeout(() => { measure(); buildTicks(); schedule(); }, 120);
  });

  measure();
  buildTicks();
  paint(0);
  paintDir();
  schedule();

  // Lightweight status surface for automated QA / debugging.
  window.__W10_VIDEO_SCROLL__ = {
    get progress() { return shown; },
    get target() { return target; },
    get mode() { return mode; },
    get ready() { return ready; },
    get direction() { return dir; },
    get frame() { return clamp(Math.round(shown * (totalFrames() - 1)), 0, totalFrames() - 1); },
    get currentTime() { return video ? video.currentTime : 0; }
  };
})();

const { chromium } = require('playwright');

const base = (process.argv[2] || 'http://127.0.0.1:8794/').replace(/\/+$/, '') + '/';
const url = (suffix) => base + '?' + suffix + '=' + Date.now();
const iphoneUA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Mobile/15E148 Safari/604.1';

(async () => {
  const browser = await chromium.launch({ headless: true });

  // Desktop/Chromium keeps the video path and must scrub both directions.
  const desktop = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const desktopErrors = [];
  desktop.on('console', m => { if (m.type() === 'error') desktopErrors.push(m.text()); });
  desktop.on('pageerror', e => desktopErrors.push(e.message));
  await desktop.goto(url('desktopqa'), { waitUntil: 'domcontentloaded', timeout: 30000 });
  await desktop.waitForFunction(() => window.__W10_VIDEO_SCROLL__?.mode === 'video' && window.__W10_VIDEO_SCROLL__?.ready === true, null, { timeout: 15000 });
  const d0 = await desktop.evaluate(() => ({
    mode: window.__W10_VIDEO_SCROLL__.mode,
    duration: document.querySelector('#video')?.duration || 0,
    overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    noindex: (document.querySelector('meta[name="robots"]')?.content || '').includes('noindex')
  }));
  await desktop.evaluate(() => scrollTo(0, (document.documentElement.scrollHeight - innerHeight) * .72));
  await desktop.waitForTimeout(1500);
  const df = await desktop.evaluate(() => ({ time: document.querySelector('#video')?.currentTime || 0, p: window.__W10_SCROLL_PROGRESS__ || 0 }));
  await desktop.evaluate(() => scrollTo(0, (document.documentElement.scrollHeight - innerHeight) * .18));
  await desktop.waitForTimeout(1500);
  const dr = await desktop.evaluate(() => ({ time: document.querySelector('#video')?.currentTime || 0, p: window.__W10_SCROLL_PROGRESS__ || 0 }));
  console.log(JSON.stringify({ desktop: { d0, df, dr, errors: desktopErrors } }));
  if (d0.mode !== 'video' || d0.duration < 7.5 || d0.overflow || !d0.noindex || desktopErrors.length || df.time <= .5 || df.p < .3 || dr.time >= df.time || dr.p >= df.p) process.exit(2);
  await desktop.close();

  // iPhone/iPad path must not request video at all; it uses derived WebP frames.
  const iphone = await browser.newPage({ viewport: { width: 390, height: 844 }, userAgent: iphoneUA, isMobile: true, hasTouch: true });
  const iphoneErrors = [];
  const iphoneVideos = [];
  iphone.on('console', m => { if (m.type() === 'error') iphoneErrors.push(m.text()); });
  iphone.on('pageerror', e => iphoneErrors.push(e.message));
  iphone.on('request', r => { if (/\.(mp4|webm)(\?|$)/.test(r.url())) iphoneVideos.push(r.url()); });
  await iphone.goto(url('iosqa'), { waitUntil: 'domcontentloaded', timeout: 30000 });
  await iphone.waitForFunction(() => window.__W10_VIDEO_SCROLL__?.mode === 'frames' && window.__W10_VIDEO_SCROLL__?.ready === true, null, { timeout: 15000 });
  const i0 = await iphone.evaluate(() => ({
    mode: window.__W10_VIDEO_SCROLL__.mode,
    frame: window.__W10_VIDEO_SCROLL__.frame,
    src: document.querySelector('.stage-poster')?.src || '',
    overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    noteHidden: document.querySelector('#railNote')?.hidden ?? false
  }));
  await iphone.evaluate(() => scrollTo(0, (document.documentElement.scrollHeight - innerHeight) * .72));
  await iphone.waitForTimeout(1400);
  const iff = await iphone.evaluate(() => ({ frame: window.__W10_VIDEO_SCROLL__.frame, src: document.querySelector('.stage-poster')?.src || '', p: window.__W10_SCROLL_PROGRESS__ || 0 }));
  await iphone.evaluate(() => scrollTo(0, (document.documentElement.scrollHeight - innerHeight) * .18));
  await iphone.waitForTimeout(1400);
  const ir = await iphone.evaluate(() => ({ frame: window.__W10_VIDEO_SCROLL__.frame, src: document.querySelector('.stage-poster')?.src || '', p: window.__W10_SCROLL_PROGRESS__ || 0 }));
  console.log(JSON.stringify({ iphone: { i0, iff, ir, iphoneVideos, errors: iphoneErrors } }));
  if (i0.mode !== 'frames' || i0.overflow || !i0.noteHidden || !i0.src.includes('frame-001.webp') || iphoneVideos.length || iphoneErrors.length || iff.frame < 50 || !iff.src.includes('/frames/frame-') || ir.frame >= iff.frame || ir.p >= iff.p) process.exit(3);
  await iphone.close();

  // Reduced motion must stay static and avoid both video and frame-sequence downloads.
  const reduced = await browser.newPage({ viewport: { width: 390, height: 844 }, userAgent: iphoneUA, isMobile: true, hasTouch: true, reducedMotion: 'reduce' });
  const media = [];
  reduced.on('request', r => { if (/\.(mp4|webm)(\?|$)|\/frames\/frame-\d+\.webp/.test(r.url())) media.push(r.url()); });
  await reduced.goto(url('rmqa'), { waitUntil: 'domcontentloaded', timeout: 30000 });
  await reduced.waitForTimeout(800);
  const rm = await reduced.evaluate(() => ({
    mode: window.__W10_VIDEO_SCROLL__?.mode,
    staticClass: document.body.classList.contains('is-static'),
    video: getComputedStyle(document.querySelector('#video')).display,
    poster: getComputedStyle(document.querySelector('.stage-poster')).display
  }));
  console.log(JSON.stringify({ reduced: { rm, media } }));
  if (rm.mode !== 'static' || !rm.staticClass || rm.poster === 'none' || media.length) process.exit(4);
  await reduced.close();

  await browser.close();
  console.log('W10_SCROLL_QA_OK=yes');
})().catch(err => {
  console.error(err);
  process.exit(1);
});

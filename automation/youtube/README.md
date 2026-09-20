# What10Things YouTube production lane

This directory defines the zero-incremental-cost YouTube and podcast production
lane for What10Things.

## Brand format

One evidence-backed What10Things topic is reused across four outputs:

1. a normal 8–15 minute YouTube explainer;
2. a 90–150 minute calm bedtime/sleep version when the category is suitable;
3. ten Shorts, one per sourced item;
4. the long-form audio as a podcast episode.

The sleep format is not footage of somebody sleeping. It is deliberately calm
long-form factual narration that a viewer can listen to in bed.

## Content focus

Initial long-form categories are history/culture, science/nature, world,
general knowledge, travel and selected technology. Money/buying-guide content is
kept out of the bedtime lane unless deliberately enabled later.

## Production contract

The existing W10 research pipeline remains authoritative for facts. This lane
must not turn a short evidence-backed fact into unsourced filler merely to hit a
two-hour runtime. Expansion may add scene-setting, definitions, chronology and
context only when each material factual claim is supported by retained evidence
or by a new evidence pack.

Routine production is intended to run without manual approval, but it fails
closed when evidence, licensing or publishing authentication is missing.

### Zero-cost stack

- Research: existing What10Things evidence pipeline and UrbanSky free model router.
- Planning: deterministic `plan.py`.
- Script generation: shared free writer route with strict evidence input.
- Narration: local/offline open-source TTS on the UrbanSky automation server.
- Images: licensed/public-domain assets first; generated imagery only through
  an already-approved free route.
- Video: FFmpeg composition with slow pan/zoom and calm transitions.
- Podcast: reuse the approved long-form audio.
- Paid Higgsfield generation: disabled for this lane.

## Target long-form shape

The bedtime format uses exactly ten chapters. A useful default is around 1,450
words per chapter plus a short intro/outro, giving roughly 15,000 words total.
At 118–125 words per minute this is around two hours of narration.

The objective is not to maximise duration at any cost. Retention, factual
quality, originality and policy compliance are more important than reaching an
exact two-hour mark.

## Publishing boundary

Creation and publishing are separate jobs. Rendering can run before YouTube
authentication exists. Uploading must not start until the What10Things channel
has valid OAuth credentials and a durable idempotent publisher stores the
remote YouTube video ID.

## First acceptance target

Produce one private/unlisted pilot from an already-published evergreen topic and
verify:

- exactly ten sourced chapters;
- no unsupported claims in a sampled claim audit;
- intelligible calm UK-English narration;
- 16:9 1080p render with no rapid visual changes;
- thumbnail/title/description generated;
- no paid provider call;
- no public publication during the controlled test.

After that, enable bounded routine production at 2–4 long-form videos per week,
not mass-volume templated generation.

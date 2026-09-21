# Night Atlas self-hosted podcast feed

Night Atlas uses a public RSS feed on What10Things so the same long-form sleep
production can be distributed to Spotify and other podcast directories without
a paid podcast host.

Public endpoints after deployment:

- `https://what10things.co.uk/night-atlas/`
- `https://what10things.co.uk/night-atlas/rss.xml`
- `https://what10things.co.uk/night-atlas/cover.png`

## Publishing flow

1. The What10Things long-form job renders the sleep video and approved audio.
2. FFmpeg exports the podcast derivative as MP3.
3. n8n uploads the MP3 to Dropbox under the Night Atlas media area.
4. n8n creates/reuses a public download link that works without a Dropbox login.
5. The job records the direct HTTPS audio URL, exact byte length and duration.
6. `add_episode.py` appends the episode to `episodes.json`.
7. Commit/push to `main`. The existing GoDaddy deployment rebuilds the RSS feed.
8. Spotify and other subscribed directories poll the feed and discover the episode.

The RSS enclosure URL must remain stable, publicly reachable without cookies or
authentication, and point to the MP3. Do not put Dropbox OAuth tokens or any
other credentials in this repository.

## Add one episode locally

```bash
python automation/night_atlas/add_episode.py \
  --slug rainy-night-cabin-8-hours \
  --title "Rainy Night Cabin | 8 Hours of Rain for Sleep & Relaxation" \
  --description "Eight hours of immersive rainfall and cabin ambience for sleep, relaxation, reading and winding down." \
  --audio-url "https://example.invalid/night-atlas/rainy-night-cabin.mp3" \
  --audio-bytes 123456789 \
  --duration-seconds 28800 \
  --published-at "2026-09-21T20:00:00Z"
```

The example URL is deliberately invalid. Production publishing must supply the
real Dropbox-backed direct URL.

## Spotify migration

The currently created Spotify-hosted Night Atlas show has no published episodes.
Do not manually upload one just to create the RSS feed. Once this self-hosted feed
contains the first real episode, add/claim it in Spotify for Creators as a show
hosted somewhere else and verify ownership using the email in `show.json`.

Spotify may take time to poll a new or changed feed; the RSS file remains the
source of truth for audio distribution.

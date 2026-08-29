# What10Things automation system

What10Things uses small queue-driven automations rather than one long workflow.

## Research pipeline

- **W10-T01 Trend Discovery** — Google Trends and other public-interest signals are normalised and sent to the site signal queue.
- **W10-M01 Evergreen Topic Mapper** — converts a live signal into durable subjects worth explaining. Breaking events are triggers, not pages to rewrite.
- **W10-R01 Evidence Research & Publisher** — researches one queued topic, requires evidence for exactly ten facts, then publishes through the authenticated site API.

Published topics can add high-quality related subjects back to the candidate queue, creating the knowledge graph without uncontrolled exponential expansion.

## Media pipeline

Publishing automatically queues three media jobs per topic: `fact_cards`, `carousel`, and `short_video`. Downstream workflows will use licensed/public imagery where possible, generation where needed, deterministic image composition, FFmpeg video assembly and reusable voice generation.

## Publishing and engagement

Media jobs are separate from platform publishing. Completed assets enter a publishing queue so generation failures do not break schedules. Comment ingestion and evidence-grounded replies are a separate final stage.

## API

Public:

- `GET /api/status`
- `GET /api/topics`
- `GET /api/topics/<slug>`

Automation-only requests use `X-Automation-Key`. The website source stores only the SHA-256 digest of the existing Oracle automation secret; the raw secret stays in the n8n environment.

Research endpoints:

- `POST /api/automation/signals/batch`
- `POST /api/automation/signals/claim`
- `POST /api/automation/signals/<id>/result`
- `POST /api/automation/candidates/claim`
- `POST /api/automation/candidates/<id>/result`

Media endpoints:

- `POST /api/automation/social/claim`
- `POST /api/automation/social/<id>/result`

## Persistence

The live Passenger application stores the knowledge graph in `runtime/knowledge.db` using Python's built-in SQLite. The deployment workflow explicitly excludes the runtime database, so application deployments do not overwrite generated content.

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from content_quality import QUALITY_GATE_VERSION, normalise_article_count, topic_quality_issues
from legacy_quality_holds import reviewed_legacy_issue

ROOT = Path(__file__).resolve().parent
RUNTIME = Path(os.getenv("W10_RUNTIME_DIR", ROOT / "runtime"))
DB_PATH = Path(os.getenv("W10_KNOWLEDGE_DB", RUNTIME / "knowledge.db"))
SAFE_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@contextmanager
def connection():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    with connection() as conn:
        conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                summary TEXT NOT NULL,
                intro TEXT NOT NULL,
                reading_time TEXT NOT NULL DEFAULT '6 min read',
                status TEXT NOT NULL DEFAULT 'published',
                quality_score REAL NOT NULL DEFAULT 0,
                trigger_json TEXT NOT NULL DEFAULT '{}',
                generation_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_topics_status_updated ON topics(status, updated_at DESC);
            CREATE INDEX IF NOT EXISTS idx_topics_category ON topics(category, status);

            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_key TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS topic_facts (
                topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
                fact_id INTEGER NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
                position INTEGER NOT NULL CHECK(position BETWEEN 1 AND 10),
                PRIMARY KEY(topic_id, position),
                UNIQUE(topic_id, fact_id)
            );
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                title TEXT,
                publisher TEXT,
                source_type TEXT,
                checked_at TEXT
            );
            CREATE TABLE IF NOT EXISTS fact_sources (
                fact_id INTEGER NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
                source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
                evidence_excerpt TEXT,
                PRIMARY KEY(fact_id, source_id)
            );
            CREATE TABLE IF NOT EXISTS topic_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
                to_slug TEXT NOT NULL,
                to_title TEXT NOT NULL,
                relation TEXT NOT NULL DEFAULT 'related',
                score REAL NOT NULL DEFAULT 0.5,
                status TEXT NOT NULL DEFAULT 'candidate',
                UNIQUE(from_topic_id, to_slug, relation)
            );

            CREATE TABLE IF NOT EXISTS trend_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                source_key TEXT NOT NULL,
                country TEXT NOT NULL DEFAULT 'GB',
                title TEXT NOT NULL,
                query TEXT NOT NULL,
                source_url TEXT,
                observed_at TEXT NOT NULL,
                metric_name TEXT,
                metric_value REAL,
                raw_json TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'new',
                priority REAL NOT NULL DEFAULT 0,
                lease_until TEXT,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(source, source_key)
            );
            CREATE INDEX IF NOT EXISTS idx_signals_claim ON trend_signals(status, priority DESC, observed_at DESC);

            CREATE TABLE IF NOT EXISTS topic_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL,
                title TEXT NOT NULL,
                subject TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'general-knowledge',
                rationale TEXT NOT NULL DEFAULT '',
                parent_slug TEXT NOT NULL DEFAULT '',
                signal_id INTEGER REFERENCES trend_signals(id) ON DELETE SET NULL,
                source_kind TEXT NOT NULL DEFAULT 'trend',
                score REAL NOT NULL DEFAULT 0.5,
                evergreen_score REAL NOT NULL DEFAULT 0.5,
                status TEXT NOT NULL DEFAULT 'queued',
                lease_until TEXT,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(slug, source_kind, parent_slug)
            );
            CREATE INDEX IF NOT EXISTS idx_candidates_claim ON topic_candidates(status, score DESC, created_at);

            CREATE TABLE IF NOT EXISTS social_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
                job_type TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'queued',
                priority REAL NOT NULL DEFAULT 0.5,
                lease_until TEXT,
                attempts INTEGER NOT NULL DEFAULT 0,
                result_json TEXT,
                last_error TEXT,
                publish_after TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(topic_id, job_type)
            );
            CREATE INDEX IF NOT EXISTS idx_social_claim ON social_jobs(status, priority DESC, created_at);

            CREATE TABLE IF NOT EXISTS quality_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL REFERENCES topics(id),
                gate_version TEXT NOT NULL,
                reasons_json TEXT NOT NULL,
                snapshot_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(topic_id, gate_version)
            );
            CREATE TABLE IF NOT EXISTS publication_rejections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER,
                gate_version TEXT NOT NULL,
                reasons_json TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS quality_audits (
                gate_version TEXT PRIMARY KEY,
                topics_checked INTEGER NOT NULL,
                topics_held INTEGER NOT NULL,
                completed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS comments_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                external_id TEXT NOT NULL UNIQUE,
                topic_slug TEXT,
                text TEXT NOT NULL,
                author_ref TEXT,
                classification TEXT,
                status TEXT NOT NULL DEFAULT 'new',
                response_text TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, separators=(",", ":"))


def _load(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return default


def _validate_slug(value: str) -> str:
    slug = str(value or "").strip().lower()
    if not SAFE_SLUG.fullmatch(slug) or len(slug) > 120:
        raise ValueError("invalid slug")
    return slug


def _validate_url(value: str) -> str:
    url = str(value or "").strip()
    if not url.startswith(("https://", "http://")) or len(url) > 2000:
        raise ValueError("invalid source URL")
    return url


def add_signals(signals: Iterable[dict[str, Any]]) -> dict[str, int]:
    now = utcnow()
    inserted = updated = 0
    with connection() as conn:
        for signal in list(signals)[:100]:
            title = str(signal.get("title") or "").strip()[:300]
            query = str(signal.get("query") or title).strip()[:300]
            source = str(signal.get("source") or "unknown").strip()[:80]
            source_key = str(signal.get("source_key") or signal.get("source_url") or f"{query}:{signal.get('observed_at', now)}").strip()[:500]
            if not title or not query or not source_key:
                continue
            observed = str(signal.get("observed_at") or now)[:40]
            metric_value = signal.get("metric_value")
            try:
                metric_value = float(metric_value) if metric_value is not None else None
            except (TypeError, ValueError):
                metric_value = None
            priority = min(1.0, 0.35 + (0.1 if metric_value and metric_value >= 10_000 else 0) + (0.15 if metric_value and metric_value >= 100_000 else 0))
            cur = conn.execute("SELECT id FROM trend_signals WHERE source=? AND source_key=?", (source, source_key))
            exists = cur.fetchone() is not None
            conn.execute(
                """
                INSERT INTO trend_signals(source,source_key,country,title,query,source_url,observed_at,metric_name,metric_value,raw_json,status,priority,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?, 'new', ?,?,?)
                ON CONFLICT(source,source_key) DO UPDATE SET
                    title=excluded.title, query=excluded.query, source_url=excluded.source_url,
                    observed_at=excluded.observed_at, metric_name=excluded.metric_name,
                    metric_value=excluded.metric_value, raw_json=excluded.raw_json,
                    priority=MAX(trend_signals.priority, excluded.priority), updated_at=excluded.updated_at
                """,
                (
                    source, source_key, str(signal.get("country") or "GB")[:2], title, query,
                    str(signal.get("source_url") or "")[:2000], observed,
                    str(signal.get("metric_name") or "")[:80], metric_value,
                    _json(signal.get("raw_data") or {}), priority, now, now,
                ),
            )
            if exists:
                updated += 1
            else:
                inserted += 1
    return {"inserted": inserted, "updated": updated}


def _claim_row(table: str, statuses: tuple[str, ...], order_sql: str, lease_minutes: int = 30, eligible_sql: str = "1=1") -> dict[str, Any] | None:
    now = utcnow()
    lease = (datetime.now(timezone.utc) + timedelta(minutes=lease_minutes)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    placeholders = ",".join("?" for _ in statuses)
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            f"SELECT * FROM {table} WHERE (status IN ({placeholders}) OR (status='claimed' AND lease_until < ?)) AND ({eligible_sql}) ORDER BY {order_sql} LIMIT 1",
            (*statuses, now),
        ).fetchone()
        if row is None:
            return None
        conn.execute(
            f"UPDATE {table} SET status='claimed', lease_until=?, attempts=attempts+1, updated_at=? WHERE id=?",
            (lease, now, row["id"]),
        )
        data = dict(row)
        data["status"] = "claimed"
        data["lease_until"] = lease
        data["attempts"] = int(data.get("attempts") or 0) + 1
        if "raw_json" in data:
            data["raw_data"] = _load(data.pop("raw_json"), {})
        if "payload_json" in data:
            data["payload"] = _load(data.pop("payload_json"), {})
        return data


def claim_signal() -> dict[str, Any] | None:
    return _claim_row("trend_signals", ("new", "retry"), "priority DESC, observed_at DESC")


def finish_signal(signal_id: int, status: str, error: str | None = None) -> None:
    if status not in {"mapped", "ignored", "retry", "failed"}:
        raise ValueError("invalid signal status")
    with connection() as conn:
        conn.execute(
            "UPDATE trend_signals SET status=?, lease_until=NULL, last_error=?, updated_at=? WHERE id=?",
            (status, str(error or "")[:2000] or None, utcnow(), int(signal_id)),
        )


def add_candidates(candidates: Iterable[dict[str, Any]], signal_id: int | None = None) -> dict[str, int]:
    now = utcnow()
    inserted = updated = 0
    with connection() as conn:
        for item in list(candidates)[:20]:
            slug = _validate_slug(item.get("slug", ""))
            title = str(item.get("title") or "").strip()[:300]
            subject = str(item.get("subject") or title).strip()[:300]
            if not title or not subject:
                continue
            source_kind = str(item.get("source_kind") or ("trend" if signal_id else "graph_expansion"))[:40]
            parent_slug = str(item.get("parent_slug") or "").strip().lower()[:120]
            try:
                score = max(0.0, min(1.0, float(item.get("score", 0.5))))
                evergreen = max(0.0, min(1.0, float(item.get("evergreen_score", 0.5))))
            except (TypeError, ValueError):
                score, evergreen = 0.5, 0.5
            # Expansion candidates need to be genuinely strong to stop exponential page growth.
            if source_kind == "graph_expansion" and (score < 0.70 or evergreen < 0.75):
                continue
            exists = conn.execute(
                "SELECT id FROM topic_candidates WHERE slug=? AND source_kind=? AND parent_slug=?",
                (slug, source_kind, parent_slug),
            ).fetchone() is not None
            conn.execute(
                """
                INSERT INTO topic_candidates(slug,title,subject,category,rationale,parent_slug,signal_id,source_kind,score,evergreen_score,status,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?, 'queued', ?,?)
                ON CONFLICT DO UPDATE SET
                    title=excluded.title, subject=excluded.subject, category=excluded.category,
                    rationale=excluded.rationale, signal_id=COALESCE(topic_candidates.signal_id, excluded.signal_id),
                    score=MAX(topic_candidates.score, excluded.score), evergreen_score=MAX(topic_candidates.evergreen_score, excluded.evergreen_score),
                    status=CASE WHEN topic_candidates.status IN ('published','claimed','held') THEN topic_candidates.status ELSE 'queued' END,
                    updated_at=excluded.updated_at
                """,
                (slug, title, subject, str(item.get("category") or "general-knowledge")[:80], str(item.get("rationale") or "")[:1200], parent_slug, signal_id, source_kind, score, evergreen, now, now),
            )
            if exists: updated += 1
            else: inserted += 1
    return {"inserted": inserted, "updated": updated}


def claim_candidate() -> dict[str, Any] | None:
    return _claim_row("topic_candidates", ("queued", "retry"), "score DESC, evergreen_score DESC, created_at")


def finish_candidate(candidate_id: int, status: str, error: str | None = None) -> str | None:
    if status not in {"published", "ignored", "retry", "failed"}:
        raise ValueError("invalid candidate status")
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT status,attempts FROM topic_candidates WHERE id=?", (int(candidate_id),)).fetchone()
        if row is None:
            return None
        if row["status"] == "held":
            return "held"
        if status == "retry" and int(row["attempts"] or 0) >= 3:
            status = "failed"
        conn.execute(
            "UPDATE topic_candidates SET status=?, lease_until=NULL, last_error=?, updated_at=? WHERE id=?",
            (status, str(error or "")[:2000] or None, utcnow(), int(candidate_id)),
        )
    return status


def validate_topic_payload(payload: dict[str, Any]) -> dict[str, Any]:
    slug = _validate_slug(payload.get("slug", ""))
    title = normalise_article_count(payload.get("title")).strip()[:300]
    category = _validate_slug(payload.get("category") or "general-knowledge")
    summary = normalise_article_count(payload.get("summary")).strip()[:600]
    intro = normalise_article_count(payload.get("intro")).strip()[:1800]
    items = payload.get("items")
    if not title or not summary or not intro or not isinstance(items, list) or len(items) != 10:
        raise ValueError("published topics require title, summary, intro and exactly 10 facts")
    seen_keys: set[str] = set()
    clean_items = []
    for pos, raw in enumerate(items, 1):
        if not isinstance(raw, dict):
            raise ValueError(f"fact {pos} is not an object")
        fact_title = str(raw.get("title") or "").strip()[:300]
        body = str(raw.get("body") or "").strip()[:2500]
        if len(fact_title) < 5 or len(body) < 40:
            raise ValueError(f"fact {pos} is incomplete")
        try:
            confidence = float(raw.get("confidence", 0))
        except (TypeError, ValueError):
            confidence = 0
        if not math.isfinite(confidence) or confidence < 0.70 or confidence > 1.0:
            raise ValueError(f"fact {pos} confidence must be between 0.70 and 1.0")
        fact_key = str(raw.get("fact_key") or "").strip().lower()
        if not fact_key:
            fact_key = "fact-" + hashlib.sha256((fact_title.casefold() + "\n" + body.casefold()).encode()).hexdigest()[:20]
        fact_key = re.sub(r"[^a-z0-9._:-]+", "-", fact_key).strip("-")[:160]
        if fact_key in seen_keys:
            raise ValueError("duplicate fact_key in topic")
        seen_keys.add(fact_key)
        sources = raw.get("sources")
        if not isinstance(sources, list) or not sources:
            raise ValueError(f"fact {pos} requires at least one source")
        clean_sources = []
        for src in sources[:4]:
            if not isinstance(src, dict):
                continue
            url = _validate_url(src.get("url", ""))
            excerpt = str(src.get("evidence_excerpt") or "").strip()[:700]
            if len(excerpt) < 15:
                continue
            clean_sources.append({
                "url": url,
                "title": str(src.get("title") or "")[:400],
                "publisher": str(src.get("publisher") or "")[:220],
                "source_type": str(src.get("source_type") or "independent")[:80],
                "checked_at": str(src.get("checked_at") or utcnow())[:40],
                "evidence_excerpt": excerpt,
            })
        if not clean_sources:
            raise ValueError(f"fact {pos} has no valid source")
        clean_items.append({
            "fact_key": fact_key,
            "title": fact_title,
            "body": body,
            "confidence": confidence,
            "sources": clean_sources,
            "related_topics": raw.get("related_topics") if isinstance(raw.get("related_topics"), list) else [],
        })
    try:
        quality = float(payload.get("quality_score", 0.8))
    except (TypeError, ValueError):
        quality = 0.8
    if not math.isfinite(quality) or quality < 0.72 or quality > 1.0:
        raise ValueError("topic quality_score is below the publish gate")
    return {
        "slug": slug,
        "title": title,
        "category": category,
        "summary": summary,
        "intro": intro,
        "reading_time": str(payload.get("reading_time") or "7 min read")[:40],
        "quality_score": min(1.0, quality),
        "trigger": payload.get("trigger") if isinstance(payload.get("trigger"), dict) else {},
        "generation": payload.get("generation") if isinstance(payload.get("generation"), dict) else {},
        "items": clean_items,
        "related_topics": payload.get("related_topics") if isinstance(payload.get("related_topics"), list) else [],
    }


def publish_topic(payload: dict[str, Any], candidate_id: int | None = None) -> dict[str, Any]:
    candidate = None
    if candidate_id is not None:
        with connection() as conn:
            row = conn.execute("SELECT * FROM topic_candidates WHERE id=?", (int(candidate_id),)).fetchone()
            candidate = dict(row) if row else None
    try:
        if candidate_id is not None:
            if candidate is None:
                raise ValueError("candidate does not exist")
            if candidate["status"] not in {"claimed", "published"}:
                raise ValueError("candidate is not claimed or already published")
            if payload.get("slug") != candidate["slug"]:
                raise ValueError("topic slug does not match claimed candidate")
        clean = validate_topic_payload(payload)
        issues = topic_quality_issues(
            clean,
            expected_title=candidate["title"] if candidate else clean["slug"].replace("-", " "),
            expected_subject=candidate["subject"] if candidate else None,
        )
        if issues:
            raise ValueError("content quality: " + ", ".join(issues))
    except ValueError as exc:
        with connection() as conn:
            conn.execute(
                "INSERT INTO publication_rejections(candidate_id,gate_version,reasons_json,payload_json,created_at) VALUES(?,?,?,?,?)",
                (candidate_id, QUALITY_GATE_VERSION, _json([str(exc)]), _json(payload), utcnow()),
            )
        raise
    now = utcnow()
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        if candidate_id is not None:
            current = conn.execute("SELECT status,slug,title,subject FROM topic_candidates WHERE id=?", (int(candidate_id),)).fetchone()
            if current is None or current["status"] not in {"claimed", "published"} or any(current[key] != candidate[key] for key in ("slug", "title", "subject")):
                raise ValueError("candidate changed while the result was being validated")
        existing = conn.execute("SELECT id, created_at FROM topics WHERE slug=?", (clean["slug"],)).fetchone()
        created = existing["created_at"] if existing else now
        conn.execute(
            """
            INSERT INTO topics(slug,title,category,summary,intro,reading_time,status,quality_score,trigger_json,generation_json,created_at,updated_at)
            VALUES(?,?,?,?,?,?,'published',?,?,?,?,?)
            ON CONFLICT(slug) DO UPDATE SET title=excluded.title, category=excluded.category, summary=excluded.summary,
                intro=excluded.intro, reading_time=excluded.reading_time, status='published', quality_score=excluded.quality_score,
                trigger_json=excluded.trigger_json, generation_json=excluded.generation_json, updated_at=excluded.updated_at
            """,
            (clean["slug"], clean["title"], clean["category"], clean["summary"], clean["intro"], clean["reading_time"], clean["quality_score"], _json(clean["trigger"]), _json(clean["generation"]), created, now),
        )
        topic_id = int(conn.execute("SELECT id FROM topics WHERE slug=?", (clean["slug"],)).fetchone()["id"])
        conn.execute("DELETE FROM topic_facts WHERE topic_id=?", (topic_id,))
        conn.execute("DELETE FROM topic_relations WHERE from_topic_id=?", (topic_id,))
        for position, item in enumerate(clean["items"], 1):
            fact_existing = conn.execute("SELECT id, created_at FROM facts WHERE fact_key=?", (item["fact_key"],)).fetchone()
            fact_created = fact_existing["created_at"] if fact_existing else now
            conn.execute(
                """INSERT INTO facts(fact_key,title,body,confidence,created_at,updated_at) VALUES(?,?,?,?,?,?)
                ON CONFLICT(fact_key) DO UPDATE SET title=excluded.title, body=excluded.body, confidence=excluded.confidence, updated_at=excluded.updated_at""",
                (item["fact_key"], item["title"], item["body"], item["confidence"], fact_created, now),
            )
            fact_id = int(conn.execute("SELECT id FROM facts WHERE fact_key=?", (item["fact_key"],)).fetchone()["id"])
            conn.execute("INSERT OR REPLACE INTO topic_facts(topic_id,fact_id,position) VALUES(?,?,?)", (topic_id, fact_id, position))
            for src in item["sources"]:
                conn.execute(
                    """INSERT INTO sources(url,title,publisher,source_type,checked_at) VALUES(?,?,?,?,?)
                    ON CONFLICT(url) DO UPDATE SET title=COALESCE(NULLIF(excluded.title,''),sources.title), publisher=COALESCE(NULLIF(excluded.publisher,''),sources.publisher), source_type=COALESCE(NULLIF(excluded.source_type,''),sources.source_type), checked_at=excluded.checked_at""",
                    (src["url"], src["title"], src["publisher"], src["source_type"], src["checked_at"]),
                )
                source_id = int(conn.execute("SELECT id FROM sources WHERE url=?", (src["url"],)).fetchone()["id"])
                conn.execute("INSERT OR REPLACE INTO fact_sources(fact_id,source_id,evidence_excerpt) VALUES(?,?,?)", (fact_id, source_id, src["evidence_excerpt"]))
            for related in item["related_topics"][:3]:
                if not isinstance(related, dict):
                    continue
                try:
                    to_slug = _validate_slug(related.get("slug", ""))
                except ValueError:
                    continue
                if to_slug == clean["slug"]:
                    continue
                conn.execute(
                    "INSERT OR IGNORE INTO topic_relations(from_topic_id,to_slug,to_title,relation,score,status) VALUES(?,?,?,?,?,'candidate')",
                    (topic_id, to_slug, str(related.get("title") or to_slug.replace('-', ' ').title())[:300], str(related.get("relationship") or "related")[:80], max(0.0, min(1.0, float(related.get("score", 0.65))))),
                )
        for related in clean["related_topics"][:12]:
            if not isinstance(related, dict):
                continue
            try:
                to_slug = _validate_slug(related.get("slug", ""))
            except ValueError:
                continue
            if to_slug == clean["slug"]:
                continue
            score = max(0.0, min(1.0, float(related.get("score", 0.65))))
            evergreen = max(0.0, min(1.0, float(related.get("evergreen_score", score))))
            conn.execute(
                "INSERT OR IGNORE INTO topic_relations(from_topic_id,to_slug,to_title,relation,score,status) VALUES(?,?,?,?,?,'candidate')",
                (topic_id, to_slug, str(related.get("title") or to_slug.replace('-', ' ').title())[:300], str(related.get("relationship") or "related")[:80], score),
            )
            if score >= 0.70 and evergreen >= 0.75:
                conn.execute(
                    """INSERT INTO topic_candidates(slug,title,subject,category,rationale,parent_slug,source_kind,score,evergreen_score,status,created_at,updated_at)
                    VALUES(?,?,?,?,?,?,'graph_expansion',?,?,'queued',?,?) ON CONFLICT DO NOTHING""",
                    (to_slug, str(related.get("title") or to_slug.replace('-', ' ').title())[:300], str(related.get("subject") or related.get("title") or to_slug.replace('-', ' '))[:300], str(related.get("category") or clean["category"])[:80], str(related.get("rationale") or "Linked from a verified What10Things fact")[:1200], clean["slug"], score, evergreen, now, now),
                )
        # One queued job per media class. A downstream workflow can fan these into platform-specific assets.
        for job_type, priority in (("fact_cards", 0.75), ("carousel", 0.85), ("short_video", 0.90)):
            conn.execute(
                """INSERT INTO social_jobs(topic_id,job_type,payload_json,status,priority,created_at,updated_at)
                VALUES(?,?,?,'queued',?,?,?) ON CONFLICT(topic_id,job_type) DO UPDATE SET payload_json=excluded.payload_json, status=CASE WHEN social_jobs.status='published' THEN 'published' ELSE 'queued' END, priority=excluded.priority, updated_at=excluded.updated_at""",
                (topic_id, job_type, _json({"topic_slug": clean["slug"], "topic_title": clean["title"]}), priority, now, now),
            )
        if candidate_id is not None:
            conn.execute("UPDATE topic_candidates SET status='published', lease_until=NULL, last_error=NULL, updated_at=? WHERE id=?", (now, int(candidate_id)))
    return {"topic_id": topic_id, "slug": clean["slug"], "facts": 10, "social_jobs_queued": 3}


def topic_summaries(limit: int = 100, category: str | None = None) -> list[dict[str, Any]]:
    sql = "SELECT slug,title,category,summary,intro,reading_time,quality_score,trigger_json,created_at,updated_at FROM topics WHERE status='published'"
    args: list[Any] = []
    if category:
        sql += " AND category=?"
        args.append(category)
    sql += " ORDER BY updated_at DESC LIMIT ?"
    args.append(max(1, min(500, int(limit))))
    with connection() as conn:
        rows = conn.execute(sql, args).fetchall()
    output = []
    for row in rows:
        item = dict(row)
        item["trigger"] = _load(item.pop("trigger_json"), {})
        output.append(item)
    return output


def get_topic(slug: str) -> dict[str, Any] | None:
    try:
        slug = _validate_slug(slug)
    except ValueError:
        return None
    with connection() as conn:
        topic = conn.execute("SELECT * FROM topics WHERE slug=? AND status='published'", (slug,)).fetchone()
        if topic is None:
            return None
        fact_rows = conn.execute(
            """SELECT tf.position,f.id,f.fact_key,f.title,f.body,f.confidence FROM topic_facts tf JOIN facts f ON f.id=tf.fact_id WHERE tf.topic_id=? ORDER BY tf.position""",
            (topic["id"],),
        ).fetchall()
        items = []
        for fact in fact_rows:
            source_rows = conn.execute(
                """SELECT s.url,s.title,s.publisher,s.source_type,s.checked_at FROM fact_sources fs JOIN sources s ON s.id=fs.source_id WHERE fs.fact_id=? ORDER BY s.source_type,s.publisher,s.title""",
                (fact["id"],),
            ).fetchall()
            rel_rows = conn.execute(
                "SELECT to_slug,to_title,relation,score,status FROM topic_relations WHERE from_topic_id=? ORDER BY score DESC,to_title LIMIT 12",
                (topic["id"],),
            ).fetchall()
            items.append({
                "position": fact["position"], "fact_key": fact["fact_key"], "title": fact["title"], "body": fact["body"], "confidence": fact["confidence"],
                "sources": [dict(r) for r in source_rows],
            })
        relations = [dict(r) for r in conn.execute("SELECT to_slug,to_title,relation,score,status FROM topic_relations WHERE from_topic_id=? ORDER BY score DESC,to_title LIMIT 20", (topic["id"],)).fetchall()]
        data = dict(topic)
        data["trigger"] = _load(data.pop("trigger_json"), {})
        data["generation"] = _load(data.pop("generation_json"), {})
        data["items"] = items
        data["related_topics"] = relations
        return data



def get_topic_by_id(topic_id: int) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute("SELECT slug FROM topics WHERE id=? AND status='published'", (int(topic_id),)).fetchone()
    return get_topic(row["slug"]) if row else None


def search_topics(query: str, limit: int = 20) -> list[dict[str, Any]]:
    terms = [t for t in re.split(r"\s+", str(query).casefold().strip()) if len(t) >= 2]
    if not terms:
        return []
    with connection() as conn:
        rows = conn.execute("SELECT slug,title,category,summary,intro FROM topics WHERE status='published' ORDER BY updated_at DESC LIMIT 500").fetchall()
        fact_by_topic = {r["slug"]: "" for r in rows}
        for fr in conn.execute("""SELECT t.slug,f.title,f.body FROM topics t JOIN topic_facts tf ON tf.topic_id=t.id JOIN facts f ON f.id=tf.fact_id WHERE t.status='published'""").fetchall():
            fact_by_topic[fr["slug"]] = fact_by_topic.get(fr["slug"], "") + " " + fr["title"] + " " + fr["body"]
    results = []
    for row in rows:
        hay = (" ".join([row["slug"], row["title"], row["summary"], row["intro"], fact_by_topic.get(row["slug"], "")])).casefold()
        score = sum(hay.count(t) for t in terms)
        if score:
            results.append({"score": score, **dict(row)})
    return sorted(results, key=lambda x: (-x["score"], x["title"]))[:limit]


def claim_social_job() -> dict[str, Any] | None:
    job = _claim_row("social_jobs", ("queued", "retry"), "priority DESC, created_at",
                     eligible_sql="EXISTS (SELECT 1 FROM topics WHERE topics.id=social_jobs.topic_id AND topics.status='published')")
    if not job:
        return None
    job["topic"] = get_topic_by_id(job["topic_id"])
    return job


def finish_social_job(job_id: int, status: str, result: dict[str, Any] | None = None, error: str | None = None) -> None:
    if status not in {"ready", "published", "retry", "failed"}:
        raise ValueError("invalid social job status")
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        topic = conn.execute("SELECT t.status,j.status AS job_status FROM social_jobs j JOIN topics t ON t.id=j.topic_id WHERE j.id=?", (int(job_id),)).fetchone()
        if topic is not None and topic["status"] != "published":
            # The audit retains already-published media as historical records.
            # A duplicate callback must not erase their external IDs/results.
            if topic["job_status"] == "published":
                return
            status, result, error = "held", None, "Source topic is held by the content quality gate"
        conn.execute(
            "UPDATE social_jobs SET status=?, result_json=?, lease_until=NULL, last_error=?, updated_at=? WHERE id=?",
            (status, _json(result) if result is not None else None, str(error or "")[:2000] or None, utcnow(), int(job_id)),
        )


def stats() -> dict[str, Any]:
    with connection() as conn:
        counts = {
            "topics": conn.execute("SELECT COUNT(*) FROM topics WHERE status='published'").fetchone()[0],
            "topics_held": conn.execute("SELECT COUNT(*) FROM topics WHERE status='held'").fetchone()[0],
            "content_quality_gate": QUALITY_GATE_VERSION,
            "facts": conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0],
            "sources": conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0],
            "signals_new": conn.execute("SELECT COUNT(*) FROM trend_signals WHERE status IN ('new','retry')").fetchone()[0],
            "candidates_queued": conn.execute("SELECT COUNT(*) FROM topic_candidates WHERE status IN ('queued','retry')").fetchone()[0],
            "social_queued": conn.execute("SELECT COUNT(*) FROM social_jobs WHERE status IN ('queued','retry')").fetchone()[0],
        }
    return counts




def _quality_payload(conn: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    """Reconstruct evidence privately for audit; public API omits excerpts."""
    payload = dict(row)
    payload["trigger"] = _load(payload.pop("trigger_json"), {})
    payload["generation"] = _load(payload.pop("generation_json"), {})
    payload["items"] = []
    for fact in conn.execute("SELECT f.* FROM facts f JOIN topic_facts tf ON tf.fact_id=f.id WHERE tf.topic_id=? ORDER BY tf.position", (row["id"],)).fetchall():
        item = dict(fact)
        item["sources"] = [dict(source) for source in conn.execute(
            "SELECT s.*,fs.evidence_excerpt FROM fact_sources fs JOIN sources s ON s.id=fs.source_id WHERE fs.fact_id=?", (fact["id"],)
        ).fetchall()]
        payload["items"].append(item)
    return payload


def audit_existing_topics() -> dict[str, int]:
    """Hold failed legacy output once per gate revision, preserving every row.

    Each full original payload and affected queue row is snapshotted in SQLite
    before a status changes. This is transactional and needs no new service or
    credential. A crash rolls back the audit and the next startup retries it.
    """
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        done = conn.execute("SELECT topics_checked,topics_held FROM quality_audits WHERE gate_version=?", (QUALITY_GATE_VERSION,)).fetchone()
        if done is not None:
            return dict(done)
        rows = conn.execute("SELECT * FROM topics WHERE status='published' ORDER BY id").fetchall()
        held = 0
        for row in rows:
            payload = _quality_payload(conn, row)
            candidate = conn.execute("SELECT title,subject FROM topic_candidates WHERE slug=? ORDER BY CASE WHEN status='published' THEN 0 ELSE 1 END,id DESC LIMIT 1", (row["slug"],)).fetchone()
            issues = topic_quality_issues(
                payload,
                expected_title=candidate["title"] if candidate else row["slug"].replace("-", " "),
                expected_subject=candidate["subject"] if candidate else None,
                require_evidence=False, legacy=True,  # Keep the legacy audit conservative.
            )
            reviewed_issue = reviewed_legacy_issue(payload)
            if reviewed_issue:
                issues.append(reviewed_issue)
            if not issues:
                continue
            now = utcnow()
            snapshot = {
                "topic": dict(row), "payload": payload,
                "relations": [dict(item) for item in conn.execute("SELECT * FROM topic_relations WHERE from_topic_id=?", (row["id"],)).fetchall()],
                "candidates": [dict(item) for item in conn.execute("SELECT * FROM topic_candidates WHERE slug=? OR (parent_slug=? AND status!='published')", (row["slug"],row["slug"])).fetchall()],
                "social_jobs": [dict(item) for item in conn.execute("SELECT * FROM social_jobs WHERE topic_id=? AND status!='published'", (row["id"],)).fetchall()],
            }
            conn.execute("INSERT INTO quality_reviews(topic_id,gate_version,reasons_json,snapshot_json,created_at) VALUES(?,?,?,?,?)", (row["id"],QUALITY_GATE_VERSION,_json(issues),_json(snapshot),now))
            reason = "Content quality hold: " + ", ".join(issues)
            conn.execute("UPDATE topics SET status='held' WHERE id=?", (row["id"],))
            conn.execute("UPDATE topic_candidates SET status='held',lease_until=NULL,last_error=?,updated_at=? WHERE slug=? OR (parent_slug=? AND status!='published')", (reason[:2000],now,row["slug"],row["slug"]))
            conn.execute("UPDATE social_jobs SET status='held',lease_until=NULL,last_error=?,updated_at=? WHERE topic_id=? AND status!='published'", (reason[:2000],now,row["id"]))
            held += 1
        conn.execute("INSERT INTO quality_audits(gate_version,topics_checked,topics_held,completed_at) VALUES(?,?,?,?)", (QUALITY_GATE_VERSION,len(rows),held,utcnow()))
        return {"topics_checked": len(rows), "topics_held": held}


init_db()
audit_existing_topics()

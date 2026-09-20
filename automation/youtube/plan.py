"""Deterministic media planning for What10Things YouTube derivatives.

This module does not call models, networks, TTS providers or publishing APIs.
It converts one already-published, evidence-backed What10Things topic into a
bounded production plan for normal YouTube, bedtime/sleep long-form, Shorts and
podcast audio.
"""
from __future__ import annotations

import re
from typing import Any

SLEEP_CATEGORIES = {
    "history-culture",
    "science-nature",
    "world",
    "general-knowledge",
    "travel",
    "technology",
}

_WORD_RE = re.compile(r"\s+")


class PlanError(ValueError):
    """Raised when a topic cannot safely be converted into a media plan."""


def _clean(value: Any, *, limit: int = 300) -> str:
    text = _WORD_RE.sub(" ", str(value or "")).strip()
    return text[:limit]


def _subject_from_title(title: str) -> str:
    value = _clean(title, limit=240)
    value = re.sub(r"^\s*10\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^things\s+", "", value, flags=re.IGNORECASE)
    return value.strip(" -:|") or "this topic"


def build_plan(topic: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(topic, dict):
        raise PlanError("topic must be an object")

    slug = _clean(topic.get("slug"), limit=120)
    title = _clean(topic.get("title"), limit=300)
    category = _clean(topic.get("category"), limit=80).lower()
    items = topic.get("items")

    if not slug or not title:
        raise PlanError("topic requires slug and title")
    if not isinstance(items, list) or len(items) != 10:
        raise PlanError("topic must contain exactly ten evidence-backed items")

    chapters: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise PlanError(f"item {index} must be an object")
        item_title = _clean(item.get("title"), limit=220)
        item_body = _clean(item.get("body"), limit=1600)
        sources = item.get("sources") or []
        if not item_title or len(item_body) < 40 or not isinstance(sources, list) or not sources:
            raise PlanError(f"item {index} is missing usable title, body or sources")
        chapters.append(
            {
                "number": index,
                "title": item_title,
                "source_item_index": index - 1,
                "source_count": len(sources),
                "standard_target_words": 125,
                "sleep_target_words": 1450,
            }
        )

    subject = _subject_from_title(title)
    sleep_eligible = category in SLEEP_CATEGORIES

    return {
        "schema_version": 1,
        "site_key": "what10things",
        "topic_slug": slug,
        "topic_title": title,
        "category": category,
        "sleep_eligible": sleep_eligible,
        "evidence_rule": (
            "All material factual claims must remain traceable to the published "
            "topic evidence or a new retained source pack. Unsupported expansion "
            "must be rejected, not improvised."
        ),
        "formats": {
            "youtube_standard": {
                "enabled": True,
                "target_duration_minutes": 12,
                "target_words": 1700,
                "chapter_count": 10,
                "title": f"{title} | What10Things",
                "voice_style": "clear neutral UK English; useful and conversational",
                "visual_strategy": "licensed/public-domain imagery plus slow deterministic motion",
                "chapters": chapters,
            },
            "youtube_sleep": {
                "enabled": sleep_eligible,
                "target_duration_minutes": 120,
                "target_words": 15000,
                "chapter_count": 10,
                "title": f"10 {subject} to Fall Asleep To | 2 Hours of Calm Facts",
                "voice_style": "calm neutral UK English; 118-125 words per minute; no sudden emphasis",
                "visual_strategy": (
                    "low-change 16:9 imagery; gentle pan/zoom; dark-friendly transitions; "
                    "no rapid cuts or flashing text"
                ),
                "chapters": chapters,
                "script_constraints": {
                    "intro_target_words": 250,
                    "chapter_target_words": 1450,
                    "outro_target_words": 250,
                    "no_fake_first_person": True,
                    "no_unverified_superlatives": True,
                    "no_repetitive_padding": True,
                },
            },
            "youtube_shorts": {
                "enabled": True,
                "count": 10,
                "target_duration_seconds_each": 45,
                "source_rule": "one Short per evidence-backed item; preserve source traceability",
            },
            "podcast_audio": {
                "enabled": sleep_eligible,
                "source_format": "youtube_sleep",
                "title": f"10 {subject} to Fall Asleep To",
                "artwork_strategy": "reuse approved long-form thumbnail artwork without YouTube UI",
            },
        },
        "production": {
            "incremental_cost_target": 0,
            "tts_preference": "local/offline open-source voice",
            "video_assembly": "ffmpeg",
            "paid_media_generation_allowed": False,
            "publish_requires_channel_auth": True,
            "manual_review_required_for_routine_jobs": False,
            "fail_closed_on_missing_evidence": True,
        },
    }

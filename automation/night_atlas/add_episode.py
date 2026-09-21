#!/usr/bin/env python3
"""Append one published Night Atlas episode to the RSS manifest."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def _https(value: str) -> str:
    value = str(value or "").strip()
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("audio URL must be absolute HTTPS")
    return value


def _iso(value: str) -> str:
    value = str(value or "").strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError("published_at must include timezone")
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("episodes.json"))
    parser.add_argument("--slug", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--audio-url", required=True)
    parser.add_argument("--audio-bytes", type=int, required=True)
    parser.add_argument("--duration-seconds", type=int, required=True)
    parser.add_argument("--published-at", required=True)
    parser.add_argument("--episode-number", type=int)
    args = parser.parse_args()

    if args.audio_bytes <= 0 or args.duration_seconds <= 0:
        raise SystemExit("audio-bytes and duration-seconds must be greater than zero")
    if len(" ".join(args.description.split())) < 20:
        raise SystemExit("description is too short")

    episodes = json.loads(args.manifest.read_text(encoding="utf-8"))
    if not isinstance(episodes, list):
        raise SystemExit("manifest must contain a JSON array")

    slug = args.slug.strip()
    guid = f"urn:night-atlas:{slug}"
    if any(item.get("slug") == slug or item.get("guid") == guid for item in episodes):
        raise SystemExit(f"episode already exists: {slug}")

    item = {
        "slug": slug,
        "guid": guid,
        "title": " ".join(args.title.split()).strip(),
        "description": " ".join(args.description.split()).strip(),
        "audio_url": _https(args.audio_url),
        "audio_bytes": args.audio_bytes,
        "duration_seconds": args.duration_seconds,
        "published_at": _iso(args.published_at),
    }
    if args.episode_number:
        item["episode_number"] = args.episode_number

    episodes.append(item)
    args.manifest.write_text(json.dumps(episodes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Added Night Atlas episode: {slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

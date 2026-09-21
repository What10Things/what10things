#!/usr/bin/env python3
"""Build the self-hosted Night Atlas podcast RSS feed.

No third-party packages are required. Episodes are intentionally kept in a
small JSON manifest so the Urban Sky automation can add one published audio
asset and let the normal What10Things deployment publish the updated feed.
"""
from __future__ import annotations

import argparse
import email.utils
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM = "http://www.w3.org/2005/Atom"

ET.register_namespace("itunes", ITUNES)
ET.register_namespace("atom", ATOM)


class FeedError(ValueError):
    pass


def _https(value: str, field: str) -> str:
    value = str(value or "").strip()
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise FeedError(f"{field} must be an absolute https URL")
    return value


def _text(value, field: str, minimum: int = 1) -> str:
    value = " ".join(str(value or "").split()).strip()
    if len(value) < minimum:
        raise FeedError(f"{field} is missing or too short")
    return value


def _positive_int(value, field: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise FeedError(f"{field} must be an integer") from exc
    if number <= 0:
        raise FeedError(f"{field} must be greater than zero")
    return number


def _published(value: str) -> datetime:
    raw = _text(value, "published_at")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise FeedError("published_at must be ISO-8601") from exc
    if dt.tzinfo is None:
        raise FeedError("published_at must include a timezone")
    return dt.astimezone(timezone.utc)


def _duration(seconds: int) -> str:
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_show(show: dict) -> dict:
    if not isinstance(show, dict):
        raise FeedError("show metadata must be an object")
    required = [
        "title", "link", "feed_url", "description", "language", "author",
        "owner_name", "owner_email", "category", "image_url", "copyright",
    ]
    for key in required:
        if key not in show:
            raise FeedError(f"show metadata missing {key}")
    result = dict(show)
    result["title"] = _text(show["title"], "title")
    result["link"] = _https(show["link"], "link")
    result["feed_url"] = _https(show["feed_url"], "feed_url")
    result["image_url"] = _https(show["image_url"], "image_url")
    result["description"] = _text(show["description"], "description", 20)
    result["owner_email"] = _text(show["owner_email"], "owner_email")
    if "@" not in result["owner_email"]:
        raise FeedError("owner_email must look like an email address")
    return result


def validate_episodes(raw) -> list[dict]:
    if not isinstance(raw, list):
        raise FeedError("episodes manifest must be an array")

    seen_slug: set[str] = set()
    seen_guid: set[str] = set()
    episodes: list[dict] = []

    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise FeedError(f"episode {index} must be an object")
        episode = dict(item)
        slug = _text(item.get("slug"), f"episode {index} slug")
        if slug in seen_slug:
            raise FeedError(f"duplicate episode slug: {slug}")
        seen_slug.add(slug)

        guid = _text(item.get("guid") or f"urn:night-atlas:{slug}", f"episode {index} guid")
        if guid in seen_guid:
            raise FeedError(f"duplicate episode guid: {guid}")
        seen_guid.add(guid)

        episode["slug"] = slug
        episode["guid"] = guid
        episode["title"] = _text(item.get("title"), f"episode {index} title")
        episode["description"] = _text(item.get("description"), f"episode {index} description", 20)
        episode["audio_url"] = _https(item.get("audio_url"), f"episode {index} audio_url")
        episode["audio_bytes"] = _positive_int(item.get("audio_bytes"), f"episode {index} audio_bytes")
        episode["duration_seconds"] = _positive_int(item.get("duration_seconds"), f"episode {index} duration_seconds")
        episode["_published"] = _published(item.get("published_at"))
        episodes.append(episode)

    episodes.sort(key=lambda item: item["_published"], reverse=True)
    return episodes


def build_feed(show: dict, episodes: list[dict]) -> ET.ElementTree:
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = show["title"]
    ET.SubElement(channel, "link").text = show["link"]
    ET.SubElement(channel, "description").text = show["description"]
    ET.SubElement(channel, "language").text = show["language"]
    ET.SubElement(channel, "copyright").text = show["copyright"]
    ET.SubElement(
        channel,
        f"{{{ATOM}}}link",
        {"href": show["feed_url"], "rel": "self", "type": "application/rss+xml"},
    )
    ET.SubElement(channel, f"{{{ITUNES}}}author").text = show["author"]
    ET.SubElement(channel, f"{{{ITUNES}}}summary").text = show["description"]
    ET.SubElement(channel, f"{{{ITUNES}}}explicit").text = "true" if show.get("explicit") else "false"
    ET.SubElement(channel, f"{{{ITUNES}}}type").text = "episodic"
    ET.SubElement(channel, f"{{{ITUNES}}}image", {"href": show["image_url"]})

    owner = ET.SubElement(channel, f"{{{ITUNES}}}owner")
    ET.SubElement(owner, f"{{{ITUNES}}}name").text = show["owner_name"]
    ET.SubElement(owner, f"{{{ITUNES}}}email").text = show["owner_email"]

    category = ET.SubElement(channel, f"{{{ITUNES}}}category", {"text": show["category"]})
    subcategory = str(show.get("subcategory") or "").strip()
    if subcategory:
        ET.SubElement(category, f"{{{ITUNES}}}category", {"text": subcategory})

    for item in episodes:
        node = ET.SubElement(channel, "item")
        ET.SubElement(node, "title").text = item["title"]
        ET.SubElement(node, "description").text = item["description"]
        ET.SubElement(node, "guid", {"isPermaLink": "false"}).text = item["guid"]
        ET.SubElement(node, "pubDate").text = email.utils.format_datetime(item["_published"])
        ET.SubElement(
            node,
            "enclosure",
            {
                "url": item["audio_url"],
                "length": str(item["audio_bytes"]),
                "type": "audio/mpeg",
            },
        )
        ET.SubElement(node, f"{{{ITUNES}}}author").text = show["author"]
        ET.SubElement(node, f"{{{ITUNES}}}summary").text = item["description"]
        ET.SubElement(node, f"{{{ITUNES}}}explicit").text = "false"
        ET.SubElement(node, f"{{{ITUNES}}}duration").text = _duration(item["duration_seconds"])
        ET.SubElement(node, f"{{{ITUNES}}}episodeType").text = "full"
        ET.SubElement(node, f"{{{ITUNES}}}image", {"href": show["image_url"]})
        if item.get("episode_number"):
            ET.SubElement(node, f"{{{ITUNES}}}episode").text = str(_positive_int(item["episode_number"], "episode_number"))

    return ET.ElementTree(rss)


def write_feed(show_path: Path, episodes_path: Path, output_path: Path) -> int:
    show = validate_show(load_json(show_path))
    episodes = validate_episodes(load_json(episodes_path))
    tree = build_feed(show, episodes)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(tree, space="  ")
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    return len(episodes)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--show", type=Path, required=True)
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        count = write_feed(args.show, args.episodes, args.output)
    except (FeedError, json.JSONDecodeError, OSError) as exc:
        print(f"Night Atlas feed build failed: {exc}", file=sys.stderr)
        return 1
    print(f"Night Atlas RSS written to {args.output} with {count} episode(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

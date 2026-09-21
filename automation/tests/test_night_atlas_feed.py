from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

MODULE_PATH = Path(__file__).parents[1] / "night_atlas" / "build_feed.py"
SPEC = importlib.util.spec_from_file_location("night_atlas_feed", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


SHOW = {
    "title": "Night Atlas",
    "link": "https://what10things.co.uk/night-atlas/",
    "feed_url": "https://what10things.co.uk/night-atlas/rss.xml",
    "description": "Immersive soundscapes and calm long-form audio for sleep and relaxation.",
    "language": "en-gb",
    "author": "Night Atlas",
    "owner_name": "Night Atlas",
    "owner_email": "admin@what10things.com",
    "category": "Health & Fitness",
    "subcategory": "Mental Health",
    "image_url": "https://what10things.co.uk/night-atlas/cover.png",
    "copyright": "2026 Urban Sky Web Ltd",
    "explicit": False,
}


class FeedTests(unittest.TestCase):
    def test_empty_feed_builds(self):
        show = MODULE.validate_show(SHOW)
        episodes = MODULE.validate_episodes([])
        tree = MODULE.build_feed(show, episodes)
        root = tree.getroot()
        self.assertEqual(root.findtext("./channel/title"), "Night Atlas")
        self.assertEqual(len(root.findall("./channel/item")), 0)

    def test_episode_has_enclosure_and_duration(self):
        episode = {
            "slug": "rainy-night-cabin",
            "title": "Rainy Night Cabin",
            "description": "A long, calm rainfall soundscape intended for sleep and quiet relaxation.",
            "audio_url": "https://cdn.example.test/rainy-night-cabin.mp3",
            "audio_bytes": 1234567,
            "duration_seconds": 7200,
            "published_at": "2026-09-21T20:00:00Z",
        }
        show = MODULE.validate_show(SHOW)
        episodes = MODULE.validate_episodes([episode])
        tree = MODULE.build_feed(show, episodes)
        item = tree.getroot().find("./channel/item")
        self.assertIsNotNone(item)
        enclosure = item.find("enclosure")
        self.assertEqual(enclosure.attrib["type"], "audio/mpeg")
        self.assertEqual(enclosure.attrib["length"], "1234567")
        duration = item.find(f"{{{MODULE.ITUNES}}}duration")
        self.assertEqual(duration.text, "02:00:00")

    def test_write_feed_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            show_path = root / "show.json"
            episodes_path = root / "episodes.json"
            out = root / "rss.xml"
            show_path.write_text(json.dumps(SHOW), encoding="utf-8")
            episodes_path.write_text("[]", encoding="utf-8")
            self.assertEqual(MODULE.write_feed(show_path, episodes_path, out), 0)
            ET.parse(out)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).parents[1] / "youtube" / "plan.py"
SPEC = importlib.util.spec_from_file_location("w10_youtube_plan", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def sample_topic(category: str = "history-culture"):
    return {
        "slug": "ten-things-about-pompeii",
        "title": "10 Things About Pompeii",
        "category": category,
        "items": [
            {
                "title": f"Fact {i}",
                "body": "A sufficiently detailed evidence-backed body explaining the factual point.",
                "sources": [{"url": f"https://example.org/{i}"}],
            }
            for i in range(1, 11)
        ],
    }


class YouTubePlanTests(unittest.TestCase):
    def test_builds_four_bounded_formats(self):
        plan = MODULE.build_plan(sample_topic())
        self.assertEqual(plan["topic_slug"], "ten-things-about-pompeii")
        self.assertTrue(plan["sleep_eligible"])
        self.assertEqual(set(plan["formats"]), {
            "youtube_standard",
            "youtube_sleep",
            "youtube_shorts",
            "podcast_audio",
        })
        self.assertEqual(len(plan["formats"]["youtube_sleep"]["chapters"]), 10)
        self.assertEqual(plan["formats"]["youtube_sleep"]["target_words"], 15000)
        self.assertEqual(plan["production"]["incremental_cost_target"], 0)
        self.assertFalse(plan["production"]["paid_media_generation_allowed"])

    def test_non_sleep_category_keeps_standard_and_shorts(self):
        plan = MODULE.build_plan(sample_topic("buying-guides"))
        self.assertFalse(plan["formats"]["youtube_sleep"]["enabled"])
        self.assertFalse(plan["formats"]["podcast_audio"]["enabled"])
        self.assertTrue(plan["formats"]["youtube_standard"]["enabled"])
        self.assertTrue(plan["formats"]["youtube_shorts"]["enabled"])

    def test_requires_exactly_ten_evidence_backed_items(self):
        topic = sample_topic()
        topic["items"] = topic["items"][:9]
        with self.assertRaises(MODULE.PlanError):
            MODULE.build_plan(topic)

        topic = sample_topic()
        topic["items"][2]["sources"] = []
        with self.assertRaises(MODULE.PlanError):
            MODULE.build_plan(topic)

    def test_is_deterministic(self):
        topic = sample_topic()
        self.assertEqual(MODULE.build_plan(topic), MODULE.build_plan(topic))


if __name__ == "__main__":
    unittest.main()

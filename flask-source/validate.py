from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from pathlib import Path

TEST_SECRET = "what10things-validation-only"
TEST_RUNTIME = Path(tempfile.gettempdir()) / "w10-validation-runtime"
shutil.rmtree(TEST_RUNTIME, ignore_errors=True)
os.environ["W10_RUNTIME_DIR"] = str(TEST_RUNTIME)
os.environ["W10_AUTOMATION_KEY_SHA256"] = hashlib.sha256(TEST_SECRET.encode()).hexdigest()

from app import app, CATEGORIES, DESTINATIONS, GUIDES  # noqa: E402

assert len(GUIDES) >= 10
assert len(CATEGORIES) >= 10
assert len(DESTINATIONS) >= 10
for slug, guide in GUIDES.items():
    assert len(guide.get("items", [])) == 10, slug

sample = {
    "slug": "validation-landslides",
    "title": "10 validation facts about landslides",
    "category": "science-nature",
    "summary": "A validation-only landslides topic used to prove the evidence-backed publishing path.",
    "intro": "This landslides record is written only to a temporary database during deployment validation.",
    "reading_time": "6 min read",
    "quality_score": 0.92,
    "trigger": {"source": "validation", "query": "landslides"},
    "generation": {"workflow": "validation"},
    "items": [
        {
            "title": f"Validation fact {i} about landslides",
            "body": f"This is validation evidence text for fact {i}; it is deliberately long enough to pass the structural publication gate without being production content.",
            "confidence": 0.9,
            "sources": [{
                "url": f"https://example.org/validation-source-{i}",
                "title": f"Landslides validation source {i}",
                "publisher": "Example validation source",
                "source_type": "validation",
                "evidence_excerpt": f"Landslides validation evidence text for fact {i}; it is deliberately long enough to pass the structural publication gate without being production content.",
            }],
        }
        for i in range(1, 11)
    ],
    "related_topics": [{
        "slug": "how-landslides-happen",
        "title": "10 things to know about how landslides happen",
        "subject": "how landslides happen",
        "category": "science-nature",
        "score": 0.85,
        "evergreen_score": 0.9,
    }],
}

with app.test_client() as client:
    checks = {
        "/": "Ten clear things",
        "/topics": "Knowledge network",
        "/guides": "Seed guides",
        "/guides/air-fryer-buying-guide": "Start with usable capacity",
        "/travel": "Know the ten things",
        "/travel/rome": "Rome",
        "/search?q=wifi": "improve Wi-Fi",
        "/methodology": "Map the evergreen subject",
    }
    for path, text in checks.items():
        response = client.get(path)
        assert response.status_code == 200, (path, response.status_code)
        assert text.encode() in response.data, (path, text)

    for path in ("/", "/about", "/privacy", "/terms", "/affiliate-disclosure"):
        response = client.get(path)
        assert response.status_code == 200, (path, response.status_code)
        assert b"What10Things.co.uk is operated by Urban Sky Web Ltd." in response.data, path
        assert b"17421062" in response.data, path
        assert b"14/2E Docklands Business Centre" in response.data, path
        assert b"registered in England and Wales" in response.data, path
        assert b"trading name of Urban Sky Web Ltd" in response.data, path

    privacy = client.get("/privacy").data
    assert b"Information, purposes and lawful bases" in privacy
    assert b"Information Commissioner" in privacy
    disclosure = client.get("/affiliate-disclosure").data
    assert b"visibly marked <strong>Ad</strong>" in disclosure

    unauthorised = client.post("/api/automation/signals/claim")
    assert unauthorised.status_code == 401

    headers = {"X-Automation-Key": TEST_SECRET}
    signal = client.post("/api/automation/signals/batch", headers=headers, json={"signals": [{
        "source": "validation",
        "source_key": "validation-landslide-signal",
        "title": "Landslides validation signal",
        "query": "landslides",
        "source_url": "https://example.org/trend",
        "metric_name": "searches",
        "metric_value": 100000,
    }]})
    assert signal.status_code == 200, signal.data
    claimed = client.post("/api/automation/signals/claim", headers=headers).get_json()["signal"]
    assert claimed and claimed["query"] == "landslides"

    mapped = client.post(f"/api/automation/signals/{claimed['id']}/result", headers=headers, json={
        "status": "mapped",
        "candidates": [{
            "slug": sample["slug"],
            "title": sample["title"],
            "subject": "landslides",
            "category": "science-nature",
            "rationale": "Validation of trend to evergreen topic mapping.",
            "score": 0.9,
            "evergreen_score": 0.95,
        }],
    })
    assert mapped.status_code == 200, mapped.data
    candidate = client.post("/api/automation/candidates/claim", headers=headers).get_json()["candidate"]
    assert candidate and candidate["slug"] == sample["slug"]

    published = client.post(f"/api/automation/candidates/{candidate['id']}/result", headers=headers, json={"status": "published", "topic": sample})
    assert published.status_code == 200, published.data
    assert published.get_json()["facts"] == 10

    topic = client.get("/topics/validation-landslides")
    assert topic.status_code == 200
    assert b"Sources" in topic.data
    assert b"Evidence confidence" in topic.data
    assert b"not live-news coverage" in topic.data
    assert client.get("/api/status").get_json()["knowledge"]["topics"] == 1

print("What 10 Things knowledge-pipeline validation passed")
shutil.rmtree(TEST_RUNTIME, ignore_errors=True)

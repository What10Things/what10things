"""Regression tests for the actual wrong-topic publication failures.

Run against the reconstructed application with PYTHONPATH=deploy. The fixture
files are captures of the site's public API from 19 October 2026; their source
excerpts were not public and are not invented for the fixture assertions.
"""
from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

TEST_RUNTIME = tempfile.TemporaryDirectory(prefix="w10-content-quality-")
os.environ["W10_RUNTIME_DIR"] = TEST_RUNTIME.name
os.environ["W10_AUTOMATION_KEY_SHA256"] = hashlib.sha256(b"content-quality-tests-only").hexdigest()

import knowledge_store as store  # noqa: E402
from app import app  # noqa: E402
from content_quality import failed_generation_text, fact_has_support, matches_subject, normalise_article_count, topic_quality_issues  # noqa: E402
from legacy_quality_holds import REVIEWED_LEGACY_HOLDS, reviewed_legacy_issue  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def observed(slug):
    return json.loads((FIXTURES / (slug + ".json")).read_text())["topic"]


def valid_topic(slug="mount-fuji"):
    # Deliberately synthetic fixtures, never posted to the production site.
    return {
        "slug": slug, "title": "10 facts about Mount Fuji", "category": "world",
        "summary": "A local test explainer of ten distinct points about Mount Fuji.",
        "intro": "Mount Fuji is the canonical subject for this isolated publication test.",
        "quality_score": .9, "reading_time": "6 min read",
        "trigger": {"query": "Mount Fuji"}, "generation": {"workflow": "local test"},
        "items": [{
            "title": f"Mount Fuji test point {i}",
            "body": f"Mount Fuji test point {i} has an independent identifier and sufficient detail to exercise the source association and publication path.",
            "confidence": .9,
            "sources": [{"url": f"https://example.org/fuji/{i}", "title": "Mount Fuji test source", "evidence_excerpt": f"Mount Fuji test point {i} uses an independent identifier for source association and publication validation."}],
        } for i in range(1, 11)],
    }


def seed_legacy(payload):
    """Model a pre-fix row directly without calling the new publication gate."""
    now = store.utcnow()
    with store.connection() as conn:
        conn.execute("INSERT INTO topics(slug,title,category,summary,intro,quality_score,trigger_json,generation_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (payload["slug"],payload["title"],payload["category"],payload["summary"],payload["intro"],.85,json.dumps(payload.get("trigger",{})),json.dumps(payload.get("generation",{})),now,now))
        topic_id = conn.execute("SELECT id FROM topics WHERE slug=?", (payload["slug"],)).fetchone()[0]
        conn.execute("INSERT INTO topic_candidates(slug,title,subject,status,attempts,created_at,updated_at) VALUES(?,?,?,'published',1,?,?)", (payload["slug"],payload["title"],payload["title"],now,now))
        for position, item in enumerate(payload["items"],1):
            key = f"legacy-{topic_id}-{position}"
            conn.execute("INSERT INTO facts(fact_key,title,body,confidence,created_at,updated_at) VALUES(?,?,?,?,?,?)", (key,item["title"],item["body"],.85,now,now))
            fact_id = conn.execute("SELECT id FROM facts WHERE fact_key=?", (key,)).fetchone()[0]
            conn.execute("INSERT INTO topic_facts(topic_id,fact_id,position) VALUES(?,?,?)", (topic_id,fact_id,position))
            for source in item["sources"]:
                conn.execute("INSERT OR IGNORE INTO sources(url,title) VALUES(?,?)", (source["url"],source["title"]))
                source_id = conn.execute("SELECT id FROM sources WHERE url=?", (source["url"],)).fetchone()[0]
                conn.execute("INSERT OR IGNORE INTO fact_sources(fact_id,source_id,evidence_excerpt) VALUES(?,?,?)", (fact_id,source_id,source.get("evidence_excerpt")))
        for kind, status in (("fact_cards","queued"),("carousel","claimed"),("short_video","published")):
            conn.execute("INSERT INTO social_jobs(topic_id,job_type,status,created_at,updated_at) VALUES(?,?,?,?,?)", (topic_id,kind,status,now,now))
    return topic_id


class ContentQualityTests(unittest.TestCase):
    def setUp(self):
        with store.connection() as conn:
            for table in ("quality_reviews","publication_rejections","quality_audits","fact_sources","topic_facts","topic_relations","social_jobs","topic_candidates","trend_signals","topics","facts","sources"):
                conn.execute(f"DELETE FROM {table}")

    def test_observed_office_article_and_insufficient_evidence_article_are_rejected(self):
        wrong = topic_quality_issues(observed("erechtheion"),require_evidence=False)
        self.assertIn("article_does_not_address_subject", wrong)
        self.assertIn("facts_do_not_address_subject", wrong)
        failed = topic_quality_issues(observed("acropolis-athens"),require_evidence=False)
        self.assertIn("failed_generation_message", failed)

    def test_relevant_facts_need_relevant_source_evidence(self):
        topic = valid_topic()
        self.assertEqual(topic_quality_issues(topic), [])
        for fact in topic["items"]:
            fact["sources"] = [{"url":"https://example.org/office","title":"Office installation", "evidence_excerpt":"Install Outlook and Microsoft Office applications on Windows computers."}]
        issues = topic_quality_issues(topic)
        self.assertIn("fact_1_sources_do_not_address_subject", issues)

    def test_failure_detection_leaves_normal_model_and_uncertainty_prose_alone(self):
        for prose in (
            "A language model predicts the next token in a sequence.",
            "Archaeologists have insufficient evidence to identify the original builder of Stonehenge.",
            "Available evidence does not establish the original colour of the temple roof.",
            "Historians cannot provide verified facts about every stage of the construction.",
            "None of the six references contain a named builder of Stonehenge. The missing records leave its origins uncertain.",
            "Although the date is uncertain, available evidence concerns the temple's construction. The following points explain the scholarly debate.",
        ):
            self.assertFalse(failed_generation_text(prose),prose)
        self.assertTrue(failed_generation_text("The supplied evidence does not contain information about the requested destination."))

    def test_observed_source_absence_and_redirection_are_not_articles(self):
        captures=json.loads((FIXTURES/"acropolis-athens.json").read_text())["related_lead_captures"]["topics"]
        for capture in captures:
            with self.subTest(slug=capture["slug"]):
                lead=capture["summary"]+" "+capture["intro"]
                self.assertTrue(failed_generation_text(lead))
                topic=valid_topic(capture["slug"])
                topic.update(capture)
                self.assertIn("failed_generation_message",topic_quality_issues(topic,require_evidence=False,legacy=True))

    def test_legacy_audit_keeps_a_valid_historical_product_rename(self):
        topic=json.loads(json.dumps(valid_topic("microsoft-office-365")).replace("Mount Fuji","Microsoft 365"))
        topic["title"]="Microsoft 365"
        topic["summary"]="Microsoft 365 is Microsoft's subscription productivity suite, bringing together Word, Excel, PowerPoint, Outlook, Teams and OneDrive with cloud storage."
        topic["intro"]="This guide sets out the key facts about Microsoft 365, based on official Microsoft pages. It covers the main apps, free web access, subscription plans and sign-in options."
        topic_id=seed_legacy(topic)
        with store.connection() as conn:
            conn.execute("UPDATE topic_candidates SET title='Microsoft Office 365',subject='Microsoft Office 365' WHERE slug=?",(topic["slug"],))
        self.assertFalse(matches_subject(topic["summary"],"Microsoft Office 365"))
        self.assertEqual(store.audit_existing_topics()["topics_held"],0)
        with store.connection() as conn:
            self.assertEqual(conn.execute("SELECT status FROM topics WHERE id=?",(topic_id,)).fetchone()[0],"published")

    def test_legacy_audit_keeps_captured_subject_name_variants(self):
        controls=json.loads((FIXTURES/"acropolis-athens.json").read_text())["legacy_topic_controls"]
        for capture in controls:
            with self.subTest(slug=capture["topic"]["slug"]):
                payload=capture["topic"]
                self.assertEqual(topic_quality_issues(payload,require_evidence=False,legacy=True),[])
                seed_legacy(payload)
        report=store.audit_existing_topics()
        self.assertEqual(report["topics_checked"],len(controls))
        self.assertEqual(report["topics_held"],0)

    def test_multiword_identity_requires_the_complete_name(self):
        for body,subject in (("New Microsoft Office","New York"),("Statue of Unity","Statue of Liberty"),("British Columbia museum visits","British Museum of London")):
            self.assertFalse(matches_subject(body,subject),(body,subject))
        self.assertTrue(matches_subject("The Statue of Liberty stands on Liberty Island.","Statue of Liberty"))
        self.assertTrue(matches_subject("The museum in London is the British Museum.","British Museum of London"))

    def test_reviewed_legacy_holds_only_match_the_exact_captured_lead(self):
        captures=json.loads((FIXTURES/"reviewed-legacy-leads.json").read_text())["topics"]
        self.assertEqual({row["slug"] for row in captures},set(REVIEWED_LEGACY_HOLDS))
        for capture in captures:
            with self.subTest(slug=capture["slug"]):
                self.assertIsNotNone(reviewed_legacy_issue(capture))
                for field in ("title","summary","intro"):
                    corrected={**capture,field:capture[field]+" Updated after the review."}
                    self.assertIsNone(reviewed_legacy_issue(corrected),field)
                if capture["classification"]=="confirmed_trigger_substitution":
                    retargeted={**capture,"trigger":{"query":capture["title"]}}
                    self.assertIsNone(reviewed_legacy_issue(retargeted))
        self.assertIsNone(reviewed_legacy_issue(valid_topic()))

    def test_reviewed_overlap_failure_is_held_with_original_content_snapshotted(self):
        captures=json.loads((FIXTURES/"reviewed-legacy-leads.json").read_text())["topics"]
        capture=next(row for row in captures if row["slug"]=="livingstone-island")
        payload=valid_topic(capture["slug"])
        payload.update(capture)
        topic_id=seed_legacy(payload)
        # A generic lexical overlap is deliberately insufficient to automate a
        # legacy hold; the independently reviewed exact prose supplies evidence.
        for item in payload["items"]:
            item["body"]+=" UK property market overview."
        with store.connection() as conn:
            conn.execute("UPDATE facts SET body=body || ' UK property market overview.'")
        self.assertEqual(topic_quality_issues(payload,expected_title=payload["title"],require_evidence=False,legacy=True),[])
        self.assertEqual(store.audit_existing_topics(),{"topics_checked":1,"topics_held":1})
        with store.connection() as conn:
            review=conn.execute("SELECT reasons_json,snapshot_json FROM quality_reviews WHERE topic_id=?",(topic_id,)).fetchone()
            self.assertIn(reviewed_legacy_issue(payload),json.loads(review["reasons_json"]))
            snapshot=json.loads(review["snapshot_json"])
            self.assertEqual(snapshot["topic"]["status"],"published")
            self.assertEqual(snapshot["payload"]["summary"],capture["summary"])
            self.assertEqual(len(snapshot["payload"]["items"]),10)

    def test_one_on_topic_fact_cannot_authenticate_nine_off_topic_facts(self):
        topic=valid_topic()
        for index,item in enumerate(topic["items"][1:],2):
            item["title"]=f"Office installation step {index}"
            item["body"]="Microsoft Office installs Word, Excel and Outlook applications on Windows computers using the setup installer."
        issues=topic_quality_issues(topic)
        for index in range(2,11):
            self.assertIn(f"fact_{index}_not_grounded_in_source",issues)
        # A spoofed source title cannot authenticate unrelated actual content.
        topic=valid_topic()
        for item in topic["items"]:
            item["sources"][0]["evidence_excerpt"]="Office installation uses a setup installer to install Microsoft applications on Windows computers."
        self.assertIn("fact_1_sources_do_not_address_subject",topic_quality_issues(topic))

    def test_pronouns_and_aliases_can_be_grounded_in_actual_excerpt_text(self):
        excerpt="The Erechtheion, also called the Erechtheum, is an Ionic temple on the Athenian Acropolis. Its southern porch has six sculpted female figures supporting the roof."
        for fact in (
            "Its southern porch has six sculpted female figures supporting the roof.",
            "The Erechtheum is an Ionic temple on the Athenian Acropolis.",
        ):
            self.assertTrue(fact_has_support(fact,excerpt,"Erechtheion"),fact)
        self.assertFalse(fact_has_support("Microsoft Office installs Word, Excel and Outlook applications on Windows computers.",excerpt,"Erechtheion"))

    def test_wrong_candidate_binding_rejects_and_logs_before_creating_topic(self):
        store.add_candidates([{"slug":"erechtheion","title":"Erechtheion","subject":"Erechtheion","source_kind":"trend","score":.9}])
        candidate = store.claim_candidate()
        with self.assertRaisesRegex(ValueError,"slug does not match"):
            store.publish_topic(valid_topic(),candidate_id=candidate["id"])
        with store.connection() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM topics").fetchone()[0],0)
            rejection = conn.execute("SELECT payload_json FROM publication_rejections").fetchone()
            self.assertEqual(json.loads(rejection[0])["slug"],"mount-fuji")

    def test_valid_candidate_and_non_finite_scores(self):
        store.add_candidates([{"slug":"mount-fuji","title":"10 facts about Mount Fuji","subject":"Mount Fuji","source_kind":"trend","score":.9}])
        candidate=store.claim_candidate()
        store.publish_topic(valid_topic(),candidate_id=candidate["id"])
        self.assertIsNotNone(store.get_topic("mount-fuji"))
        for value in (float("nan"),float("inf")):
            broken=valid_topic();broken["items"][0]["confidence"]=value
            with self.assertRaises(ValueError):
                store.publish_topic(broken,candidate_id=candidate["id"])

    def test_failure_response_reports_actual_retry_failed_or_held_state(self):
        store.add_candidates([{"slug":"mount-fuji","title":"10 facts about Mount Fuji","subject":"Mount Fuji","source_kind":"trend","score":.9}])
        candidate=store.claim_candidate()
        payload=valid_topic()
        payload["summary"]="The supplied evidence does not contain information about Mount Fuji."
        with app.test_client() as client:
            for original,attempts,expected in (("claimed",2,"retry"),("claimed",3,"failed"),("held",3,"held")):
                with self.subTest(status=expected):
                    with store.connection() as conn:
                        conn.execute("UPDATE topic_candidates SET status=?,attempts=? WHERE id=?",(original,attempts,candidate["id"]))
                    response=client.post(f"/api/automation/candidates/{candidate['id']}/result",headers={"X-Automation-Key":"content-quality-tests-only"},json={"status":"published","topic":payload})
                    self.assertEqual(response.status_code,422)
                    self.assertEqual(response.get_json()["status"],expected)
                    with store.connection() as conn:
                        self.assertEqual(conn.execute("SELECT status FROM topic_candidates WHERE id=?",(candidate["id"],)).fetchone()[0],expected)

    def test_quarantine_preserves_original_content_and_removes_all_public_routes(self):
        bad=observed("erechtheion")
        topic_id=seed_legacy(bad)
        seed_legacy(valid_topic())
        report=store.audit_existing_topics()
        self.assertEqual(report,{"topics_checked":2,"topics_held":1})
        with store.connection() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0],20)
            row=conn.execute("SELECT summary,status FROM topics WHERE id=?",(topic_id,)).fetchone()
            self.assertEqual(row["summary"],bad["summary"])
            self.assertEqual(row["status"],"held")
            backup=json.loads(conn.execute("SELECT snapshot_json FROM quality_reviews WHERE topic_id=?",(topic_id,)).fetchone()[0])
            self.assertEqual(backup["payload"]["items"][0]["body"],bad["items"][0]["body"])
            self.assertEqual(len(backup["payload"]["items"]),10)
            statuses=dict(conn.execute("SELECT job_type,status FROM social_jobs WHERE topic_id=?",(topic_id,)).fetchall())
            self.assertEqual(statuses,{"fact_cards":"held","carousel":"held","short_video":"published"})
        with app.test_client() as client:
            for path in ("/topics/erechtheion","/api/topics/erechtheion"):
                self.assertEqual(client.get(path).status_code,404,path)
            for path in ("/","/topics","/api/topics","/search?q=Erechtheion","/sitemap.xml"):
                self.assertNotIn(b"/topics/erechtheion",client.get(path).data,path)
            self.assertEqual(client.get("/topics/mount-fuji").status_code,200)
            for path,text in (("/guides/air-fryer-buying-guide",b"Start with usable capacity"),("/guides/improve-home-wifi",b"Wi-Fi"),("/guides/gaming-chair-buying-guide",b"gaming chair")):
                response=client.get(path)
                self.assertEqual(response.status_code,200)
                self.assertIn(text,response.data)
        self.assertEqual(store.audit_existing_topics(),report)
        with store.connection() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM quality_reviews").fetchone()[0],1)

    def test_quarantine_cannot_be_undone_by_a_late_job_result(self):
        topic_id=seed_legacy(observed("acropolis-athens"))
        store.audit_existing_topics()
        with store.connection() as conn:
            candidate_id=conn.execute("SELECT id FROM topic_candidates WHERE slug='acropolis-athens'").fetchone()[0]
            job_id=conn.execute("SELECT id FROM social_jobs WHERE topic_id=? AND job_type='carousel'",(topic_id,)).fetchone()[0]
        store.finish_candidate(candidate_id,"retry","stale execution")
        store.finish_social_job(job_id,"published",{"external_id":"fixture"})
        with store.connection() as conn:
            self.assertEqual(conn.execute("SELECT status FROM topic_candidates WHERE id=?",(candidate_id,)).fetchone()[0],"held")
            self.assertEqual(conn.execute("SELECT status FROM social_jobs WHERE id=?",(job_id,)).fetchone()[0],"held")
        self.assertIsNone(store.claim_social_job())

    def test_completion_read_and_write_cannot_straddle_a_concurrent_audit(self):
        # Pause a real completion after its SELECT has returned. The audit must
        # not acquire its write transaction until that completion commits. The
        # pre-fix implementation allowed the audit between SELECT and UPDATE.
        for kind in ("candidate","social"):
            with self.subTest(kind=kind):
                self.setUp()
                topic_id=seed_legacy(observed("erechtheion"))
                with store.connection() as conn:
                    candidate_id=conn.execute("SELECT id FROM topic_candidates WHERE slug='erechtheion'").fetchone()[0]
                    conn.execute("UPDATE topic_candidates SET status='claimed',attempts=2 WHERE id=?",(candidate_id,))
                    job_id=conn.execute("SELECT id FROM social_jobs WHERE topic_id=? AND job_type='carousel'",(topic_id,)).fetchone()[0]
                read_done=threading.Event();release=threading.Event();audit_attempt=threading.Event();audit_acquired=threading.Event()
                original_connection=store.connection

                class Cursor:
                    def __init__(self,cursor,pause=False):self.cursor,self.pause=cursor,pause
                    def fetchone(self):
                        row=self.cursor.fetchone()
                        if self.pause:
                            read_done.set()
                            if not release.wait(3):raise AssertionError("completion test barrier timed out")
                        return row
                    def __getattr__(self,name):return getattr(self.cursor,name)

                class Connection:
                    def __init__(self,conn):self.conn=conn
                    def execute(self,sql,*args):
                        name=threading.current_thread().name
                        if name=="quality-audit" and sql=="BEGIN IMMEDIATE":
                            audit_attempt.set()
                            cursor=self.conn.execute(sql,*args)
                            audit_acquired.set()
                            return cursor
                        pause=name=="late-completion" and (sql.startswith("SELECT status,attempts FROM topic_candidates") or sql.startswith("SELECT t.status,j.status AS job_status FROM social_jobs"))
                        return Cursor(self.conn.execute(sql,*args),pause)
                    def __getattr__(self,name):return getattr(self.conn,name)

                @contextmanager
                def instrumented_connection():
                    with original_connection() as conn:yield Connection(conn)

                def complete():
                    threading.current_thread().name="late-completion"
                    if kind=="candidate":return store.finish_candidate(candidate_id,"retry","worker finished")
                    return store.finish_social_job(job_id,"published",{"external_id":"local fixture"})

                def audit():
                    threading.current_thread().name="quality-audit"
                    return store.audit_existing_topics()

                with patch.object(store,"connection",instrumented_connection),ThreadPoolExecutor(max_workers=2) as pool:
                    completion=pool.submit(complete)
                    self.assertTrue(read_done.wait(2))
                    audit_job=pool.submit(audit)
                    try:
                        self.assertTrue(audit_attempt.wait(2))
                        self.assertFalse(audit_acquired.wait(.3),"audit acquired between completion SELECT and UPDATE")
                    finally:
                        release.set()
                    completion.result(timeout=3)
                    self.assertEqual(audit_job.result(timeout=3)["topics_held"],1)
                with original_connection() as conn:
                    self.assertEqual(conn.execute("SELECT status FROM topic_candidates WHERE id=?",(candidate_id,)).fetchone()[0],"held")
                    snapshot=json.loads(conn.execute("SELECT snapshot_json FROM quality_reviews WHERE topic_id=?",(topic_id,)).fetchone()[0])
                    if kind=="social":
                        # A publication committed before the audit remains a
                        # historical published job; it was never snapshotted as
                        # held and then overwritten by a stale completion.
                        self.assertNotIn(job_id,[job["id"] for job in snapshot["social_jobs"]])

    def test_duplicate_media_callback_preserves_previously_published_history(self):
        topic_id=seed_legacy(observed("erechtheion"))
        with store.connection() as conn:
            job_id=conn.execute("SELECT id FROM social_jobs WHERE topic_id=? AND job_type='short_video'",(topic_id,)).fetchone()[0]
            conn.execute("UPDATE social_jobs SET result_json=? WHERE id=?",(json.dumps({"external_id":"historical-test-id","url":"https://example.org/existing-publication"}),job_id))
            original=dict(conn.execute("SELECT * FROM social_jobs WHERE id=?",(job_id,)).fetchone())
        store.audit_existing_topics()
        for status,result in (("published",{"external_id":"duplicate-callback"}),("failed",None)):
            with self.subTest(status=status):
                store.finish_social_job(job_id,status,result,"late callback")
                with store.connection() as conn:
                    self.assertEqual(dict(conn.execute("SELECT * FROM social_jobs WHERE id=?",(job_id,)).fetchone()),original)

    def test_format_count_repair_does_not_rewrite_factual_numbers(self):
        self.assertEqual(normalise_article_count("14 Essential Experiences"),"10 Essential Experiences")
        self.assertEqual(normalise_article_count("fourteen verified facts about Athens"),"10 verified facts about Athens")
        self.assertEqual(normalise_article_count("The building has 14 windows and is fourteen metres wide."),"The building has 14 windows and is fourteen metres wide.")


if __name__ == "__main__":
    unittest.main()

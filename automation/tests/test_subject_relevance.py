"""Execute the shipped n8n code nodes against wrong-topic source fixtures."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
workflow = json.loads((ROOT / "automation/n8n/W10-R01-evidence-research.json").read_text())[0]
nodes = {node["name"]: node for node in workflow["nodes"]}
sys.path.insert(0,str(ROOT/"flask-source"))
from content_quality import failed_generation_text, fact_has_support, matches_subject  # noqa: E402


def run(name, data, named=None, items=None):
    payload = {"code": nodes[name]["parameters"]["jsCode"], "data": data, "named": named or {}, "items": items or []}
    js = "const fs=require('fs'),vm=require('vm'),p=JSON.parse(fs.readFileSync(0,'utf8'));const out=vm.runInNewContext('(function(){'+p.code+'})()',{$json:p.data,$:n=>({item:{json:p.named[n]},all:()=>(p.named[n]||[]).map(json=>({json}))}),$input:{all:()=>p.items.map(json=>({json}))},$execution:{id:'local-test'}},{timeout:1000});console.log(JSON.stringify(out));"
    return json.loads(subprocess.check_output(["node","-e",js],input=json.dumps(payload),text=True))


def candidate(subject="Erechtheion", category="world", attempts=1):
    return {"id":582,"slug":"erechtheion","title":"Erechtheion","subject":subject,"category":category,"attempts":attempts}


def source_rows():
    return [{"source_id":i,"url":f"https://source{i}.example/erechtheion","title":"Erechtheion museum source","snippet":"Erechtheion sourced history. "*10,"content":"Erechtheion sourced facts about its architecture, location, history and distinctive features. "*20} for i in range(1,4)]


def helper_results(cases):
    helper=nodes["Prepare evidence search"]["parameters"]["jsCode"].split("/* W10_R01",1)[0]
    payload={"helper":helper,"cases":cases}
    js="const fs=require('fs'),vm=require('vm'),p=JSON.parse(fs.readFileSync(0,'utf8'));const result=vm.runInNewContext('(function(){'+p.helper+'return cases.map(c=>({failure:w10Failed(c.text),identity:w10Matches(c.text,c.subject),support:w10FactSupport(c.text,c.excerpt,c.subject)}));})()',{cases:p.cases},{timeout:1000});console.log(JSON.stringify(result));"
    return json.loads(subprocess.check_output(["node","-e",js],input=json.dumps(payload),text=True))


class SubjectRelevanceTests(unittest.TestCase):
    def test_backend_and_worker_have_the_same_narrow_failure_identity_and_support_contract(self):
        excerpt="The Erechtheion, also called the Erechtheum, is an Ionic temple on the Athenian Acropolis. Its southern porch has six sculpted female figures supporting the roof."
        cases=[
            {"text":"A language model predicts the next token in a sequence.","subject":"Language model","excerpt":"A language model predicts the next token in a sequence using a probability distribution."},
            {"text":"Archaeologists have insufficient evidence to identify the original builder of Stonehenge.","subject":"Stonehenge","excerpt":"Archaeologists have insufficient evidence to identify the original builder of Stonehenge."},
            {"text":"New Microsoft Office","subject":"New York","excerpt":"New Microsoft Office includes an installer."},
            {"text":"Statue of Unity","subject":"Statue of Liberty","excerpt":"The Statue of Unity commemorates an Indian statesman."},
            {"text":"Its southern porch has six sculpted female figures supporting the roof.","subject":"Erechtheion","excerpt":excerpt},
            {"text":"The Erechtheum is an Ionic temple on the Athenian Acropolis.","subject":"Erechtheion","excerpt":excerpt},
            {"text":"Microsoft Office installs Word, Excel and Outlook applications on Windows computers.","subject":"Erechtheion","excerpt":excerpt},
            {"text":"The supplied evidence does not contain any information about Erechtheion.","subject":"Erechtheion","excerpt":excerpt},
        ]
        actual=helper_results(cases)
        expected=[{"failure":failed_generation_text(case["text"]),"identity":matches_subject(case["text"],case["subject"]),"support":fact_has_support(case["text"],case["excerpt"],case["subject"])} for case in cases]
        self.assertEqual(actual,expected)
        self.assertFalse(actual[0]["failure"])
        self.assertFalse(actual[1]["failure"])
        self.assertFalse(actual[2]["identity"])
        self.assertFalse(actual[3]["identity"])
        self.assertTrue(actual[4]["support"])
        self.assertTrue(actual[5]["support"])
        self.assertFalse(actual[6]["support"])
        self.assertTrue(actual[7]["failure"])

    def test_observed_generation_absence_and_redirection_match_backend(self):
        captures=json.loads((ROOT/"automation/tests/fixtures/acropolis-athens.json").read_text())["related_lead_captures"]["topics"]
        cases=[{"text":row["summary"]+" "+row["intro"],"subject":row["title"],"excerpt":""} for row in captures]
        cases.extend({"text":prose,"subject":"Stonehenge","excerpt":""} for prose in (
            "None of the six references contain a named builder of Stonehenge. The missing records leave its origins uncertain.",
            "Although the date is uncertain, available evidence concerns the temple's construction. The following points explain the scholarly debate.",
        ))
        results=helper_results(cases)
        for index,(case,result) in enumerate(zip(cases,results)):
            with self.subTest(text=case["text"]):
                self.assertEqual(result["failure"],failed_generation_text(case["text"]))
                self.assertEqual(result["failure"],index<len(captures))

    def test_generic_world_candidate_subject_is_replaced_by_canonical_topic(self):
        base=run("Prepare evidence search",{"candidate":{**candidate("ancient citadel"),"slug":"acropolis-athens","title":"Acropolis of Athens"}})[0]["json"]
        self.assertEqual(base["query"],'"Acropolis of Athens"')
        self.assertEqual(base["canonical_subject"],"Acropolis of Athens")

    def test_unrelated_search_results_fail_for_world_and_history_as_well_as_travel(self):
        rss="<rss><channel>"+"".join(f"<item><title>Office downloads</title><link>https://source{i}.example/office</link><description>Install Outlook on Windows.</description></item>" for i in range(3))+"</channel></rss>"
        for category in ("world","history-culture","travel","general-knowledge"):
            for attempts, status in ((1,"retry"),(3,"failed")):
                base=run("Prepare evidence search",{"candidate":candidate(category=category,attempts=attempts)})[0]["json"]
                result=run("Parse Bing evidence",{"body":rss,"statusCode":200},{"Prepare evidence search":base})[0]["json"]
                self.assertTrue(result["research_failed"])
                self.assertEqual(result["status"],status)
                self.assertIsNone(result["topic"])

    def test_actual_fetched_body_must_match_even_if_jina_header_repeats_target(self):
        base=run("Prepare evidence search",{"candidate":candidate()})[0]["json"]
        named={"Prepare evidence search":base,"Parse Bing evidence":source_rows()}
        false_body="Title: Erechtheion\nURL Source: https://example.org/erechtheion\nMarkdown Content:\n"+"Install Microsoft Office and Outlook on Windows computers. "*20
        result=run("Assemble evidence pack",{},named,[{"body":false_body,"statusCode":200}]*3)[0]["json"]
        self.assertTrue(result["research_failed"])
        good=run("Assemble evidence pack",{},named,[{"body":row["content"],"statusCode":200} for row in source_rows()])[0]["json"]
        self.assertEqual(len(good["evidence"]),3)

    def test_failed_writer_output_is_never_published(self):
        evidence=source_rows()
        base={"candidate":candidate(),"evidence":evidence,"canonical_subject":"Erechtheion"}
        x={"title":"Erechtheion","summary":"The supplied evidence does not contain any information about Erechtheion.","intro":"The candidate topic is Erechtheion, but the provided sources cover Office installation.","items":[{"title":f"Evidence gap {i}","body":"The provided sources do not contain information about the site or its history.","confidence":.9,"source_ids":[1]} for i in range(14)]}
        result=run("Validate ten sourced facts",{"content":json.dumps(x)},{"Build evidence-grounded research prompt":base})[0]["json"]
        self.assertEqual(result["status"],"retry")
        self.assertIsNone(result["topic"])

    def test_valid_writer_selects_ten_and_repairs_only_public_count_promises(self):
        base={"candidate":candidate(),"evidence":source_rows(),"canonical_subject":"Erechtheion"}
        x={"title":"Erechtheion: 14 Essential Facts","summary":"Fourteen verified facts about Erechtheion.","intro":"Erechtheion is the subject of this isolated writer validation fixture.","items":[{"title":f"Erechtheion point {i}","body":f"Erechtheion point {i} uses the source architecture, location, history and distinctive features to describe this temple.","confidence":.9,"source_ids":[1,2]} for i in range(14)]}
        result=run("Validate ten sourced facts",{"content":json.dumps(x)},{"Build evidence-grounded research prompt":base})[0]["json"]
        self.assertEqual(result["status"],"published",result)
        self.assertEqual(len(result["topic"]["items"]),10)
        self.assertEqual(result["topic"]["title"],"Erechtheion: 10 Essential Facts")
        self.assertEqual(result["topic"]["summary"],"10 verified facts about Erechtheion.")
        x["items"]=[x["items"][0]]+[{**item,"title":f"Office point {i}","body":f"Microsoft Office fixture point {i} only discusses installing Outlook on Windows and its application features."} for i,item in enumerate(x["items"][1:10],1)]
        rejected=run("Validate ten sourced facts",{"content":json.dumps(x)},{"Build evidence-grounded research prompt":base})[0]["json"]
        self.assertIsNone(rejected["topic"])
        self.assertIn("valid sourced facts instead of 10",rejected["error"])


if __name__ == "__main__":
    unittest.main()

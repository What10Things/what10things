import json
import subprocess
import unittest
from pathlib import Path
from automation.scripts.patch_generic_travel_gate import patch


class GenericTravelGateTests(unittest.TestCase):
    def setUp(self):
        value=json.loads((Path(__file__).resolve().parents[1]/'n8n/W10-R01-evidence-research.json').read_text())
        self.original=value[0] if isinstance(value,list) else value
        self.flow=patch(self.original)
        self.code=next(n for n in self.flow['nodes'] if n['name']=='Prepare evidence search')['parameters']['jsCode']

    def run_candidate(self,title,subject,category='travel'):
        js='const x=JSON.parse(process.argv[1]);process.stdout.write(JSON.stringify(new Function("$json",x.code)({candidate:x.c})));'
        data={'code':self.code,'c':{'id':106,'title':title,'subject':subject,'category':category}}
        return json.loads(subprocess.check_output(['node','-e',js,json.dumps(data)],text=True))[0]['json']

    def test_specific_places_repair_generic_subject_labels(self):
        for title,subject in [('Mount Fuji','Natural landmark'),('Natural History Museum','Museum'),('Peak District National Park','National park')]:
            result=self.run_candidate(title,subject)
            self.assertEqual(result['destination'],title)
            self.assertFalse(result.get('skip_research'))

    def test_only_truly_generic_travel_topics_are_ignored(self):
        for title in ['Natural landmark','10 things to know about Natural landmark']:
            result=self.run_candidate(title,'Natural landmark')
            self.assertEqual(result['status'],'ignored')
            self.assertIsNone(result['topic'])
            self.assertNotIn('bingUrl',result)
        self.assertIn('bingUrl',self.run_candidate('Museum','Museum','history-culture'))

    def test_preserves_ten_fact_checks_and_is_idempotent(self):
        self.assertEqual(patch(self.flow),self.flow)
        for key in ('id','name','active','settings'):
            self.assertEqual(self.original.get(key),self.flow.get(key))
        old=next(n for n in self.original['nodes'] if n['name']=='Validate ten sourced facts')
        self.assertEqual(old,next(n for n in self.flow['nodes'] if n['name']==old['name']))
        gate=self.flow['connections']['Generic travel category?']['main']
        self.assertEqual(gate[0][0]['node'],'Publish or retry candidate')
        self.assertEqual(gate[1][0]['node'],'Search evidence with Bing RSS')

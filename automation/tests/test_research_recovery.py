import importlib.util
import json
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
FLOW=ROOT/'automation/n8n/W10-R01-evidence-research.json'
spec=importlib.util.spec_from_file_location('repair',ROOT/'automation/scripts/patch_research_recovery.py')
repair=importlib.util.module_from_spec(spec);spec.loader.exec_module(repair)
wf=json.loads(FLOW.read_text());wf=wf[0] if isinstance(wf,list) else wf
nodes={n['name']:n for n in wf['nodes']}


def run(name, data, named=None, items=None):
    payload={'code':nodes[name]['parameters']['jsCode'],'data':data,'named':named or {},'items':items or []}
    js="const fs=require('fs'),vm=require('vm'),p=JSON.parse(fs.readFileSync(0,'utf8'));let out=vm.runInNewContext('(function(){'+p.code+'})()',{$json:p.data,$:n=>({item:{json:p.named[n]},all:()=>(p.named[n]||[]).map(json=>({json}))}),$input:{all:()=>p.items.map(json=>({json}))},$execution:{id:'fixture'}},{timeout:1000});console.log(JSON.stringify(out));"
    return json.loads(subprocess.check_output(['node','-e',js],input=json.dumps(payload),text=True))


def candidate(attempts=1):
    return {'id':7,'attempts':attempts,'category':'travel','subject':'Mount Fuji','destination':'Mount Fuji','title':'10 facts about Mount Fuji'}


def base(attempts=1):
    return {'candidate':candidate(attempts),'destination':'Mount Fuji','query':'"Mount Fuji"'}


def rss(rows):
    return '<rss><channel>'+''.join(f'<item><title>{title}</title><link>{url}</link><description>Mount Fuji official destination information and sourced history.</description></item>' for title,url in rows)+'</channel></rss>'


class RecoveryTests(unittest.TestCase):
    def test_exact_destination_search_and_exhausted_preflight(self):
        result=run('Prepare evidence search',{'candidate':candidate()})[0]['json']
        self.assertEqual(result['query'],'"Mount Fuji"')
        for attempts in [4,99,None,0]:
            result=run('Prepare evidence search',{'candidate':candidate(attempts)})[0]['json']
            self.assertTrue(result['skip_research']);self.assertEqual(result['status'],'failed')
            self.assertNotIn('bingUrl',result)

    def test_thin_or_failed_search_records_bounded_failure(self):
        for attempt,status in [(1,'retry'),(3,'failed')]:
            result=run('Parse Bing evidence',{'body':rss([('Mason Mount','https://example.org/mason')]),'statusCode':200},{'Prepare evidence search':base(attempt)})[0]['json']
            self.assertTrue(result['research_failed']);self.assertEqual(result['status'],status);self.assertIsNone(result['topic'])
        result=run('Parse Bing evidence',{'body':'failure','statusCode':503},{'Prepare evidence search':base()})[0]['json']
        self.assertEqual(result['error'],'Evidence search HTTP failure')

    def test_bounded_search_prefers_primary_sources_before_truncation(self):
        rows=[('Mount Fuji guide',f'https://example{i}.org/fuji') for i in range(8)]
        rows+=[('Mount Fuji official guide','https://www.japan.travel/en/fuji-guide/'),('Mount Fuji heritage','https://whc.unesco.org/en/list/1418/')]
        result=run('Parse Bing evidence',{'body':rss(rows),'statusCode':200},{'Prepare evidence search':base()})
        self.assertEqual(len(result),8)
        self.assertEqual(result[0]['json']['url'],'https://www.japan.travel/en/fuji-guide/')
        self.assertEqual(result[1]['json']['url'],'https://whc.unesco.org/en/list/1418/')
        self.assertEqual([r['json']['source_id'] for r in result],list(range(1,9)))

    def test_assembly_rejects_http_error_bodies_and_keeps_domain_gates(self):
        meta=[{'url':f'https://source{i}.org/fuji','title':'Mount Fuji','snippet':'Mount Fuji source. '*10} for i in range(3)]
        named={'Prepare evidence search':base(3),'Parse Bing evidence':meta}
        failed=run('Assemble evidence pack',{},named,[{'statusCode':403,'body':'Access denied. '*100}]*3)[0]['json']
        self.assertTrue(failed['research_failed']);self.assertEqual(failed['status'],'failed')
        good=run('Assemble evidence pack',{},named,[{'statusCode':200,'body':'Mount Fuji sourced destination facts. '*20}]*3)[0]['json']
        self.assertEqual(len(good['evidence']),3);self.assertEqual(len(good['evidence_domains']),3)
        named['Prepare evidence search']['candidate']['location_type']='country'
        for m in meta:m['url']='https://one.example/'+m['url'].split('//')[1]
        thin=run('Assemble evidence pack',{},named,[{'statusCode':200,'body':'Supported fact. '*20}]*3)[0]['json']
        self.assertTrue(thin['research_failed'])

    def test_writer_failure_bounded_and_graph_skips_writing_on_research_failure(self):
        for attempt,status in [(2,'retry'),(3,'failed')]:
            result=run('Validate ten sourced facts',{'error':{'message':'allowance exhausted'}},{'Build evidence-grounded research prompt':base(attempt)})[0]['json']
            self.assertEqual(result['status'],status);self.assertIsNone(result['topic'])
        for name in ['Search evidence usable?','Fetched evidence usable?']:
            self.assertEqual(wf['connections'][name]['main'][0],[repair.edge('Publish or retry candidate')])
            self.assertIn('$json.research_failed === true',nodes[name]['parameters']['conditions']['conditions'][0]['leftValue'])
        self.assertEqual(repair.patch(wf),wf)


if __name__=='__main__':unittest.main()

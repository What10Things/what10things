#!/usr/bin/env python3
"""Finish obsolete generic travel candidates without search or model calls."""
import copy
import json
import sys
from pathlib import Path

MARKER = 'W10_GENERIC_TRAVEL_GATE_V1'
GUARD = r'''
/* W10_GENERIC_TRAVEL_GATE_V1: apply the existing real-place policy to old queued candidates. */
const genericTravel=/^(natural landmark|historical site|historic site|museum|beach|national park|park|city|town|island|region|attraction|landmark|tourist attraction|heritage site|world heritage site|nature reserve|cultural site|religious site|archaeological site|scenic area|coastal area)$/i;
const bad=v=>genericTravel.test(String(v||'').trim());
if(String(c.category)==='travel'&&(bad(c.subject)||bad(c.destination)||(!c.subject&&!c.destination))){
 const titlePlace=String(c.title||'').replace(/^(?:10|ten)?\s*(?:things to do in|places to visit in|facts about|things to know about|things to know before visiting|before visiting)\s+/i,'').trim();
 const place=[c.destination,c.subject,titlePlace].map(v=>String(v||'').trim()).find(v=>v&&!bad(v));
 if(!place)return [{json:{skip_research:true,candidate_id:c.id,status:'ignored',topic:null,error:'Generic travel category has no specific destination; existing real-place policy applies.'}}];
 c={...c,destination:place,subject:bad(c.subject)||!c.subject?place:c.subject};
}

'''


def patch(workflow):
    out = copy.deepcopy(workflow)
    if out.get('id') != 'W10R01EvidenceResearch':
        raise ValueError('Expected W10-R01 only')
    nodes = {n['name']: n for n in out['nodes']}
    node = nodes['Prepare evidence search']
    code = node['parameters']['jsCode']
    gate_name = 'Generic travel category?'
    if MARKER in code:
        if gate_name not in nodes:
            raise ValueError('Incomplete existing gate')
        return out
    anchor = "const c=$json.candidate||null;if(!c)return [];"
    if code.count(anchor) != 1 or gate_name in nodes:
        raise ValueError('Unexpected workflow source')
    node['parameters']['jsCode'] = code.replace(anchor, anchor.replace('const c=', 'let c=')+GUARD)
    original = out['connections']['Prepare evidence search']
    if original != {'main': [[{'node':'Search evidence with Bing RSS','type':'main','index':0}]]}:
        raise ValueError('Unexpected search connection')
    out['nodes'].append({
        'id':'w10-generic-travel-gate-v1', 'name':gate_name,
        'type':'n8n-nodes-base.if', 'typeVersion':2.2,
        'position':[0,-260],
        'parameters':{'conditions':{
            'options':{'caseSensitive':True,'leftValue':'','typeValidation':'strict','version':2},
            'conditions':[{'id':'is-generic-travel','leftValue':'={{$json.skip_research === true}}',
                           'rightValue':True,'operator':{'type':'boolean','operation':'true','singleValue':True}}],
            'combinator':'and'},'options':{}}})
    out['connections']['Prepare evidence search'] = {'main':[[{'node':gate_name,'type':'main','index':0}]]}
    out['connections'][gate_name] = {'main':[
        [{'node':'Publish or retry candidate','type':'main','index':0}],
        [{'node':'Search evidence with Bing RSS','type':'main','index':0}]]}
    return out


if __name__ == '__main__':
    inp,out = map(Path,sys.argv[1:])
    value=json.loads(inp.read_text(encoding='utf-8-sig'))
    row=value[0] if isinstance(value,list) and len(value)==1 else value
    changed=patch(row)
    out.write_text(json.dumps([changed] if isinstance(value,list) else changed,indent=2,ensure_ascii=False)+'\n')

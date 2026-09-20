"""Keep W10 searches specific and persist bounded research failures."""
import copy
import json
import sys
from pathlib import Path

MARKER = 'W10_RESEARCH_RECOVERY_V1'
FAILURE = "const failure=message=>[{json:{research_failed:true,candidate_id:base.candidate.id,status:Number(base.candidate.attempts)>=3?'failed':'retry',topic:null,error:message}}];\n"
HOST = r"const host=u=>{const m=String(u||'').match(/^https?:\/\/([a-z0-9.-]+)(?::\d+)?(?:[/?#]|$)/i);return m?m[1].toLowerCase().replace(/^www\./,''):''};"


def edge(name):
    return {'node': name, 'type': 'main', 'index': 0}


def patch(workflow):
    out=copy.deepcopy(workflow)
    assert out.get('id')=='W10R01EvidenceResearch'
    nodes={n['name']:n for n in out['nodes']}
    prepare=nodes['Prepare evidence search']['parameters']
    if MARKER in prepare['jsCode']:
        assert all(name in nodes for name in ('Search evidence usable?', 'Fetched evidence usable?'))
        return out
    code=prepare['jsCode']; anchor="let c=$json.candidate||null;if(!c)return [];"
    assert code.count(anchor)==1
    # The durable API increments attempts when claiming. Do not reset it.
    guard="\n/* "+MARKER+" */\nif(!Number.isInteger(Number(c.attempts))||Number(c.attempts)<1||Number(c.attempts)>3)return [{json:{skip_research:true,candidate_id:c.id,status:'failed',topic:null,error:'Research attempt ceiling reached or claim attempt missing; no further source/model calls.'}}];\n"
    code=code.replace(anchor,anchor+guard)
    start=code.index('let query;'); end=code.index("const bingUrl=",start)
    code=code[:start]+'''// Extra query terms caused Bing RSS to drop the destination phrase.
const subject=String(c.category)==='travel'?destination:String(c.subject||title).trim();
const query='"'+subject.replace(/"/g,'').trim()+'"';
'''+code[end:]
    prepare['jsCode']=code
    p=nodes['Parse Bing evidence']['parameters'];code=p['jsCode']
    anchor="const blocks=[...xml.matchAll"
    assert anchor in code
    code=code.replace(anchor,FAILURE+"if(Number($json.statusCode||200)<200||Number($json.statusCode||200)>=300)return failure('Evidence search HTTP failure');\n"+anchor)
    old="if(out.length>=8)break;"
    assert old in code;code=code.replace(old,'')
    old="if(out.length<3)throw new Error(`Bing RSS returned only ${out.length} destination-relevant sources for ${base.destination||base.query}`);"
    assert old in code;code=code.replace(old,"if(out.length<3)return failure(`Bing RSS returned only ${out.length} destination-relevant sources for ${base.destination||base.query}`);")
    code=code.replace('return out.map((r,i)=>',HOST+"\nconst preferred=u=>/\\.(gov|gov\\.[a-z]{2}|edu|ac\\.uk)$/.test(host(u))||/(unesco|tourism|tourist|travel|visit|nationalpark|parks\\.)/.test(host(u));\nout.sort((a,b)=>Number(preferred(b.url))-Number(preferred(a.url)));\nreturn out.slice(0,8).map((r,i)=>")
    p['jsCode']=code
    p=nodes['Assemble evidence pack']['parameters'];code=p['jsCode']
    old="const host=u=>{try{return new URL(u).hostname.toLowerCase().replace(/^www\\./,'')}catch{return ''}};"
    assert old in code;code=code.replace(old,FAILURE+HOST)
    old="const m=meta[i],f=fetched[i]||{};let body="
    assert old in code;code=code.replace(old,"const m=meta[i],f=fetched[i]||{};if(f.error||Number(f.statusCode||200)<200||Number(f.statusCode||200)>=300)continue;let body=")
    code=code.replace("throw new Error(`Only ${rows.length} readable destination-relevant evidence sources after free fetch`)","return failure(`Only ${rows.length} readable destination-relevant evidence sources after free fetch`)")
    code=code.replace("throw new Error(`Country travel evidence has only ${domains.size} independent source domain(s)`)","return failure(`Country travel evidence has only ${domains.size} independent source domain(s)`)")
    p['jsCode']=code
    p=nodes['Validate ten sourced facts']['parameters'];code=p['jsCode']
    old="status:topic?'published':'retry'";assert old in code
    code=code.replace(old,"status:topic?'published':(Number(c.attempts)>=3?'failed':'retry')")
    old="const host=u=>{try{return new URL(u).hostname.replace(/^www\\./,'')}catch{return ''}};"
    assert old in code;code=code.replace(old,HOST)
    p['jsCode']=code
    nodes['Extract ten facts with free AI router']['onError']='continueRegularOutput'
    for upstream,gate,downstream in [('Parse Bing evidence','Search evidence usable?','Fetch source pages free'),('Assemble evidence pack','Fetched evidence usable?','Build evidence-grounded research prompt')]:
        assert out['connections'][upstream]=={'main':[[edge(downstream)]]}
        node=copy.deepcopy(nodes['Generic travel category?']);node.update(id='w10-'+gate.lower().replace(' ','-').replace('?',''),name=gate)
        node['parameters']['conditions']['conditions'][0].update(id=node['id'],leftValue='={{$json.research_failed === true}}')
        out['nodes'].append(node)
        out['connections'][upstream]={'main':[[edge(gate)]]}
        out['connections'][gate]={'main':[[edge('Publish or retry candidate')],[edge(downstream)]]}
    return out


if __name__=='__main__':
    src,dst=map(Path,sys.argv[1:]);data=json.loads(src.read_text());single=data[0] if isinstance(data,list) else data
    result=patch(single);dst.write_text(json.dumps([result] if isinstance(data,list) else result,indent=2,ensure_ascii=False)+'\n')

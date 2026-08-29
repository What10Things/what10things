import json
from pathlib import Path

path = Path('automation/n8n/W10-R01-evidence-research.json')
data = json.loads(path.read_text())
w = data[0]
nodes = {n['name']: n for n in w['nodes']}

# Source diversity (idempotent: already present in current main after the first patch).
n = nodes['Assemble evidence pack']
code = n['parameters']['jsCode']
assert 'W10_R01_ASSEMBLE_FREE_EVIDENCE_V3_DIVERSITY' in code

n = nodes['Build evidence-grounded research prompt']
code = n['parameters']['jsCode']
if 'W10_R01_PROMPT_V9_GRAPH_QUALITY' not in code:
    code = code.replace('/* W10_R01_PROMPT_V8_SOURCE_DIVERSITY */', '/* W10_R01_PROMPT_V9_GRAPH_QUALITY */')
    anchor = 'For travel topics, favour related cities, regions, landmarks and companion destination guides.'
    repl = anchor + " Related travel topics must name a specific real place, city, region, island, landmark, museum, park or attraction. Never return generic category labels such as 'Natural landmark', 'Historical site', 'Museum', 'Beach', 'National park', 'City' or 'Attraction' as a related topic."
    assert anchor in code, 'related prompt anchor not found'
    code = code.replace(anchor, repl)
n['parameters']['jsCode'] = code

n = nodes['Validate ten sourced facts']
code = n['parameters']['jsCode']
if 'W10_R01_VALIDATE_V8_GRAPH_QUALITY' not in code:
    code = code.replace('/* W10_R01_VALIDATE_V7_SOURCE_DIVERSITY */', '/* W10_R01_VALIDATE_V8_GRAPH_QUALITY */')
    old = """const rel=[];for(const r of (Array.isArray(x.related_topics)?x.related_topics:[]).slice(0,6)){const slug=slugify(r?.slug||r?.subject||r?.title);const cat=allowed.has(String(r?.category))?String(r.category):String(c.category||'general-knowledge');const score=Math.max(0,Math.min(1,Number(r?.score)||.65)),ever=Math.max(0,Math.min(1,Number(r?.evergreen_score)||score));if(slug&&slug!==c.slug&&score>=.65&&ever>=.70)rel.push({slug,title:String(r?.title||slug.replace(/-/g,' ')).slice(0,300),subject:String(r?.subject||r?.title||slug.replace(/-/g,' ')).slice(0,300),category:cat,relationship:String(r?.relationship||'related').slice(0,80),score,evergreen_score:ever,rationale:String(r?.rationale||'Related evidence-backed follow-up subject.').slice(0,1200)});}"""
    new = """const rel=[];const genericTravel=/^(natural landmark|historical site|historic site|museum|beach|national park|park|city|town|island|region|attraction|landmark|tourist attraction|heritage site|world heritage site|nature reserve|cultural site|religious site|archaeological site|scenic area|coastal area)$/i;for(const r of (Array.isArray(x.related_topics)?x.related_topics:[]).slice(0,6)){const rawTitle=String(r?.title||r?.subject||'').trim();const rawSubject=String(r?.subject||r?.title||'').trim();const slug=slugify(r?.slug||rawSubject||rawTitle);const cat=allowed.has(String(r?.category))?String(r.category):String(c.category||'general-knowledge');let score=Math.max(0,Math.min(1,Number(r?.score)||.65)),ever=Math.max(0,Math.min(1,Number(r?.evergreen_score)||score));if(cat==='travel'){if(genericTravel.test(rawTitle)||genericTravel.test(rawSubject))continue;score=Math.min(score,.84);ever=Math.min(ever,.90);}if(slug&&slug!==c.slug&&rawTitle.length>=3&&rawSubject.length>=3&&score>=.65&&ever>=.70)rel.push({slug,title:rawTitle.slice(0,300),subject:rawSubject.slice(0,300),category:cat,relationship:String(r?.relationship||'related').slice(0,80),score,evergreen_score:ever,rationale:String(r?.rationale||'Related evidence-backed follow-up subject.').slice(0,1200)});}"""
    assert old in code, 'related-topic validator anchor not found'
    code = code.replace(old, new, 1)
n['parameters']['jsCode'] = code

path.write_text(json.dumps(data, separators=(',', ':'), ensure_ascii=False) + '\n')
check = json.loads(path.read_text())[0]
nodes = {n['name']: n for n in check['nodes']}
assert check.get('active') is False
assert 'W10_R01_ASSEMBLE_FREE_EVIDENCE_V3_DIVERSITY' in nodes['Assemble evidence pack']['parameters']['jsCode']
assert 'W10_R01_PROMPT_V9_GRAPH_QUALITY' in nodes['Build evidence-grounded research prompt']['parameters']['jsCode']
assert 'W10_R01_VALIDATE_V8_GRAPH_QUALITY' in nodes['Validate ten sourced facts']['parameters']['jsCode']
assert 'genericTravel' in nodes['Validate ten sourced facts']['parameters']['jsCode']
assert 'Math.min(score,.84)' in nodes['Validate ten sourced facts']['parameters']['jsCode']
print('R01 source-diversity + graph-quality patch applied')

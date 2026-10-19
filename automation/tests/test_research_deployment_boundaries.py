"""Exercise the real W10 deployment shell and Python patches at the Docker boundary.

Copy to automation/tests/test_research_deployment_boundaries.py. In scratch, run
with W10_DEPLOY_TEST_ROOT pointing to the repository under review. The immutable
baseline fixture is embedded, so these tests also work in a shallow checkout
whose HEAD already contains the new workflow. No Docker daemon or network is
used. The fake models workflow database state separately from the running
process, which changes only when the shell requests a restart.
"""
from __future__ import annotations

import base64
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zlib

ROOT = Path(os.environ.get("W10_DEPLOY_TEST_ROOT", Path(__file__).resolve().parents[2]))
WORKFLOW = "automation/n8n/W10-R01-evidence-research.json"
PATCH_SCRIPTS = ("deploy_research_recovery.sh", "patch_research_recovery.py", "patch_subject_quality.py")
TARGETS = frozenset(("Prepare evidence search", "Parse Bing evidence", "Assemble evidence pack", "Build evidence-grounded research prompt", "Validate ten sourced facts"))

# Exact public tracked workflow from b0e7ebb, before the subject-quality change.
# zlib/base64 keeps this historical fixture self-contained without depending on
# Git history or duplicating a large workflow as an extra test-support file.
# The real guarded patch checks its five baseline Code-node hashes at runtime.
BASELINE_ZLIB_B64 = """
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
"""

FAKE_DOCKER = r'''#!/usr/bin/env python3
import copy,json,os,sys
from pathlib import Path

state_path=Path(os.environ['W10_PROBE_STATE'])
state=json.loads(state_path.read_text())
args=sys.argv[1:]
state['calls'].append(args)

def save():state_path.write_text(json.dumps(state))
def event(name,**values):state['events'].append({'event':name,**values})
def fail(message):raise AssertionError(message+': '+repr(args))

def main():
    if args and args[0]=='cp':
        if len(args)!=3 or not args[1].startswith('mainbuyer-automation-n8n-1:'):fail('unexpected copy')
        source=args[1].split(':',1)[1]
        Path(args[2]).write_text(state['files'][source])
        event('copy_out',source=source,destination=args[2])
        return
    if args and args[0]=='restart':
        if args!=['restart','--timeout','45','mainbuyer-automation-n8n-1']:fail('restart must allow 45 seconds')
        state['running_workflow']=copy.deepcopy(state['workflow'])
        state['restarts']+=1
        event('restart',timeout=45)
        print('mainbuyer-automation-n8n-1')
        return
    if not args or args[0]!='exec':fail('unexpected Docker operation')
    rest=args[1:]
    interactive=bool(rest and rest[0]=='-i')
    if interactive:rest=rest[1:]
    container,command=rest[0],rest[1:]
    if container=='mainbuyer-automation-postgres-1':
        if not interactive or command[:2]!=['sh','-c'] or 'psql ' not in command[2]:fail('idle query must use interactive PostgreSQL stdin')
        query=sys.stdin.read()
        if "SELECT COUNT(*) FROM execution_entity WHERE status IN ('running','new');" not in query:fail('wrong global execution guard')
        index=state['idle_checks']
        if index>=len(state['counts']):fail('unexpected additional idle check')
        count=state['counts'][index]
        state['idle_checks']+=1
        event('idle',count=count)
        print(count)
        return
    if container!='mainbuyer-automation-n8n-1':fail('unexpected container')
    if command[:2]==['mktemp','-d']:
        event('temporary_import_directory')
        print('/tmp/w10-deployment-probe')
        return
    if command[:2]==['rm','-rf']:
        if command[2]!='/tmp/w10-deployment-probe':fail('unexpected cleanup target')
        event('cleanup')
        return
    if interactive and command[:2]==['sh','-c']:
        if command[2]!='umask 077; cat > "$1"' or command[3]!='sh':fail('unexpected upload command')
        destination=command[4]
        state['files'][destination]=sys.stdin.read()
        event('copy_in',destination=destination)
        return
    if command[:2]==['node','-e']:
        if '/healthz' not in command[2]:fail('unexpected node command')
        event('health')
        return
    if not command or command[0]!='n8n':fail('unexpected exec command')
    operation=command[1]
    if operation=='export:workflow':
        if '--id=W10R01EvidenceResearch' not in command:fail('export must remain scoped')
        destination=next(value.split('=',1)[1] for value in command if value.startswith('--output='))
        exported=copy.deepcopy(state['workflow'])
        if destination.endswith('/verified.json') and state['corrupt_verification']:
            # Exercise the shell's real post-restart Python verification and
            # ERR trap, without waiting through repeated health-check sleeps.
            exported['name']='Unexpected post-restart workflow drift'
        state['files'][destination]=json.dumps([exported])
        event('export',destination=destination)
        return
    if operation in ('unpublish:workflow','publish:workflow'):
        if command[2:]!=['--id=W10R01EvidenceResearch']:fail('publication must remain scoped')
        state['workflow']['active']=operation=='publish:workflow'
        event(operation)
        return
    if operation=='import:workflow':
        if len(command)!=3 or not command[2].startswith('--input='):fail('unexpected import')
        source=command[2].split('=',1)[1]
        state['workflow']=json.loads(state['files'][source])[0]
        # Import alone must not stand in for the explicit publication command.
        state['workflow']['active']=False
        event(operation,source=source)
        return
    fail('unexpected n8n operation')

try:
    main()
finally:
    save()
'''


class ResearchDeploymentBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix="w10-shell-boundary-")
        self.addCleanup(self.temporary.cleanup)
        self.directory=Path(self.temporary.name)
        self.source=self.directory/"source"
        scripts=self.source/"automation/scripts"
        scripts.mkdir(parents=True)
        for name in PATCH_SCRIPTS:
            shutil.copy2(ROOT/"automation/scripts"/name,scripts/name)
        destination=self.source/WORKFLOW
        destination.parent.mkdir(parents=True)
        shutil.copy2(ROOT/WORKFLOW,destination)
        self.desired=json.loads(destination.read_text())[0]
        self.baseline=json.loads(zlib.decompress(base64.b64decode(BASELINE_ZLIB_B64)))[0]
        # The deployment must preserve live metadata and unrelated nodes; it
        # cannot pass by replacing the whole workflow with the source export.
        self.baseline['name']='Live workflow with preserved local metadata'
        self.baseline['nodes'].append({'id':'unrelated-deployment-sentinel','name':'Untouched local node','type':'n8n-nodes-base.noOp','typeVersion':1,'parameters':{},'position':[0,0]})
        binary=self.directory/"bin"
        binary.mkdir()
        docker=binary/"docker"
        docker.write_text(FAKE_DOCKER)
        docker.chmod(0o700)
        self.test_home=self.directory/"home"
        self.test_home.mkdir()
        self.state_path=self.directory/"state.json"
        self.environment={**os.environ,'HOME':str(self.test_home),'PATH':str(binary)+os.pathsep+os.environ['PATH'],'W10_PROBE_STATE':str(self.state_path)}

    def run_deploy(self,counts,*,active=True,corrupt_verification=False):
        original=copy.deepcopy(self.baseline)
        original['active']=active
        state={'workflow':original,'running_workflow':copy.deepcopy(original),'files':{},'events':[],'calls':[],'counts':counts,'idle_checks':0,'restarts':0,'corrupt_verification':corrupt_verification}
        self.state_path.write_text(json.dumps(state))
        result=subprocess.run(['bash',str(self.source/'automation/scripts/deploy_research_recovery.sh')],env=self.environment,text=True,capture_output=True,timeout=15)
        state=json.loads(self.state_path.read_text())
        backups=list((self.test_home/'.urbansky-backups').glob('w10-research-recovery.*'))
        self.assertEqual(len(backups),1,result.stderr)
        self.assertEqual(json.loads((backups[0]/'before.json').read_text()),[original])
        self.assertTrue((backups[0]/'after.json').is_file(),result.stderr)
        expected=json.loads((backups[0]/'after.json').read_text())[0]
        # Both real Python patch programs must have produced an actual scoped
        # code update before any busy deferral; fixtures cannot be no-ops.
        old_nodes={node['name']:node for node in original['nodes']}
        new_nodes={node['name']:node for node in expected['nodes']}
        desired_nodes={node['name']:node for node in self.desired['nodes']}
        changed={name for name,node in old_nodes.items() if node!=new_nodes[name]}
        self.assertEqual(changed,TARGETS)
        for name in TARGETS:
            self.assertEqual(new_nodes[name]['parameters']['jsCode'],desired_nodes[name]['parameters']['jsCode'])
        for key in ('id','name','active','connections','settings'):
            self.assertEqual(expected.get(key),original.get(key))
        return result,state,original,expected,backups[0]

    @staticmethod
    def mutation_events(state):
        return [event for event in state['events'] if event['event'] in ('unpublish:workflow','import:workflow','publish:workflow','restart')]

    def assert_restored(self,state,original):
        self.assertEqual(state['workflow'],original)
        self.assertEqual(state['running_workflow'],original)
        imports=[event['source'] for event in state['events'] if event['event']=='import:workflow']
        self.assertEqual(imports,['/tmp/w10-deployment-probe/after.json','/tmp/w10-deployment-probe/rollback.json'])
        self.assertEqual(state['events'][-1]['event'],'cleanup')

    def test_work_arriving_after_export_defers_without_mutating_or_restarting(self):
        result,state,original,_,_=self.run_deploy([0,1])
        self.assertEqual(result.returncode,75,result.stderr)
        self.assertEqual(state['idle_checks'],2)
        self.assertEqual(self.mutation_events(state),[])
        self.assertEqual(state['workflow'],original)
        self.assertEqual(state['running_workflow'],original)
        self.assertNotIn('W10_SUBJECT_QUALITY_ROLLBACK',result.stderr)
        self.assertNotIn('W10_SUBJECT_QUALITY_DEPLOY_VERIFIED',result.stdout)
        events=[event['event'] for event in state['events']]
        self.assertLess(events.index('export'),len(events)-1-events[::-1].index('idle'))
        self.assertEqual(events[-1],'cleanup')

    def test_work_arriving_after_publication_restores_active_workflow_without_restart(self):
        result,state,original,_,_=self.run_deploy([0,0,1])
        self.assertEqual(result.returncode,75,result.stderr)
        self.assertEqual(state['idle_checks'],3)
        self.assertEqual(state['restarts'],0)
        self.assert_restored(state,original)
        events=[event['event'] for event in state['events']]
        self.assertEqual(events.count('publish:workflow'),2)
        last_idle=len(events)-1-events[::-1].index('idle')
        self.assertLess(events.index('publish:workflow'),last_idle)
        self.assertIn('W10_SUBJECT_QUALITY_ROLLBACK',result.stderr)
        self.assertNotIn('W10_SUBJECT_QUALITY_DEPLOY_VERIFIED',result.stdout)

    def test_busy_deferral_also_preserves_an_initially_inactive_workflow(self):
        result,state,original,_,_=self.run_deploy([0,0,1],active=False)
        self.assertEqual(result.returncode,75,result.stderr)
        self.assert_restored(state,original)
        self.assertEqual(state['restarts'],0)
        self.assertFalse(state['workflow']['active'])
        self.assertNotIn('publish:workflow',[event['event'] for event in state['events']])

    def test_all_idle_update_is_scoped_restarted_with_45_seconds_and_verified(self):
        result,state,_,expected,backup=self.run_deploy([0,0,0])
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(state['idle_checks'],3)
        self.assertEqual(state['workflow'],expected)
        self.assertEqual(state['running_workflow'],expected)
        self.assertEqual(state['restarts'],1)
        self.assertEqual([call for call in state['calls'] if call[0]=='restart'],[['restart','--timeout','45','mainbuyer-automation-n8n-1']])
        self.assertEqual(json.loads((backup/'verified.json').read_text()),[expected])
        self.assertIn('W10_SUBJECT_QUALITY_DEPLOY_VERIFIED',result.stdout)
        self.assertNotIn('W10_SUBJECT_QUALITY_ROLLBACK',result.stderr)
        events=[event['event'] for event in state['events']]
        self.assertLess(events.index('restart'),events.index('health'))
        self.assertEqual(events[-1],'cleanup')

    def test_postrestart_verification_failure_restores_then_restarts_original(self):
        result,state,original,_,_=self.run_deploy([0,0,0],corrupt_verification=True)
        self.assertEqual(result.returncode,1,result.stderr)
        self.assertEqual(state['restarts'],2)
        self.assert_restored(state,original)
        self.assertEqual([call for call in state['calls'] if call[0]=='restart'],[['restart','--timeout','45','mainbuyer-automation-n8n-1']]*2)
        self.assertIn('W10_SUBJECT_QUALITY_ROLLBACK',result.stderr)
        self.assertNotIn('W10_SUBJECT_QUALITY_DEPLOY_VERIFIED',result.stdout)
        events=[event['event'] for event in state['events']]
        imports=[i for i,name in enumerate(events) if name=='import:workflow']
        restarts=[i for i,name in enumerate(events) if name=='restart']
        self.assertLess(restarts[0],imports[1])
        self.assertLess(imports[1],restarts[1])


if __name__=='__main__':
    unittest.main()

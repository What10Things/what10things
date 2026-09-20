"""Exercise the deployment shell's actual Docker stdin and idle/busy boundary."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SCRIPTS=['deploy_research_recovery.sh']
FAKE_DOCKER='''#!/usr/bin/env python3
import os,sys
args=sys.argv[1:]
if any('psql ' in a for a in args):
    query=sys.stdin.read() if '-i' in args else ''
    with open(os.environ['PROBE_LOG'],'a') as f:f.write('QUERY:'+query+'\\n')
    if query.strip():print(os.environ['PROBE_COUNT'])
    sys.exit(0)
with open(os.environ['PROBE_LOG'],'a') as f:f.write('NEXT_DOCKER_OPERATION\\n')
sys.exit(66)
'''


class DeploymentIdleGuardTests(unittest.TestCase):
    def test_idle_proceeds_and_busy_defers_using_supplied_query(self):
        for name in SCRIPTS:
            for count,expected in [('0',66),('1',75)]:
                with self.subTest(script=name,count=count),tempfile.TemporaryDirectory() as d:
                    p=Path(d);docker=p/'docker';docker.write_text(FAKE_DOCKER);docker.chmod(0o700)
                    env={**os.environ,'HOME':d,'PATH':d+os.pathsep+os.environ['PATH'],'PROBE_COUNT':count,'PROBE_LOG':str(p/'probe.log')}
                    result=subprocess.run(['bash',str(ROOT/'automation/scripts'/name)],env=env,text=True,capture_output=True)
                    log=(p/'probe.log').read_text()
                    self.assertIn('SELECT COUNT(*) FROM execution_entity',log)
                    self.assertEqual(result.returncode,expected,result.stderr)
                    self.assertEqual('NEXT_DOCKER_OPERATION' in log,count=='0')


if __name__=='__main__':unittest.main()

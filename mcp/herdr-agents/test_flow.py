"""用隔离的 Herdr 回包验证从可见派工到回执释放的调用链。"""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import server
from registry import Registry


class Flow(unittest.TestCase):
    def test_visible_receipt_close(self):
        names = ('codex','claude','omp','ds-tui','pi')
        for owner in names:
            for worker in names:
                with self.subTest(owner=owner,worker=worker):
                    self.check_flow(owner,worker)

    def test_release_running(self):
        self.check_flow("pi", "claude", cancel=True)

    def check_flow(self, owner, worker, cancel=False):
        with TemporaryDirectory() as tmp:
            db = Registry(Path(tmp) / 'state')
            tabs = [{'id':'tab0','panes':[{'terminal':'t1'}]}]
            calls = []
            exit_state = "finished"
            def cli(*args):
                calls.append(args[:3])
                if args[:2] == ('hc','get'):
                    live = args[2]=='t1' or len(tabs)>1
                    return dict(address=args[2], state='live' if live else exit_state,created_ms=1,
                                foreground={'name':owner,'pid':123},argv=[server.sys.executable,server.HERE,'worker',key] if args[2]!='t1' else [])
                if args[:2] == ('herdr-app','ls'): return {'spaces':[{'id':'s','tabs':tabs}]}
                if args[2]=='tab.new':
                    tabs.append({'id':'tab1','panes':[{'terminal':'t2'}]})
                    return dict(tab='tab1',terminal='t2')
                if args[2]=='tab.close': tabs.pop()
                return {}
            with patch.object(server,'registry',db,create=True), patch.object(server,'cli',cli), patch.object(server,'identity',return_value='t1'), patch('shutil.which',return_value='/bin/test'):
                ref=server.invoke('spawn',dict(harness=worker,task='试单',name='示例',folder=tmp))
                key=ref['task'];self.assertEqual(len(tabs),2)
                if cancel:
                    result = server.invoke('ack',dict(task_id=key,turn=1,action='release'))
                    self.assertEqual(result['state'],'closed')
                    self.assertEqual(len(tabs),1)
                    return
                server.deliver(key,1,'review','fixture 完成')
                self.assertEqual(server.invoke('inbox',{})[0]['summary'],'fixture 完成')
                tabs[1]['panes'].append({'terminal':'t3'})
                with self.assertRaisesRegex(ValueError,'ownership changed'):
                    server.invoke('ack',dict(task_id=key,turn=1,action='accept'))
                self.assertEqual(len(tabs),2)
                self.assertEqual(len(server.invoke('inbox',{})),1)
                tabs[1]['panes'].pop()
                exit_state = 'unknown'
                with self.assertRaisesRegex(ValueError, 'exit unconfirmed'):
                    server.invoke('ack',dict(task_id=key,turn=1,action='accept'))
                self.assertEqual(len(server.invoke('inbox',{})),1)
                exit_state = 'finished'
                self.assertEqual(server.invoke('ack',dict(task_id=key,turn=1,action='accept')),{'state':'closed'})
                self.assertEqual(len(tabs),1)
                self.assertEqual(server.invoke('inbox',{}),[])
                self.assertIn(('hc','send','t1'),calls)

    def test_resume_replay(self):
        with TemporaryDirectory() as tmp:
            db = Registry(Path(tmp) / 'state')
            db.create('prior','owner','codex','long','worker','first',tmp)
            db.db.execute("UPDATE tasks SET state='closed'")
            db.db.commit()
            tabs = [{'id':'owner-tab','panes':[{'terminal':'t1'}]}]
            def cli(*args):
                if args[2] == 'tab.new':
                    tabs.append({'id':'child-tab','panes':[{'terminal':'t2'}]})
                    return dict(tab='child-tab',terminal='t2')
                return {}
            with patch.object(server,'registry',db,create=True), patch.object(server,'owner_key',return_value='owner'), patch.object(server,'identity',return_value='t1'), patch.object(server,'tabs',side_effect=lambda: [('s',tab) for tab in tabs]), patch.object(server,'cli',cli), patch('shutil.which',return_value='codex'):
                request = dict(task_id='prior',instruction='continue')
                first = server.invoke('resume',request)
                replay = server.invoke('resume',request)
                self.assertEqual(first['task'],replay['task'])
                self.assertEqual(len(tabs),2)
                with self.assertRaisesRegex(ValueError,'conflict'):
                    server.invoke('resume',dict(task_id='prior',instruction='other'))

"""用隔离的 Herdr 回包验证从可见派工到回执释放的调用链。"""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import server
from registry import Registry


class Flow(unittest.TestCase):
    def test_visible_receipt_close(self):
        with TemporaryDirectory() as tmp:
            db = Registry(Path(tmp) / 'state')
            tabs = [{'id':'tab0','panes':[{'terminal':'t1'}]}]
            calls = []
            def cli(*args):
                calls.append(args[:3])
                if args[:2] == ('hc','get'):
                    live = args[2]=='t1' or len(tabs)>1
                    return dict(address=args[2], state='live' if live else 'finished',created_ms=1,
                                foreground={'name':'codex'},argv=[server.sys.executable,server.HERE,'worker',key] if args[2]!='t1' else [])
                if args[:2] == ('herdr-app','ls'): return {'spaces':[{'id':'s','tabs':tabs}]}
                if args[2]=='tab.new':
                    tabs.append({'id':'tab1','panes':[{'terminal':'t2'}]})
                    return dict(tab='tab1',terminal='t2')
                if args[2]=='tab.close': tabs.pop()
                return {}
            with patch.object(server,'registry',db,create=True), patch.object(server,'cli',cli), patch.object(server,'identity',return_value='t1'), patch('shutil.which',return_value='/bin/test'):
                ref=server.invoke('spawn',dict(harness='codex',task='试单',name='示例',folder=tmp))
                key=ref['task'];self.assertEqual(len(tabs),2)
                server.deliver(key,1,'review','fixture 完成')
                self.assertEqual(server.invoke('inbox',{})[0]['summary'],'fixture 完成')
                tabs[1]['panes'].append({'terminal':'t3'})
                with self.assertRaisesRegex(ValueError,'ownership changed'):
                    server.invoke('ack',dict(task_id=key,turn=1,action='accept'))
                self.assertEqual(len(tabs),2)
                tabs[1]['panes'].pop()
                self.assertEqual(server.invoke('ack',dict(task_id=key,turn=1,action='accept')),{'state':'closed'})
                self.assertEqual(len(tabs),1)
                self.assertIn(('hc','send','t1'),calls)

import tempfile
import unittest
from pathlib import Path
from registry import Registry


class Lifecycle(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.r = Registry(Path(tmp.name)/'tasks.db')
        self.r.create('x', 'owner', 'codex', 'once', '检查', '输入', '/tmp')
        self.r.bind('x', 't7', 'tab7')

    def test_replay(self):
        self.assertTrue(self.r.report('x', 1, 'review', '完成'))
        self.assertFalse(self.r.report('x', 1, 'review', '完成'))
        self.assertEqual(len(self.r.inbox('owner')), 1)
        self.assertEqual(self.r.inbox('other'), [])

    def test_stale_turn(self):
        with self.assertRaises(ValueError):
            self.r.report('x', 2, 'review', '迟到')

    def test_conflicting_delivery(self):
        self.r.report('x', 1, 'review', '完成')
        with self.assertRaises(ValueError):
            self.r.report('x', 1, 'failed', '失败')

    def test_tree_is_scoped_to_owner(self):
        self.r.create('y','t7@2','codex','short','复核','检查','/tmp',parent='x')
        self.r.create('z','unrelated','claude','once','其他','检查','/tmp')
        self.assertEqual([r['id'] for r in self.r.tree('owner')], ['x','y'])
        self.assertEqual([r['id'] for r in self.r.tree('t7@2')], ['y'])

    def test_retry_carries_last_delivery_and_current_ruling(self):
        self.r.report('x', 1, 'review', '第一版结果 41')
        handoff = self.r.handoff('x', '把结果加一')
        self.assertIn('第一版结果 41', handoff)
        self.assertTrue(handoff.endswith('把结果加一'))

    def test_spawn_replay_uses_original_instruction(self):
        def replay(prompt):
            return self.r.reserve('x','owner','codex','once','检查',prompt,'/tmp',None,None,None)

        with self.r.db:
            self.r.db.execute("UPDATE tasks SET prompt='修改后的任务',turn=2 WHERE id='x'")
        self.assertEqual(replay('输入')['terminal'], 't7')
        with self.assertRaisesRegex(ValueError, 'conflict'):
            replay('修改后的任务')

    def test_unknown_state_rejected_in_storage(self):
        import sqlite3
        for query in ("UPDATE tasks SET state='completed' WHERE id='x'",
                      "INSERT INTO events(task,turn,state,summary) VALUES('x',1,'completed','done')"):
            with self.assertRaises(sqlite3.IntegrityError), self.r.db:
                self.r.db.execute(query)

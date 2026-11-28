"""单机任务登记与持久交件箱。"""
import sqlite3


class Registry:
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, owner TEXT, harness TEXT,
            mode TEXT, name TEXT, prompt TEXT, folder TEXT, terminal TEXT, tab TEXT,
            state TEXT DEFAULT 'starting', turn INTEGER DEFAULT 1);
          CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, task TEXT, turn INTEGER,
            state TEXT, summary TEXT, acknowledged INTEGER DEFAULT 0,
            UNIQUE(task,turn,state,summary));''')

        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            if 'parent' not in {r['name'] for r in self.db.execute('PRAGMA table_info(tasks)')}:
                self.db.execute('ALTER TABLE tasks ADD COLUMN parent TEXT')

            columns = {r['name'] for r in self.db.execute('PRAGMA table_info(tasks)')}
            for name, kind in [('owner_pid','INTEGER'),('launch_argv','TEXT')]:
                if name not in columns:
                    self.db.execute(f'ALTER TABLE tasks ADD COLUMN {name} {kind}')

    def tree(self, owner):
        rows = self.db.execute('''
            WITH RECURSIVE owned(id) AS (
                SELECT id FROM tasks WHERE owner=?
                UNION SELECT t.id FROM tasks t JOIN owned ON t.parent=owned.id
            ) SELECT t.id,parent,name,harness,mode,terminal,tab,state,turn
              FROM tasks t JOIN owned ON t.id=owned.id ORDER BY t.rowid
        ''', (owner,))
        return [dict(r) for r in rows]

    def create(self, key, owner, harness, mode, name, prompt, folder, parent=None, pid=None, argv=None):
        with self.db:
            self.db.execute('INSERT INTO tasks(id,owner,harness,mode,name,prompt,folder,parent,owner_pid,launch_argv) VALUES(?,?,?,?,?,?,?,?,?,?)',
                            (key, owner, harness, mode, name, prompt, folder, parent, pid, argv))

    def reserve(self, key, owner, harness, mode, name, prompt, folder, parent, pid, argv):
        try:
            self.create(key, owner, harness, mode, name, prompt, folder, parent, pid, argv)
            return None
        except sqlite3.IntegrityError:
            row = self.get(key)
            if any(row[k] != v for k,v in [('owner',owner),('harness',harness),('mode',mode),('name',name),('folder',folder)]):
                raise ValueError('task id conflict')
            return {k:row[k] for k in ('id','state','terminal','tab','turn')}

    def get(self, key):
        row = self.db.execute('SELECT * FROM tasks WHERE id=?', (key,)).fetchone()
        if not row:
            raise ValueError('unknown task')
        return dict(row)

    def bind(self, key, terminal, tab):
        with self.db:
            self.db.execute('UPDATE tasks SET terminal=?,tab=?,state="working" WHERE id=?', (terminal, tab, key))

    def report(self, key, turn, state, summary):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row = self.get(key)
            if turn != row['turn']:
                raise ValueError('stale turn')
            args = (key, turn, state, summary)
            if self.db.execute('SELECT 1 FROM events WHERE task=? AND turn=? AND state=? AND summary=?', args).fetchone():
                return False
            if row['state'] not in ('starting','working','blocked','needs_decision'):
                raise ValueError('turn already ended')
            self.db.execute('INSERT INTO events(task,turn,state,summary) VALUES(?,?,?,?)',args)
            self.db.execute('UPDATE tasks SET state=? WHERE id=?',(state,key))
            return True

    def inbox(self, owner):
        return [dict(r) for r in self.db.execute('SELECT e.* FROM events e JOIN tasks t ON t.id=e.task WHERE owner=? AND acknowledged=0 ORDER BY e.id',(owner,))]

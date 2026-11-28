import json
import tempfile
from pathlib import Path
import unittest
from adapters import load


class Adapters(unittest.TestCase):
    def test_custom_registration(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp)/'custom.json'
            config.write_text(json.dumps({'example': ['example-cli','--input','{task}']}))
            profiles = load(config)
            self.assertEqual(profiles['example'], ['example-cli','--input','{task}'])
            for name in ('omp','ds-tui','pi','claude','codex','opencode'):
                self.assertIn(name, profiles)

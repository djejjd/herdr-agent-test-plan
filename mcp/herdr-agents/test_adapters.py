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

    def test_native_receipt_is_single_argument(self):
        from adapters import command
        args = command(load()['codex'], 'answer only', '/tmp/demo receipt')
        self.assertEqual(args[args.index('--output-last-message') + 1], '/tmp/demo receipt')
        self.assertEqual(args[-1], 'answer only')

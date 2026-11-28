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

    def test_claude_final_result(self):
        from claude_receipt import final_result
        event = dict(type='result', subtype='success', is_error=False, result='31')
        self.assertEqual(final_result(event), '31')
        for changes in (dict(is_error=True),dict(subtype='error'),dict(result='  ')):
            with self.assertRaises(ValueError):
                final_result(dict(event, **changes))

    def test_stdout_receipt(self):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as tmp:
            receipt = Path(tmp)/'receipt'
            adapter = Path(__file__).with_name('stdout_receipt.py')
            for code in ('raise SystemExit(1)', 'print(" ")', 'print("kiwi-82")'):
                result = subprocess.run([sys.executable, adapter, receipt, sys.executable, '-c', code], capture_output=True)
                expected = 'kiwi' in code
                self.assertEqual(result.returncode == 0, expected)
                self.assertEqual(receipt.exists(), expected)
            self.assertEqual(receipt.read_text(), 'kiwi-82')

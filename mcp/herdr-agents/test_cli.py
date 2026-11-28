"""验证主管从终端调用无参数工具时能正常进入身份检查。"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class Cli(unittest.TestCase):
    def test_no_argument_tools_reach_identity_check(self):
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, HERDR_AGENTS_DIR=directory, HC_TERMINAL_ID='')
            for tool in ('inbox', 'list'):
                result = subprocess.run(
                    [sys.executable, '-B', Path(__file__).with_name('server.py'), 'call', tool],
                    env=env, capture_output=True, text=True, check=False,
                )
                self.assertIn('local Herdr terminal required', result.stderr)

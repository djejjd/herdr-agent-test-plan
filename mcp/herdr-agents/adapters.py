"""从发行配置及用户配置读取 harness 的 argv，无 shell 插值。"""
import json
import os
from pathlib import Path


def load(config=None):
    profiles = json.loads(Path(__file__).with_name('profiles.json').read_text())
    override = config or os.environ.get('HERDR_AGENTS_PROFILES')
    if override:
        profiles.update(json.loads(Path(override).read_text()))
    for name, argv in profiles.items():
        if not isinstance(argv, list) or not argv or not all(isinstance(v,str) and v for v in argv) or argv.count('{task}') != 1 or argv[0] == '{task}':
            raise ValueError(f'invalid harness profile: {name}')
    return profiles


def command(argv, task, receipt):
    """将任务和原生最终回复文件作为独立参数传给执行器。"""
    fields = {'{task}': task, '{receipt}': str(receipt)}
    return [fields.get(arg, arg) for arg in argv]

"""把 Claude 的结构化最终回复转换为本轮私有回执。"""
import json
from pathlib import Path
import subprocess
import sys


def final_result(event):
    if not isinstance(event, dict) or event.get('type') != 'result' or event.get('subtype') != 'success' or event.get('is_error') is not False:
        raise ValueError('Claude 未返回成功交付')
    text = event.get('result')
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Claude 最终回复为空')
    return text.strip()


if __name__ == '__main__':
    result = subprocess.run(sys.argv[2:], stdout=subprocess.PIPE)
    if result.returncode:
        sys.exit(result.returncode)
    try:
        summary = final_result(json.loads(result.stdout))
    except (UnicodeError, ValueError):
        sys.exit('Claude 结构化回执无效')
    with Path(sys.argv[1]).open('x', encoding='utf-8') as receipt:
        receipt.write(summary[:800])
    print(summary[:800], flush=True)

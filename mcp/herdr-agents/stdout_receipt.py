"""转发文本型 harness 的标准输出，成功退出后将末尾摘要作为回执。"""
import subprocess
import sys
from pathlib import Path


if __name__ == '__main__':
    tail = b''
    with subprocess.Popen(sys.argv[2:], stdout=subprocess.PIPE) as child:
        while chunk := child.stdout.read1(8192):
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
            tail = (tail + chunk)[-4096:]
        status = child.wait()
    if status:
        sys.exit(status)
    summary = tail.decode('utf-8', errors='replace').strip()[-800:]
    if not summary:
        sys.exit('harness 最终输出为空')
    with Path(sys.argv[1]).open('x', encoding='utf-8') as receipt:
        receipt.write(summary)

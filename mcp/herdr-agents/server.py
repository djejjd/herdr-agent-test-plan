"""Herdr 可见派工 MCP：stdio JSON-RPC，子进程与主管共用私有 SQLite。"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid
from registry import Registry
from adapters import load, command

HERE = str(Path(__file__).resolve())


def cli(*args):
    run = subprocess.run(args, capture_output=True, timeout=12)
    if run.returncode:
        raise ValueError(f'{args[0]} {args[1]} failed ({run.returncode})')
    return json.loads(run.stdout or b'{}')


def identity():
    terminal = os.environ.get('HC_TERMINAL_ID','')
    if not re.fullmatch(r't[0-9a-z]+',terminal):
        raise ValueError('local Herdr terminal required')
    return terminal


def terminal_ids(obj):
    if isinstance(obj, dict):
        for k,v in obj.items():
            if k in ('terminal','address','id') and isinstance(v,str) and re.fullmatch('t[0-9a-z]+',v):
                yield v
            yield from terminal_ids(v)
    elif isinstance(obj,list):
        for item in obj:
            yield from terminal_ids(item)



def owns_worker(live,key):
    argv = live.get('argv') or []
    expected = [sys.executable,HERE,'worker',key]
    return argv == expected or (argv[:4] == ['/bin/zsh','-lic','"$@"; exec "$0" -li','/bin/zsh'] and argv[4:] == expected)


def tabs():
    for space in cli('herdr-app','ls')['spaces']:
        for tab in space['tabs']:
            yield space['id'],tab


def notify(task):
    owner_terminal = task['owner'].split('@')[0]
    foreground = cli('hc','get',owner_terminal).get('foreground') or {}
    if not task.get('owner_pid') or foreground.get('pid') != task['owner_pid']:
        raise ValueError('owner process changed')
    if owner_key(owner_terminal) != task['owner']:
        raise ValueError('owner session changed')
    cli('hc','send',owner_terminal, f'Herdr 任务 {task["id"]} 有新反馈，请读取 inbox。')


def owner_key(terminal):
    live = cli('hc','get',terminal)
    if live['state'] != 'live' or live['address'] != terminal:
        raise ValueError('owner unavailable')
    # 使用终端创建时间防止地址被重新分配。
    return f'{terminal}@{live["created_ms"]}'


def deliver(key, turn, state, summary):
    fresh = registry.report(key, turn, state, summary[:800])
    if fresh:
        try:
            notify(registry.get(key))
        except (ValueError,OSError,subprocess.TimeoutExpired):
            return {'stored':True,'notification':'pending in inbox'}
    return {'stored':True,'new':fresh}


def worker(key):
    # 先显示窗格，再由主管绑定地址，最后才启动 harness。
    terminal = identity()
    for _ in range(150):
        task = registry.get(key)
        if task['terminal'] == terminal and task['state']=='working':
            break
        time.sleep(.2)
    else:
        return 1
    while True:
        turn = task['turn']
        env = dict(os.environ, HERDR_TASK=key, HERDR_TURN=str(turn))
        try:
            receipt = directory / f'{key}-{turn}.receipt'
            instruction = (task['prompt'] + '\n完成后将简短交付摘要和证据位置作为 UTF-8 文本写入 '
                           + str(receipt) + '，也可以用已配置的 report 工具交件。')
            argv = json.loads(task['launch_argv'])
            if '{receipt}' in argv:
                instruction = task['prompt'] + '\n请在最终回复中给出简短交付摘要和证据位置。'
            result = subprocess.run(command(argv, instruction, receipt),env=env)
            status = 'review' if result.returncode==0 else 'failed'
            if registry.get(key)['state'] not in ('review','failed'):
                if status == 'review' and receipt.is_file() and not receipt.is_symlink():
                    with receipt.open(encoding='utf-8',errors='replace') as stream:
                        summary=stream.read(800).strip()
                else:
                    summary=''
                deliver(key,turn,'review' if summary else ('failed' if result.returncode else 'unverified'),
                        summary or f'harness exit={result.returncode}；请核对产物')
        except OSError:
            deliver(key,turn,'failed','harness 启动失败')
        # 保留可见终端供主管核对，后续轮次沿用同一角色和目录。
        while True:
            task = registry.get(key)
            if task['state']=='closed':
                return 0
            if task['turn']!=turn:
                break
            time.sleep(.5)


def invoke(name,a):
    terminal=identity()
    if name=='report':
        key=os.environ['HERDR_TASK']; task=registry.get(key)
        if task['terminal']!=terminal or a['state'] not in ('blocked','needs_decision','review','failed'):
            raise ValueError('invalid report')
        return deliver(key,int(os.environ['HERDR_TURN']),a['state'],a['summary'])
    owner=owner_key(terminal)
    if name=='inbox': return registry.inbox(owner)
    if name=='list':
        rows = registry.tree(owner)
        for row in rows:
            row['runtime'] = 'unknown'
            if row['terminal'] and row['state'] != 'closed':
                try:
                    live = cli('hc','get',row['terminal'])
                    if live.get('address') == row['terminal'] and owns_worker(live,row['id']):
                        row['runtime'] = (live.get('status') or {}).get('state') or live.get('state','unknown')
                except (ValueError,OSError,subprocess.TimeoutExpired):
                    pass
        return rows
    previous = None
    if name=='resume':
        previous=registry.get(a['task_id'])
        if previous['owner']!=owner or previous['mode']!='long' or previous['state']!='closed':
            raise ValueError('closed long role required')
        a=dict(name=previous['name'],folder=previous['folder'],mode='long',harness=previous['harness'],
               task=registry.handoff(previous['id'], a['instruction']))
        name='spawn'
    if name=='spawn':
        h=a['harness']; mode=a.get('mode','once'); folder=str(Path(a['folder']).resolve(strict=True))
        profiles = load()
        if h not in profiles or not shutil.which(profiles[h][0]) or mode not in ('once','short','long') or not Path(folder).is_dir():
            raise ValueError('invalid harness/mode/folder')
        space=next((s for s,t in tabs() if terminal in terminal_ids(t)),None)
        if not space: raise ValueError('owner has no visible tab')
        key = uuid.uuid5(uuid.NAMESPACE_URL, owner+'/' + a['task_id']).hex if a.get('task_id') else uuid.uuid4().hex
        if previous:
            key = uuid.uuid5(uuid.NAMESPACE_OID, previous['id']).hex
        parent = os.environ.get('HERDR_TASK')
        if parent and registry.get(parent)['terminal'] != terminal:
            raise ValueError('parent terminal mismatch')
        foreground = cli('hc','get',terminal).get('foreground') or {}
        pid = foreground.get('pid') if foreground.get('name') not in ('sh','bash','zsh','fish','pwsh','cmd') else None
        existing = registry.reserve(key,owner,h,mode,a['name'],a['task'],folder,parent,pid,json.dumps(profiles[h]),previous)
        if existing:
            return dict(task=key, **existing)
        args=dict(space=space,name=a['name'],folder=folder,argv=[sys.executable,HERE,'worker',key])
        try:
            ref=cli('herdr-app','do','tab.new',json.dumps(args))
            if not any(s==space and t['id']==ref['tab'] and ref['terminal'] in terminal_ids(t) for s,t in tabs()):
                raise ValueError('visible binding unconfirmed')
            registry.bind(key,ref['terminal'],ref['tab'])
        except Exception:
            deliver(key,1,'failed','visible spawn/bind failed'); raise
        return dict(task=key,role_id=previous['role_id'] if previous else key,resumed_from=previous['id'] if previous else None,**ref)
    task=registry.get(a['task_id']); key=task['id']
    if task['owner']!=owner or task['turn']!=a['turn']: raise ValueError('owner/turn mismatch')
    action=a['action']
    if action=='release' and task['state']=='closed':
        return {'state':'closed'}
    if action!='release' and task['state'] not in ('review','failed','unverified','idle','closing'):
        raise ValueError('not ready for receipt')
    if action=='release' and not task['terminal']:
        raise ValueError('terminal binding unavailable')
    if action not in ('accept','release','retry'): raise ValueError('invalid action')
    with registry.db:
        if action=='retry':
            if not a.get('instruction'): raise ValueError('instruction required')
            cur=registry.db.execute('UPDATE tasks SET prompt=?,turn=turn+1,state="working" WHERE id=? AND turn=? AND state=?',(registry.handoff(key, a['instruction']),key,task['turn'],task['state']))
        else:
            state='idle' if action=='accept' and task['mode']=='short' else 'closing'
            cur=registry.db.execute('UPDATE tasks SET state=? WHERE id=? AND turn=? AND state=?',(state,key,task['turn'],task['state']))
        if cur.rowcount!=1: raise ValueError('concurrent change')
        registry.db.execute('UPDATE events SET acknowledged=1 WHERE task=? AND turn=?',(key,task['turn']))
    if action!='retry' and state=='closing':
        tab=next((t for _,t in tabs() if t['id']==task['tab']),None)
        if tab:
            live=cli('hc','get',task['terminal'])
            if live.get('state')=='live' and not owns_worker(live,key):
                raise ValueError('terminal taken over; manual cleanup')
            ids=set(terminal_ids(tab))-{tab['id']}
            if ids!={task['terminal']}: raise ValueError('tab ownership changed; manual cleanup')
            cli('herdr-app','do','tab.close',json.dumps(dict(id=task['tab'],confirmed=True)))
        if any(t['id']==task['tab'] for _,t in tabs()): raise ValueError('tab still present')
        if cli('hc','get',task['terminal'])['state']=='live': raise ValueError('terminal still live')
        with registry.db: registry.db.execute('UPDATE tasks SET state="closed" WHERE id=?',(key,))
    return {'state':registry.get(key)['state']}


FIELDS={
    'spawn': ('在主管的 Herdr Space 打开可见子任务。', ['name','folder','task','harness'],['mode','task_id']),
    'resume': ('用上次交件摘要重新打开长期角色的可见窗格。',['task_id','instruction'],[]),
    'list': ('列出当前主管登记的子任务。',[],[]),
    'inbox': ('读取持久化的未收件反馈。',[],[]),
    'report': ('子任务交件或报告阻塞；summary 填脱敏摘要与证据位置。',['state','summary'],[]),
    'ack': ('主管收件 accept，返修 retry，或释放 release。',['task_id','turn','action'],['instruction'])}


def tools_list():
    result=[]
    for name,(desc,required,optional) in FIELDS.items():
        props={k:{'type':'integer' if k=='turn' else 'string'} for k in required+optional}
        result.append(dict(name=name,description=desc,inputSchema=dict(type='object',properties=props,required=required,additionalProperties=False)))
    return result


def serve():
    for line in sys.stdin:
        request={}
        try:
            request=json.loads(line)
            if 'id' not in request: continue
            method=request['method']
            if method=='initialize':
                result=dict(protocolVersion='2024-11-05',capabilities={'tools':{}},serverInfo={'name':'herdr-agents','version':'0.1.0'})
            elif method=='ping': result={}
            elif method=='tools/list': result={'tools':tools_list()}
            elif method=='tools/call':
                params=request['params']; name=params['name']; args=params.get('arguments',{})
                if name not in FIELDS: raise ValueError('unknown tool')
                _,required,optional=FIELDS[name]
                if not set(required)<=args.keys()<=set(required+optional): raise ValueError('invalid fields')
                if any(type(v) is not (int if k=='turn' else str) for k,v in args.items()): raise ValueError('invalid argument type')
                result={'content':[{'type':'text','text':json.dumps(invoke(name,args),ensure_ascii=False)}]}
            else: raise ValueError('unknown method')
            response={'result':result}
        except Exception as exc:
            response={'error':{'code':-32603,'message':str(exc)[:200] if isinstance(exc,ValueError) else type(exc).__name__}}
        print(json.dumps(dict(jsonrpc='2.0',id=request.get('id'),**response)),flush=True)


if __name__=='__main__':
    os.umask(0o077)
    directory=Path(os.environ.get('HERDR_AGENTS_DIR',Path.home()/'.local/state/herdr-agents'))
    directory.mkdir(mode=0o700,parents=True,exist_ok=True)
    registry=Registry(directory/'tasks.db')
    if sys.argv[1:2]==['worker']: sys.exit(worker(sys.argv[2]))
    if sys.argv[1:2] == ['call']:
        print(json.dumps(invoke(sys.argv[2],json.loads(sys.argv[3])),ensure_ascii=False))
    else:
        serve()

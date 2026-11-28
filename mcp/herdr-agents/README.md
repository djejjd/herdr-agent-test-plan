状态: 试验中
创建: 2026-11-25
最后更新: 2026-11-28
关联: ../../workflow/collab.md

# 可见子 Agent MCP

MCP 客户端使用 stdio，命令为 `python3`，参数为本目录 `server.py` 的绝对路径。主管客户端应由 Herdr 终端启动并继承 `HC_TERMINAL_ID`。此工作树尚未安装到全局 harness 配置。

主管调用 `spawn`，传入 `name`、`folder`、`task`、`harness` 和可选的 `mode`。程序按主管终端查找所属 space，通过 `tab.new` 开可见标签。子进程在绑定确认后启动。适配命令见 profiles.json。`list` 返回登记的整棵子任务树，并分列交付状态与终端运行状态。终端身份或连接无法核实时显示 unknown。`inbox` 读取当前主管待处理事件。

子方显式 `report(state="review", summary="产物及验证摘要")`。缺少交件的正常退出登记为 `unverified`，异常退出登记为 `failed`。主管调用 `ack` 并提供 `task_id`、`turn`、`action`。`retry` 需附新 `instruction`；`accept` 对 once 进入关闭，对 short 转 idle；`release` 释放空闲任务。long 收件后释放窗格。resume 使用交付摘要在新窗格重开同名角色。请仅在隔离环境试用。

| 状态变化 | 核验或清理 |
|---|---|
| starting → working | 窗口列出指定 tab 和 terminal 后才放行 |
| working → blocked / needs_decision | 保存事件，通知主管，保留窗格 |
| working → review / failed / unverified | 等主管核对实际产物 |
| review → working / idle | 返修递增轮次，短期收件保留窗格 |
| review / idle → closing → closed | 核对终端启动参数及标签归属，检查关闭结果 |

在当前目录运行 `python3 -B -m unittest -v`。SQLite 默认位于用户状态目录，`HERDR_AGENTS_DIR` 可为测试指定其他目录，主管和窗口内的 worker 必须使用同一目录。

## Harness 接入

`profiles.json` 登记 Codex、Claude、OMP、ds-tui（程序名 `dsh-tui`）、Pi 及 OpenCode。各项为 argv 数组，其中 `{task}` 是任务参数。用 `HERDR_AGENTS_PROFILES` 指向本机 JSON 可增加或覆盖适配。服务将本轮启动参数保存到任务登记，子窗格读取同一份登记。主管由 Herdr 会话及派工时的前台 PID 识别。

支持 stdio MCP 的主管配置 `python3 /绝对路径/server.py`。其他 harness 可调用 `python3 /绝对路径/server.py call 工具名 'JSON参数'`。主管给 `spawn` 传入稳定 `task_id` 即可重试相同派工。执行者在当前任务的环境中调用 `report`，交件摘要需指出证据和待决事项。短期任务用 `ack(action="retry", instruction=...)` 进入下一轮。长期角色恢复依据摘要创建新会话。

## 第一次派工

在 Herdr App 的主管终端中进入本仓库根目录。下面的 CLI 与 stdio MCP 调用同一套工具。先确认主管能看到自己的任务列表。

```sh
server="$PWD/mcp/herdr-agents/server.py"
python3 -B "$server" call list
```

例如，要让 Pi 检查当前项目的 README，可在同一终端运行以下命令。每次发起新任务可换一个 `task_id`，网络中断后重发同一请求则沿用原值。

```sh
request=$(python3 -c 'import json, os; print(json.dumps(dict(name="文档检查", folder=os.getcwd(), harness="pi", mode="once", task_id="readme-check-1", task="读取 README.md，返回第一个 Markdown 标题和文件路径。")))')
python3 -B "$server" call spawn "$request"
```

Herdr 会打开对应标签页。主管收到通知后运行 `python3 -B "$server" call inbox`，使用返回事件里的 `task` 和 `turn`，对照 README 核实标题。通过后调用 `ack`，例如 `python3 -B "$server" call ack '{"task_id":"替换为事件里的task","turn":1,"action":"accept"}'`。需要返修时将 `action` 改为 `retry`，并用 `instruction` 写明要改什么、怎样验证。一次性任务接受后应返回 `closed`。

支持 `mcpServers` 格式的客户端可将以下条目加入项目级配置，将示例路径替换为实际绝对路径。从同一个 Herdr 终端启动主管，工具名与上例一致。

```json
{"mcpServers":{"herdr":{"command":"python3","args":["-B","/绝对路径/herdr-agent-test-plan/mcp/herdr-agents/server.py"]}}}
```

## 验证范围

五种主管与五种执行者的 25 种组合已通过模拟 Herdr 的调用测试。下表记录真实 Herdr 标签页中的执行结果。主管侧已实测 Codex 派工，以及 Pi → OMP 和 OMP → Pi 两个方向的派工、文件验收、回执与终端释放。主管可直接运行 `python3 /绝对路径/server.py call inbox` 读取待办。

| 执行者 | 已验证的行为 | 待验证或修复 |
|---|---|---|
| Codex | 一次性交付、短期返修、长期恢复。相同恢复请求返回同一任务和标签页 | 跨 harness 主管派工 |
| OMP、Pi | 一次性任务各自写出指定文件，自动交件。主管独立读取文件并验收，关闭后终端为 `finished` | 返修、长期恢复 |
| Claude | 可见窗口内完成一次性计算。适配器从 `--output-format json` 的成功结果生成回执，主管核验答案并关闭终端。Claude 通过 stdio MCP 向 Pi 派工，读取文件，验收 review 回执并释放子终端 | Claude 作为执行者写文件、返修、长期恢复 |
| ds-tui | 启动失败可反馈并释放窗口 | 本机 `dsh-tui run` 与已安装 DSH 版本不匹配，原生入口的成功交付待验 |
| OpenCode | 保留启动配置 | 本轮未做真机验收 |

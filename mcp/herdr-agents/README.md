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

## 验证范围

五种主管与五种执行者的 25 种组合已通过模拟 Herdr 的调用测试。下表记录真实 Herdr 标签页中的执行结果。主管侧目前只验证了 Codex。

| 执行者 | 已验证的行为 | 待验证或修复 |
|---|---|---|
| Codex | 一次性交付、短期返修、长期恢复。相同恢复请求返回同一任务和标签页 | 跨 harness 主管派工 |
| OMP、Pi | 一次性任务各自写出指定文件，自动交件。主管独立读取文件并验收，关闭后终端为 `finished` | 返修、长期恢复、担任主管 |
| Claude | 可见窗口启动，失败后释放 | 本机模型返回 `unrecognized_model`，成功交付待验 |
| ds-tui | 启动失败可反馈并释放窗口 | 本机 `dsh-tui run` 与已安装 DSH 版本不匹配，原生入口的成功交付待验 |
| OpenCode | 保留启动配置 | 本轮未做真机验收 |

状态: 试验中
创建: 2026-11-25
最后更新: 2026-11-25
关联: ../../workflow/collab.md

# 可见子 Agent MCP

MCP 客户端使用 stdio，命令为 `python3`，参数为本目录 `server.py` 的绝对路径。主管客户端应由 Herdr 终端启动并继承 `HC_TERMINAL_ID`。此工作树尚未安装到全局 harness 配置。

主管调用 `spawn`，传入 `name`、`folder`、`task`、`harness` 和可选的 `mode`。程序按主管终端查找所属 space，通过 `tab.new` 开可见标签。子进程在绑定确认后启动。适配命令为 Codex exec、Claude print、OpenCode run。`list` 返回登记的整棵子任务树，并分列交付状态与终端运行状态。终端身份或连接无法核实时显示 unknown。`inbox` 读取当前主管待处理事件。

子方显式 `report(state="review", summary="产物及验证摘要")`。缺少交件的正常退出登记为 `unverified`，异常退出登记为 `failed`。主管调用 `ack` 并提供 `task_id`、`turn`、`action`。`retry` 需附新 `instruction`；`accept` 对 once 进入关闭，对 short 转 idle；`release` 释放空闲任务。long 收件后释放窗格。resume 使用交付摘要在新窗格重开同名角色。请仅在隔离环境试用。

| 状态变化 | 核验或清理 |
|---|---|
| starting → working | 窗口列出指定 tab 和 terminal 后才放行 |
| working → blocked / needs_decision | 保存事件，通知主管，保留窗格 |
| working → review / failed / unverified | 等主管核对实际产物 |
| review → working / idle | 返修递增轮次，短期收件保留窗格 |
| review / idle → closing → closed | 核对终端启动参数及标签归属，检查关闭结果 |

在当前目录运行 `python3 -B -m unittest -v`。SQLite 默认位于用户状态目录，`HERDR_AGENTS_DIR` 可为测试指定其他目录，主管和窗口内的 worker 必须使用同一目录。

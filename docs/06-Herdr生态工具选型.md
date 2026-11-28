# Herdr生态工具选型
状态: active  
创建: 2026-11-25  
最后更新: 2026-11-28
关联: ../README.md

沿用已有 Herdr、MCP 和 hooks。选择工具时先看它连接的运行时。

| 想解决的问题 | 可参考的公开项目 | 采用时机 |
|---|---|---|
| 向持久终端发任务、等回复 | [herdr-core 与 hc](https://github.com/herdrdev/herdr-core) | 已用 Core 或桌面 App 时从这里核对命令 |
| 让 Agent 操作 TUI 的 pane | [官方 herdr Skill](https://github.com/herdrdev/herdr/blob/master/skills/herdr/SKILL.md) | 使用 `herdr` TUI |
| 查看上一轮 diff 并发送行级评论 | [herdr-reviewr](https://github.com/persiyanov/herdr-reviewr) | 需要人工提前纠偏，先核对 TUI 插件兼容性 |
| 在桌面 App 对照提交和文件 | [eliasyoung/herdr-review](https://github.com/eliasyoung/herdr-review) | 使用桌面 mod 的项目 |
| 跨 tab 整理待决事项 | [herdr-pm](https://github.com/yigitkonur/herdr-pm) | 项目多到主管汇总吃力时 |
| 多位 reviewer 可见地协作 | [zinin/herdr-review](https://github.com/zinin/herdr-review) | 已明确单个 reviewer 的盲区时 |

社区 [Herdr MCP](https://github.com/Orange-County-AI/herdr-mcp) 可参考其 schema 与方法过滤。既有 MCP 已能投递和回报时，先用真实任务验证重复、乱序与失联处理。以上链接供选型，兼容性以各仓库和实际运行版本为准。

## herdr-nix 和 Jarvis 各解决什么问题

**herdrdev/herdr-nix** 把 Herdr 官方发布的 Linux、macOS 预编译二进制包装成 Nix 包。团队用 Nix 管理开发环境时，可以锁定同一版本，减少机器之间的差异。已有可用的桌面 App 和 `hc` 时，可直接开展可见派工验收。GitHub 上有多个同名 flake，选用时要核对仓库所有者。[官方仓库](https://github.com/herdrdev/herdr-nix)

**jmseguin/Jarvis** 是桌面悬浮 AI 助手。它用 Tauri 2 显示界面，Node.js 进程驱动 Agent，支持语音输入和工具调用。与 Herdr 直接相关的是 `tools/herdr.mjs` 和 `tools/herdr-mcp/`，前者把 Herdr 工具接入助手的执行循环，后者对接 Core 和 TUI。例如，今后想让用户通过语音向主管下达指令，可以参考这层接入。当前工作流用现有主管对话、可见标签页和持久 inbox 即可落地。本项依据公开仓库说明，未安装 Jarvis 做端到端测试。[项目说明](https://github.com/jmseguin/Jarvis) · [Herdr 适配器](https://github.com/jmseguin/Jarvis/blob/main/tools/herdr.mjs)

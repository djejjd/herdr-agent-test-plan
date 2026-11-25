# Herdr生态工具选型
状态: active  
创建: 2026-11-25  
最后更新: 2026-11-25  
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

# Herdr 多 Agent 开发与测试指导书
状态: active  
创建: 2026-11-25  
最后更新: 2026-11-25  
关联: docs/07-落地步骤与检查表.md

适合通过一个主管 Agent 带多个执行者开发的人。第一轮只挑一个可演示的小任务。你向主管确认目标和边界，执行者交出最小链路，独立验证者尝试让它失败。每次纠偏都留下可复查的验收例子。

**开始使用**　把[主管工作协议](docs/03-主管Agent工作协议.md)交给主管，选一张[任务卡](templates/task-card.md)派工，再用[审查报告](templates/review-report.md)收件。项目已有计划、状态表和决策记录时，直接填入原文件。模板按需取用。

## 指南

- [问题与原则](docs/01-问题与原则.md)
- [工作模式与状态机](docs/02-工作模式与状态机.md)
- [主管Agent工作协议](docs/03-主管Agent工作协议.md)
- [多Agent分工与交接](docs/04-多Agent分工与交接.md)
- [测试与独立Review](docs/05-测试与独立Review.md)
- [Herdr生态工具选型](docs/06-Herdr生态工具选型.md)
- [落地步骤与检查表](docs/07-落地步骤与检查表.md)

[六份可复制模板](templates/)

## 本地工作流与 Herdr MCP

从[协作总纲](workflow/collab.md)进入[派工与验收](workflow/collab/work.md)、[工作区与收尾](workflow/collab/ops.md)和[全局规则](workflow/rules.md)。原文中的 `~/ai` 对应本包的 `workflow/`。每个使用者单独维护自己的待批账本。`merge-gate.sh` 可以通过 `MERGE_GATE_LEDGER` 指向自己的账本。

[MCP 原型与配置](mcp/herdr-agents/README.md)来自 HerdrCLI 提交 `afa5e80`。它提供可见派工、子任务树、持久收件及关闭操作。已验证 Codex 临时配置和 stdio 握手；可见启动、自动回报及窗格关闭仍待真实窗口验收。

在仓库根目录运行以下离线检查：

```bash
BIN="$PWD/workflow/bin" bash workflow/bin/card-check.test.sh
bash workflow/bin/merge-gate.test.sh
python3 -B -m unittest discover -s mcp/herdr-agents -v
```

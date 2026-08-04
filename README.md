# FinCopilot 🚀

## 金融风控与理赔多智能体协同平台

基于 **AgentTeams** 框架，面向 **GOAI 世界人工智能开源大赛 · Agent Infra 赛道** 的参赛方案。

---

### 🎯 一句话

> 面向银行/保险机构的风控理赔全链路多 Agent 协同平台，实现「信号入 → 处置出 → 知识沉淀」端到端自主决策闭环。

---

### 🏗️ 架构概览

```
信号入 ──▶ RiskAggregator ──▶ RiskAnalyzer ──▶ DispositionAgent ──▶ ComplianceAuditor ──▶ 知识沉淀
             信号聚合            欺诈分析           处置执行              合规审计
               │                   │                  │                    │
               └───────────────────┴──────────────────┴────────────────────┘
                                       │
                          ┌────────────┼────────────┐
                          ▼            ▼            ▼
                     6 Skills      4 MCP      RAG 知识库
```

---

### 📂 版本说明

| 版本 | 目录 | 说明 |
|------|------|------|
| **v1** · 4-Agent 版 | 根目录 | RiskAggregator → RiskAnalyzer → DispositionAgent → ComplianceAuditor（4 步 Pipeline） |
| **v2** · 3-Agent 版（推荐） | `v2-3agent/` | RiskDetective → DispositionAgent → ComplianceAuditor（3 步 Pipeline，更精简） |

> 两个版本共享同一套 6 Skill + 4 MCP，Agent 决策逻辑一致，仅编排层不同。v2 版是最终提交版本。

## 📦 快速开始

```bash
# 克隆项目
git clone <repo-url> finco-pilot
cd finco-pilot

# 安装依赖
pip install -r requirements.txt

# 运行欺诈检测 Demo
python main.py --input examples/sample_input_fraud.json

# 运行理赔评估 Demo
python main.py --input examples/sample_input_claim.json

# 运行测试
python -m pytest tests/ -v
```

---

### 📋 核心组成

| 层 | 组件 | 数量 | 说明 |
|----|------|------|------|
| Agent 层 | RiskAggregator / RiskAnalyzer / DispositionAgent / ComplianceAuditor | 4 | 各司其职，Pipeline 串联 |
| Skill 层 | signal_aggregation / fraud_detection / claim_assessment / disposition_executor / compliance_audit / case_review | 6 | 可复用能力抽象 |
| MCP 层 | tx-system / credit / claims-system / sentiment | 4 | 外部工具连接 |
| RAG 层 | 风控案例库 / 法规库 | 2 | 上下文增强 |
| 可观测 | OpenTelemetry Trace + Log + Metrics | 3 | 全链路追踪 |

---

### 🔒 安全机制

- **审批网关**：高风险动作（冻结账户 / 大额赔付 > ¥50,000 / 拒保）强制人工审批
- **回滚引擎**：所有操作记录 rollback_token，支持一键撤销
- **审计日志**：Hash 链式存储，不可篡改，满足银保监会要求
- **数据脱敏**：PII（姓名、身份证、银行卡号）Agent 不可见明文

---

### 📊 示例输出

```json
{
  "task_id": "TASK-20250115-001",
  "status": "awaiting_approval",
  "analysis": {
    "fraud_score": 90.0,
    "fraud_level": "high",
    "impact": { "level": "critical", "estimated_loss": 517000 }
  },
  "disposition": {
    "approval_required": true,
    "approval_items": ["freeze_account"]
  },
  "audit": {
    "compliance_score": 90,
    "report_hash": "a1b2c3d4e5f6a7b8"
  }
}
```

---

### 🗺️ 路线图

| 阶段 | 时间 | 目标 |
|------|------|------|
| 初赛 | ✅ 当前 | 方案设计 + PPT + 代码框架 |
| MVP v0.1 | 初赛后 2 周 | AgentTeams 可运行 Demo（车险理赔） |
| MVP v0.5 | 初赛后 4 周 | 4 Agent + 4 MCP + 6 Skill 端到端集成 |
| v1.0-beta | 复赛前 | 全场景覆盖 + 评测报告 + GitHub 开源 |
| v1.0 | 决赛 | 生产级打磨 + 社区运营 |

---

### 📄 参赛提交材料

| 材料 | 状态 | 文件 |
|------|------|------|
| 作品简介 (≤500字) | ✅ | `../FinCopilot作品简介.docx` |
| 方案 PPT | ✅ | `../FinCopilot初赛方案.pptx` |
| AgentTeams 代码包 | ✅ | 本仓库 |

---

### 👤 团队

- **骆程浩** — 杭州电子科技大学
- 项目负责人，负责方案设计 + Agent 架构 + Skill 体系 + 工程实现

---

### 📜 协议

Apache 2.0 License — Skills 与 MCP SDK 开源，文档 CC BY 4.0

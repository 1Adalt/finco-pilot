# FinCopilot 架构文档

## 概述

FinCopilot 是一个基于 AgentTeams 框架的多 Agent 协同平台，面向金融风控与理赔自动化场景。

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentTeams 协同编排层                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │RiskAggregator│─▶│ RiskAnalyzer │─▶│DispositionAgt│       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                  │               │
│         └─────────────────▼──────────────────┘               │
│                   ComplianceAuditor                          │
└─────────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Skills  │    │   MCP    │    │   RAG    │
    │  (6个)   │    │  (4组)   │    │ (2个库)  │
    └──────────┘    └──────────┘    └──────────┘
```

## Pipeline 流程

1. **聚合** → RiskAggregator 从多源接入信号
2. **分析** → RiskAnalyzer 执行欺诈检测与影响评估
3. **处置** → DispositionAgent 生成并执行方案（高风险需审批）
4. **审计** → ComplianceAuditor 核验结果并归档证据

## 目录结构

```
finco-pilot/
├── main.py                    # 入口文件
├── requirements.txt           # 依赖
├── config/
│   ├── agents.yaml            # Agent Identity 清单
│   ├── skills.yaml            # Skill 规格清单
│   ├── mcp_servers.yaml       # MCP Server 配置
│   └── settings.yaml          # 全局配置
├── agents/
│   ├── orchestrator.py        # 主控编排器
│   ├── risk_aggregator.py     # 风险聚合 Agent
│   ├── risk_analyzer.py       # 风险分析 Agent
│   ├── disposition_agent.py   # 处置执行 Agent
│   └── compliance_auditor.py  # 合规审计 Agent
├── skills/
│   ├── base.py                # Skill 基类
│   ├── signal_aggregation.py  # 信号聚合 Skill
│   ├── fraud_detection.py     # 欺诈检测 Skill
│   ├── claim_assessment.py    # 理赔评估 Skill
│   ├── disposition_executor.py # 处置执行 Skill
│   └── compliance_audit.py    # 合规审计 & 案例复盘 Skill
├── mcp/
│   └── connectors.py          # MCP 连接器 (4组)
├── examples/
│   ├── sample_input_fraud.json   # 欺诈检测样例
│   ├── sample_input_claim.json   # 理赔评估样例
│   └── expected_output.json      # 期望输出
└── tests/
    └── test_pipeline.py       # 测试用例
```

## 运行方式

```bash
# 安装依赖
pip install -r requirements.txt

# 运行欺诈检测场景
python main.py --input examples/sample_input_fraud.json

# 运行理赔评估场景
python main.py --input examples/sample_input_claim.json

# 运行测试
python -m pytest tests/ -v
```

## AgentTeams 映射

| AgentTeams 能力 | FinCopilot 映射 |
|----------------|----------------|
| 角色编排 | 4 Agent Pipeline (aggregation→analysis→disposition→audit) |
| 任务拆解 | Orchestrator 按 Stage 拆解，每阶段调用对应 Agent |
| 上下文传递 | TaskContext 对象在 Agent 间流转 |
| 协同执行 | AgentTeams sequential mode，按依赖顺序执行 |
| 状态追踪 | TaskStatus 状态机 (PENDING→IN_PROGRESS→AWAITING_APPROVAL→COMPLETED/FAILED) |

## 技术选型

| 组件 | 选择 | 备注 |
|------|------|------|
| 多Agent框架 | AgentTeams | 必选 |
| Skills | 阿里云 Skills 门户 + 自研 6 Skill | 复用 + 自建 |
| MCP | 4 组自建 MCP Server | 交易/征信/理赔/舆情 |
| AI网关 | Higress | 推荐 |
| 配置中心 | Nacos | 推荐 |
| 数据层 | PolarDB for PostgreSQL | 向量+RAG+审计 |
| 消息队列 | RocketMQ | Agent 间异步消息 |
| 可观测 | LoongSuite + AgentScope Studio | Trace/Log/Metrics |

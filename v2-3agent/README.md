# FinCopilot 3-Agent 精简版 🚀

金融风控与理赔多智能体协同平台 · GOAI Agent Infra 赛道

## 与 4-Agent 版的区别

| | 4-Agent 版（v1） | 3-Agent 版（v2·当前） |
|------|-----------|-------------------|
| Agent | Aggregator / Analyzer / Disposition / Auditor | **RiskDetective** / Disposition / Auditor |
| Pipeline | 4 步（聚合→分析→处置→审计） | **3 步**（感知→处置→审计） |
| 核心变化 | 聚合和分析独立 | RiskDetective 内聚聚合+分析，减少编排开销 ~25% |
| Skill/MCP | 6 Skill + 4 MCP | 相同（共用） |
| 测试 | 9 个 | 3 个（全通过） |

## 快速运行

```bash
pip install -r requirements.txt
python main.py --input examples/sample_input_fraud.json
```

## 运行证据

### 欺诈检测场景

```
$ python main.py --input examples/sample_input_fraud.json

============================================================
  FinCopilot 3-Agent Pipeline
  Task: TASK-20250115-001 | Source: fraud_alert
============================================================

  状态: awaiting_approval
  聚合事件: 4 | 欺诈评分: 100
  影响面: critical (¥1,068,000)
  处置: ⚠️ 需审批!
    - freeze_account: 欺诈评分 100

============================================================
```

### 测试结果

```
$ python -m pytest tests/ -v

test_pipeline.py::Test3Agent::test_init PASSED      [ 33%]
test_pipeline.py::Test3Agent::test_pipeline PASSED   [ 66%]
test_pipeline.py::Test3Agent::test_detective PASSED  [100%]

3 passed in 0.04s ✅
```

## 目录结构

```
v2-3agent/
├── main.py                        # 入口：3 步 Pipeline
├── agents/
│   ├── orchestrator.py            # 编排器
│   ├── risk_detective.py          # 🆕 聚合+分析合并
│   ├── disposition_agent.py       # 处置执行
│   └── compliance_auditor.py      # 合规审计
├── skills/                        # 6 Skill（与 v1 共用）
├── mcp/                           # 4 MCP 连接器（与 v1 共用）
├── config/
│   └── agents.yaml                # 3 Agent Identity 清单
├── examples/                      # 2 套样例数据
├── tests/                         # 3 测试用例 ✅
└── FinCopilot初赛方案-3Agent.pptx # 19 页 PPT
```

## AgentTeams 迁移路径

当前代码在本地 Python 环境验证了 Agent 决策逻辑和 Pipeline 流程。生产迁移至 AgentTeams 后：
- 每个 Agent 作为独立容器运行于 AgentTeams Runtime
- Matrix Room 消息机制替代函数调用传递上下文
- TeamHarness 的 Task 状态机替代 TaskContext 管理状态流转
- Human-in-the-loop 审批节点变为 Matrix Room 人工实时消息确认
- Agent 决策逻辑、Skill 接口、MCP 契约均不变——迁移本质是通信层协议适配

## 开源协议

Apache 2.0 · GitHub: github.com/1Adalt/finco-pilot

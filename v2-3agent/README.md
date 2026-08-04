# FinCopilot 3-Agent 精简版 🚀

金融风控与理赔多智能体协同平台 · GOAI Agent Infra 赛道

## 与 4-Agent 版的区别

| | 4-Agent 版 | 3-Agent 版（本版） |
|------|-----------|-------------------|
| Agent | Aggregator/Analyzer/Disposition/Auditor | Detective/Disposition/Auditor |
| Pipeline | 4 步 | 3 步 |
| 核心变化 | 聚合和分析独立 | RiskDetective 内聚聚合+分析 |
| Skill/MCP | 6 Skill + 4 MCP | 相同（共用） |

## 快速运行

```bash
pip install -r requirements.txt
python main.py --input examples/sample_input_fraud.json
python -m pytest tests/ -v
```

## 目录

```
finco-pilot/
├── main.py
├── config/agents.yaml
├── agents/
│   ├── orchestrator.py
│   ├── risk_detective.py      ← 新：合并聚合+分析
│   ├── disposition_agent.py
│   └── compliance_auditor.py
├── skills/ (6 Skill)
├── mcp/    (4 MCP)
├── examples/
└── tests/
```

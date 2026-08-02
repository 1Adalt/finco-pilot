"""
FinCopilot 测试用例
验证多 Agent Pipeline 端到端流程
"""
import pytest
import asyncio
import json
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from agents.orchestrator import FinCopilotOrchestrator, TaskStatus


# 加载配置
def load_settings():
    import yaml
    settings = {
        "pipeline": {
            "stages": [
                {"stage": "aggregation", "agent": "risk_aggregator", "skills": ["signal_aggregation"], "timeout": 60},
                {"stage": "analysis", "agent": "risk_analyzer", "skills": ["fraud_detection", "claim_assessment"], "timeout": 120},
                {"stage": "disposition", "agent": "disposition_agent", "skills": ["disposition_executor"], "timeout": 180},
                {"stage": "audit", "agent": "compliance_auditor", "skills": ["compliance_audit", "case_review"], "timeout": 90},
            ]
        },
        "approval": {
            "large_payment_threshold": 50000,
            "require_approval_actions": ["freeze_account", "claim_denial", "large_payment"],
        },
        "rag": {"enabled": True},
    }
    return settings


@pytest.fixture
def orchestrator():
    return FinCopilotOrchestrator(load_settings())


@pytest.fixture
def fraud_input():
    path = os.path.join(PROJECT_ROOT, "examples", "sample_input_fraud.json")
    with open(path, "r") as f:
        return json.load(f)


@pytest.fixture
def claim_input():
    path = os.path.join(PROJECT_ROOT, "examples", "sample_input_claim.json")
    with open(path, "r") as f:
        return json.load(f)


class TestPipeline:
    """测试完整 Pipeline"""

    def test_orchestrator_init(self, orchestrator):
        """测试编排器初始化"""
        assert orchestrator is not None
        assert len(orchestrator.pipeline) == 4

    def test_fraud_pipeline(self, orchestrator, fraud_input):
        """测试欺诈检测 Pipeline"""
        ctx = asyncio.run(orchestrator.run(fraud_input))

        # 聚合阶段应有事件
        assert len(ctx.aggregated_events) > 0, "应聚合到风险事件"

        # 分析阶段应有报告
        assert ctx.analysis_report is not None, "应有分析报告"
        fraud_score = ctx.analysis_report["fraud_result"]["score"]
        assert fraud_score > 50, f"欺诈评分应较高，实际: {fraud_score}"

        # 高风险 → 应触发审批
        assert ctx.status == TaskStatus.AWAITING_APPROVAL, \
            f"高风险应触发审批，实际状态: {ctx.status}"

    def test_claim_pipeline(self, orchestrator, claim_input):
        """测试理赔 Pipeline"""
        ctx = asyncio.run(orchestrator.run(claim_input))

        # 聚合阶段
        assert len(ctx.aggregated_events) > 0

        # 分析报告应包含影响评估
        assert ctx.analysis_report is not None
        impact = ctx.analysis_report.get("impact_assessment", {})
        assert "level" in impact

    def test_pipeline_stages_order(self, orchestrator, fraud_input):
        """测试 Pipeline 阶段顺序"""
        ctx = asyncio.run(orchestrator.run(fraud_input))

        stages_completed = []
        if ctx.aggregated_events:
            stages_completed.append("aggregation")
        if ctx.analysis_report:
            stages_completed.append("analysis")
        if ctx.disposition_result:
            stages_completed.append("disposition")

        assert stages_completed == ["aggregation", "analysis", "disposition"], \
            f"阶段顺序错误: {stages_completed}"


class TestAgents:
    """测试各 Agent 独立功能"""

    def test_risk_aggregator(self):
        from agents.risk_aggregator import RiskAggregatorAgent
        from agents.orchestrator import TaskContext

        agent = RiskAggregatorAgent(load_settings())
        ctx = TaskContext(task_id="test-001", source="fraud_alert", raw_input={
            "account_id": "ACC-123",
            "entity_id": "ENT-456",
            "entity_name": "Test Corp",
        })

        ctx = asyncio.run(agent.process(ctx))
        assert len(ctx.aggregated_events) >= 2

    def test_risk_analyzer(self):
        from agents.risk_analyzer import RiskAnalyzerAgent
        from agents.risk_aggregator import RiskAggregatorAgent
        from agents.orchestrator import TaskContext

        settings = load_settings()
        ctx = TaskContext(task_id="test-002", source="fraud_alert", raw_input={
            "account_id": "ACC-123",
            "entity_id": "ENT-456",
        })

        # 先聚合
        agg = RiskAggregatorAgent(settings)
        ctx = asyncio.run(agg.process(ctx))

        # 再分析
        analyzer = RiskAnalyzerAgent(settings)
        ctx = asyncio.run(analyzer.process(ctx))

        assert ctx.analysis_report is not None
        assert "fraud_result" in ctx.analysis_report


class TestSkills:
    """测试 Skill 模块"""

    def test_signal_aggregation(self):
        from skills.signal_aggregation import SignalAggregationSkill

        skill = SignalAggregationSkill()
        result = asyncio.run(skill.run(sources=[
            {"source": "tx_system", "raw": {"amount": 1000}, "timestamp": "2025-01-15T10:00:00Z"},
            {"source": "credit_system", "raw": {"score": 420}, "timestamp": "2025-01-15T10:00:00Z"},
        ]))

        assert result.success
        assert result.data["total"] == 2

    def test_fraud_detection(self):
        from skills.fraud_detection import FraudDetectionSkill

        skill = FraudDetectionSkill()
        result = asyncio.run(skill.execute(
            risk_event={"event_id": "EVT-001", "source": "credit_system"},
            detection_rules=[
                {"field": "credit_system", "weight": 30, "name": "征信异常"},
            ],
        ))

        assert result.success
        assert result.data["fraud_score"] > 0

    def test_claim_assessment(self):
        from skills.claim_assessment import ClaimAssessmentSkill

        skill = ClaimAssessmentSkill()
        result = asyncio.run(skill.execute(
            claim_request={"claim_type": "car", "amount": 30000},
            policy_data={"coverage_amount": 100000},
        ))

        assert result.success
        assert result.data["result"] == "approved"

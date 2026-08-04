"""3-Agent 版测试"""
import pytest, asyncio, json, sys, os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
from agents.orchestrator import FinCopilotOrchestrator, TaskStatus

SETTINGS = {"approval": {"large_payment_threshold": 50000,
    "require_approval_actions": ["freeze_account", "claim_denial", "large_payment"]}}

@pytest.fixture
def orch(): return FinCopilotOrchestrator(SETTINGS)

@pytest.fixture
def fraud_input():
    with open(os.path.join(PROJECT_ROOT, "examples", "sample_input_fraud.json")) as f:
        return json.load(f)

class Test3Agent:
    def test_init(self, orch): assert orch is not None

    def test_pipeline(self, orch, fraud_input):
        ctx = asyncio.run(orch.run(fraud_input))
        assert ctx.detection_report is not None
        assert ctx.detection_report["fraud_result"]["score"] > 50
        assert ctx.status in (TaskStatus.AWAITING_APPROVAL, TaskStatus.COMPLETED)

    def test_detective(self, fraud_input):
        from agents.risk_detective import RiskDetectiveAgent
        from agents.orchestrator import TaskContext
        ctx = TaskContext(task_id="t1", source="fraud", raw_input=fraud_input)
        ctx = asyncio.run(RiskDetectiveAgent(SETTINGS).process(ctx))
        assert ctx.detection_report is not None
        assert len(ctx.detection_report["events"]) >= 3

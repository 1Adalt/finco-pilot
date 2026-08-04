"""
FinCopilot 3-Agent 主控编排器
Pipeline: RiskDetective → DispositionAgent → ComplianceAuditor
"""
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TaskContext:
    task_id: str
    source: str
    raw_input: dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    detection_report: Optional[dict] = None     # RiskDetective 输出
    disposition_result: Optional[dict] = None   # DispositionAgent 输出
    audit_report: Optional[dict] = None         # ComplianceAuditor 输出

class FinCopilotOrchestrator:
    """3-Agent Pipeline 编排器"""

    def __init__(self, settings: dict):
        self.settings = settings
        self.approval_config = settings.get("approval", {})

    async def run(self, task_input: dict) -> TaskContext:
        ctx = TaskContext(
            task_id=task_input.get("id", "unknown"),
            source=task_input.get("source", "unknown"),
            raw_input=task_input,
        )
        logger.info("3-Agent Pipeline started: %s", ctx.task_id)

        try:
            # Stage 1: 风险感知（聚合+分析）
            from agents.risk_detective import RiskDetectiveAgent
            ctx = await RiskDetectiveAgent(self.settings).process(ctx)

            # Stage 2: 处置执行
            from agents.disposition_agent import DispositionAgent
            ctx = await DispositionAgent(self.settings).process(ctx)

            if ctx.status == TaskStatus.AWAITING_APPROVAL:
                return ctx

            # Stage 3: 合规审计
            from agents.compliance_auditor import ComplianceAuditorAgent
            ctx = await ComplianceAuditorAgent(self.settings).process(ctx)

            ctx.status = TaskStatus.COMPLETED
        except Exception as e:
            ctx.status = TaskStatus.FAILED
            logger.error("Pipeline failed: %s", e)

        return ctx

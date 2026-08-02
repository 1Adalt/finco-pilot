"""
FinCopilot 主控编排器
基于 AgentTeams 框架，负责角色编排、任务拆解、上下文传递与状态追踪
"""
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    AGGREGATION = "aggregation"
    ANALYSIS = "analysis"
    DISPOSITION = "disposition"
    AUDIT = "audit"


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class TaskContext:
    """任务上下文——在 Agent 之间传递"""
    task_id: str
    source: str                          # 任务来源（tx_alert / claim_request / manual）
    raw_input: dict[str, Any]            # 原始输入
    stage: PipelineStage = PipelineStage.AGGREGATION
    status: TaskStatus = TaskStatus.PENDING

    # 各阶段产出
    aggregated_events: list[dict] = field(default_factory=list)
    analysis_report: Optional[dict] = None
    disposition_result: Optional[dict] = None
    audit_report: Optional[dict] = None

    # 元信息
    trace_id: str = ""
    created_at: str = ""
    updated_at: str = ""


class FinCopilotOrchestrator:
    """
    FinCopilot 主控编排器

    使用 AgentTeams 框架进行多 Agent 协同编排：
    1. 接收任务输入 → 创建 TaskContext
    2. 按 Pipeline 阶段依次调度 Agent
    3. 管理上下文传递与状态流转
    4. 处理异常分支与审批节点
    """

    def __init__(self, settings: dict):
        self.settings = settings
        self.pipeline = settings.get("pipeline", {}).get("stages", [])
        self.approval_config = settings.get("approval", {})
        logger.info("FinCopilot Orchestrator initialized with %d pipeline stages",
                     len(self.pipeline))

    async def run(self, task_input: dict) -> TaskContext:
        """
        主入口：运行完整的端到端 Pipeline

        Args:
            task_input: 原始任务输入，格式取决于来源（告警/理赔/手动）

        Returns:
            TaskContext: 包含全链路执行结果的上下文
        """
        ctx = TaskContext(
            task_id=task_input.get("id", "unknown"),
            source=task_input.get("source", "unknown"),
            raw_input=task_input,
        )
        logger.info("Pipeline started: task_id=%s, source=%s", ctx.task_id, ctx.source)

        try:
            # Stage 1: 信号聚合
            ctx = await self._run_aggregation(ctx)

            # Stage 2: 风险分析
            ctx = await self._run_analysis(ctx)

            # Stage 3: 处置执行（可能触发审批）
            ctx = await self._run_disposition(ctx)

            # 审批检查
            if ctx.status == TaskStatus.AWAITING_APPROVAL:
                logger.info("Task %s awaiting human approval", ctx.task_id)
                return ctx

            # Stage 4: 合规审计
            ctx = await self._run_audit(ctx)

            ctx.status = TaskStatus.COMPLETED
            logger.info("Pipeline completed: task_id=%s", ctx.task_id)

        except Exception as e:
            ctx.status = TaskStatus.FAILED
            logger.error("Pipeline failed: task_id=%s, error=%s", ctx.task_id, e)

        return ctx

    async def _run_aggregation(self, ctx: TaskContext) -> TaskContext:
        """Stage 1: 风险信号聚合"""
        ctx.stage = PipelineStage.AGGREGATION
        ctx.status = TaskStatus.IN_PROGRESS
        logger.info("[Stage 1/4] Aggregating risk signals...")

        from agents.risk_aggregator import RiskAggregatorAgent
        agent = RiskAggregatorAgent(self.settings)
        ctx = await agent.process(ctx)
        return ctx

    async def _run_analysis(self, ctx: TaskContext) -> TaskContext:
        """Stage 2: 风险分析"""
        ctx.stage = PipelineStage.ANALYSIS
        ctx.status = TaskStatus.IN_PROGRESS
        logger.info("[Stage 2/4] Analyzing risks...")

        from agents.risk_analyzer import RiskAnalyzerAgent
        agent = RiskAnalyzerAgent(self.settings)
        ctx = await agent.process(ctx)
        return ctx

    async def _run_disposition(self, ctx: TaskContext) -> TaskContext:
        """Stage 3: 处置执行"""
        ctx.stage = PipelineStage.DISPOSITION
        ctx.status = TaskStatus.IN_PROGRESS
        logger.info("[Stage 3/4] Executing disposition...")

        from agents.disposition_agent import DispositionAgent
        agent = DispositionAgent(self.settings)
        ctx = await agent.process(ctx)

        # 高风险检查
        if ctx.disposition_result and ctx.disposition_result.get("approval_required"):
            ctx.status = TaskStatus.AWAITING_APPROVAL
            logger.warning("Task %s requires human approval!", ctx.task_id)

        return ctx

    async def _run_audit(self, ctx: TaskContext) -> TaskContext:
        """Stage 4: 合规审计"""
        ctx.stage = PipelineStage.AUDIT
        ctx.status = TaskStatus.IN_PROGRESS
        logger.info("[Stage 4/4] Auditing and archiving...")

        from agents.compliance_auditor import ComplianceAuditorAgent
        agent = ComplianceAuditorAgent(self.settings)
        ctx = await agent.process(ctx)
        return ctx

"""
DispositionAgent — 处置方案生成与执行

职责：
- 根据分析报告生成处置方案
- 限额内自动执行，高风险升级审批
- 记录回滚凭证，支持撤销
"""
import logging
from agents.orchestrator import TaskContext, TaskStatus

logger = logging.getLogger(__name__)

APPROVAL_THRESHOLD = 50000  # 自动执行金额上限


class DispositionAgent:
    """
    处置执行 Agent

    接收 RiskAnalyzer 的处置建议，生成具体执行方案。
    高风险动作自动推至人工审批队列。
    """

    def __init__(self, settings: dict):
        self.settings = settings
        self.agent_name = "DispositionAgent"
        self.approval_config = settings.get("approval", {})
        self.threshold = self.approval_config.get(
            "large_payment_threshold", APPROVAL_THRESHOLD
        )
        logger.info("%s initialized (auto threshold: ¥%s)",
                     self.agent_name, self.threshold)

    async def process(self, ctx: TaskContext) -> TaskContext:
        """执行处置流程"""
        logger.info("[%s] Processing task %s", self.agent_name, ctx.task_id)

        recommendations = ctx.analysis_report.get(
            "disposition_recommendations", []) if ctx.analysis_report else []

        # 生成处置方案
        plan = self._generate_plan(recommendations)

        # 检查是否需要审批
        approval_required = self._check_approval(plan, ctx)

        if approval_required:
            logger.warning("[%s] Task %s requires HUMAN APPROVAL",
                           self.agent_name, ctx.task_id)
            ctx.disposition_result = {
                "plan": plan,
                "approval_required": True,
                "approval_items": self._get_approval_items(plan),
                "executed": [],
                "message": "高风险操作已提交人工审批",
            }
            ctx.status = TaskStatus.AWAITING_APPROVAL
        else:
            # 自动执行
            results = self._execute_plan(plan)
            ctx.disposition_result = {
                "plan": plan,
                "approval_required": False,
                "executed": results,
                "message": f"已自动执行 {len(results)} 项操作",
            }

        return ctx

    def _generate_plan(self, recommendations: list[dict]) -> dict:
        """根据建议生成操作计划"""
        steps = []
        for i, rec in enumerate(recommendations):
            step = {
                "step_id": f"STEP-{i+1:03d}",
                "action": rec["action"],
                "priority": rec["priority"],
                "reason": rec["reason"],
                "auto_execute": rec.get("auto_execute", True),
                "rollback_token": f"RB-{rec['action']}-{i+1:03d}",
            }
            steps.append(step)

        return {
            "plan_id": f"PLAN-{hash(str(recommendations)):08x}",
            "total_steps": len(steps),
            "steps": steps,
        }

    def _check_approval(self, plan: dict, ctx: TaskContext) -> bool:
        """
        审批检查：
        - 涉及 account_freeze 的操作
        - 涉及 claim_denial 的操作
        - 大额赔付（> ¥50,000）
        """
        approval_actions = self.approval_config.get(
            "require_approval_actions", []
        )

        for step in plan.get("steps", []):
            action = step.get("action", "")
            if action in approval_actions:
                return True

        # 检查金额
        impact = (ctx.analysis_report or {}).get("impact_assessment", {})
        if impact.get("estimated_loss", 0) > self.threshold:
            return True

        return False

    def _get_approval_items(self, plan: dict) -> list[dict]:
        """列出需要审批的具体项"""
        approval_actions = self.approval_config.get(
            "require_approval_actions", []
        )
        items = []
        for step in plan.get("steps", []):
            if step["action"] in approval_actions:
                items.append({
                    "step_id": step["step_id"],
                    "action": step["action"],
                    "reason": step["reason"],
                    "status": "pending_approval",
                })
        return items

    def _execute_plan(self, plan: dict) -> list[dict]:
        """执行操作计划（模拟）"""
        results = []
        for step in plan.get("steps", []):
            if step.get("auto_execute", True):
                results.append({
                    "step_id": step["step_id"],
                    "action": step["action"],
                    "status": "success",
                    "rollback_token": step["rollback_token"],
                    "executed_at": "2025-01-15T10:30:00Z",
                })
            else:
                results.append({
                    "step_id": step["step_id"],
                    "action": step["action"],
                    "status": "skipped",
                    "reason": "manual_approval_required",
                })
        return results


async def execute_rollback(disposition_result: dict) -> list[dict]:
    """
    回滚操作
    按执行顺序逆序回滚，基于 rollback_token
    """
    rollback_results = []
    executed = disposition_result.get("executed", [])
    for step in reversed(executed):
        if step.get("status") == "success":
            rollback_results.append({
                "step_id": step["step_id"],
                "rollback_token": step["rollback_token"],
                "status": "rolled_back",
            })
    return rollback_results

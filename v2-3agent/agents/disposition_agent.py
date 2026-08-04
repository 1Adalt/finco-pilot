"""DispositionAgent — 3-Agent 版"""
import logging
from agents.orchestrator import TaskContext, TaskStatus
logger = logging.getLogger(__name__)

class DispositionAgent:
    def __init__(self, settings: dict):
        self.settings = settings
        self.agent_name = "DispositionAgent"
        self.approval_config = settings.get("approval", {})
        self.threshold = self.approval_config.get("large_payment_threshold", 50000)

    async def process(self, ctx: TaskContext) -> TaskContext:
        logger.info("[%s] Processing %s", self.agent_name, ctx.task_id)
        recs = (ctx.detection_report or {}).get("recommendations", [])
        plan = self._gen_plan(recs)
        needs_approval = self._check(plan, ctx)

        if needs_approval:
            ctx.disposition_result = {"plan": plan, "approval_required": True,
                "approval_items": [{"step_id": s["step_id"], "action": s["action"],
                    "reason": s["reason"], "status": "pending_approval"}
                    for s in plan["steps"] if s["action"] in self.approval_config.get("require_approval_actions", [])],
                "executed": [], "message": "高风险操作已提交人工审批"}
            ctx.status = TaskStatus.AWAITING_APPROVAL
        else:
            ctx.disposition_result = {"plan": plan, "approval_required": False,
                "executed": [{"step_id": s["step_id"], "action": s["action"], "status": "success",
                    "rollback_token": s["rollback_token"]} for s in plan["steps"] if s.get("auto_execute", True)],
                "message": "已自动执行"}
        return ctx

    def _gen_plan(self, recs): return {"plan_id": f"PLAN-{hash(str(recs)):08x}", "total_steps": len(recs),
        "steps": [{"step_id": f"STEP-{i+1:03d}", "action": r["action"], "priority": r["priority"],
            "reason": r.get("reason",""), "auto_execute": r.get("auto_execute", True),
            "rollback_token": f"RB-{r['action']}-{i+1:03d}"} for i, r in enumerate(recs)]}

    def _check(self, plan, ctx):
        for s in plan["steps"]:
            if s["action"] in self.approval_config.get("require_approval_actions", []): return True
        impact = (ctx.detection_report or {}).get("impact_assessment", {})
        if impact.get("estimated_loss", 0) > self.threshold: return True
        return False

"""
disposition_executor Skill — 处置执行器
"""
from skills.base import BaseSkill, SkillResult


class DispositionExecutorSkill(BaseSkill):
    """处置方案执行与回滚"""

    def __init__(self):
        super().__init__("disposition_executor", "1.0.0")

    async def execute(self, disposition_plan: dict = None,
                      auth_context: dict = None,
                      **kwargs) -> SkillResult:
        if not disposition_plan:
            return SkillResult(success=False, error="no disposition_plan")

        results = []
        for step in disposition_plan.get("steps", []):
            action = step.get("action", "")

            # 审批检查
            if action in ("freeze_account", "large_payment"):
                if not auth_context or not auth_context.get("approved"):
                    results.append({
                        "step_id": step["step_id"],
                        "status": "awaiting_approval",
                        "action": action,
                    })
                    continue

            # 执行
            results.append({
                "step_id": step["step_id"],
                "action": action,
                "status": "success",
                "rollback_token": f"RB-{step['step_id']}",
            })

        return SkillResult(success=True, data={"results": results})

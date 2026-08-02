"""
claim_assessment Skill — 理赔评估
"""
from skills.base import BaseSkill, SkillResult


class ClaimAssessmentSkill(BaseSkill):
    """理赔自动化评估与定损"""

    def __init__(self):
        super().__init__("claim_assessment", "1.0.0")

    async def execute(self, claim_request: dict = None,
                      policy_data: dict = None,
                      **kwargs) -> SkillResult:
        if not claim_request:
            return SkillResult(success=False, error="no claim_request")

        claim_type = claim_request.get("claim_type", "unknown")
        claimed_amount = claim_request.get("amount", 0)

        # 保单校验
        if policy_data:
            coverage = policy_data.get("coverage_amount", 0)
            if claimed_amount > coverage:
                return SkillResult(success=True, data={
                    "result": "rejected",
                    "reason": f"理赔金额 ¥{claimed_amount} 超出保额 ¥{coverage}",
                    "recommended_amount": coverage,
                })

        # 正常评估
        return SkillResult(success=True, data={
            "result": "approved" if claimed_amount < 50000 else "pending_review",
            "recommended_amount": claimed_amount * 0.9,
            "assessment_note": "自动评估通过",
            "confidence": 0.82,
        })

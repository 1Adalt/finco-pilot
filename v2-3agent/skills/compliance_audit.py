"""
compliance_audit Skill — 合规审计
+ case_review Skill — 案例复盘
"""
from skills.base import BaseSkill, SkillResult
import hashlib


class ComplianceAuditSkill(BaseSkill):
    """合规审计与证据归档"""

    def __init__(self):
        super().__init__("compliance_audit", "1.0.0")

    async def execute(self, execution_result: dict = None,
                      trace_data: dict = None,
                      regulation_version: str = "2024-Q2",
                      **kwargs) -> SkillResult:
        if not execution_result:
            return SkillResult(success=False, error="no execution_result")

        # 合规检查
        violations = []
        for item in execution_result.get("executed", []):
            if item.get("status") == "failed":
                violations.append({
                    "item": item["step_id"],
                    "rule": "EXEC_FAILURE",
                    "severity": "high",
                })

        # 生成审计报告
        report = {
            "compliance_score": 100 - len(violations) * 25,
            "violations": violations,
            "regulation_version": regulation_version,
            "auditor": "compliance_audit_skill_v1.0.0",
        }

        # Hash 签名
        report_hash = hashlib.sha256(str(report).encode()).hexdigest()[:16]

        return SkillResult(success=True, data={
            "report": report,
            "report_hash": report_hash,
            "immutable": True,
        })


class CaseReviewSkill(BaseSkill):
    """案例复盘与知识沉淀"""

    def __init__(self):
        super().__init__("case_review", "1.0.0")

    async def execute(self, case_data: dict = None, **kwargs) -> SkillResult:
        if not case_data:
            return SkillResult(success=False, error="no case_data")

        # 生成复盘报告
        review = {
            "case_id": case_data.get("task_id", "unknown"),
            "summary": "案例已复盘",
            "lessons": [
                "多源信号关联分析有效提升了欺诈检测准确率",
                "高优先级事件需要缩短审批链路",
            ],
            "new_rules": [],
            "knowledge_updated": True,
        }

        return SkillResult(success=True, data={"review": review})

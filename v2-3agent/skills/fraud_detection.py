"""
fraud_detection Skill — 欺诈检测引擎
"""
from skills.base import BaseSkill, SkillResult


class FraudDetectionSkill(BaseSkill):
    """欺诈模式匹配与风险评分"""

    def __init__(self):
        super().__init__("fraud_detection", "1.0.0")

    async def execute(self, risk_event: dict = None,
                      history_cases: list = None,
                      detection_rules: list = None,
                      **kwargs) -> SkillResult:
        if not risk_event:
            return SkillResult(success=False, error="no risk_event provided")

        score = 0.0
        matched = []

        # 1. 规则引擎
        if detection_rules:
            for rule in detection_rules:
                if self._match_rule(risk_event, rule):
                    matched.append(rule)
                    score += rule.get("weight", 10)

        # 2. RAG 历史案例匹配
        if history_cases:
            for case in history_cases:
                similarity = self._case_similarity(risk_event, case)
                if similarity > 0.7:
                    matched.append({
                        "type": "historical_match",
                        "case_id": case.get("id"),
                        "similarity": similarity,
                    })
                    score += 15 * similarity

        # 3. 综合评分
        score = min(score, 100)

        return SkillResult(success=True, data={
            "fraud_score": score,
            "level": "high" if score > 60 else ("medium" if score > 30 else "low"),
            "matched_patterns": matched,
            "confidence": 0.85 if matched else 0.5,
        })

    def _match_rule(self, event, rule) -> bool:
        return rule.get("field", "") in str(event)

    def _case_similarity(self, event, case) -> float:
        # 简化：生产环境用向量相似度
        return 0.65

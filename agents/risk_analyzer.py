"""
RiskAnalyzer Agent — 根因定位与欺诈检测

职责：
- 多维度关联分析（时间/实体/交易图谱）
- 欺诈模式匹配（RAG 检索 + 规则 + LLM 推理）
- 影响面量化评估
- 生成根因报告与处置建议
"""
import logging
from agents.orchestrator import TaskContext

logger = logging.getLogger(__name__)


class RiskAnalyzerAgent:
    """
    风险分析 Agent

    接收 RiskAggregator 输出的标准化事件，进行深度分析，
    输出根因报告、欺诈评分和处置建议。
    """

    def __init__(self, settings: dict):
        self.settings = settings
        self.agent_name = "RiskAnalyzer"
        self.rag_config = settings.get("rag", {})
        logger.info("%s initialized", self.agent_name)

    async def process(self, ctx: TaskContext) -> TaskContext:
        """执行风险分析流程"""
        logger.info("[%s] Analyzing task %s", self.agent_name, ctx.task_id)

        events = ctx.aggregated_events
        if not events:
            logger.warning("[%s] No events to analyze", self.agent_name)
            return ctx

        # Step 1: 多维度关联分析
        correlation = await self._correlate(events, ctx)

        # Step 2: 欺诈检测
        fraud_result = await self._detect_fraud(events, correlation, ctx)

        # Step 3: 影响面评估
        impact = self._assess_impact(events, fraud_result)

        # Step 4: 生成处置建议
        recommendations = self._generate_recommendations(fraud_result, impact)

        # 汇总分析报告
        ctx.analysis_report = {
            "correlation": correlation,
            "fraud_result": fraud_result,
            "impact_assessment": impact,
            "disposition_recommendations": recommendations,
        }

        logger.info("[%s] Analysis complete: fraud_score=%.1f, impact_level=%s",
                     self.agent_name, fraud_result.get("score", 0), impact.get("level"))

        return ctx

    async def _correlate(self, events: list[dict], ctx: TaskContext) -> dict:
        """
        多维度关联分析：
        - 时间维度：事件时间线
        - 实体维度：关联账户/人员/企业
        - 交易维度：资金流向图谱
        """
        correlation = {
            "timeline": [],
            "related_entities": set(),
            "total_events": len(events),
            "high_severity_count": sum(1 for e in events if e.get("severity") in ("S0", "S1")),
        }

        for event in events:
            correlation["timeline"].append({
                "event_id": event["event_id"],
                "timestamp": event["timestamp"],
                "source": event["source"],
                "severity": event["severity"],
            })

            # 提取关联实体
            data = event.get("data", {})
            for key in ("account_id", "entity_id", "entity_name"):
                if key in data:
                    correlation["related_entities"].add(str(data[key]))

        correlation["related_entities"] = list(correlation["related_entities"])
        return correlation

    async def _detect_fraud(self, events: list[dict],
                            correlation: dict, ctx: TaskContext) -> dict:
        """
        欺诈检测——三层递进：
        1. 规则引擎初筛
        2. RAG 历史案例匹配（模拟）
        3. LLM 推理分析（模拟）
        """
        # 规则引擎
        rule_matches = []
        for event in events:
            if event.get("severity") in ("S0", "S1"):
                rule_matches.append({
                    "rule": "HIGH_SEVERITY_MULTI_SOURCE",
                    "event_id": event["event_id"],
                    "confidence": 0.85,
                })

        # RAG 检索（模拟：基于关联实体数判断）
        entity_count = len(correlation.get("related_entities", []))
        rag_matches = []
        if entity_count >= 3:
            rag_matches.append({
                "case_id": "CASE-2024-0032",
                "similarity": 0.78,
                "pattern": "团伙欺诈_多账户协同",
            })

        # 综合评分
        base_score = 0.0
        if rule_matches:
            base_score += 30
        if rag_matches:
            base_score += 25
        if correlation.get("high_severity_count", 0) >= 2:
            base_score += 20
        base_score += min(entity_count * 5, 25)

        return {
            "score": min(base_score, 100),
            "level": "high" if base_score > 60 else ("medium" if base_score > 30 else "low"),
            "rule_matches": rule_matches,
            "rag_matches": rag_matches,
            "analysis": f"多源信号共现，{entity_count} 个关联实体，"
                        f"命中 {len(rule_matches)} 条规则、{len(rag_matches)} 个历史案例",
        }

    def _assess_impact(self, events: list[dict], fraud_result: dict) -> dict:
        """影响面评估"""
        total_tx_amount = 0
        for event in events:
            data = event.get("data", {})
            for tx in data.get("transactions", []):
                total_tx_amount += tx.get("amount", 0)

        level = "critical" if total_tx_amount > 100000 else \
                ("high" if total_tx_amount > 50000 else \
                 ("medium" if total_tx_amount > 10000 else "low"))

        return {
            "level": level,
            "estimated_loss": total_tx_amount,
            "affected_accounts": len(events),
            "affected_systems": list(set(e["source"] for e in events)),
        }

    def _generate_recommendations(self, fraud_result: dict,
                                  impact: dict) -> list[dict]:
        """生成处置建议"""
        recommendations = []
        score = fraud_result.get("score", 0)

        if score > 60:
            recommendations.append({
                "action": "freeze_account",
                "priority": "S0",
                "reason": f"欺诈评分 {score}，建议立即冻结",
                "auto_execute": False,  # 需审批
            })
        if impact.get("level") in ("critical", "high"):
            recommendations.append({
                "action": "flag_for_review",
                "priority": "S1",
                "reason": f"影响面 {impact['level']}，预估损失 ¥{impact['estimated_loss']:,}",
                "auto_execute": True,
            })
        if fraud_result.get("rag_matches"):
            recommendations.append({
                "action": "update_fraud_rules",
                "priority": "S2",
                "reason": "匹配到历史案例，建议更新检测规则",
                "auto_execute": True,
            })
        if not recommendations:
            recommendations.append({
                "action": "monitor",
                "priority": "S3",
                "reason": "低风险，持续监控",
                "auto_execute": True,
            })

        return recommendations

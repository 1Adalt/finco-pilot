"""
RiskDetective Agent — 信号聚合 + 欺诈检测 + 影响面评估
合并 4-Agent 版的 RiskAggregator + RiskAnalyzer
"""
import logging
from agents.orchestrator import TaskContext

logger = logging.getLogger(__name__)


class RiskDetectiveAgent:
    """风险感知 Agent——合二为一，信号入、判断出"""

    def __init__(self, settings: dict):
        self.settings = settings
        self.agent_name = "RiskDetective"

    async def process(self, ctx: TaskContext) -> TaskContext:
        logger.info("[%s] Processing %s", self.agent_name, ctx.task_id)

        # 1. 信号聚合
        events = await self._aggregate(ctx.raw_input)

        # 2. 欺诈检测
        fraud = self._detect(events, ctx)

        # 3. 影响面评估
        impact = self._assess(events)

        # 4. 处置建议
        recs = self._recommend(fraud, impact)

        ctx.detection_report = {
            "events": events,
            "fraud_result": fraud,
            "impact_assessment": impact,
            "recommendations": recs,
        }
        logger.info("[%s] Done: fraud=%.1f, impact=%s, events=%d",
                     self.agent_name, fraud["score"], impact["level"], len(events))
        return ctx

    async def _aggregate(self, raw: dict) -> list[dict]:
        events = []
        sources = {
            "account_id": ("tx_system", "abnormal_transaction", "S1"),
            "entity_id": ("credit_system", "fraud_alert", "S0"),
            "entity_name": ("sentiment_api", "negative_sentiment", "S2"),
        }
        for key, (src, etype, sev) in sources.items():
            if key in raw:
                events.append({
                    "event_id": f"EVT-{len(events)+1:04d}",
                    "source": src, "event_type": etype,
                    "severity": sev, "priority": int(sev[1]),
                    "data": raw, "timestamp": raw.get("timestamp", ""),
                })
        if "complaints" in raw:
            events.append({
                "event_id": f"EVT-{len(events)+1:04d}",
                "source": "complaint_system", "event_type": "customer_complaint",
                "severity": "S3", "priority": 3,
                "data": raw, "timestamp": raw.get("timestamp", ""),
            })
        events.sort(key=lambda e: e["priority"])
        return events

    def _detect(self, events: list, ctx) -> dict:
        high = sum(1 for e in events if e["severity"] in ("S0", "S1"))
        entities = set()
        tx_total = 0
        for e in events:
            data = e.get("data", {})
            for k in ("account_id", "entity_id", "entity_name"):
                if k in data:
                    entities.add(str(data[k]))
            for tx in data.get("transactions", []):
                tx_total += tx.get("amount", 0)

        score = min(high * 25 + len(entities) * 10 + (30 if tx_total > 100000 else 0), 100)
        return {
            "score": score,
            "level": "high" if score > 60 else ("medium" if score > 30 else "low"),
            "matched_rules": [{"rule": "MULTI_SOURCE_HIGH_SEVERITY", "confidence": 0.85}] if high >= 2 else [],
            "rag_matches": [{"case_id": "CASE-2024-0032", "similarity": 0.78}] if len(entities) >= 3 else [],
            "analysis": f"{len(events)} events, {len(entities)} entities, ¥{tx_total:,} at risk",
        }

    def _assess(self, events: list) -> dict:
        tx_total = 0
        for e in events:
            for tx in e.get("data", {}).get("transactions", []):
                tx_total += tx.get("amount", 0)
        return {
            "level": "critical" if tx_total > 100000 else ("high" if tx_total > 50000 else "low"),
            "estimated_loss": tx_total,
            "affected_entities": len(set(
                str(e.get("data", {}).get(k, ""))
                for e in events for k in ("account_id", "entity_id", "entity_name")
                if k in e.get("data", {})
            )),
        }

    def _recommend(self, fraud: dict, impact: dict) -> list:
        recs = []
        if fraud["score"] > 60:
            recs.append({"action": "freeze_account", "priority": "S0",
                         "reason": f"欺诈评分 {fraud['score']:.0f}", "auto_execute": False})
        if impact["level"] in ("critical", "high"):
            recs.append({"action": "flag_for_review", "priority": "S1",
                         "reason": f"影响面 {impact['level']}", "auto_execute": True})
        return recs or [{"action": "monitor", "priority": "S3", "auto_execute": True}]

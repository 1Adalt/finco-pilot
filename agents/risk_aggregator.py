"""
RiskAggregator Agent — 多源风险信号聚合与降噪

职责：
- 从交易系统、征信平台、舆情 API、投诉系统接入风险信号
- 执行去重、格式标准化、优先级分级
- 输出标准化 RiskEvent 列表
"""
import logging
from agents.orchestrator import TaskContext

logger = logging.getLogger(__name__)


class RiskAggregatorAgent:
    """
    风险聚合 Agent

    作为 Pipeline 第一道关卡，负责把分散在多系统的原始信号
    转化为统一格式的标准化风险事件。
    """

    def __init__(self, settings: dict):
        self.settings = settings
        self.agent_name = "RiskAggregator"
        logger.info("%s initialized", self.agent_name)

    async def process(self, ctx: TaskContext) -> TaskContext:
        """执行信号聚合流程"""
        logger.info("[%s] Processing task %s", self.agent_name, ctx.task_id)

        # Step 1: 从多源接入信号
        raw_signals = await self._fetch_signals(ctx)

        # Step 2: 去重
        deduped = self._deduplicate(raw_signals)

        # Step 3: 格式标准化
        standardized = self._standardize(deduped)

        # Step 4: 优先级分级
        prioritized = self._prioritize(standardized)

        # 写入上下文
        ctx.aggregated_events = prioritized
        logger.info("[%s] Aggregated %d events (from %d raw signals)",
                     self.agent_name, len(prioritized), len(raw_signals))

        return ctx

    async def _fetch_signals(self, ctx: TaskContext) -> list[dict]:
        """从多个 MCP 数据源获取原始信号"""
        signals = []
        task_input = ctx.raw_input

        # 从交易系统获取信号
        if "account_id" in task_input:
            signals.append({
                "source": "tx_system",
                "raw": {
                    "account_id": task_input["account_id"],
                    "transactions": task_input.get("transactions", []),
                },
                "timestamp": task_input.get("timestamp", ""),
            })

        # 从征信系统获取信号
        if "entity_id" in task_input:
            signals.append({
                "source": "credit_system",
                "raw": {
                    "entity_id": task_input["entity_id"],
                    "credit_data": task_input.get("credit_data", {}),
                },
                "timestamp": task_input.get("timestamp", ""),
            })

        # 从舆情系统获取信号
        if "entity_name" in task_input:
            signals.append({
                "source": "sentiment_api",
                "raw": {
                    "entity_name": task_input["entity_name"],
                    "sentiment_items": task_input.get("sentiment_items", []),
                },
                "timestamp": task_input.get("timestamp", ""),
            })

        # 从投诉系统获取信号
        if "complaints" in task_input:
            signals.append({
                "source": "complaint_system",
                "raw": {
                    "complaints": task_input["complaints"],
                },
                "timestamp": task_input.get("timestamp", ""),
            })

        return signals

    def _deduplicate(self, signals: list[dict]) -> list[dict]:
        """基于 idempotency_key 去重"""
        seen = set()
        unique = []
        for sig in signals:
            key = sig.get("source", "") + str(sig.get("timestamp", ""))
            if key not in seen:
                seen.add(key)
                unique.append(sig)
        return unique

    def _standardize(self, signals: list[dict]) -> list[dict]:
        """将异构信号转化为统一的 RiskEvent Schema"""
        events = []
        for i, sig in enumerate(signals):
            events.append({
                "event_id": f"EVT-{i+1:04d}",
                "source": sig["source"],
                "event_type": self._classify_event_type(sig),
                "severity": "unknown",  # 待优先级分级
                "data": sig["raw"],
                "timestamp": sig.get("timestamp", ""),
            })
        return events

    def _prioritize(self, events: list[dict]) -> list[dict]:
        """优先级分级：S0(紧急) / S1(高) / S2(中) / S3(低)"""
        for event in events:
            source = event.get("source", "")
            event_type = event.get("event_type", "")

            # 简单规则分级（实际场景中可配置化）
            if source == "credit_system" and event_type == "fraud_alert":
                event["severity"] = "S0"
                event["priority"] = 0
            elif source == "tx_system" and event_type == "abnormal_transaction":
                event["severity"] = "S1"
                event["priority"] = 1
            elif source == "sentiment_api":
                event["severity"] = "S2"
                event["priority"] = 2
            else:
                event["severity"] = "S3"
                event["priority"] = 3

        events.sort(key=lambda e: e["priority"])
        return events

    def _classify_event_type(self, signal: dict) -> str:
        """根据信号来源和内容分类事件类型"""
        source = signal.get("source", "")
        raw = signal.get("raw", {})

        if source == "credit_system":
            credit_score = raw.get("credit_data", {}).get("score", 700)
            return "fraud_alert" if credit_score < 500 else "credit_change"
        elif source == "tx_system":
            txs = raw.get("transactions", [])
            if any(t.get("amount", 0) > 50000 for t in txs):
                return "abnormal_transaction"
            return "transaction_report"
        elif source == "sentiment_api":
            items = raw.get("sentiment_items", [])
            if any("诈骗" in item.get("content", "") for item in items):
                return "negative_sentiment"
            return "sentiment_report"
        elif source == "complaint_system":
            return "customer_complaint"
        return "unknown"

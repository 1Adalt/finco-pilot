"""
signal_aggregation Skill — 多源信号聚合
"""
from skills.base import BaseSkill, SkillResult


class SignalAggregationSkill(BaseSkill):
    """多源风险信号聚合与降噪"""

    def __init__(self):
        super().__init__("signal_aggregation", "1.0.0")

    async def execute(self, sources: list = None,
                      time_window: int = 300,
                      filters: dict = None,
                      **kwargs) -> SkillResult:
        """
        从多源接入信号，执行去重和标准化

        Args:
            sources: 数据源列表
            time_window: 去重时间窗口（秒）
            filters: 过滤条件

        Returns:
            SkillResult: 聚合后的标准化事件列表
        """
        if not sources:
            return SkillResult(success=False, error="no sources provided")

        events = []
        for src in sources:
            source_name = src.get("source", "unknown")
            raw = src.get("raw", {})

            # 标准化
            event = {
                "source": source_name,
                "timestamp": src.get("timestamp", ""),
                "data": self._normalize(source_name, raw),
                "dedup_key": f"{source_name}:{hash(str(raw))}",
            }

            # 去重检查
            if self._is_duplicate(event, time_window):
                self.logger.debug("Duplicate event skipped: %s", event["dedup_key"])
                continue

            # 优先级
            event["priority"] = self._assign_priority(source_name, raw)
            events.append(event)

        return SkillResult(
            success=True,
            data={
                "events": events,
                "total": len(events),
                "time_window": time_window,
            },
        )

    def _normalize(self, source: str, raw: dict) -> dict:
        """格式标准化"""
        return {
            "source": source,
            "content": raw,
            "normalized_at": "2025-01-15T10:00:00Z",
        }

    def _is_duplicate(self, event: dict, window: int) -> bool:
        """去重逻辑"""
        # 简化实现：生产环境应基于 Redis/DB
        return False

    def _assign_priority(self, source: str, raw: dict) -> str:
        """优先级分级"""
        if source == "credit_system":
            score = raw.get("credit_data", {}).get("score", 700)
            return "S0" if score < 500 else "S2"
        elif source == "tx_system":
            return "S1"
        elif source == "sentiment_api":
            return "S2"
        else:
            return "S3"

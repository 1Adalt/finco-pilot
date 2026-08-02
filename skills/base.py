"""
Skill 基类 — 所有 Skill 的抽象基类
定义输入/输出契约、失败处理、安全边界
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
import logging


@dataclass
class SkillResult:
    """Skill 执行结果"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    execution_time_ms: int = 0


class BaseSkill(ABC):
    """
    所有 Skill 必须继承此基类并实现 execute() 方法

    Skill 设计原则：
    - 单一职责：一个 Skill 只完成一类任务
    - 明确契约：输入/输出 Schema 清晰
    - 可复用：不包含一次性业务逻辑
    - 可观测：记录调用参数、耗时、结果
    """

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.logger = logging.getLogger(f"skill.{name}")

    @abstractmethod
    async def execute(self, **kwargs) -> SkillResult:
        """Skill 主逻辑——子类实现"""
        ...

    async def run(self, max_retries: int = 3, **kwargs) -> SkillResult:
        """
        带重试的执行包装器
        """
        import time
        start = time.time()

        for attempt in range(max_retries + 1):
            try:
                result = await self.execute(**kwargs)
                result.retry_count = attempt
                result.execution_time_ms = int((time.time() - start) * 1000)
                self.logger.info(
                    "%s v%s completed in %dms (retries=%d)",
                    self.name, self.version,
                    result.execution_time_ms, attempt,
                )
                return result
            except Exception as e:
                self.logger.warning(
                    "%s attempt %d/%d failed: %s",
                    self.name, attempt + 1, max_retries + 1, e,
                )
                if attempt >= max_retries:
                    return SkillResult(
                        success=False,
                        error=str(e),
                        retry_count=attempt,
                        execution_time_ms=int((time.time() - start) * 1000),
                    )

        return SkillResult(success=False, error="max_retries_exceeded")

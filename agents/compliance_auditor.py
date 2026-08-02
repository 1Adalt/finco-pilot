"""
ComplianceAuditor Agent — 结果核验与合规审计

职责：
- 处置结果核验（预期 vs 实际）
- 合规规则匹配
- 审计轨迹生成
- 证据包归档
- 触发案例复盘 Skill
"""
import logging
import hashlib
from agents.orchestrator import TaskContext

logger = logging.getLogger(__name__)


class ComplianceAuditorAgent:
    """
    合规审计 Agent

    Pipeline 最后一环，确保所有处置操作合规、可追溯、可审计。
    """

    def __init__(self, settings: dict):
        self.settings = settings
        self.agent_name = "ComplianceAuditor"
        logger.info("%s initialized", self.agent_name)

    async def process(self, ctx: TaskContext) -> TaskContext:
        """执行合规审计流程"""
        logger.info("[%s] Auditing task %s", self.agent_name, ctx.task_id)

        # Step 1: 核验处置结果
        verification = await self._verify_disposition(ctx)

        # Step 2: 合规规则检查
        compliance_check = await self._check_compliance(ctx, verification)

        # Step 3: 生成审计轨迹
        audit_trail = self._generate_audit_trail(ctx)

        # Step 4: 打包证据
        evidence = self._package_evidence(ctx, audit_trail)

        # Step 5: 触发案例复盘
        await self._trigger_case_review(ctx)

        # 汇总审计报告
        ctx.audit_report = {
            "verification": verification,
            "compliance_check": compliance_check,
            "audit_trail": audit_trail,
            "evidence_package": evidence,
            "compliance_score": self._calculate_score(verification, compliance_check),
            "report_hash": self._hash_report(verification, compliance_check, audit_trail),
        }

        logger.info("[%s] Audit complete: compliance_score=%d/100",
                     self.agent_name, ctx.audit_report["compliance_score"])

        return ctx

    async def _verify_disposition(self, ctx: TaskContext) -> dict:
        """核验处置结果：比对预期 vs 实际"""
        disposition = ctx.disposition_result or {}
        executed = disposition.get("executed", [])

        success_count = sum(1 for e in executed if e.get("status") == "success")
        skipped_count = sum(1 for e in executed if e.get("status") == "skipped")
        failed_count = sum(1 for e in executed if e.get("status") == "failed")

        return {
            "verified": failed_count == 0,
            "total_actions": len(executed),
            "success": success_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "details": executed,
        }

    async def _check_compliance(self, ctx: TaskContext,
                                verification: dict) -> dict:
        """合规规则检查（模拟：基于法规库 RAG）"""
        violations = []
        warnings = []

        # 检查是否有未审批的高风险操作
        disposition = ctx.disposition_result or {}
        if disposition.get("approval_required") and verification.get("success", 0) > 0:
            violations.append({
                "rule": "CBRC-2024-003",
                "description": "高风险操作未经审批即执行",
                "severity": "critical",
            })

        # 检查审计日志完整性
        if not ctx.trace_id:
            warnings.append({
                "rule": "CBRC-2024-007",
                "description": "缺少 Trace ID，审计链路不完整",
                "severity": "warning",
            })

        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "regulation_version": "2024-Q2",
        }

    def _generate_audit_trail(self, ctx: TaskContext) -> dict:
        """生成不可篡改审计轨迹"""
        trail = {
            "task_id": ctx.task_id,
            "trace_id": ctx.trace_id,
            "pipeline_stages": [],
            "timestamp": "2025-01-15T10:30:00Z",
        }

        # 记录每个阶段
        events = ctx.aggregated_events or []
        if events:
            trail["pipeline_stages"].append({
                "stage": "aggregation",
                "event_count": len(events),
                "sources": list(set(e["source"] for e in events)),
            })

        if ctx.analysis_report:
            trail["pipeline_stages"].append({
                "stage": "analysis",
                "fraud_score": ctx.analysis_report.get("fraud_result", {}).get("score"),
            })

        if ctx.disposition_result:
            trail["pipeline_stages"].append({
                "stage": "disposition",
                "approval_required": ctx.disposition_result.get("approval_required"),
                "actions": len(ctx.disposition_result.get("executed", [])),
            })

        return trail

    def _package_evidence(self, ctx: TaskContext, trail: dict) -> dict:
        """打包审计证据"""
        return {
            "package_id": f"EVD-{ctx.task_id}",
            "contents": [
                {"type": "audit_trail", "data": trail},
                {"type": "agent_decisions", "data": {
                    "analysis_report": ctx.analysis_report,
                    "disposition_result": ctx.disposition_result,
                }},
                {"type": "compliance_report", "data": ctx.audit_report},
            ],
            "hash_algorithm": "SHA-256",
        }

    async def _trigger_case_review(self, ctx: TaskContext):
        """触发案例复盘 Skill"""
        # 在实际部署中，这里会调用 case_review Skill
        # 将完整案例数据写入知识库，供后续检索
        logger.info("[%s] Triggering case review for task %s",
                     self.agent_name, ctx.task_id)

    def _calculate_score(self, verification: dict,
                         compliance_check: dict) -> int:
        """计算合规评分"""
        score = 100
        if not verification.get("verified"):
            score -= 30
        if not compliance_check.get("passed"):
            score -= 40
        score -= len(compliance_check.get("warnings", [])) * 10
        return max(0, score)

    def _hash_report(self, verification: dict,
                     compliance_check: dict,
                     audit_trail: dict) -> str:
        """对审计报告进行 Hash 签名（不可篡改）"""
        content = f"{verification}{compliance_check}{audit_trail}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

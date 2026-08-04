"""ComplianceAuditor — 3-Agent 版"""
import logging, hashlib
from agents.orchestrator import TaskContext
logger = logging.getLogger(__name__)

class ComplianceAuditorAgent:
    def __init__(self, settings: dict):
        self.settings = settings
        self.agent_name = "ComplianceAuditor"

    async def process(self, ctx: TaskContext) -> TaskContext:
        logger.info("[%s] Auditing %s", self.agent_name, ctx.task_id)
        disp = ctx.disposition_result or {}
        execd = disp.get("executed", [])
        ok = sum(1 for e in execd if e["status"]=="success")
        fail = sum(1 for e in execd if e["status"]=="failed")
        
        violations = []
        if disp.get("approval_required") and ok > 0:
            violations.append({"rule":"CBRC-APPROVAL","desc":"高风险操作未经审批","severity":"critical"})

        score = max(0, 100 - len(violations)*30)
        report = {"verification": {"ok": fail==0, "success": ok, "failed": fail},
            "compliance": {"passed": len(violations)==0, "violations": violations},
            "compliance_score": score,
            "report_hash": hashlib.sha256(f"{disp}{score}".encode()).hexdigest()[:16]}
        
        ctx.audit_report = report
        logger.info("[%s] Score: %d/100", self.agent_name, score)
        return ctx

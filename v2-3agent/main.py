#!/usr/bin/env python3
"""FinCopilot 3-Agent 版 · 金融风控与理赔多智能体协同平台"""
import asyncio, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agents.orchestrator import FinCopilotOrchestrator

def load_settings():
    return {
        "approval": {
            "large_payment_threshold": 50000,
            "require_approval_actions": ["freeze_account", "claim_denial", "large_payment"],
        }
    }

async def main():
    orchestrator = FinCopilotOrchestrator(load_settings())
    args = sys.argv[1:]
    input_file = "examples/sample_input_fraud.json"
    for i, a in enumerate(args):
        if a == "--input" and i+1 < len(args):
            input_file = args[i+1]
    with open(input_file, "r") as f:
        task_input = json.load(f)

    print(f"\n{'='*60}")
    print(f"  FinCopilot 3-Agent Pipeline")
    print(f"  Task: {task_input['task_id']} | Source: {task_input['source']}")
    print(f"{'='*60}\n")

    ctx = await orchestrator.run(task_input)

    print(f"  状态: {ctx.status.value}")
    if ctx.detection_report:
        dr = ctx.detection_report
        print(f"  聚合事件: {len(dr['events'])} | 欺诈评分: {dr['fraud_result']['score']:.0f}")
        print(f"  影响面: {dr['impact_assessment']['level']} (¥{dr['impact_assessment']['estimated_loss']:,})")
    if ctx.disposition_result:
        d = ctx.disposition_result
        print(f"  处置: {'⚠️ 需审批!' if d.get('approval_required') else '已自动执行'}")
        if d.get("approval_items"):
            for item in d["approval_items"]:
                print(f"    - {item['action']}: {item['reason']}")
    if ctx.audit_report:
        print(f"  合规评分: {ctx.audit_report['compliance_score']}/100")
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(main())

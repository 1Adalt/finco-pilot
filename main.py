#!/usr/bin/env python3
"""
FinCopilot — 金融风控与理赔多智能体协同平台
基于 AgentTeams 框架的参赛方案 Demo

用法:
    # 欺诈检测场景
    python main.py --input examples/sample_input_fraud.json

    # 理赔评估场景
    python main.py --input examples/sample_input_claim.json

    # 运行测试
    python -m pytest tests/ -v
"""
import asyncio
import json
import sys
import os

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import FinCopilotOrchestrator, TaskStatus


def load_settings():
    """加载配置（简化版，实际部署从 config/settings.yaml 读取）"""
    try:
        import yaml
        with open("config/settings.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception:
        pass

    return {
        "pipeline": {
            "stages": [
                {"stage": "aggregation", "agent": "risk_aggregator",
                 "skills": ["signal_aggregation"], "timeout": 60},
                {"stage": "analysis", "agent": "risk_analyzer",
                 "skills": ["fraud_detection", "claim_assessment"], "timeout": 120},
                {"stage": "disposition", "agent": "disposition_agent",
                 "skills": ["disposition_executor"], "timeout": 180},
                {"stage": "audit", "agent": "compliance_auditor",
                 "skills": ["compliance_audit", "case_review"], "timeout": 90},
            ]
        },
        "approval": {
            "large_payment_threshold": 50000,
            "require_approval_actions": [
                "freeze_account", "claim_denial", "large_payment"
            ],
        },
        "rag": {"enabled": True},
    }


async def main():
    settings = load_settings()
    orchestrator = FinCopilotOrchestrator(settings)

    # 从命令行参数读取输入文件
    input_file = None
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--input" and i + 1 < len(args):
            input_file = args[i + 1]

    if not input_file:
        input_file = "examples/sample_input_fraud.json"
        print(f"ℹ️  未指定输入文件，使用默认: {input_file}")

    # 加载输入
    with open(input_file, "r") as f:
        task_input = json.load(f)

    print(f"\n{'='*60}")
    print(f"  FinCopilot · Pipeline 启动")
    print(f"  Task ID: {task_input['task_id']}")
    print(f"  Source:  {task_input['source']}")
    print(f"{'='*60}\n")

    # 运行 Pipeline
    ctx = await orchestrator.run(task_input)

    # 输出结果
    print(f"\n{'='*60}")
    print(f"  Pipeline 结果")
    print(f"{'='*60}")
    print(f"  状态: {ctx.status.value}")
    print(f"  聚合事件数: {len(ctx.aggregated_events)}")

    if ctx.analysis_report:
        ar = ctx.analysis_report
        print(f"  欺诈评分: {ar['fraud_result']['score']:.1f}")
        print(f"  欺诈等级: {ar['fraud_result']['level']}")
        print(f"  影响面: {ar['impact_assessment']['level']} "
              f"(预估 ¥{ar['impact_assessment']['estimated_loss']:,})")

    if ctx.disposition_result:
        dr = ctx.disposition_result
        print(f"  处置步骤: {len(dr.get('executed', []))} 项")
        if dr.get("approval_required"):
            print(f"  ⚠️  需要人工审批!")
            for item in dr.get("approval_items", []):
                print(f"     - {item['action']}: {item['reason']}")

    if ctx.audit_report:
        ar = ctx.audit_report
        print(f"  合规评分: {ar['compliance_score']}/100")
        print(f"  审计 Hash: {ar['report_hash']}")

    print(f"\n{'='*60}")
    print(f"  ✅ Pipeline 完成")
    print(f"{'='*60}")

    # 输出完整 JSON（可用于下游消费）
    output = {
        "task_id": ctx.task_id,
        "status": ctx.status.value,
        "aggregation": {
            "event_count": len(ctx.aggregated_events),
            "events": ctx.aggregated_events,
        },
        "analysis": ctx.analysis_report,
        "disposition": ctx.disposition_result,
        "audit": ctx.audit_report,
    }
    print("\n📦 完整输出 (JSON):")
    print(json.dumps(output, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())

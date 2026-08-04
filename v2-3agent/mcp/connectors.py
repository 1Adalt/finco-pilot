"""
MCP 连接器基类 — 统一的 MCP Server 调用封装
"""
import json
import hashlib
import hmac
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError


class MCPBaseConnector:
    """MCP Server 连接器基类"""

    def __init__(self, name: str, config: dict):
        self.name = name
        self.endpoint = config.get("endpoint", "")
        self.auth = config.get("auth", {})
        self.retry_config = config.get("error_handling", {})
        self.logger = logging.getLogger(f"mcp.{name}")

    def _sign_request(self, payload: dict) -> dict:
        """HMAC-SHA256 签名"""
        if self.auth.get("method") != "ak_sk":
            return {}
        secret = self.auth.get("secret_key", "mock-secret")
        msg = json.dumps(payload, sort_keys=True)
        sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
        return {"X-Signature": sig, "Content-Type": "application/json"}

    async def call(self, tool: str, params: dict) -> dict:
        """
        调用 MCP 工具

        实际部署时使用 MCP SDK：
            from mcp import ClientSession
            async with ClientSession(endpoint) as session:
                result = await session.call_tool(tool, params)
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool, "arguments": params},
            "id": 1,
        }

        headers = self._sign_request(payload)
        self.logger.info("[%s] Calling %s(%s)", self.name, tool, params)

        # Mock 返回（初赛阶段演示）
        return self._mock_response(tool, params)

    def _mock_response(self, tool: str, params: dict) -> dict:
        """模拟 MCP Server 返回（初赛阶段）"""
        return {
            "jsonrpc": "2.0",
            "result": {"status": "ok", "mock": True, "tool": tool},
            "id": 1,
        }


class TxSystemConnector(MCPBaseConnector):
    def __init__(self, config: dict):
        super().__init__("mcp-tx-system", config)

    async def query_transactions(self, account_id: str, **kwargs) -> dict:
        return await self.call("query_transactions", {"account_id": account_id, **kwargs})

    async def freeze_account(self, account_id: str, reason: str, operator_id: str) -> dict:
        return await self.call("freeze_account", {
            "account_id": account_id, "reason": reason, "operator_id": operator_id,
        })


class CreditSystemConnector(MCPBaseConnector):
    def __init__(self, config: dict):
        super().__init__("mcp-credit", config)

    async def query_credit_report(self, entity_id: str, report_type: str = "personal") -> dict:
        return await self.call("query_credit_report", {
            "entity_id": entity_id, "report_type": report_type,
        })


class ClaimsSystemConnector(MCPBaseConnector):
    def __init__(self, config: dict):
        super().__init__("mcp-claims-system", config)

    async def query_policy(self, policy_id: str) -> dict:
        return await self.call("query_policy", {"policy_id": policy_id})

    async def submit_claim(self, policy_id: str, claim_type: str,
                           description: str, evidence: list) -> dict:
        return await self.call("submit_claim", {
            "policy_id": policy_id, "claim_type": claim_type,
            "description": description, "evidence": evidence,
        })


class SentimentConnector(MCPBaseConnector):
    def __init__(self, config: dict):
        super().__init__("mcp-sentiment", config)

    async def search_sentiment(self, entity_name: str, **kwargs) -> dict:
        return await self.call("search_sentiment", {"entity_name": entity_name, **kwargs})

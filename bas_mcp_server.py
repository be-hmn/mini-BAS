"""
BAS Orchestrator MCP Server.

Claude Desktop이 MCP client로 접속해 security_assessment 도구를 호출하면
vulnerability.py의 진단 로직(포트 스캔 + DB 취약점 조회)을 실행하고
결과 JSON을 반환한다. 위험도/대응 방안 분석은 Claude Desktop이 수행한다.
"""

import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

import vulnerability

server = Server("bas-orchestrator")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="security_assessment",
            description="대상의 보안 평가 (포트 스캔 + 취약점 분석 통합)",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "대상 IP 주소"}
                },
                "required": ["target"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    target = arguments.get("target")

    if name == "security_assessment":
        result = vulnerability.security_assessment(target)
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False)
        )]

    return [types.TextContent(
        type="text",
        text=json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False)
    )]


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

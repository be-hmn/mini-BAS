"""
BAS Orchestrator MCP Server.

Claude Desktop이 MCP client로 접속해 recon / map_vulnerabilities / security_assessment
도구를 호출하면 vulnerability.py의 진단 로직(포트 스캔 + DB 취약점 조회)을 실행하고
결과 JSON을 반환한다. 대상은 격리된 랩 환경(LAB_SCOPE)의 소유 장비로 제한된다.
위험도/대응 방안 분석은 Claude Desktop이 수행한다.
"""

import asyncio
import json
import logging
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

import vulnerability

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

server = Server("bas-orchestrator")

IPV4_PATTERN = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="recon",
            description=(
                "격리된 랩 환경(LAB_SCOPE)의 소유 장비 대상 TCP 포트 스캔. "
                "반환: {open_ports, scan_range, status}."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "대상 IP 주소", "pattern": IPV4_PATTERN}
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="map_vulnerabilities",
            description=(
                "격리된 랩 환경(LAB_SCOPE)의 소유 장비 대상 포트-CVE 매핑. "
                "open_ports를 주면 재스캔하지 않음. "
                "반환: {vulnerabilities, priority, recommended_path, db_reachable, errors, partial}."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "대상 IP 주소", "pattern": IPV4_PATTERN},
                    "open_ports": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "이미 알려진 열린 포트 목록 (생략 시 자체 스캔)"
                    }
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="security_assessment",
            description=(
                "격리된 랩 환경(LAB_SCOPE)의 소유 장비 대상 보안 평가 (포트 스캔 1회 + 취약점 분석 통합). "
                "반환: {scan_result, vulnerability_analysis, summary}."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "대상 IP 주소", "pattern": IPV4_PATTERN}
                },
                "required": ["target"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "recon":
            target = arguments.get("target")
            result = vulnerability.scan(target)
        elif name == "map_vulnerabilities":
            target = arguments.get("target")
            open_ports = arguments.get("open_ports")
            scan_result = {"open_ports": open_ports} if open_ports is not None else None
            result = vulnerability.map_vulnerabilities(target, scan_result=scan_result)
        elif name == "security_assessment":
            target = arguments.get("target")
            result = vulnerability.security_assessment(target)
        else:
            result = {"error": f"Unknown tool: {name}"}

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False)
        )]
    except ValueError as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e), "code": "OUT_OF_SCOPE"}, ensure_ascii=False)
        )]
    except Exception as e:
        logger.exception("call_tool(%s) failed", name)
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e), "code": "INTERNAL_ERROR"}, ensure_ascii=False)
        )]


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

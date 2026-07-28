"""
BAS Orchestrator MCP Server.

CVE 모듈 추가 방법:
1. <cve>.py 파일에 scan(target, exploit_result=None)와 exploit(target) 두 함수를 구현
   (표준 인터페이스: ms17010.py 참고)
2. killchains/<cve>.json에 킬체인 정의 추가
3. 이 파일은 killchains/*.json을 스캔해서 도구를 자동 노출하므로 서버 코드 수정 불필요
"""

import asyncio
import json
import importlib
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

KILLCHAIN_DIR = Path(__file__).parent / "killchains"

server = Server("bas-orchestrator")


def _load_killchains():
    chains = {}
    for f in KILLCHAIN_DIR.glob("*.json"):
        with open(f, "r", encoding="utf-8") as fp:
            chain = json.load(fp)
        chains[f.stem] = chain
    return chains


KILLCHAINS = _load_killchains()


def _get_module(cve_key):
    return importlib.import_module(cve_key)


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    tools = [
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
    for key, chain in KILLCHAINS.items():
        scan_name = chain["tools"]["scan"]
        exploit_name = chain["tools"]["exploit"]
        cve = chain.get("cve", key)
        alias = chain.get("alias", "")

        tools.append(types.Tool(
            name=scan_name,
            description=f"Recon/assess {cve} ({alias}) vulnerability exposure",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target IP address"},
                    "exploit_result": {"type": "string", "description": "Optional: SUCCESS/FAILED/NONE"}
                },
                "required": ["target"]
            }
        ))
        tools.append(types.Tool(
            name=exploit_name,
            description=f"Execute {cve} ({alias}) PoC exploit against target",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target IP address"}
                },
                "required": ["target"]
            }
        ))
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    target = arguments.get("target")

    if name == "security_assessment":
        module = _get_module("vulnerability")
        result = module.security_assessment(target)
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False)
        )]

    for key, chain in KILLCHAINS.items():
        module = _get_module(key)

        if name == chain["tools"]["scan"]:
            result = module.scan(target, exploit_result=arguments.get("exploit_result"))
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]

        if name == chain["tools"]["exploit"]:
            try:
                result = module.exploit(target)
            except NotImplementedError as e:
                result = {"target": target, "exploit_result": "NONE", "error": str(e)}
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

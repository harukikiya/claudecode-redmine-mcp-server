"""Redmine MCP server のエントリポイントモジュール。

stdio transportでMCP serverを起動する。ADR-0002 (公式low-level MCP SDK) に従い、
Server クラスを直接使ってprotocol層を明示的に構成する。
"""

from __future__ import annotations

import asyncio
from typing import Any

from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

SERVER_NAME: str = "redmine-mcp-server"

server: Server = Server(SERVER_NAME)


@server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
async def handle_list_tools() -> list[types.Tool]:
    """利用可能なMCP toolの一覧を返す。

    M1ではhello world確認用の ``ping`` toolのみ登録する。
    Tier 1 toolはM2で追加する。

    Returns:
        登録済みtoolのリスト。
    """
    return [
        types.Tool(
            name="ping",
            description="サーバーの疎通確認。常に pong を返す。Redmineへの接続は行わない。",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()  # type: ignore[untyped-decorator]
async def handle_call_tool(
    name: str,
    arguments: dict[str, Any],
) -> list[types.TextContent]:
    """MCP tool呼び出しを処理する。

    Args:
        name: 呼び出すtool名。
        arguments: tool引数のdict。

    Returns:
        TextContentのリスト。

    Raises:
        ValueError: 未知のtool名が指定された場合。
    """
    if name == "ping":
        return [types.TextContent(type="text", text="pong")]

    raise ValueError(f"Unknown tool: {name!r}")


async def _run_server() -> None:
    """stdio transportでMCP serverを起動する。

    stdin/stdoutをMCP messageのストリームとして使用する。
    """
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    """CLIエントリポイント。

    ``uv run redmine-mcp`` または ``python -m redmine_mcp.server`` で起動する。
    """
    asyncio.run(_run_server())


if __name__ == "__main__":
    main()

"""Redmine MCP server のエントリポイントモジュール。

stdio transportでMCP serverを起動する。ADR-0002 (公式low-level MCP SDK) に従い、
Server クラスを直接使ってprotocol層を明示的に構成する。
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from redmine_mcp.client import RedmineClient
from redmine_mcp.config import RedmineConfig
from redmine_mcp.errors import RedmineError
from redmine_mcp.tools import projects as tools_projects
from redmine_mcp.tools import users as tools_users

SERVER_NAME: str = "redmine-mcp-server"

server: Server = Server(SERVER_NAME)


@server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
async def handle_list_tools() -> list[types.Tool]:
    """利用可能なMCP toolの一覧を返す。

    Returns:
        登録済みtoolのリスト。
    """
    return [
        types.Tool(
            name="ping",
            description="サーバーの疎通確認。常に pong を返す。Redmineへの接続は行わない。",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_current_user",
            description=(
                "現在の認証ユーザーの情報を取得する。自分のuser IDの解決やAPIキー疎通確認に使う。"
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_projects",
            description=(
                "自分が参照できるプロジェクト一覧を取得する。"
                "create_issue や list_issues の前に project_id（identifier）を調べるために使う。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "include": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "追加取得するリソース名のリスト。"
                            "指定可能な値: trackers, issue_categories, "
                            "enabled_modules, time_entry_activities。"
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得件数上限（default 25, max 100）",
                        "default": 25,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "ページネーションオフセット",
                        "default": 0,
                    },
                },
            },
        ),
    ]


@server.call_tool()  # type: ignore[untyped-decorator]
async def handle_call_tool(
    name: str,
    arguments: dict[str, Any],
) -> list[types.TextContent]:
    """MCP tool呼び出しを処理する。

    Redmine toolはconfig/clientを生成して各tool関数に委譲する。
    RedmineErrorはcategorized JSON errorとして返す（ADR-0008）。

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

    config: RedmineConfig = RedmineConfig()  # type: ignore[call-arg]
    try:
        async with RedmineClient(config) as client:
            if name == "get_current_user":
                result: tools_users.CurrentUser = await tools_users.get_current_user(client)
                return [types.TextContent(type="text", text=result.model_dump_json())]
            if name == "list_projects":
                include_raw: list[str] | None = arguments.get("include")
                limit: int = int(arguments.get("limit", 25))
                offset: int = int(arguments.get("offset", 0))
                projects_result: tools_projects.ListProjectsResult = (
                    await tools_projects.list_projects(
                        client,
                        include=include_raw,
                        limit=limit,
                        offset=offset,
                    )
                )
                return [types.TextContent(type="text", text=projects_result.model_dump_json())]
    except RedmineError as e:
        error_body: str = json.dumps({"error": str(e.category), "message": e.message})
        return [types.TextContent(type="text", text=error_body)]

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

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
from redmine_mcp.tools import enumerations as tools_enums
from redmine_mcp.tools import issues as tools_issues
from redmine_mcp.tools import project_resources as tools_project_resources
from redmine_mcp.tools import projects as tools_projects
from redmine_mcp.tools import time_entries as tools_time
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
        types.Tool(
            name="list_issue_statuses",
            description=(
                "利用可能なissueステータス一覧を取得する。"
                "create_issue / update_issue で status_id を指定するときに使う。"
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_trackers",
            description=(
                "利用可能なトラッカー（issue種別）一覧を取得する。"
                "create_issue で tracker_id を指定するときに使う。"
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_priorities",
            description=(
                "利用可能なissue優先度一覧を取得する。"
                "create_issue で priority_id を指定するときに使う。"
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_issues",
            description=(
                "filter付きでissue一覧を取得する。"
                "project_id / status_id / assigned_to_id 等でfilterできる。"
                "assigned_to_id='me' で自分担当のissueを取得できる。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "プロジェクトのidentifierまたは数値IDでfilterする。",
                    },
                    "status_id": {
                        "type": "string",
                        "description": (
                            "ステータスでfilter。特殊値: open（デフォルト）, closed, *（全て）。"
                            "list_issue_statuses で取得した数値IDも使える。"
                        ),
                    },
                    "assigned_to_id": {
                        "type": "string",
                        "description": "担当者の数値IDでfilter。'me' で自分担当のみ取得。",
                    },
                    "tracker_id": {
                        "type": "integer",
                        "description": "トラッカーの数値IDでfilter。",
                    },
                    "priority_id": {
                        "type": "integer",
                        "description": "優先度の数値IDでfilter。",
                    },
                    "subject": {
                        "type": "string",
                        "description": "タイトルの部分一致でfilter。",
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
                    "sort": {
                        "type": "string",
                        "description": "ソート条件（例: updated_on:desc, priority:asc）",
                    },
                    "include": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "追加取得するリソース名のリスト。"
                            "指定可能な値: journals, attachments, relations, watchers, children。"
                        ),
                    },
                },
            },
        ),
        types.Tool(
            name="get_issue",
            description=(
                "単一issueの詳細を取得する。"
                "journals を include すると変更履歴・コメントも取得できる。"
            ),
            inputSchema={
                "type": "object",
                "required": ["issue_id"],
                "properties": {
                    "issue_id": {
                        "type": "integer",
                        "description": "取得するissueの数値ID。",
                    },
                    "include": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "追加取得するリソース名のリスト。"
                            "指定可能な値: journals, attachments, relations, watchers, children。"
                        ),
                    },
                },
            },
        ),
        types.Tool(
            name="create_issue",
            description=(
                "Redmineにissueを起票する。"
                "project_id と subject が必須。"
                "tracker_id / priority_id は list_trackers / list_priorities で取得できる。"
            ),
            inputSchema={
                "type": "object",
                "required": ["project_id", "subject"],
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "起票先プロジェクトのidentifierまたは数値ID。",
                    },
                    "subject": {"type": "string", "description": "issueのタイトル。"},
                    "tracker_id": {
                        "type": "integer",
                        "description": "トラッカーの数値ID。",
                    },
                    "status_id": {
                        "type": "integer",
                        "description": "ステータスの数値ID。",
                    },
                    "priority_id": {
                        "type": "integer",
                        "description": "優先度の数値ID。",
                    },
                    "description": {"type": "string", "description": "issue詳細説明。"},
                    "assigned_to_id": {
                        "type": "integer",
                        "description": "担当者の数値ID。",
                    },
                    "category_id": {
                        "type": "integer",
                        "description": "issueカテゴリーの数値ID。",
                    },
                    "fixed_version_id": {
                        "type": "integer",
                        "description": "対象バージョン（マイルストーン）の数値ID。",
                    },
                    "parent_issue_id": {
                        "type": "integer",
                        "description": "親issueの数値ID。",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "開始日（YYYY-MM-DD形式）。",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "期日（YYYY-MM-DD形式）。",
                    },
                    "estimated_hours": {
                        "type": "number",
                        "description": "予定工数（時間）。",
                    },
                    "done_ratio": {
                        "type": "integer",
                        "description": "進捗率（0〜100）。",
                    },
                    "watcher_user_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "ウォッチャーに追加するユーザーIDのリスト。",
                    },
                },
            },
        ),
        types.Tool(
            name="update_issue",
            description=(
                "Redmineのissueを更新する。"
                "ステータス遷移・コメント追加（notes）・担当者変更等に使う。"
                "変更したいフィールドだけ渡せばよい。"
            ),
            inputSchema={
                "type": "object",
                "required": ["issue_id"],
                "properties": {
                    "issue_id": {
                        "type": "integer",
                        "description": "更新するissueの数値ID。",
                    },
                    "subject": {"type": "string", "description": "新しいタイトル。"},
                    "tracker_id": {
                        "type": "integer",
                        "description": "新しいトラッカーの数値ID。",
                    },
                    "status_id": {
                        "type": "integer",
                        "description": "新しいステータスの数値ID。",
                    },
                    "priority_id": {
                        "type": "integer",
                        "description": "新しい優先度の数値ID。",
                    },
                    "description": {
                        "type": "string",
                        "description": "新しい詳細説明。",
                    },
                    "assigned_to_id": {
                        "type": "integer",
                        "description": "新しい担当者の数値ID。",
                    },
                    "done_ratio": {
                        "type": "integer",
                        "description": "新しい進捗率（0〜100）。",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "新しい期日（YYYY-MM-DD形式）。",
                    },
                    "estimated_hours": {
                        "type": "number",
                        "description": "新しい予定工数（時間）。",
                    },
                    "notes": {
                        "type": "string",
                        "description": "ジャーナルに残すコメントテキスト。",
                    },
                    "private_notes": {
                        "type": "boolean",
                        "description": "Trueのとき非公開コメントとして記録。",
                    },
                },
            },
        ),
        types.Tool(
            name="list_time_entries",
            description=("工数記録の一覧を取得する。issue_id / project_id / 日付でfilterできる。"),
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "integer",
                        "description": "特定issueの工数記録のみ取得する場合に指定。",
                    },
                    "project_id": {
                        "type": "string",
                        "description": "特定プロジェクトの工数記録のみ取得する場合に指定。",
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "特定ユーザーの工数記録のみ取得する場合に指定。",
                    },
                    "spent_on": {
                        "type": "string",
                        "description": "特定日（YYYY-MM-DD）の工数記録のみ取得。",
                    },
                    "from_date": {
                        "type": "string",
                        "description": "指定日以降の工数記録を取得（YYYY-MM-DD）。",
                    },
                    "to_date": {
                        "type": "string",
                        "description": "指定日以前の工数記録を取得（YYYY-MM-DD）。",
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
        types.Tool(
            name="create_time_entry",
            description=(
                "Redmineに工数を記録する。"
                "hours と issue_id（または project_id）が必須。"
                "spent_on を省略すると本日の日付で記録される。"
            ),
            inputSchema={
                "type": "object",
                "required": ["hours"],
                "properties": {
                    "hours": {
                        "type": "number",
                        "description": "記録する工数（時間）。必須。",
                    },
                    "issue_id": {
                        "type": "integer",
                        "description": "工数を紐付けるissueの数値ID。",
                    },
                    "project_id": {
                        "type": "string",
                        "description": (
                            "工数を紐付けるプロジェクトのidentifierまたは数値ID。"
                            "issue_id を指定しない場合は必須。"
                        ),
                    },
                    "spent_on": {
                        "type": "string",
                        "description": "作業日（YYYY-MM-DD形式）。省略時は本日。",
                    },
                    "activity_id": {
                        "type": "integer",
                        "description": "作業種別の数値ID。",
                    },
                    "comments": {
                        "type": "string",
                        "description": "作業内容のメモ。",
                    },
                },
            },
        ),
        types.Tool(
            name="update_time_entry",
            description=("Redmineの工数記録を修正する。変更したいフィールドだけ渡せばよい。"),
            inputSchema={
                "type": "object",
                "required": ["time_entry_id"],
                "properties": {
                    "time_entry_id": {
                        "type": "integer",
                        "description": "更新する工数記録の数値ID。",
                    },
                    "hours": {"type": "number", "description": "新しい工数（時間）。"},
                    "spent_on": {
                        "type": "string",
                        "description": "新しい作業日（YYYY-MM-DD形式）。",
                    },
                    "activity_id": {
                        "type": "integer",
                        "description": "新しい作業種別の数値ID。",
                    },
                    "comments": {"type": "string", "description": "新しいコメント。"},
                    "issue_id": {
                        "type": "integer",
                        "description": "紐付け先issueの数値IDを変更する場合に指定。",
                    },
                    "project_id": {
                        "type": "string",
                        "description": "紐付け先プロジェクトのidentifierを変更する場合に指定。",
                    },
                },
            },
        ),
        types.Tool(
            name="list_versions",
            description=(
                "プロジェクト内のバージョン（マイルストーン）一覧を取得する。"
                "create_issue で fixed_version_id を指定するときに使う。"
            ),
            inputSchema={
                "type": "object",
                "required": ["project_id"],
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "バージョンを取得するプロジェクトのidentifierまたは数値ID。",
                    },
                },
            },
        ),
        types.Tool(
            name="list_issue_categories",
            description=(
                "プロジェクト内のissueカテゴリー一覧を取得する。"
                "create_issue で category_id を指定するときに使う。"
            ),
            inputSchema={
                "type": "object",
                "required": ["project_id"],
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "カテゴリーを取得するプロジェクトのidentifierまたは数値ID。",
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
            if name == "list_issue_statuses":
                statuses: list[tools_enums.IssueStatus] = await tools_enums.list_issue_statuses(
                    client
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps([s.model_dump() for s in statuses], ensure_ascii=False),
                    )
                ]
            if name == "list_trackers":
                trackers: list[tools_enums.Tracker] = await tools_enums.list_trackers(client)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps([t.model_dump() for t in trackers], ensure_ascii=False),
                    )
                ]
            if name == "list_priorities":
                priorities: list[tools_enums.IssuePriority] = await tools_enums.list_priorities(
                    client
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps([p.model_dump() for p in priorities], ensure_ascii=False),
                    )
                ]
            if name == "list_issues":
                issues_result: tools_issues.ListIssuesResult = await tools_issues.list_issues(
                    client,
                    project_id=arguments.get("project_id"),
                    status_id=arguments.get("status_id"),
                    assigned_to_id=arguments.get("assigned_to_id"),
                    tracker_id=arguments.get("tracker_id"),
                    priority_id=arguments.get("priority_id"),
                    subject=arguments.get("subject"),
                    limit=int(arguments.get("limit", 25)),
                    offset=int(arguments.get("offset", 0)),
                    sort=arguments.get("sort"),
                    include=arguments.get("include"),
                )
                return [types.TextContent(type="text", text=issues_result.model_dump_json())]
            if name == "get_issue":
                issue_result: tools_issues.Issue = await tools_issues.get_issue(
                    client,
                    issue_id=int(arguments["issue_id"]),
                    include=arguments.get("include"),
                )
                return [types.TextContent(type="text", text=issue_result.model_dump_json())]
            if name == "create_issue":
                created: tools_issues.Issue = await tools_issues.create_issue(
                    client,
                    project_id=str(arguments["project_id"]),
                    subject=str(arguments["subject"]),
                    tracker_id=arguments.get("tracker_id"),
                    status_id=arguments.get("status_id"),
                    priority_id=arguments.get("priority_id"),
                    description=arguments.get("description"),
                    assigned_to_id=arguments.get("assigned_to_id"),
                    category_id=arguments.get("category_id"),
                    fixed_version_id=arguments.get("fixed_version_id"),
                    parent_issue_id=arguments.get("parent_issue_id"),
                    start_date=arguments.get("start_date"),
                    due_date=arguments.get("due_date"),
                    estimated_hours=arguments.get("estimated_hours"),
                    done_ratio=arguments.get("done_ratio"),
                    watcher_user_ids=arguments.get("watcher_user_ids"),
                )
                return [types.TextContent(type="text", text=created.model_dump_json())]
            if name == "update_issue":
                updated: tools_issues.Issue = await tools_issues.update_issue(
                    client,
                    issue_id=int(arguments["issue_id"]),
                    subject=arguments.get("subject"),
                    tracker_id=arguments.get("tracker_id"),
                    status_id=arguments.get("status_id"),
                    priority_id=arguments.get("priority_id"),
                    description=arguments.get("description"),
                    assigned_to_id=arguments.get("assigned_to_id"),
                    category_id=arguments.get("category_id"),
                    fixed_version_id=arguments.get("fixed_version_id"),
                    parent_issue_id=arguments.get("parent_issue_id"),
                    start_date=arguments.get("start_date"),
                    due_date=arguments.get("due_date"),
                    estimated_hours=arguments.get("estimated_hours"),
                    done_ratio=arguments.get("done_ratio"),
                    notes=arguments.get("notes"),
                    private_notes=arguments.get("private_notes"),
                )
                return [types.TextContent(type="text", text=updated.model_dump_json())]
            if name == "list_time_entries":
                te_result: tools_time.ListTimeEntriesResult = await tools_time.list_time_entries(
                    client,
                    issue_id=arguments.get("issue_id"),
                    project_id=arguments.get("project_id"),
                    user_id=arguments.get("user_id"),
                    spent_on=arguments.get("spent_on"),
                    from_date=arguments.get("from_date"),
                    to_date=arguments.get("to_date"),
                    limit=int(arguments.get("limit", 25)),
                    offset=int(arguments.get("offset", 0)),
                )
                return [types.TextContent(type="text", text=te_result.model_dump_json())]
            if name == "create_time_entry":
                created_te: tools_time.TimeEntry = await tools_time.create_time_entry(
                    client,
                    hours=float(arguments["hours"]),
                    issue_id=arguments.get("issue_id"),
                    project_id=arguments.get("project_id"),
                    spent_on=arguments.get("spent_on"),
                    activity_id=arguments.get("activity_id"),
                    comments=arguments.get("comments"),
                )
                return [types.TextContent(type="text", text=created_te.model_dump_json())]
            if name == "update_time_entry":
                updated_te: tools_time.TimeEntry = await tools_time.update_time_entry(
                    client,
                    time_entry_id=int(arguments["time_entry_id"]),
                    hours=arguments.get("hours"),
                    spent_on=arguments.get("spent_on"),
                    activity_id=arguments.get("activity_id"),
                    comments=arguments.get("comments"),
                    issue_id=arguments.get("issue_id"),
                    project_id=arguments.get("project_id"),
                )
                return [types.TextContent(type="text", text=updated_te.model_dump_json())]
            if name == "list_versions":
                versions: list[
                    tools_project_resources.Version
                ] = await tools_project_resources.list_versions(
                    client,
                    project_id=str(arguments["project_id"]),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps([v.model_dump() for v in versions], ensure_ascii=False),
                    )
                ]
            if name == "list_issue_categories":
                categories: list[
                    tools_project_resources.IssueCategory
                ] = await tools_project_resources.list_issue_categories(
                    client,
                    project_id=str(arguments["project_id"]),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps([c.model_dump() for c in categories], ensure_ascii=False),
                    )
                ]
    except RedmineError as e:
        error_body: str = json.dumps({"error": str(e.category), "message": e.message})
        return [types.TextContent(type="text", text=error_body)]

    raise ValueError(f"Unknown tool: {name!r}")


async def _run_server() -> None:  # pragma: no cover
    """stdio transportでMCP serverを起動する。

    stdin/stdoutをMCP messageのストリームとして使用する。
    """
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:  # pragma: no cover
    """CLIエントリポイント。

    ``uv run redmine-mcp`` または ``python -m redmine_mcp.server`` で起動する。
    """
    asyncio.run(_run_server())


if __name__ == "__main__":  # pragma: no cover
    main()

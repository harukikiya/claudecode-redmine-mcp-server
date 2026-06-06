"""server.py の handle_list_tools / handle_call_tool に対する integration テスト。

pytest-httpx でRedmine APIをmockし、MCPディスパッチ層（server.py）の
全分岐を網羅する。ADR-0008のcategorized error整形パスも検証する。
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from mcp import types
from pytest_httpx import HTTPXMock

from redmine_mcp.server import handle_call_tool, handle_list_tools

# ---------------------------------------------------------------------------
# テスト用定数
# ---------------------------------------------------------------------------

_TEST_URL: str = "http://test.redmine.example"
_TEST_API_KEY: str = "test-api-key-abc123"

# 共通issueペイロード（issues系toolが使い回す）
_ISSUE_DATA: dict[str, object] = {
    "id": 42,
    "project": {"id": 1, "name": "My Project"},
    "tracker": {"id": 1, "name": "Bug"},
    "status": {"id": 1, "name": "New"},
    "priority": {"id": 4, "name": "Normal"},
    "author": {"id": 1, "name": "Admin"},
    "subject": "Fix login bug",
    "done_ratio": 0,
    "created_on": "2026-05-01T00:00:00Z",
    "updated_on": "2026-05-29T00:00:00Z",
}

# 共通time entryペイロード（time_entries系toolが使い回す）
_ENTRY_DATA: dict[str, object] = {
    "id": 123,
    "project": {"id": 1, "name": "My Project"},
    "issue": {"id": 42, "name": "Fix login bug"},
    "user": {"id": 1, "name": "Admin"},
    "activity": {"id": 9, "name": "Development"},
    "hours": 2.5,
    "comments": "Investigated",
    "spent_on": "2026-05-30",
    "created_on": "2026-05-30T10:00:00Z",
    "updated_on": "2026-05-30T10:00:00Z",
}


# ---------------------------------------------------------------------------
# A. handle_list_tools
# ---------------------------------------------------------------------------


async def test_handle_list_tools_returns_all_tools() -> None:
    """handle_list_tools が13ツール全ての名前を返すこと。

    ping + 12 Redmine toolが登録されていることを確認する。
    """
    tools: list[types.Tool] = await handle_list_tools()
    names: set[str] = {t.name for t in tools}

    expected: set[str] = {
        "ping",
        "get_current_user",
        "list_projects",
        "list_issue_statuses",
        "list_trackers",
        "list_priorities",
        "list_issues",
        "get_issue",
        "create_issue",
        "update_issue",
        "list_time_entries",
        "create_time_entry",
        "update_time_entry",
    }
    assert names == expected


async def test_handle_list_tools_each_has_input_schema() -> None:
    """全toolにinputSchemaが設定されていること。"""
    tools: list[types.Tool] = await handle_list_tools()
    for tool in tools:
        assert tool.inputSchema is not None, f"{tool.name} に inputSchema がない"


# ---------------------------------------------------------------------------
# B. ping
# ---------------------------------------------------------------------------


async def test_ping_returns_pong() -> None:
    """ping toolが pong を返すこと（env・Redmine接続不要）。"""
    result: list[types.TextContent] = await handle_call_tool("ping", {})

    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    assert result[0].text == "pong"


# ---------------------------------------------------------------------------
# C. 未知tool
# ---------------------------------------------------------------------------


async def test_unknown_tool_raises_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """未知tool名でValueErrorが発生すること。

    handle_call_tool はpingを除く全toolでRedmineConfigを先に構築するため、
    env varを設定した上でValueErrorが発生することを確認する。
    """
    monkeypatch.setenv("REDMINE_URL", _TEST_URL)
    monkeypatch.setenv("REDMINE_API_KEY", _TEST_API_KEY)

    with pytest.raises(ValueError, match="Unknown tool"):
        await handle_call_tool("no_such_tool", {})


# ---------------------------------------------------------------------------
# D. 各toolのディスパッチ（12分岐全て）
# ---------------------------------------------------------------------------


async def test_dispatch_get_current_user(
    httpx_mock: HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_current_user: ユーザー情報がTextContent JSONで返ること。"""
    monkeypatch.setenv("REDMINE_URL", _TEST_URL)
    monkeypatch.setenv("REDMINE_API_KEY", _TEST_API_KEY)

    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/users/current.json",
        json={
            "user": {
                "id": 1,
                "login": "jsmith",
                "firstname": "John",
                "lastname": "Smith",
                "created_on": "2020-01-01T00:00:00Z",
                "last_login_on": "2026-05-29T10:00:00Z",
            }
        },
    )

    result: list[types.TextContent] = await handle_call_tool("get_current_user", {})

    assert len(result) == 1
    data: dict[str, Any] = json.loads(result[0].text)
    assert data["id"] == 1
    assert data["login"] == "jsmith"


async def test_dispatch_list_projects(
    httpx_mock: HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """list_projects: プロジェクト一覧がTextContent JSONで返ること。"""
    monkeypatch.setenv("REDMINE_URL", _TEST_URL)
    monkeypatch.setenv("REDMINE_API_KEY", _TEST_API_KEY)

    httpx_mock.add_response(
        method="GET",
        json={
            "projects": [
                {
                    "id": 1,
                    "identifier": "myproject",
                    "name": "My Project",
                    "status": 1,
                    "created_on": "2020-01-01T00:00:00Z",
                    "updated_on": "2026-05-01T00:00:00Z",
                }
            ],
            "total_count": 1,
            "offset": 0,
            "limit": 25,
        },
    )

    result: list[types.TextContent] = await handle_call_tool("list_projects", {})

    assert len(result) == 1
    data: dict[str, Any] = json.loads(result[0].text)
    assert data["total_count"] == 1
    assert data["projects"][0]["identifier"] == "myproject"


async def test_dispatch_list_issue_statuses(
    httpx_mock: HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """list_issue_statuses: ステータス一覧がTextContent JSONで返ること。"""
    monkeypatch.setenv("REDMINE_URL", _TEST_URL)
    monkeypatch.setenv("REDMINE_API_KEY", _TEST_API_KEY)

    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/issue_statuses.json",
        json={
            "issue_statuses": [
                {"id": 1, "name": "New", "is_closed": False},
                {"id": 5, "name": "Closed", "is_closed": True},
            ]
        },
    )

    result: list[types.TextContent] = await handle_call_tool("list_issue_statuses", {})

    assert len(result) == 1
    data: list[dict[str, Any]] = json.loads(result[0].text)
    assert len(data) == 2
    assert data[0]["name"] == "New"


async def test_dispatch_list_trackers(
    httpx_mock: HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """list_trackers: トラッカー一覧がTextContent JSONで返ること。"""
    monkeypatch.setenv("REDMINE_URL", _TEST_URL)
    monkeypatch.setenv("REDMINE_API_KEY", _TEST_API_KEY)

    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/trackers.json",
        json={
            "trackers": [
                {"id": 1, "name": "Bug"},
                {"id": 2, "name": "Feature"},
            ]
        },
    )

    result: list[types.TextContent] = await handle_call_tool("list_trackers", {})

    assert len(result) == 1
    data: list[dict[str, Any]] = json.loads(result[0].text)
    assert data[0]["name"] == "Bug"


async def test_dispatch_list_priorities(
    httpx_mock: HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """list_priorities: 優先度一覧がTextContent JSONで返ること。"""
    monkeypatch.setenv("REDMINE_URL", _TEST_URL)
    monkeypatch.setenv("REDMINE_API_KEY", _TEST_API_KEY)

    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/enumerations/issue_priorities.json",
        json={
            "issue_priorities": [
                {"id": 4, "name": "Normal", "is_default": True},
                {"id": 5, "name": "High", "is_default": False},
            ]
        },
    )

    result: list[types.TextContent] = await handle_call_tool("list_priorities", {})

    assert len(result) == 1
    data: list[dict[str, Any]] = json.loads(result[0].text)
    assert data[0]["name"] == "Normal"


async def test_dispatch_list_issues(
    httpx_mock: HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """list_issues: issue一覧がTextContent JSONで返ること。"""
    monkeypatch.setenv("REDMINE_URL", _TEST_URL)
    monkeypatch.setenv("REDMINE_API_KEY", _TEST_API_KEY)

    httpx_mock.add_response(
        method="GET",
        json={
            "issues": [_ISSUE_DATA],
            "total_count": 1,
            "offset": 0,
            "limit": 25,
        },
    )

    result: list[types.TextContent] = await handle_call_tool(
        "list_issues",
        {"project_id": "myproject", "status_id": "open"},
    )

    assert len(result) == 1
    data: dict[str, Any] = json.loads(result[0].text)
    assert data["total_count"] == 1
    assert data["issues"][0]["id"] == 42


async def test_dispatch_get_issue(
    httpx_mock: HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_issue: issue詳細がTextContent JSONで返ること。"""
    monkeypatch.setenv("REDMINE_URL", _TEST_URL)
    monkeypatch.setenv("REDMINE_API_KEY", _TEST_API_KEY)

    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/issues/42.json",
        json={"issue": _ISSUE_DATA},
    )

    result: list[types.TextContent] = await handle_call_tool("get_issue", {"issue_id": 42})

    assert len(result) == 1
    data: dict[str, Any] = json.loads(result[0].text)
    assert data["id"] == 42
    assert data["subject"] == "Fix login bug"


async def test_dispatch_create_issue(
    httpx_mock: HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """create_issue: 起票したissueがTextContent JSONで返ること。"""
    monkeypatch.setenv("REDMINE_URL", _TEST_URL)
    monkeypatch.setenv("REDMINE_API_KEY", _TEST_API_KEY)

    httpx_mock.add_response(
        method="POST",
        url=f"{_TEST_URL}/issues.json",
        status_code=201,
        json={"issue": _ISSUE_DATA},
    )

    result: list[types.TextContent] = await handle_call_tool(
        "create_issue",
        {"project_id": "myproject", "subject": "Fix login bug"},
    )

    assert len(result) == 1
    data: dict[str, Any] = json.loads(result[0].text)
    assert data["id"] == 42


async def test_dispatch_update_issue(
    httpx_mock: HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """update_issue: 更新後のissueがTextContent JSONで返ること。"""
    monkeypatch.setenv("REDMINE_URL", _TEST_URL)
    monkeypatch.setenv("REDMINE_API_KEY", _TEST_API_KEY)

    updated_issue: dict[str, object] = {**_ISSUE_DATA, "done_ratio": 50}
    # PUT /issues/42.json → 200 (no body)
    httpx_mock.add_response(
        method="PUT",
        url=f"{_TEST_URL}/issues/42.json",
        status_code=200,
    )
    # GET /issues/42.json → 更新後のデータ
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/issues/42.json",
        json={"issue": updated_issue},
    )

    result: list[types.TextContent] = await handle_call_tool(
        "update_issue",
        {"issue_id": 42, "done_ratio": 50},
    )

    assert len(result) == 1
    data: dict[str, Any] = json.loads(result[0].text)
    assert data["done_ratio"] == 50


async def test_dispatch_list_time_entries(
    httpx_mock: HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """list_time_entries: 工数記録一覧がTextContent JSONで返ること。"""
    monkeypatch.setenv("REDMINE_URL", _TEST_URL)
    monkeypatch.setenv("REDMINE_API_KEY", _TEST_API_KEY)

    httpx_mock.add_response(
        method="GET",
        json={
            "time_entries": [_ENTRY_DATA],
            "total_count": 1,
            "offset": 0,
            "limit": 25,
        },
    )

    result: list[types.TextContent] = await handle_call_tool(
        "list_time_entries",
        {"issue_id": 42},
    )

    assert len(result) == 1
    data: dict[str, Any] = json.loads(result[0].text)
    assert data["total_count"] == 1
    assert data["time_entries"][0]["id"] == 123


async def test_dispatch_create_time_entry(
    httpx_mock: HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """create_time_entry: 記録した工数がTextContent JSONで返ること。"""
    monkeypatch.setenv("REDMINE_URL", _TEST_URL)
    monkeypatch.setenv("REDMINE_API_KEY", _TEST_API_KEY)

    httpx_mock.add_response(
        method="POST",
        url=f"{_TEST_URL}/time_entries.json",
        status_code=201,
        json={"time_entry": _ENTRY_DATA},
    )

    result: list[types.TextContent] = await handle_call_tool(
        "create_time_entry",
        {"hours": 2.5, "issue_id": 42, "comments": "Investigated"},
    )

    assert len(result) == 1
    data: dict[str, Any] = json.loads(result[0].text)
    assert data["id"] == 123
    assert data["hours"] == 2.5


async def test_dispatch_update_time_entry(
    httpx_mock: HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """update_time_entry: 更新後の工数記録がTextContent JSONで返ること。"""
    monkeypatch.setenv("REDMINE_URL", _TEST_URL)
    monkeypatch.setenv("REDMINE_API_KEY", _TEST_API_KEY)

    updated_entry: dict[str, object] = {**_ENTRY_DATA, "hours": 3.0}
    httpx_mock.add_response(
        method="PUT",
        url=f"{_TEST_URL}/time_entries/123.json",
        status_code=200,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/time_entries/123.json",
        json={"time_entry": updated_entry},
    )

    result: list[types.TextContent] = await handle_call_tool(
        "update_time_entry",
        {"time_entry_id": 123, "hours": 3.0},
    )

    assert len(result) == 1
    data: dict[str, Any] = json.loads(result[0].text)
    assert data["hours"] == 3.0


# ---------------------------------------------------------------------------
# E. RedmineError整形パス（categorized error JSON）
# ---------------------------------------------------------------------------


async def test_redmine_error_returns_categorized_json(
    httpx_mock: HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Redmine 401エラーがcategorized error JSONとして返ること（raiseしない）。

    ADR-0008のエラー整形パス（handle_call_tool内のexcept RedmineError）を検証する。
    """
    monkeypatch.setenv("REDMINE_URL", _TEST_URL)
    monkeypatch.setenv("REDMINE_API_KEY", _TEST_API_KEY)

    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/users/current.json",
        status_code=401,
    )

    # RedmineErrorはraiseされず、TextContent JSONとして返る
    result: list[types.TextContent] = await handle_call_tool("get_current_user", {})

    assert len(result) == 1
    error_data: dict[str, Any] = json.loads(result[0].text)
    assert "error" in error_data
    assert "message" in error_data
    assert error_data["error"] == "AuthFailed"

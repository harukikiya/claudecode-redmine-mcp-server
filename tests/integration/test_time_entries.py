"""list_time_entries / create_time_entry / update_time_entry tools の integration テスト。

pytest-httpx でRedmine APIをmockし、tool関数の動作を検証する。
"""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

from redmine_mcp.client import RedmineClient
from redmine_mcp.config import RedmineConfig
from redmine_mcp.errors import ErrorCategory, RedmineError
from redmine_mcp.tools.time_entries import (
    ListTimeEntriesResult,
    TimeEntry,
    create_time_entry,
    list_time_entries,
    update_time_entry,
)

_TEST_URL: str = "http://test.redmine.example"
_TEST_API_KEY: str = "test-api-key-abc123"

_TEST_CONFIG: RedmineConfig = RedmineConfig(
    url=_TEST_URL,
    api_key=_TEST_API_KEY,
)

_ENTRY_DATA: dict[str, object] = {
    "id": 123,
    "project": {"id": 1, "name": "My Project"},
    "issue": {"id": 42, "name": "Fix login bug"},
    "user": {"id": 1, "name": "Admin"},
    "activity": {"id": 9, "name": "Development"},
    "hours": 2.5,
    "comments": "Investigated the login flow",
    "spent_on": "2026-05-30",
    "created_on": "2026-05-30T10:00:00Z",
    "updated_on": "2026-05-30T10:00:00Z",
}

_LIST_PAYLOAD: dict[str, object] = {
    "time_entries": [_ENTRY_DATA],
    "total_count": 1,
    "offset": 0,
    "limit": 25,
}


# ---------------------------------------------------------------------------
# list_time_entries
# ---------------------------------------------------------------------------


async def test_list_time_entries_success(httpx_mock: HTTPXMock) -> None:
    """正常系: 工数記録一覧をパースして返すこと。"""
    httpx_mock.add_response(method="GET", json=_LIST_PAYLOAD)

    async with RedmineClient(_TEST_CONFIG) as client:
        result: ListTimeEntriesResult = await list_time_entries(client)

    assert result.total_count == 1
    assert len(result.time_entries) == 1

    entry: TimeEntry = result.time_entries[0]
    assert entry.id == 123
    assert entry.hours == 2.5
    assert entry.comments == "Investigated the login flow"
    assert entry.issue is not None
    assert entry.issue.id == 42


async def test_list_time_entries_sends_filters(httpx_mock: HTTPXMock) -> None:
    """filter引数がクエリパラメータに含まれること。"""
    httpx_mock.add_response(method="GET", json=_LIST_PAYLOAD)

    async with RedmineClient(_TEST_CONFIG) as client:
        await list_time_entries(
            client,
            issue_id=42,
            project_id="myproject",
            from_date="2026-05-01",
            to_date="2026-05-31",
        )

    request = httpx_mock.get_request()
    assert request is not None
    url_str: str = str(request.url)
    assert "issue_id=42" in url_str
    assert "project_id=myproject" in url_str
    assert "from=2026-05-01" in url_str
    assert "to=2026-05-31" in url_str


async def test_list_time_entries_empty(httpx_mock: HTTPXMock) -> None:
    """0件のとき空リストを返すこと。"""
    httpx_mock.add_response(
        method="GET",
        json={"time_entries": [], "total_count": 0, "offset": 0, "limit": 25},
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: ListTimeEntriesResult = await list_time_entries(client)

    assert result.time_entries == []
    assert result.total_count == 0


async def test_list_time_entries_auth_failed(httpx_mock: HTTPXMock) -> None:
    """401で AUTH_FAILED になること。"""
    httpx_mock.add_response(method="GET", status_code=401)

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await list_time_entries(client)

    assert exc_info.value.category == ErrorCategory.AUTH_FAILED


async def test_list_time_entries_timeout(httpx_mock: HTTPXMock) -> None:
    """タイムアウトで SERVER_ERROR になること。"""
    httpx_mock.add_exception(httpx.ReadTimeout("timed out"), method="GET")

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await list_time_entries(client)

    assert exc_info.value.category == ErrorCategory.SERVER_ERROR


# ---------------------------------------------------------------------------
# create_time_entry
# ---------------------------------------------------------------------------


async def test_create_time_entry_with_issue_id(httpx_mock: HTTPXMock) -> None:
    """正常系: issue_id指定で工数が記録されること。"""
    httpx_mock.add_response(
        method="POST",
        url=f"{_TEST_URL}/time_entries.json",
        status_code=201,
        json={"time_entry": _ENTRY_DATA},
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: TimeEntry = await create_time_entry(
            client,
            hours=2.5,
            issue_id=42,
            comments="Investigated the login flow",
        )

    assert result.id == 123
    assert result.hours == 2.5


async def test_create_time_entry_with_project_id(httpx_mock: HTTPXMock) -> None:
    """正常系: project_id指定で工数が記録されること。"""
    entry_without_issue: dict[str, object] = {
        **_ENTRY_DATA,
        "issue": None,
        "hours": 1.0,
    }
    httpx_mock.add_response(
        method="POST",
        url=f"{_TEST_URL}/time_entries.json",
        status_code=201,
        json={"time_entry": entry_without_issue},
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: TimeEntry = await create_time_entry(
            client,
            hours=1.0,
            project_id="myproject",
        )

    assert result.hours == 1.0


async def test_create_time_entry_sends_body(httpx_mock: HTTPXMock) -> None:
    """hours / issue_id がリクエストボディに含まれること。"""
    httpx_mock.add_response(
        method="POST",
        url=f"{_TEST_URL}/time_entries.json",
        status_code=201,
        json={"time_entry": _ENTRY_DATA},
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        await create_time_entry(
            client,
            hours=2.5,
            issue_id=42,
            spent_on="2026-05-30",
            comments="Investigated",
        )

    request = httpx_mock.get_request()
    assert request is not None
    import json

    body: dict[str, object] = json.loads(request.content)
    te_body = body["time_entry"]
    assert te_body["hours"] == 2.5  # type: ignore[index]
    assert te_body["issue_id"] == 42  # type: ignore[index]
    assert te_body["spent_on"] == "2026-05-30"  # type: ignore[index]


async def test_create_time_entry_validation_missing_ids(httpx_mock: HTTPXMock) -> None:
    """issue_id / project_id 両方未指定で VALIDATION エラーになること（client側でvalidation）。"""
    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await create_time_entry(client, hours=1.0)

    assert exc_info.value.category == ErrorCategory.VALIDATION


async def test_create_time_entry_auth_failed(httpx_mock: HTTPXMock) -> None:
    """401で AUTH_FAILED になること。"""
    httpx_mock.add_response(
        method="POST",
        url=f"{_TEST_URL}/time_entries.json",
        status_code=401,
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await create_time_entry(client, hours=1.0, issue_id=42)

    assert exc_info.value.category == ErrorCategory.AUTH_FAILED


async def test_create_time_entry_timeout(httpx_mock: HTTPXMock) -> None:
    """タイムアウトで SERVER_ERROR になること。"""
    httpx_mock.add_exception(
        httpx.ReadTimeout("timed out"),
        method="POST",
        url=f"{_TEST_URL}/time_entries.json",
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await create_time_entry(client, hours=1.0, issue_id=42)

    assert exc_info.value.category == ErrorCategory.SERVER_ERROR


# ---------------------------------------------------------------------------
# update_time_entry
# ---------------------------------------------------------------------------


async def test_update_time_entry_success(httpx_mock: HTTPXMock) -> None:
    """正常系: PUT後にGETで取得した更新済みエントリを返すこと。"""
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

    async with RedmineClient(_TEST_CONFIG) as client:
        result: TimeEntry = await update_time_entry(
            client, time_entry_id=123, hours=3.0, comments="Revised"
        )

    assert result.hours == 3.0


async def test_update_time_entry_sends_body(httpx_mock: HTTPXMock) -> None:
    """hours / comments がリクエストボディに含まれること。"""
    httpx_mock.add_response(
        method="PUT",
        url=f"{_TEST_URL}/time_entries/123.json",
        status_code=200,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/time_entries/123.json",
        json={"time_entry": _ENTRY_DATA},
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        await update_time_entry(client, time_entry_id=123, hours=3.0, comments="Updated")

    requests = httpx_mock.get_requests()
    put_request = next(r for r in requests if r.method == "PUT")
    import json

    body: dict[str, object] = json.loads(put_request.content)
    te_body = body["time_entry"]
    assert te_body["hours"] == 3.0  # type: ignore[index]
    assert te_body["comments"] == "Updated"  # type: ignore[index]


async def test_update_time_entry_not_found(httpx_mock: HTTPXMock) -> None:
    """存在しないエントリIDで NOT_FOUND になること。"""
    httpx_mock.add_response(
        method="PUT",
        url=f"{_TEST_URL}/time_entries/9999.json",
        status_code=404,
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await update_time_entry(client, time_entry_id=9999, hours=1.0)

    assert exc_info.value.category == ErrorCategory.NOT_FOUND


async def test_update_time_entry_auth_failed(httpx_mock: HTTPXMock) -> None:
    """401で AUTH_FAILED になること。"""
    httpx_mock.add_response(
        method="PUT",
        url=f"{_TEST_URL}/time_entries/123.json",
        status_code=401,
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await update_time_entry(client, time_entry_id=123, hours=1.0)

    assert exc_info.value.category == ErrorCategory.AUTH_FAILED

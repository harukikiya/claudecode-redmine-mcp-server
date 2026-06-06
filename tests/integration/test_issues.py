"""list_issues / get_issue tools の integration テスト。

pytest-httpx でRedmine APIをmockし、tool関数の動作を検証する。
"""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

from redmine_mcp.client import RedmineClient
from redmine_mcp.config import RedmineConfig
from redmine_mcp.errors import ErrorCategory, RedmineError
from redmine_mcp.tools.issues import Issue, ListIssuesResult, get_issue, list_issues

_TEST_URL: str = "http://test.redmine.example"
_TEST_API_KEY: str = "test-api-key-abc123"

_TEST_CONFIG: RedmineConfig = RedmineConfig(
    url=_TEST_URL,
    api_key=_TEST_API_KEY,
)

_ISSUE_DATA: dict[str, object] = {
    "id": 42,
    "project": {"id": 1, "name": "My Project"},
    "tracker": {"id": 1, "name": "Bug"},
    "status": {"id": 1, "name": "New"},
    "priority": {"id": 4, "name": "Normal"},
    "author": {"id": 1, "name": "Admin"},
    "assigned_to": {"id": 2, "name": "John Smith"},
    "subject": "Fix login bug",
    "description": "Users cannot login with special characters.",
    "done_ratio": 0,
    "created_on": "2026-05-01T00:00:00Z",
    "updated_on": "2026-05-29T00:00:00Z",
}

_LIST_PAYLOAD: dict[str, object] = {
    "issues": [_ISSUE_DATA],
    "total_count": 1,
    "offset": 0,
    "limit": 25,
}

_GET_PAYLOAD: dict[str, object] = {"issue": _ISSUE_DATA}


# ---------------------------------------------------------------------------
# list_issues
# ---------------------------------------------------------------------------


async def test_list_issues_success(httpx_mock: HTTPXMock) -> None:
    """正常系: issue一覧をパースして返すこと。"""
    httpx_mock.add_response(method="GET", json=_LIST_PAYLOAD)

    async with RedmineClient(_TEST_CONFIG) as client:
        result: ListIssuesResult = await list_issues(client)

    assert result.total_count == 1
    assert len(result.issues) == 1

    issue: Issue = result.issues[0]
    assert issue.id == 42
    assert issue.subject == "Fix login bug"
    assert issue.project.name == "My Project"
    assert issue.assigned_to is not None
    assert issue.assigned_to.name == "John Smith"


async def test_list_issues_sends_filters(httpx_mock: HTTPXMock) -> None:
    """filter引数がクエリパラメータに含まれること。"""
    httpx_mock.add_response(method="GET", json=_LIST_PAYLOAD)

    async with RedmineClient(_TEST_CONFIG) as client:
        await list_issues(
            client,
            project_id="myproject",
            status_id="open",
            assigned_to_id="me",
        )

    request = httpx_mock.get_request()
    assert request is not None
    url_str: str = str(request.url)
    assert "project_id=myproject" in url_str
    assert "status_id=open" in url_str
    assert "assigned_to_id=me" in url_str


async def test_list_issues_pagination(httpx_mock: HTTPXMock) -> None:
    """limit / offset がクエリパラメータに含まれること。"""
    httpx_mock.add_response(
        method="GET",
        json={"issues": [], "total_count": 200, "offset": 50, "limit": 10},
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: ListIssuesResult = await list_issues(client, limit=10, offset=50)

    request = httpx_mock.get_request()
    assert request is not None
    assert "limit=10" in str(request.url)
    assert "offset=50" in str(request.url)
    assert result.total_count == 200


async def test_list_issues_empty(httpx_mock: HTTPXMock) -> None:
    """issueが0件のとき空リストを返すこと。"""
    httpx_mock.add_response(
        method="GET",
        json={"issues": [], "total_count": 0, "offset": 0, "limit": 25},
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: ListIssuesResult = await list_issues(client)

    assert result.issues == []
    assert result.total_count == 0


async def test_list_issues_not_found(httpx_mock: HTTPXMock) -> None:
    """project_id不正時に NOT_FOUND になること。"""
    httpx_mock.add_response(method="GET", status_code=404)

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await list_issues(client, project_id="nonexistent")

    assert exc_info.value.category == ErrorCategory.NOT_FOUND


async def test_list_issues_auth_failed(httpx_mock: HTTPXMock) -> None:
    """401で AUTH_FAILED になること。"""
    httpx_mock.add_response(method="GET", status_code=401)

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await list_issues(client)

    assert exc_info.value.category == ErrorCategory.AUTH_FAILED


async def test_list_issues_timeout(httpx_mock: HTTPXMock) -> None:
    """タイムアウトで SERVER_ERROR になること。"""
    httpx_mock.add_exception(httpx.ReadTimeout("timed out"), method="GET")

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await list_issues(client)

    assert exc_info.value.category == ErrorCategory.SERVER_ERROR


# ---------------------------------------------------------------------------
# get_issue
# ---------------------------------------------------------------------------


async def test_get_issue_success(httpx_mock: HTTPXMock) -> None:
    """正常系: issue詳細をパースして返すこと。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/issues/42.json",
        json=_GET_PAYLOAD,
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        issue: Issue = await get_issue(client, issue_id=42)

    assert issue.id == 42
    assert issue.subject == "Fix login bug"
    assert issue.description == "Users cannot login with special characters."


async def test_get_issue_with_journals(httpx_mock: HTTPXMock) -> None:
    """include=journals 指定時にジャーナルが取得できること。"""
    payload: dict[str, object] = {
        "issue": {
            **_ISSUE_DATA,
            "journals": [
                {
                    "id": 1,
                    "user": {"id": 1, "name": "Admin"},
                    "notes": "Updated status.",
                    "created_on": "2026-05-10T10:00:00Z",
                }
            ],
        }
    }
    httpx_mock.add_response(method="GET", json=payload)

    async with RedmineClient(_TEST_CONFIG) as client:
        issue: Issue = await get_issue(client, issue_id=42, include=["journals"])

    request = httpx_mock.get_request()
    assert request is not None
    assert "include=" in str(request.url)
    assert issue.journals is not None
    assert len(issue.journals) == 1
    assert issue.journals[0].notes == "Updated status."


async def test_get_issue_not_found(httpx_mock: HTTPXMock) -> None:
    """存在しないissueIDで NOT_FOUND になること。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/issues/9999.json",
        status_code=404,
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await get_issue(client, issue_id=9999)

    assert exc_info.value.category == ErrorCategory.NOT_FOUND


async def test_get_issue_auth_failed(httpx_mock: HTTPXMock) -> None:
    """401で AUTH_FAILED になること。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/issues/42.json",
        status_code=401,
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await get_issue(client, issue_id=42)

    assert exc_info.value.category == ErrorCategory.AUTH_FAILED


async def test_get_issue_timeout(httpx_mock: HTTPXMock) -> None:
    """タイムアウトで SERVER_ERROR になること。"""
    httpx_mock.add_exception(
        httpx.ReadTimeout("timed out"),
        method="GET",
        url=f"{_TEST_URL}/issues/42.json",
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await get_issue(client, issue_id=42)

    assert exc_info.value.category == ErrorCategory.SERVER_ERROR

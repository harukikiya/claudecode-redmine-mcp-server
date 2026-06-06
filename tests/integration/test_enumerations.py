"""list_issue_statuses / list_trackers / list_priorities tools の integration テスト。

pytest-httpx でRedmine APIをmockし、各tool関数の動作を検証する。
"""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

from redmine_mcp.client import RedmineClient
from redmine_mcp.config import RedmineConfig
from redmine_mcp.errors import ErrorCategory, RedmineError
from redmine_mcp.tools.enumerations import (
    IssuePriority,
    IssueStatus,
    Tracker,
    list_issue_statuses,
    list_priorities,
    list_trackers,
)

_TEST_URL: str = "http://test.redmine.example"
_TEST_API_KEY: str = "test-api-key-abc123"

_TEST_CONFIG: RedmineConfig = RedmineConfig(
    url=_TEST_URL,
    api_key=_TEST_API_KEY,
)

# ---------------------------------------------------------------------------
# list_issue_statuses
# ---------------------------------------------------------------------------

_STATUSES_PAYLOAD: dict[str, object] = {
    "issue_statuses": [
        {"id": 1, "name": "New", "is_closed": False},
        {"id": 2, "name": "In Progress", "is_closed": False},
        {"id": 5, "name": "Closed", "is_closed": True},
    ]
}


async def test_list_issue_statuses_success(httpx_mock: HTTPXMock) -> None:
    """正常系: ステータス一覧をパースして返すこと。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/issue_statuses.json",
        json=_STATUSES_PAYLOAD,
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: list[IssueStatus] = await list_issue_statuses(client)

    assert len(result) == 3
    assert result[0].id == 1
    assert result[0].name == "New"
    assert result[0].is_closed is False
    assert result[2].is_closed is True


async def test_list_issue_statuses_empty(httpx_mock: HTTPXMock) -> None:
    """ステータスが0件のとき空リストを返すこと。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/issue_statuses.json",
        json={"issue_statuses": []},
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: list[IssueStatus] = await list_issue_statuses(client)

    assert result == []


async def test_list_issue_statuses_auth_failed(httpx_mock: HTTPXMock) -> None:
    """異常系: 401で AUTH_FAILED になること。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/issue_statuses.json",
        status_code=401,
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await list_issue_statuses(client)

    assert exc_info.value.category == ErrorCategory.AUTH_FAILED


async def test_list_issue_statuses_timeout(httpx_mock: HTTPXMock) -> None:
    """タイムアウトで SERVER_ERROR になること。"""
    httpx_mock.add_exception(
        httpx.ReadTimeout("timed out"),
        method="GET",
        url=f"{_TEST_URL}/issue_statuses.json",
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await list_issue_statuses(client)

    assert exc_info.value.category == ErrorCategory.SERVER_ERROR


# ---------------------------------------------------------------------------
# list_trackers
# ---------------------------------------------------------------------------

_TRACKERS_PAYLOAD: dict[str, object] = {
    "trackers": [
        {"id": 1, "name": "Bug"},
        {"id": 2, "name": "Feature"},
        {"id": 3, "name": "Support"},
    ]
}


async def test_list_trackers_success(httpx_mock: HTTPXMock) -> None:
    """正常系: トラッカー一覧をパースして返すこと。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/trackers.json",
        json=_TRACKERS_PAYLOAD,
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: list[Tracker] = await list_trackers(client)

    assert len(result) == 3
    assert result[0].id == 1
    assert result[0].name == "Bug"
    assert result[1].name == "Feature"


async def test_list_trackers_auth_failed(httpx_mock: HTTPXMock) -> None:
    """異常系: 401で AUTH_FAILED になること。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/trackers.json",
        status_code=401,
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await list_trackers(client)

    assert exc_info.value.category == ErrorCategory.AUTH_FAILED


async def test_list_trackers_timeout(httpx_mock: HTTPXMock) -> None:
    """タイムアウトで SERVER_ERROR になること。"""
    httpx_mock.add_exception(
        httpx.ReadTimeout("timed out"),
        method="GET",
        url=f"{_TEST_URL}/trackers.json",
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await list_trackers(client)

    assert exc_info.value.category == ErrorCategory.SERVER_ERROR


# ---------------------------------------------------------------------------
# list_priorities
# ---------------------------------------------------------------------------

_PRIORITIES_PAYLOAD: dict[str, object] = {
    "issue_priorities": [
        {"id": 3, "name": "Low", "is_default": False},
        {"id": 4, "name": "Normal", "is_default": True},
        {"id": 5, "name": "High", "is_default": False},
        {"id": 6, "name": "Urgent", "is_default": False},
    ]
}


async def test_list_priorities_success(httpx_mock: HTTPXMock) -> None:
    """正常系: 優先度一覧をパースして返すこと。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/enumerations/issue_priorities.json",
        json=_PRIORITIES_PAYLOAD,
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: list[IssuePriority] = await list_priorities(client)

    assert len(result) == 4
    assert result[0].id == 3
    assert result[0].name == "Low"
    assert result[0].is_default is False
    assert result[1].is_default is True  # Normal がデフォルト


async def test_list_priorities_auth_failed(httpx_mock: HTTPXMock) -> None:
    """異常系: 401で AUTH_FAILED になること。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/enumerations/issue_priorities.json",
        status_code=401,
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await list_priorities(client)

    assert exc_info.value.category == ErrorCategory.AUTH_FAILED


async def test_list_priorities_timeout(httpx_mock: HTTPXMock) -> None:
    """タイムアウトで SERVER_ERROR になること。"""
    httpx_mock.add_exception(
        httpx.ReadTimeout("timed out"),
        method="GET",
        url=f"{_TEST_URL}/enumerations/issue_priorities.json",
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await list_priorities(client)

    assert exc_info.value.category == ErrorCategory.SERVER_ERROR

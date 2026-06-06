"""list_versions / list_issue_categories tools の integration テスト。

pytest-httpx でRedmine APIをmockし、各tool関数の動作を検証する。
"""

from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from redmine_mcp.client import RedmineClient
from redmine_mcp.config import RedmineConfig
from redmine_mcp.errors import ErrorCategory, RedmineError
from redmine_mcp.tools.project_resources import (
    IssueCategory,
    Version,
    list_issue_categories,
    list_versions,
)

_TEST_URL: str = "http://test.redmine.example"
_TEST_API_KEY: str = "test-api-key-abc123"

_TEST_CONFIG: RedmineConfig = RedmineConfig(
    url=_TEST_URL,
    api_key=_TEST_API_KEY,
)

# ---------------------------------------------------------------------------
# list_versions
# ---------------------------------------------------------------------------

_VERSIONS_PAYLOAD: dict[str, object] = {
    "versions": [
        {
            "id": 1,
            "name": "v1.0",
            "project": {"id": 1, "name": "My Project"},
            "description": "first milestone",
            "status": "closed",
            "due_date": "2026-01-31",
            "created_on": "2025-12-01T00:00:00Z",
            "updated_on": "2026-02-01T00:00:00Z",
        },
        {
            "id": 2,
            "name": "v2.0",
            "project": {"id": 1, "name": "My Project"},
            "status": "open",
            "created_on": "2026-02-01T00:00:00Z",
        },
    ]
}


async def test_list_versions_success(httpx_mock: HTTPXMock) -> None:
    """正常系: バージョン一覧をパースして返すこと。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/projects/myproject/versions.json",
        json=_VERSIONS_PAYLOAD,
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: list[Version] = await list_versions(client, "myproject")

    assert len(result) == 2
    assert result[0].id == 1
    assert result[0].name == "v1.0"
    assert result[0].project.name == "My Project"
    assert result[0].status == "closed"
    # optional フィールド省略時は None になること
    assert result[1].description is None
    assert result[1].due_date is None


async def test_list_versions_empty(httpx_mock: HTTPXMock) -> None:
    """バージョンが0件のとき空リストを返すこと。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/projects/myproject/versions.json",
        json={"versions": []},
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: list[Version] = await list_versions(client, "myproject")

    assert result == []


async def test_list_versions_not_found(httpx_mock: HTTPXMock) -> None:
    """異常系: 存在しないprojectで NOT_FOUND になること。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/projects/nope/versions.json",
        status_code=404,
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await list_versions(client, "nope")

    assert exc_info.value.category == ErrorCategory.NOT_FOUND


# ---------------------------------------------------------------------------
# list_issue_categories
# ---------------------------------------------------------------------------

_CATEGORIES_PAYLOAD: dict[str, object] = {
    "issue_categories": [
        {
            "id": 1,
            "name": "Frontend",
            "project": {"id": 1, "name": "My Project"},
            "assigned_to": {"id": 3, "name": "Jane Dev"},
        },
        {
            "id": 2,
            "name": "Backend",
            "project": {"id": 1, "name": "My Project"},
        },
    ]
}


async def test_list_issue_categories_success(httpx_mock: HTTPXMock) -> None:
    """正常系: カテゴリー一覧をパースして返すこと。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/projects/myproject/issue_categories.json",
        json=_CATEGORIES_PAYLOAD,
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: list[IssueCategory] = await list_issue_categories(client, "myproject")

    assert len(result) == 2
    assert result[0].id == 1
    assert result[0].name == "Frontend"
    assert result[0].assigned_to is not None
    assert result[0].assigned_to.name == "Jane Dev"
    # assigned_to 省略時は None になること
    assert result[1].assigned_to is None


async def test_list_issue_categories_not_found(httpx_mock: HTTPXMock) -> None:
    """異常系: 存在しないprojectで NOT_FOUND になること。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/projects/nope/issue_categories.json",
        status_code=404,
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await list_issue_categories(client, "nope")

    assert exc_info.value.category == ErrorCategory.NOT_FOUND

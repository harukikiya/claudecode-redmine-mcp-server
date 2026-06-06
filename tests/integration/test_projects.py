"""list_projects tool の integration テスト。

pytest-httpx でRedmine APIをmockし、tool関数の動作を検証する。
"""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

from redmine_mcp.client import RedmineClient
from redmine_mcp.config import RedmineConfig
from redmine_mcp.errors import ErrorCategory, RedmineError
from redmine_mcp.tools.projects import ListProjectsResult, Project, list_projects

_TEST_URL: str = "http://test.redmine.example"
_TEST_API_KEY: str = "test-api-key-abc123"

_TEST_CONFIG: RedmineConfig = RedmineConfig(
    url=_TEST_URL,
    api_key=_TEST_API_KEY,
)

_PROJECTS_PAYLOAD: dict[str, object] = {
    "projects": [
        {
            "id": 1,
            "identifier": "myproject",
            "name": "My Project",
            "description": "プロジェクトの説明",
            "status": 1,
            "created_on": "2020-01-01T00:00:00Z",
            "updated_on": "2026-05-01T00:00:00Z",
        },
        {
            "id": 2,
            "identifier": "another",
            "name": "Another Project",
            "description": None,
            "status": 1,
            "created_on": "2021-03-15T00:00:00Z",
            "updated_on": "2026-04-20T00:00:00Z",
        },
    ],
    "total_count": 2,
    "offset": 0,
    "limit": 25,
}


async def test_list_projects_success(httpx_mock: HTTPXMock) -> None:
    """正常系: プロジェクト一覧をパースして返すこと。"""
    # URLにlimit/offsetのクエリパラメータが付くのでmethodのみでマッチ
    httpx_mock.add_response(method="GET", json=_PROJECTS_PAYLOAD)

    async with RedmineClient(_TEST_CONFIG) as client:
        result: ListProjectsResult = await list_projects(client)

    assert result.total_count == 2
    assert result.offset == 0
    assert result.limit == 25
    assert len(result.projects) == 2

    p: Project = result.projects[0]
    assert p.id == 1
    assert p.identifier == "myproject"
    assert p.name == "My Project"
    assert p.status == 1


async def test_list_projects_sends_api_key_header(httpx_mock: HTTPXMock) -> None:
    """API keyヘッダーが正しく送信されること。"""
    httpx_mock.add_response(method="GET", json=_PROJECTS_PAYLOAD)

    async with RedmineClient(_TEST_CONFIG) as client:
        await list_projects(client)

    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["X-Redmine-API-Key"] == _TEST_API_KEY
    assert "/projects.json" in str(request.url)


async def test_list_projects_with_limit_offset(httpx_mock: HTTPXMock) -> None:
    """limit / offset がクエリパラメータに含まれること。"""
    httpx_mock.add_response(
        method="GET",
        json={"projects": [], "total_count": 100, "offset": 50, "limit": 10},
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: ListProjectsResult = await list_projects(client, limit=10, offset=50)

    request = httpx_mock.get_request()
    assert request is not None
    assert "limit=10" in str(request.url)
    assert "offset=50" in str(request.url)
    assert result.total_count == 100


async def test_list_projects_with_include(httpx_mock: HTTPXMock) -> None:
    """include パラメータがカンマ区切りで送信され、埋め込みリソースが返ること。"""
    payload: dict[str, object] = {
        "projects": [
            {
                "id": 1,
                "identifier": "myproject",
                "name": "My Project",
                "status": 1,
                "created_on": "2020-01-01T00:00:00Z",
                "trackers": [{"id": 1, "name": "Bug"}, {"id": 2, "name": "Feature"}],
                "issue_categories": [{"id": 1, "name": "UI"}],
            }
        ],
        "total_count": 1,
        "offset": 0,
        "limit": 25,
    }
    httpx_mock.add_response(method="GET", json=payload)

    async with RedmineClient(_TEST_CONFIG) as client:
        result: ListProjectsResult = await list_projects(
            client, include=["trackers", "issue_categories"]
        )

    request = httpx_mock.get_request()
    assert request is not None
    # include パラメータがURLに含まれること
    assert "include=" in str(request.url)
    # trackers / issue_categoriesが埋め込まれること
    assert result.projects[0].trackers is not None
    assert len(result.projects[0].trackers) == 2
    assert result.projects[0].issue_categories is not None


async def test_list_projects_empty(httpx_mock: HTTPXMock) -> None:
    """プロジェクトが0件のとき空リストを返すこと。"""
    httpx_mock.add_response(
        method="GET",
        json={"projects": [], "total_count": 0, "offset": 0, "limit": 25},
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: ListProjectsResult = await list_projects(client)

    assert result.projects == []
    assert result.total_count == 0


async def test_list_projects_auth_failed(httpx_mock: HTTPXMock) -> None:
    """異常系: 401で AUTH_FAILED になること。"""
    httpx_mock.add_response(method="GET", status_code=401)

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await list_projects(client)

    assert exc_info.value.category == ErrorCategory.AUTH_FAILED


async def test_list_projects_server_error(httpx_mock: HTTPXMock) -> None:
    """異常系: 500で SERVER_ERROR になること。"""
    httpx_mock.add_response(method="GET", status_code=500)

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await list_projects(client)

    assert exc_info.value.category == ErrorCategory.SERVER_ERROR


async def test_list_projects_timeout(httpx_mock: HTTPXMock) -> None:
    """ネットワークタイムアウトで SERVER_ERROR になること。"""
    httpx_mock.add_exception(httpx.ReadTimeout("read timed out"), method="GET")

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await list_projects(client)

    assert exc_info.value.category == ErrorCategory.SERVER_ERROR

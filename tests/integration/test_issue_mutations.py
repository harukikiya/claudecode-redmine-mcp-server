"""create_issue / update_issue tools の integration テスト。

pytest-httpx でRedmine APIをmockし、tool関数の動作を検証する。
"""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

from redmine_mcp.client import RedmineClient
from redmine_mcp.config import RedmineConfig
from redmine_mcp.errors import ErrorCategory, RedmineError
from redmine_mcp.tools.issues import Issue, create_issue, update_issue

_TEST_URL: str = "http://test.redmine.example"
_TEST_API_KEY: str = "test-api-key-abc123"

_TEST_CONFIG: RedmineConfig = RedmineConfig(  # type: ignore[call-arg]
    url=_TEST_URL,
    api_key=_TEST_API_KEY,
)

_CREATED_ISSUE: dict[str, object] = {
    "id": 101,
    "project": {"id": 1, "name": "My Project"},
    "tracker": {"id": 1, "name": "Bug"},
    "status": {"id": 1, "name": "New"},
    "priority": {"id": 4, "name": "Normal"},
    "author": {"id": 1, "name": "Admin"},
    "subject": "Fix login bug",
    "done_ratio": 0,
    "created_on": "2026-05-30T00:00:00Z",
    "updated_on": "2026-05-30T00:00:00Z",
}

_UPDATED_ISSUE: dict[str, object] = {
    **_CREATED_ISSUE,  # type: ignore[arg-type]
    "id": 42,
    "status": {"id": 5, "name": "Closed"},
    "done_ratio": 100,
}


# ---------------------------------------------------------------------------
# create_issue
# ---------------------------------------------------------------------------


async def test_create_issue_success(httpx_mock: HTTPXMock) -> None:
    """正常系: issueが起票されて作成済みissueを返すこと。"""
    httpx_mock.add_response(
        method="POST",
        url=f"{_TEST_URL}/issues.json",
        status_code=201,
        json={"issue": _CREATED_ISSUE},
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: Issue = await create_issue(
            client,
            project_id="myproject",
            subject="Fix login bug",
        )

    assert result.id == 101
    assert result.subject == "Fix login bug"
    assert result.project.name == "My Project"


async def test_create_issue_sends_required_fields(httpx_mock: HTTPXMock) -> None:
    """project_id / subject がリクエストボディに含まれること。"""
    httpx_mock.add_response(
        method="POST",
        url=f"{_TEST_URL}/issues.json",
        status_code=201,
        json={"issue": _CREATED_ISSUE},
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        await create_issue(client, project_id="myproject", subject="Fix login bug")

    request = httpx_mock.get_request()
    assert request is not None
    import json

    body: dict[str, object] = json.loads(request.content)
    issue_body = body["issue"]
    assert issue_body["project_id"] == "myproject"  # type: ignore[index]
    assert issue_body["subject"] == "Fix login bug"  # type: ignore[index]


async def test_create_issue_with_optional_fields(httpx_mock: HTTPXMock) -> None:
    """optional fields がリクエストボディに含まれること。"""
    httpx_mock.add_response(
        method="POST",
        url=f"{_TEST_URL}/issues.json",
        status_code=201,
        json={"issue": _CREATED_ISSUE},
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        await create_issue(
            client,
            project_id="myproject",
            subject="Fix login bug",
            tracker_id=1,
            priority_id=4,
            description="Detailed description.",
            assigned_to_id=2,
        )

    request = httpx_mock.get_request()
    assert request is not None
    import json

    body: dict[str, object] = json.loads(request.content)
    issue_body = body["issue"]  # type: ignore[index]
    assert issue_body["tracker_id"] == 1  # type: ignore[index]
    assert issue_body["priority_id"] == 4  # type: ignore[index]
    assert issue_body["assigned_to_id"] == 2  # type: ignore[index]


async def test_create_issue_validation_error(httpx_mock: HTTPXMock) -> None:
    """422レスポンスで VALIDATION エラーになること。"""
    httpx_mock.add_response(
        method="POST",
        url=f"{_TEST_URL}/issues.json",
        status_code=422,
        text='{"errors": ["Subject cannot be blank"]}',
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await create_issue(client, project_id="myproject", subject="")

    assert exc_info.value.category == ErrorCategory.VALIDATION


async def test_create_issue_not_found(httpx_mock: HTTPXMock) -> None:
    """project_id不正で NOT_FOUND エラーになること。"""
    httpx_mock.add_response(
        method="POST",
        url=f"{_TEST_URL}/issues.json",
        status_code=422,
        text='{"errors": ["Project is invalid"]}',
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await create_issue(client, project_id="nonexistent", subject="Test")

    assert exc_info.value.category == ErrorCategory.VALIDATION


async def test_create_issue_auth_failed(httpx_mock: HTTPXMock) -> None:
    """401で AUTH_FAILED になること。"""
    httpx_mock.add_response(
        method="POST",
        url=f"{_TEST_URL}/issues.json",
        status_code=401,
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await create_issue(client, project_id="myproject", subject="Test")

    assert exc_info.value.category == ErrorCategory.AUTH_FAILED


async def test_create_issue_timeout(httpx_mock: HTTPXMock) -> None:
    """タイムアウトで SERVER_ERROR になること。"""
    httpx_mock.add_exception(
        httpx.ReadTimeout("timed out"),
        method="POST",
        url=f"{_TEST_URL}/issues.json",
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await create_issue(client, project_id="myproject", subject="Test")

    assert exc_info.value.category == ErrorCategory.SERVER_ERROR


# ---------------------------------------------------------------------------
# update_issue
# ---------------------------------------------------------------------------


async def test_update_issue_success(httpx_mock: HTTPXMock) -> None:
    """正常系: PUT成功後にGETで取得した更新済みissueを返すこと。"""
    # PUT: 200 or 204
    httpx_mock.add_response(
        method="PUT",
        url=f"{_TEST_URL}/issues/42.json",
        status_code=200,
    )
    # GET after update
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/issues/42.json",
        json={"issue": _UPDATED_ISSUE},
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: Issue = await update_issue(client, issue_id=42, status_id=5, done_ratio=100)

    assert result.id == 42
    assert result.status.name == "Closed"
    assert result.done_ratio == 100


async def test_update_issue_with_notes(httpx_mock: HTTPXMock) -> None:
    """notes がリクエストボディに含まれること。"""
    httpx_mock.add_response(
        method="PUT",
        url=f"{_TEST_URL}/issues/42.json",
        status_code=200,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/issues/42.json",
        json={"issue": _UPDATED_ISSUE},
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        await update_issue(client, issue_id=42, notes="Resolved in v1.2", status_id=5)

    requests = httpx_mock.get_requests()
    put_request = next(r for r in requests if r.method == "PUT")
    import json

    body: dict[str, object] = json.loads(put_request.content)
    issue_body = body["issue"]  # type: ignore[index]
    assert issue_body["notes"] == "Resolved in v1.2"  # type: ignore[index]
    assert issue_body["status_id"] == 5  # type: ignore[index]


async def test_update_issue_not_found(httpx_mock: HTTPXMock) -> None:
    """存在しないissueIDで NOT_FOUND になること。"""
    httpx_mock.add_response(
        method="PUT",
        url=f"{_TEST_URL}/issues/9999.json",
        status_code=404,
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await update_issue(client, issue_id=9999, status_id=5)

    assert exc_info.value.category == ErrorCategory.NOT_FOUND


async def test_update_issue_validation_error(httpx_mock: HTTPXMock) -> None:
    """422で VALIDATION エラーになること。"""
    httpx_mock.add_response(
        method="PUT",
        url=f"{_TEST_URL}/issues/42.json",
        status_code=422,
        text='{"errors": ["Done ratio must be between 0 and 100"]}',
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await update_issue(client, issue_id=42, done_ratio=999)

    assert exc_info.value.category == ErrorCategory.VALIDATION


async def test_update_issue_auth_failed(httpx_mock: HTTPXMock) -> None:
    """401で AUTH_FAILED になること。"""
    httpx_mock.add_response(
        method="PUT",
        url=f"{_TEST_URL}/issues/42.json",
        status_code=401,
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await update_issue(client, issue_id=42, status_id=5)

    assert exc_info.value.category == ErrorCategory.AUTH_FAILED

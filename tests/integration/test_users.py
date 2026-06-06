"""get_current_user tool の integration テスト。

pytest-httpx でRedmine APIをmockし、tool関数の動作を検証する。
"""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

from redmine_mcp.client import RedmineClient
from redmine_mcp.config import RedmineConfig
from redmine_mcp.errors import ErrorCategory, RedmineError
from redmine_mcp.tools.users import CurrentUser, get_current_user

_TEST_URL: str = "http://test.redmine.example"
_TEST_API_KEY: str = "test-api-key-abc123"

_TEST_CONFIG: RedmineConfig = RedmineConfig(
    url=_TEST_URL,
    api_key=_TEST_API_KEY,
)

_USER_PAYLOAD: dict[str, object] = {
    "user": {
        "id": 1,
        "login": "jsmith",
        "firstname": "John",
        "lastname": "Smith",
        "mail": "jsmith@example.com",
        "created_on": "2020-01-01T00:00:00Z",
        "last_login_on": "2026-05-29T10:00:00Z",
        # 未知フィールド（extra="ignore" で無視されること確認）
        "api_key": "should-be-ignored",
        "status": 1,
    }
}


async def test_get_current_user_success(httpx_mock: HTTPXMock) -> None:
    """正常系: ユーザー情報を正しくパースして返すこと。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/users/current.json",
        json=_USER_PAYLOAD,
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: CurrentUser = await get_current_user(client)

    assert result.id == 1
    assert result.login == "jsmith"
    assert result.firstname == "John"
    assert result.lastname == "Smith"
    assert result.mail == "jsmith@example.com"
    assert result.last_login_on == "2026-05-29T10:00:00Z"


async def test_get_current_user_sends_api_key_header(httpx_mock: HTTPXMock) -> None:
    """API keyヘッダーが正しく送信されること。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/users/current.json",
        json=_USER_PAYLOAD,
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        await get_current_user(client)

    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["X-Redmine-API-Key"] == _TEST_API_KEY


async def test_get_current_user_auth_failed(httpx_mock: HTTPXMock) -> None:
    """異常系: 401レスポンスで AUTH_FAILED エラーになること。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/users/current.json",
        status_code=401,
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await get_current_user(client)

    assert exc_info.value.category == ErrorCategory.AUTH_FAILED


async def test_get_current_user_forbidden(httpx_mock: HTTPXMock) -> None:
    """異常系: 403レスポンスで AUTH_FAILED エラーになること。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/users/current.json",
        status_code=403,
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await get_current_user(client)

    assert exc_info.value.category == ErrorCategory.AUTH_FAILED


async def test_get_current_user_server_error(httpx_mock: HTTPXMock) -> None:
    """異常系: 500レスポンスで SERVER_ERROR になること。"""
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/users/current.json",
        status_code=500,
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await get_current_user(client)

    assert exc_info.value.category == ErrorCategory.SERVER_ERROR


async def test_get_current_user_timeout(httpx_mock: HTTPXMock) -> None:
    """ネットワークタイムアウトで SERVER_ERROR になること。"""
    httpx_mock.add_exception(
        httpx.ReadTimeout("read timed out"),
        method="GET",
        url=f"{_TEST_URL}/users/current.json",
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await get_current_user(client)

    assert exc_info.value.category == ErrorCategory.SERVER_ERROR


async def test_get_current_user_connect_error(httpx_mock: HTTPXMock) -> None:
    """接続失敗で SERVER_ERROR になること。"""
    httpx_mock.add_exception(
        httpx.ConnectError("connection refused"),
        method="GET",
        url=f"{_TEST_URL}/users/current.json",
    )

    with pytest.raises(RedmineError) as exc_info:
        async with RedmineClient(_TEST_CONFIG) as client:
            await get_current_user(client)

    assert exc_info.value.category == ErrorCategory.SERVER_ERROR


async def test_get_current_user_mail_optional(httpx_mock: HTTPXMock) -> None:
    """mailフィールドが省略されていても正常にパースできること。"""
    payload: dict[str, object] = {
        "user": {
            "id": 2,
            "login": "nomail",
            "firstname": "No",
            "lastname": "Mail",
            "created_on": "2021-06-01T00:00:00Z",
            "last_login_on": None,
        }
    }
    httpx_mock.add_response(
        method="GET",
        url=f"{_TEST_URL}/users/current.json",
        json=payload,
    )

    async with RedmineClient(_TEST_CONFIG) as client:
        result: CurrentUser = await get_current_user(client)

    assert result.mail is None
    assert result.last_login_on is None

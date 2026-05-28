"""Redmine ユーザー関連 MCP tools。

get_current_user toolを提供する。認証確認および自分のuser ID解決に使う。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from redmine_mcp.client import RedmineClient


class CurrentUser(BaseModel):
    """現在の認証ユーザー情報。

    Redmineの ``GET /users/current.json`` が返すuserオブジェクト。
    未知フィールド（api_key, custom_fields 等）は無視する。

    Attributes:
        id: ユーザーの数値ID。
        login: ログイン名。
        firstname: 名（first name）。
        lastname: 姓（last name）。
        mail: メールアドレス。Redmine設定によっては省略される場合がある。
        created_on: アカウント作成日時（ISO 8601文字列）。
        last_login_on: 最終ログイン日時（ISO 8601文字列）。未ログインはNone。
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    login: str
    firstname: str
    lastname: str
    mail: str | None = None
    created_on: str
    last_login_on: str | None = None


async def get_current_user(client: RedmineClient) -> CurrentUser:
    """現在の認証ユーザーの情報を取得する。

    Redmineの ``GET /users/current.json`` をwrapする。
    APIキーが有効かどうかの確認（auth疎通確認）および
    自分のuser IDを解決するために使う。

    Args:
        client: Redmine APIクライアント。

    Returns:
        現在の認証ユーザーの情報を含む ``CurrentUser``。

    Raises:
        RedmineError: APIキーが不正な場合（AUTH_FAILED）。

    Example:
        >>> async with RedmineClient(config) as client:
        ...     user = await get_current_user(client)
        ...     print(user.login)
        'jsmith'
    """
    data: dict[str, Any] = await client.get("/users/current.json")
    user_data: dict[str, Any] = data["user"]
    return CurrentUser.model_validate(user_data)

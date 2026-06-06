"""Redmine ユーザー関連 MCP tools。

get_current_user / list_users toolを提供する。認証確認・自分のuser ID解決、
および assignee 検索のための user 一覧取得に使う。
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


class User(BaseModel):
    """list_users が返す user 一覧の1要素。

    Redmineの ``GET /users.json`` が返すuserオブジェクト。
    login / mail 等はadmin権限や設定により省略される場合があるためoptional。
    未知フィールド（custom_fields 等）は無視する。

    Attributes:
        id: ユーザーの数値ID。assigned_to_id 等に使う。
        firstname: 名（first name）。
        lastname: 姓（last name）。
        login: ログイン名。権限により省略される場合がある。
        mail: メールアドレス。権限により省略される場合がある。
        status: アカウントステータス（1: active, 2: registered, 3: locked）。
        created_on: アカウント作成日時（ISO 8601文字列）。未取得時はNone。
        last_login_on: 最終ログイン日時（ISO 8601文字列）。未ログインはNone。
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    firstname: str
    lastname: str
    login: str | None = None
    mail: str | None = None
    status: int | None = None
    created_on: str | None = None
    last_login_on: str | None = None


class ListUsersResult(BaseModel):
    """list_users の戻り値。

    Attributes:
        users: ユーザーのリスト。
        total_count: 全件数。
        offset: 取得開始位置。
        limit: 最大取得件数。
    """

    users: list[User]
    total_count: int
    offset: int
    limit: int


async def list_users(
    client: RedmineClient,
    name: str | None = None,
    status: int | None = None,
    limit: int = 25,
    offset: int = 0,
) -> ListUsersResult:
    """user 一覧を取得する（assignee 検索用）。

    Redmineの ``GET /users.json`` をwrapする。
    issue の assigned_to_id を解決するために user を探す用途で使う。

    Note:
        このAPIはadmin権限を必要とする。個人運用ではadmin keyを使うため通常は
        問題ないが、権限不足の場合は ``AUTH_FAILED``（403）が返る。

    Args:
        client: Redmine APIクライアント。
        name: login / firstname / lastname / mail への部分一致でfilterする。
        status: アカウントステータスでfilter（1: active, 2: registered, 3: locked）。
        limit: 取得件数上限（default 25, max 100）。
        offset: ページネーションオフセット。

    Returns:
        ユーザー一覧とページネーション情報を含む ``ListUsersResult``。

    Raises:
        RedmineError: 認証エラー・権限不足（AUTH_FAILED）またはネットワークエラー。

    Example:
        >>> async with RedmineClient(config) as client:
        ...     result = await list_users(client, name="smith")
        ...     for u in result.users:
        ...         print(u.id, u.firstname, u.lastname)
        1 John Smith
    """
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if name is not None:
        params["name"] = name
    if status is not None:
        params["status"] = status

    data: dict[str, Any] = await client.get("/users.json", params=params)

    users: list[User] = [User.model_validate(u) for u in data.get("users", [])]
    total_count: int = data.get("total_count", len(users))
    resp_offset: int = data.get("offset", offset)
    resp_limit: int = data.get("limit", limit)

    return ListUsersResult(
        users=users,
        total_count=total_count,
        offset=resp_offset,
        limit=resp_limit,
    )

"""Redmine プロジェクトリソース（version / issue category）取得 MCP tools。

project_id を必須引数として受け取り、そのプロジェクトに紐づく
version（マイルストーン）と issue category の一覧を返す。
create_issue で fixed_version_id / category_id を指定するときに使う。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from redmine_mcp.client import RedmineClient


class ProjectRef(BaseModel):
    """リソースが属するプロジェクトの参照情報。

    version / issue category の ``project`` フィールドで共用する。

    Attributes:
        id: プロジェクトの数値ID。
        name: プロジェクト表示名。
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str


class Version(BaseModel):
    """Redmine バージョン（マイルストーン）。

    Attributes:
        id: バージョンの数値ID。create_issue の fixed_version_id に使う。
        name: バージョン名（例: ``v1.0``, ``Sprint 3``）。
        project: バージョンが属するプロジェクトの参照情報。
        description: バージョンの説明。未設定時はNone。
        status: バージョンのステータス（``open``, ``locked``, ``closed``）。
        due_date: 期日（YYYY-MM-DD形式）。未設定時はNone。
        created_on: 作成日時（ISO 8601文字列）。
        updated_on: 最終更新日時（ISO 8601文字列）。未設定時はNone。
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    project: ProjectRef
    description: str | None = None
    status: str
    due_date: str | None = None
    created_on: str
    updated_on: str | None = None


class IssueCategoryAssignee(BaseModel):
    """IssueCategoryのデフォルト担当者参照情報。

    Attributes:
        id: ユーザーの数値ID。
        name: ユーザー表示名。
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str


class IssueCategory(BaseModel):
    """Redmine issue カテゴリー。

    Attributes:
        id: カテゴリーの数値ID。create_issue の category_id に使う。
        name: カテゴリー名（例: ``Frontend``, ``Backend``, ``Database``）。
        project: カテゴリーが属するプロジェクトの参照情報。
        assigned_to: カテゴリーのデフォルト担当者。未設定時はNone。
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    project: ProjectRef
    assigned_to: IssueCategoryAssignee | None = None


async def list_versions(client: RedmineClient, project_id: str) -> list[Version]:
    """プロジェクト内のバージョン（マイルストーン）一覧を取得する。

    Redmineの ``GET /projects/:project_id/versions.json`` をwrapする。
    create_issue で fixed_version_id を指定するときに使う。

    Args:
        client: Redmine APIクライアント。
        project_id: バージョンを取得するプロジェクトのidentifierまたは数値ID。

    Returns:
        ``Version`` のリスト（プロジェクト内全バージョン）。

    Raises:
        RedmineError: 認証エラーまたはネットワークエラーが発生した場合。
        RedmineError(NOT_FOUND): 指定した project_id のプロジェクトが存在しない場合。

    Example:
        >>> async with RedmineClient(config) as client:
        ...     versions = await list_versions(client, "myproject")
        ...     for v in versions:
        ...         print(v.id, v.name, v.status)
        1 v1.0 open
        2 v2.0 locked
    """
    data: dict[str, Any] = await client.get(f"/projects/{project_id}/versions.json")
    return [Version.model_validate(v) for v in data.get("versions", [])]


async def list_issue_categories(client: RedmineClient, project_id: str) -> list[IssueCategory]:
    """プロジェクト内のissueカテゴリー一覧を取得する。

    Redmineの ``GET /projects/:project_id/issue_categories.json`` をwrapする。
    create_issue で category_id を指定するときに使う。

    Args:
        client: Redmine APIクライアント。
        project_id: カテゴリーを取得するプロジェクトのidentifierまたは数値ID。

    Returns:
        ``IssueCategory`` のリスト（プロジェクト内全カテゴリー）。

    Raises:
        RedmineError: 認証エラーまたはネットワークエラーが発生した場合。
        RedmineError(NOT_FOUND): 指定した project_id のプロジェクトが存在しない場合。

    Example:
        >>> async with RedmineClient(config) as client:
        ...     categories = await list_issue_categories(client, "myproject")
        ...     for c in categories:
        ...         print(c.id, c.name)
        1 Frontend
        2 Backend
    """
    data: dict[str, Any] = await client.get(f"/projects/{project_id}/issue_categories.json")
    return [IssueCategory.model_validate(c) for c in data.get("issue_categories", [])]

"""Redmine プロジェクト関連 MCP tools。

list_projects toolを提供する。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from redmine_mcp.client import RedmineClient


class Tracker(BaseModel):
    """プロジェクトに紐づくトラッカー（include=trackers で取得）。

    Attributes:
        id: トラッカーの数値ID。
        name: トラッカー名。
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str


class IssueCategory(BaseModel):
    """プロジェクトに紐づくissueカテゴリー（include=issue_categories で取得）。

    Attributes:
        id: カテゴリーの数値ID。
        name: カテゴリー名。
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str


class Project(BaseModel):
    """Redmineプロジェクト情報。

    Attributes:
        id: プロジェクトの数値ID。
        identifier: URLスラッグ（例: ``rp2040``）。
        name: プロジェクト表示名。
        description: プロジェクト説明。未設定時はNone。
        status: ステータスコード（1: active, 5: archived, 9: closed）。
        created_on: 作成日時（ISO 8601文字列）。
        updated_on: 最終更新日時（ISO 8601文字列）。
        trackers: include=trackers 指定時のみ返る。
        issue_categories: include=issue_categories 指定時のみ返る。
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    identifier: str
    name: str
    description: str | None = None
    status: int
    created_on: str
    updated_on: str | None = None
    trackers: list[Tracker] | None = None
    issue_categories: list[IssueCategory] | None = None


class ListProjectsResult(BaseModel):
    """list_projects の戻り値。

    Attributes:
        projects: プロジェクトのリスト。
        total_count: 全件数。
        offset: 取得開始位置。
        limit: 最大取得件数。
    """

    projects: list[Project]
    total_count: int
    offset: int
    limit: int


async def list_projects(
    client: RedmineClient,
    include: list[str] | None = None,
    limit: int = 25,
    offset: int = 0,
) -> ListProjectsResult:
    """自分が参照できるプロジェクト一覧を取得する。

    Redmineの ``GET /projects.json`` をwrapする。
    create_issue / list_issues の前に project_id を調べるために使う。

    Args:
        client: Redmine APIクライアント。
        include: 追加取得するリソース名のリスト。
            指定可能な値: ``trackers``, ``issue_categories``,
            ``enabled_modules``, ``time_entry_activities``.
        limit: 取得件数上限（default 25, max 100）。
        offset: ページネーションオフセット。

    Returns:
        プロジェクト一覧とページネーション情報を含む ``ListProjectsResult``。

    Raises:
        RedmineError: 認証エラーまたはネットワークエラーが発生した場合。

    Example:
        >>> async with RedmineClient(config) as client:
        ...     result = await list_projects(client, limit=10)
        ...     for p in result.projects:
        ...         print(p.identifier, p.name)
        'myproject My Project'
    """
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if include:
        params["include"] = ",".join(include)

    data: dict[str, Any] = await client.get("/projects.json", params=params)

    projects: list[Project] = [Project.model_validate(p) for p in data.get("projects", [])]
    total_count: int = data.get("total_count", len(projects))
    resp_offset: int = data.get("offset", offset)
    resp_limit: int = data.get("limit", limit)

    return ListProjectsResult(
        projects=projects,
        total_count=total_count,
        offset=resp_offset,
        limit=resp_limit,
    )

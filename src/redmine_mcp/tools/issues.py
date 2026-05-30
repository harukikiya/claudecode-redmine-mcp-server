"""Redmine issue 関連 MCP tools。

list_issues / get_issue toolを提供する。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from redmine_mcp.client import RedmineClient


class IssueRef(BaseModel):
    """他リソースへの参照（id + nameの組）。

    Attributes:
        id: 参照先の数値ID。
        name: 参照先の表示名。
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str


class Journal(BaseModel):
    """issueの変更履歴エントリ（include=journals 指定時に返る）。

    Attributes:
        id: ジャーナルの数値ID。
        user: 変更したユーザー。
        notes: コメントテキスト。空の場合はNone。
        created_on: 変更日時（ISO 8601文字列）。
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    user: IssueRef
    notes: str | None = None
    created_on: str


class Issue(BaseModel):
    """Redmine issueの詳細情報。

    Attributes:
        id: issueの数値ID。
        project: 所属プロジェクト。
        tracker: トラッカー。
        status: ステータス。
        priority: 優先度。
        author: 作成者。
        assigned_to: 担当者。未設定時はNone。
        subject: タイトル。
        description: 詳細説明。
        start_date: 開始日（YYYY-MM-DD）。
        due_date: 期日（YYYY-MM-DD）。
        done_ratio: 進捗率（0〜100）。
        estimated_hours: 予定工数。
        created_on: 作成日時（ISO 8601文字列）。
        updated_on: 最終更新日時（ISO 8601文字列）。
        journals: 変更履歴（include=journals 指定時のみ）。
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    project: IssueRef
    tracker: IssueRef
    status: IssueRef
    priority: IssueRef
    author: IssueRef
    assigned_to: IssueRef | None = None
    subject: str
    description: str | None = None
    start_date: str | None = None
    due_date: str | None = None
    done_ratio: int = 0
    estimated_hours: float | None = None
    created_on: str
    updated_on: str
    journals: list[Journal] | None = None


class ListIssuesResult(BaseModel):
    """list_issues の戻り値。

    Attributes:
        issues: issueのリスト。
        total_count: 全件数。
        offset: 取得開始位置。
        limit: 最大取得件数。
    """

    issues: list[Issue]
    total_count: int
    offset: int
    limit: int


async def list_issues(
    client: RedmineClient,
    project_id: str | None = None,
    status_id: str | None = None,
    assigned_to_id: str | None = None,
    tracker_id: int | None = None,
    priority_id: int | None = None,
    subject: str | None = None,
    limit: int = 25,
    offset: int = 0,
    sort: str | None = None,
    include: list[str] | None = None,
) -> ListIssuesResult:
    """filter付きでissue一覧を取得する。

    Redmineの ``GET /issues.json`` をwrapする。
    project / status / 担当者等でfilterできる。

    Args:
        client: Redmine APIクライアント。
        project_id: プロジェクトのidentifierまたは数値IDでfilterする。
        status_id: ステータスでfilterする。
            特殊値: ``open``（オープン全て）, ``closed``（クローズ全て）, ``*``（全て）。
            省略時はRedmineデフォルト（openのみ）。
        assigned_to_id: 担当者の数値IDでfilterする。
            ``me`` で自分にassignされたissueを取得できる。
        tracker_id: トラッカーの数値IDでfilterする。
        priority_id: 優先度の数値IDでfilterする。
        subject: タイトルの部分一致filterする（大文字小文字区別なし）。
        limit: 取得件数上限（default 25, max 100）。
        offset: ページネーションオフセット。
        sort: ソート条件（例: ``updated_on:desc``, ``priority:asc``）。
        include: 追加取得するリソース名のリスト。
            指定可能な値: ``journals``, ``attachments``, ``relations``,
            ``watchers``, ``children``.

    Returns:
        issueのリストとページネーション情報を含む ``ListIssuesResult``。

    Raises:
        RedmineError: 認証エラー、project_id不正、ネットワークエラーが発生した場合。

    Example:
        >>> async with RedmineClient(config) as client:
        ...     result = await list_issues(
        ...         client,
        ...         project_id="myproject",
        ...         status_id="open",
        ...         assigned_to_id="me",
        ...     )
        ...     for issue in result.issues:
        ...         print(issue.id, issue.subject)
        42 Fix login bug
    """
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if project_id is not None:
        params["project_id"] = project_id
    if status_id is not None:
        params["status_id"] = status_id
    if assigned_to_id is not None:
        params["assigned_to_id"] = assigned_to_id
    if tracker_id is not None:
        params["tracker_id"] = tracker_id
    if priority_id is not None:
        params["priority_id"] = priority_id
    if subject is not None:
        params["subject"] = subject
    if sort is not None:
        params["sort"] = sort
    if include:
        params["include"] = ",".join(include)

    data: dict[str, Any] = await client.get("/issues.json", params=params)

    issues: list[Issue] = [Issue.model_validate(i) for i in data.get("issues", [])]
    total_count: int = data.get("total_count", len(issues))
    resp_offset: int = data.get("offset", offset)
    resp_limit: int = data.get("limit", limit)

    return ListIssuesResult(
        issues=issues,
        total_count=total_count,
        offset=resp_offset,
        limit=resp_limit,
    )


async def get_issue(
    client: RedmineClient,
    issue_id: int,
    include: list[str] | None = None,
) -> Issue:
    """単一issueの詳細を取得する。

    Redmineの ``GET /issues/:id.json`` をwrapする。

    Args:
        client: Redmine APIクライアント。
        issue_id: 取得するissueの数値ID。
        include: 追加取得するリソース名のリスト。
            指定可能な値: ``journals``, ``attachments``, ``relations``,
            ``watchers``, ``children``.

    Returns:
        issueの詳細情報を含む ``Issue``。

    Raises:
        RedmineError: issueが存在しない場合（NOT_FOUND）、
            認証エラー（AUTH_FAILED）、ネットワークエラー（SERVER_ERROR）。

    Example:
        >>> async with RedmineClient(config) as client:
        ...     issue = await get_issue(client, 42, include=["journals"])
        ...     print(issue.subject)
        'Fix login bug'
    """
    params: dict[str, Any] = {}
    if include:
        params["include"] = ",".join(include)

    data: dict[str, Any] = await client.get(
        f"/issues/{issue_id}.json",
        params=params if params else None,
    )
    issue_data: dict[str, Any] = data["issue"]
    return Issue.model_validate(issue_data)

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


async def create_issue(
    client: RedmineClient,
    project_id: str,
    subject: str,
    tracker_id: int | None = None,
    status_id: int | None = None,
    priority_id: int | None = None,
    description: str | None = None,
    assigned_to_id: int | None = None,
    category_id: int | None = None,
    fixed_version_id: int | None = None,
    parent_issue_id: int | None = None,
    start_date: str | None = None,
    due_date: str | None = None,
    estimated_hours: float | None = None,
    done_ratio: int | None = None,
    watcher_user_ids: list[int] | None = None,
) -> Issue:
    """Redmineにissueを起票する。

    Redmineの ``POST /issues.json`` をwrapする。
    同名のissueが複数作られるリスクがあるため、重複チェックは呼び出し側の責任。

    Args:
        client: Redmine APIクライアント。
        project_id: 起票先プロジェクトのidentifierまたは数値ID（必須）。
        subject: issueのタイトル（必須）。
        tracker_id: トラッカーの数値ID。省略時はRedmineのデフォルト。
        status_id: ステータスの数値ID。省略時はRedmineのデフォルト。
        priority_id: 優先度の数値ID。省略時はRedmineのデフォルト。
        description: issue詳細説明。
        assigned_to_id: 担当者の数値ID。
        category_id: issueカテゴリーの数値ID。
        fixed_version_id: 対象バージョン（マイルストーン）の数値ID。
        parent_issue_id: 親issueの数値ID。
        start_date: 開始日（YYYY-MM-DD形式）。
        due_date: 期日（YYYY-MM-DD形式）。
        estimated_hours: 予定工数（時間）。
        done_ratio: 進捗率（0〜100の整数）。
        watcher_user_ids: ウォッチャーに追加するユーザーIDのリスト。

    Returns:
        作成されたissueの詳細を含む ``Issue``。

    Raises:
        RedmineError: project_idが不正な場合（NOT_FOUND）、
            バリデーションエラー（VALIDATION）、
            認証エラー（AUTH_FAILED）。

    Example:
        >>> async with RedmineClient(config) as client:
        ...     issue = await create_issue(
        ...         client,
        ...         project_id="myproject",
        ...         subject="Fix login bug",
        ...         description="Users cannot login.",
        ...         tracker_id=1,
        ...     )
        ...     print(issue.id, issue.subject)
        42 Fix login bug
    """
    body: dict[str, Any] = {
        "project_id": project_id,
        "subject": subject,
    }
    if tracker_id is not None:
        body["tracker_id"] = tracker_id
    if status_id is not None:
        body["status_id"] = status_id
    if priority_id is not None:
        body["priority_id"] = priority_id
    if description is not None:
        body["description"] = description
    if assigned_to_id is not None:
        body["assigned_to_id"] = assigned_to_id
    if category_id is not None:
        body["category_id"] = category_id
    if fixed_version_id is not None:
        body["fixed_version_id"] = fixed_version_id
    if parent_issue_id is not None:
        body["parent_issue_id"] = parent_issue_id
    if start_date is not None:
        body["start_date"] = start_date
    if due_date is not None:
        body["due_date"] = due_date
    if estimated_hours is not None:
        body["estimated_hours"] = estimated_hours
    if done_ratio is not None:
        body["done_ratio"] = done_ratio
    if watcher_user_ids is not None:
        body["watcher_user_ids"] = watcher_user_ids

    data: dict[str, Any] = await client.post("/issues.json", json={"issue": body})
    return Issue.model_validate(data["issue"])


async def update_issue(
    client: RedmineClient,
    issue_id: int,
    subject: str | None = None,
    tracker_id: int | None = None,
    status_id: int | None = None,
    priority_id: int | None = None,
    description: str | None = None,
    assigned_to_id: int | None = None,
    category_id: int | None = None,
    fixed_version_id: int | None = None,
    parent_issue_id: int | None = None,
    start_date: str | None = None,
    due_date: str | None = None,
    estimated_hours: float | None = None,
    done_ratio: int | None = None,
    notes: str | None = None,
    private_notes: bool | None = None,
) -> Issue:
    """Redmineのissueを更新する。ステータス遷移やコメント追加に使う。

    Redmineの ``PUT /issues/:id.json`` をwrapする。
    更新後に ``GET /issues/:id.json`` で最新状態を取得して返す。

    Args:
        client: Redmine APIクライアント。
        issue_id: 更新するissueの数値ID（必須）。
        subject: 新しいタイトル。
        tracker_id: 新しいトラッカーの数値ID。
        status_id: 新しいステータスの数値ID。
        priority_id: 新しい優先度の数値ID。
        description: 新しい詳細説明。
        assigned_to_id: 新しい担当者の数値ID。
        category_id: 新しいissueカテゴリーの数値ID。
        fixed_version_id: 新しい対象バージョンの数値ID。
        parent_issue_id: 新しい親issueの数値ID。
        start_date: 新しい開始日（YYYY-MM-DD形式）。
        due_date: 新しい期日（YYYY-MM-DD形式）。
        estimated_hours: 新しい予定工数（時間）。
        done_ratio: 新しい進捗率（0〜100の整数）。
        notes: ジャーナルに残すコメントテキスト。
        private_notes: Trueのとき非公開コメントとして記録。

    Returns:
        更新後のissueの詳細を含む ``Issue``。

    Raises:
        RedmineError: issueが存在しない場合（NOT_FOUND）、
            バリデーションエラー（VALIDATION）、
            認証エラー（AUTH_FAILED）。

    Example:
        >>> async with RedmineClient(config) as client:
        ...     issue = await update_issue(
        ...         client,
        ...         issue_id=42,
        ...         status_id=5,
        ...         notes="Resolved in v1.2",
        ...     )
        ...     print(issue.status.name)
        'Closed'
    """
    body: dict[str, Any] = {}
    if subject is not None:
        body["subject"] = subject
    if tracker_id is not None:
        body["tracker_id"] = tracker_id
    if status_id is not None:
        body["status_id"] = status_id
    if priority_id is not None:
        body["priority_id"] = priority_id
    if description is not None:
        body["description"] = description
    if assigned_to_id is not None:
        body["assigned_to_id"] = assigned_to_id
    if category_id is not None:
        body["category_id"] = category_id
    if fixed_version_id is not None:
        body["fixed_version_id"] = fixed_version_id
    if parent_issue_id is not None:
        body["parent_issue_id"] = parent_issue_id
    if start_date is not None:
        body["start_date"] = start_date
    if due_date is not None:
        body["due_date"] = due_date
    if estimated_hours is not None:
        body["estimated_hours"] = estimated_hours
    if done_ratio is not None:
        body["done_ratio"] = done_ratio
    if notes is not None:
        body["notes"] = notes
    if private_notes is not None:
        body["private_notes"] = private_notes

    await client.put(f"/issues/{issue_id}.json", json={"issue": body})

    # PUTは204を返すことがあるため、更新後のissueをGETで取得して返す
    data: dict[str, Any] = await client.get(f"/issues/{issue_id}.json")
    return Issue.model_validate(data["issue"])

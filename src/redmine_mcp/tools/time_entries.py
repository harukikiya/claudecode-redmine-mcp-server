"""Redmine 工数記録（time entry）関連 MCP tools。

list_time_entries / create_time_entry / update_time_entry toolを提供する。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from redmine_mcp.client import RedmineClient


class TimeEntryRef(BaseModel):
    """工数記録が参照するリソースの基本情報（id + name）。

    Attributes:
        id: 参照先の数値ID。
        name: 参照先の表示名。
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str


class TimeEntry(BaseModel):
    """Redmine 工数記録エントリ。

    Attributes:
        id: 工数記録の数値ID。
        project: 所属プロジェクト。
        issue: 紐付けられたissue。issue未指定の場合はNone。
        user: 記録したユーザー。
        activity: 作業種別。
        hours: 記録工数（時間）。
        comments: コメント。
        spent_on: 作業日（YYYY-MM-DD形式）。
        created_on: レコード作成日時（ISO 8601文字列）。
        updated_on: レコード最終更新日時（ISO 8601文字列）。
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    project: TimeEntryRef
    issue: TimeEntryRef | None = None
    user: TimeEntryRef
    activity: TimeEntryRef
    hours: float
    comments: str | None = None
    spent_on: str
    created_on: str
    updated_on: str


class ListTimeEntriesResult(BaseModel):
    """list_time_entries の戻り値。

    Attributes:
        time_entries: 工数記録のリスト。
        total_count: 全件数。
        offset: 取得開始位置。
        limit: 最大取得件数。
    """

    time_entries: list[TimeEntry]
    total_count: int
    offset: int
    limit: int


async def list_time_entries(
    client: RedmineClient,
    issue_id: int | None = None,
    project_id: str | None = None,
    user_id: int | None = None,
    spent_on: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> ListTimeEntriesResult:
    """工数記録一覧を取得する。

    Redmineの ``GET /time_entries.json`` をwrapする。
    issue / project / ユーザー / 日付でfilterできる。

    Args:
        client: Redmine APIクライアント。
        issue_id: 特定issueの工数記録のみ取得する場合に指定。
        project_id: 特定プロジェクトの工数記録のみ取得する場合に指定。
        user_id: 特定ユーザーの工数記録のみ取得する場合に指定。
        spent_on: 特定日（YYYY-MM-DD）の工数記録のみ取得。
        from_date: 指定日以降の工数記録を取得（YYYY-MM-DD）。
        to_date: 指定日以前の工数記録を取得（YYYY-MM-DD）。
        limit: 取得件数上限（default 25, max 100）。
        offset: ページネーションオフセット。

    Returns:
        工数記録のリストとページネーション情報を含む ``ListTimeEntriesResult``。

    Raises:
        RedmineError: 認証エラーまたはネットワークエラーが発生した場合。

    Example:
        >>> async with RedmineClient(config) as client:
        ...     result = await list_time_entries(client, issue_id=42)
        ...     total = sum(e.hours for e in result.time_entries)
        ...     print(f"Total: {total}h")
        Total: 5.5h
    """
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if issue_id is not None:
        params["issue_id"] = issue_id
    if project_id is not None:
        params["project_id"] = project_id
    if user_id is not None:
        params["user_id"] = user_id
    if spent_on is not None:
        params["spent_on"] = spent_on
    if from_date is not None:
        params["from"] = from_date
    if to_date is not None:
        params["to"] = to_date

    data: dict[str, Any] = await client.get("/time_entries.json", params=params)

    entries: list[TimeEntry] = [TimeEntry.model_validate(e) for e in data.get("time_entries", [])]
    total_count: int = data.get("total_count", len(entries))
    resp_offset: int = data.get("offset", offset)
    resp_limit: int = data.get("limit", limit)

    return ListTimeEntriesResult(
        time_entries=entries,
        total_count=total_count,
        offset=resp_offset,
        limit=resp_limit,
    )


async def create_time_entry(
    client: RedmineClient,
    hours: float,
    issue_id: int | None = None,
    project_id: str | None = None,
    spent_on: str | None = None,
    activity_id: int | None = None,
    comments: str | None = None,
) -> TimeEntry:
    """Redmineに工数を記録する。

    Redmineの ``POST /time_entries.json`` をwrapする。
    ``issue_id`` または ``project_id`` のいずれか一方は必須。

    Args:
        client: Redmine APIクライアント。
        hours: 記録する工数（時間）。必須。
        issue_id: 工数を紐付けるissueの数値ID。
            ``project_id`` と排他ではなく、共に指定可能。
        project_id: 工数を紐付けるプロジェクトのidentifierまたは数値ID。
            ``issue_id`` を指定しない場合は必須。
        spent_on: 作業日（YYYY-MM-DD形式）。省略時はRedmineのデフォルト（本日）。
        activity_id: 作業種別の数値ID。省略時はRedmineのデフォルト。
        comments: 作業内容のメモ。

    Returns:
        作成された工数記録エントリを含む ``TimeEntry``。

    Raises:
        RedmineError: ``issue_id`` / ``project_id`` が両方未指定のとき（VALIDATION）、
            IDが不正のとき（NOT_FOUND）、認証エラー（AUTH_FAILED）。

    Example:
        >>> async with RedmineClient(config) as client:
        ...     entry = await create_time_entry(
        ...         client,
        ...         hours=2.5,
        ...         issue_id=42,
        ...         comments="Investigated the login flow",
        ...     )
        ...     print(entry.id, entry.hours)
        123 2.5
    """
    if issue_id is None and project_id is None:
        from redmine_mcp.errors import ErrorCategory, RedmineError

        raise RedmineError(
            ErrorCategory.VALIDATION,
            "Either issue_id or project_id must be specified",
        )

    body: dict[str, Any] = {"hours": hours}
    if issue_id is not None:
        body["issue_id"] = issue_id
    if project_id is not None:
        body["project_id"] = project_id
    if spent_on is not None:
        body["spent_on"] = spent_on
    if activity_id is not None:
        body["activity_id"] = activity_id
    if comments is not None:
        body["comments"] = comments

    data: dict[str, Any] = await client.post("/time_entries.json", json={"time_entry": body})
    return TimeEntry.model_validate(data["time_entry"])


async def update_time_entry(
    client: RedmineClient,
    time_entry_id: int,
    hours: float | None = None,
    spent_on: str | None = None,
    activity_id: int | None = None,
    comments: str | None = None,
    issue_id: int | None = None,
    project_id: str | None = None,
) -> TimeEntry:
    """Redmineの工数記録を修正する。

    Redmineの ``PUT /time_entries/:id.json`` をwrapする。
    更新後に ``GET /time_entries/:id.json`` で最新状態を取得して返す。

    Args:
        client: Redmine APIクライアント。
        time_entry_id: 更新する工数記録の数値ID（必須）。
        hours: 新しい工数（時間）。
        spent_on: 新しい作業日（YYYY-MM-DD形式）。
        activity_id: 新しい作業種別の数値ID。
        comments: 新しいコメント。
        issue_id: 紐付け先issueの数値IDを変更する場合に指定。
        project_id: 紐付け先プロジェクトのidentifierを変更する場合に指定。

    Returns:
        更新後の工数記録エントリを含む ``TimeEntry``。

    Raises:
        RedmineError: 工数記録が存在しない場合（NOT_FOUND）、
            バリデーションエラー（VALIDATION）、
            認証エラー（AUTH_FAILED）。

    Example:
        >>> async with RedmineClient(config) as client:
        ...     entry = await update_time_entry(
        ...         client,
        ...         time_entry_id=123,
        ...         hours=3.0,
        ...         comments="Revised: also fixed edge case",
        ...     )
        ...     print(entry.hours)
        3.0
    """
    body: dict[str, Any] = {}
    if hours is not None:
        body["hours"] = hours
    if spent_on is not None:
        body["spent_on"] = spent_on
    if activity_id is not None:
        body["activity_id"] = activity_id
    if comments is not None:
        body["comments"] = comments
    if issue_id is not None:
        body["issue_id"] = issue_id
    if project_id is not None:
        body["project_id"] = project_id

    await client.put(f"/time_entries/{time_entry_id}.json", json={"time_entry": body})

    # PUTは204を返すことがあるため、更新後のエントリをGETで取得して返す
    data: dict[str, Any] = await client.get(f"/time_entries/{time_entry_id}.json")
    return TimeEntry.model_validate(data["time_entry"])

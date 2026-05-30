"""Redmine 列挙値取得 MCP tools。

issue起票時に必要な列挙値（ステータス / トラッカー / 優先度）を取得するtoolを提供する。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from redmine_mcp.client import RedmineClient


class IssueStatus(BaseModel):
    """Redmine issueステータス。

    Attributes:
        id: ステータスの数値ID。
        name: ステータス名（例: ``New``, ``In Progress``, ``Closed``）。
        is_closed: Trueのとき「完了」扱いのステータス。
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    is_closed: bool = False


class Tracker(BaseModel):
    """Redmine トラッカー（issue種別）。

    Attributes:
        id: トラッカーの数値ID。
        name: トラッカー名（例: ``Bug``, ``Feature``, ``Support``）。
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str


class IssuePriority(BaseModel):
    """Redmine issue優先度。

    Attributes:
        id: 優先度の数値ID。
        name: 優先度名（例: ``Low``, ``Normal``, ``High``, ``Urgent``）。
        is_default: Trueのとき起票時のデフォルト優先度。
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    is_default: bool = False


async def list_issue_statuses(client: RedmineClient) -> list[IssueStatus]:
    """利用可能なissueステータス一覧を取得する。

    Redmineの ``GET /issue_statuses.json`` をwrapする。
    create_issue / update_issue で status_id を指定するときに使う。

    Args:
        client: Redmine APIクライアント。

    Returns:
        ``IssueStatus`` のリスト（全ステータス）。

    Raises:
        RedmineError: 認証エラーまたはネットワークエラーが発生した場合。

    Example:
        >>> async with RedmineClient(config) as client:
        ...     statuses = await list_issue_statuses(client)
        ...     for s in statuses:
        ...         print(s.id, s.name, s.is_closed)
        1 New False
        2 In Progress False
        5 Closed True
    """
    data: dict[str, Any] = await client.get("/issue_statuses.json")
    return [IssueStatus.model_validate(s) for s in data.get("issue_statuses", [])]


async def list_trackers(client: RedmineClient) -> list[Tracker]:
    """利用可能なトラッカー（issue種別）一覧を取得する。

    Redmineの ``GET /trackers.json`` をwrapする。
    create_issue で tracker_id を指定するときに使う。

    Args:
        client: Redmine APIクライアント。

    Returns:
        ``Tracker`` のリスト（全トラッカー）。

    Raises:
        RedmineError: 認証エラーまたはネットワークエラーが発生した場合。

    Example:
        >>> async with RedmineClient(config) as client:
        ...     trackers = await list_trackers(client)
        ...     for t in trackers:
        ...         print(t.id, t.name)
        1 Bug
        2 Feature
    """
    data: dict[str, Any] = await client.get("/trackers.json")
    return [Tracker.model_validate(t) for t in data.get("trackers", [])]


async def list_priorities(client: RedmineClient) -> list[IssuePriority]:
    """利用可能なissue優先度一覧を取得する。

    Redmineの ``GET /enumerations/issue_priorities.json`` をwrapする。
    create_issue で priority_id を指定するときに使う。

    Args:
        client: Redmine APIクライアント。

    Returns:
        ``IssuePriority`` のリスト（全優先度）。

    Raises:
        RedmineError: 認証エラーまたはネットワークエラーが発生した場合。

    Example:
        >>> async with RedmineClient(config) as client:
        ...     priorities = await list_priorities(client)
        ...     for p in priorities:
        ...         print(p.id, p.name, p.is_default)
        3 Low False
        4 Normal True
        5 High False
    """
    data: dict[str, Any] = await client.get("/enumerations/issue_priorities.json")
    return [IssuePriority.model_validate(p) for p in data.get("issue_priorities", [])]

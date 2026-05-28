"""Redmine REST API クライアントモジュール。

ADR-0004 (httpx) および ADR-0006 (API key auth) に従う。
HTTPエラーおよびネットワーク層エラーをADR-0008のcategorized errorに変換する。
"""

from __future__ import annotations

from types import TracebackType
from typing import Any

import httpx

from .config import RedmineConfig
from .errors import ErrorCategory, RedmineError


class RedmineClient:
    """Redmine REST APIへのHTTPクライアント。

    httpx.AsyncClientをwrapし、全リクエストに認証ヘッダーを付与する。
    context managerとして使用し、セッションのライフサイクルを管理する。

    Args:
        config: Redmine接続設定。

    Example:
        >>> async with RedmineClient(config) as client:
        ...     data = await client.get("/users/current.json")
    """

    def __init__(self, config: RedmineConfig) -> None:
        """RedmineClientを初期化する。

        Args:
            config: Redmine接続設定（URL・APIキー・タイムアウト）。
        """
        self._config: RedmineConfig = config
        self._http: httpx.AsyncClient = httpx.AsyncClient(
            base_url=config.url,
            headers={
                "X-Redmine-API-Key": config.api_key,
                "Content-Type": "application/json",
            },
            timeout=config.timeout,
        )

    async def __aenter__(self) -> RedmineClient:
        """context manager入口。セッションを開始する。

        Returns:
            自分自身（RedmineClient）。
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """context manager出口。HTTPセッションを閉じる。

        Args:
            exc_type: 例外の型（なければNone）。
            exc_val: 例外のinstance（なければNone）。
            exc_tb: トレースバック（なければNone）。
        """
        await self._http.aclose()

    def _raise_for_status(self, response: httpx.Response) -> None:
        """HTTPステータスコードをRedmineErrorにマッピングする。

        Redmineが返す主要なHTTPステータスコードをADR-0008のカテゴリに変換する。

        Args:
            response: httpxのレスポンスオブジェクト。

        Raises:
            RedmineError: HTTPステータスが2xx以外の場合。
        """
        if response.status_code == 401:
            raise RedmineError(ErrorCategory.AUTH_FAILED, "Authentication failed: invalid API key")
        if response.status_code == 403:
            raise RedmineError(ErrorCategory.AUTH_FAILED, "Forbidden: insufficient permissions")
        if response.status_code == 404:
            raise RedmineError(
                ErrorCategory.NOT_FOUND,
                f"Resource not found: {response.request.url.path}",
            )
        if response.status_code == 422:
            raise RedmineError(
                ErrorCategory.VALIDATION,
                f"Validation failed: {response.text}",
            )
        if response.status_code == 429:
            raise RedmineError(ErrorCategory.RATE_LIMITED, "Rate limit exceeded")
        if response.status_code >= 500:
            raise RedmineError(
                ErrorCategory.SERVER_ERROR,
                f"Redmine server error: {response.status_code}",
            )

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """GETリクエストを送信してJSONレスポンスを返す。

        Args:
            path: APIパス（例: ``/issues.json``）。
            params: クエリパラメータ（省略可）。

        Returns:
            JSONレスポンスをdict型で返す。

        Raises:
            RedmineError: HTTPエラーまたはネットワークエラーが発生した場合。
        """
        try:
            response: httpx.Response = await self._http.get(path, params=params)
        except httpx.TimeoutException:
            raise RedmineError(ErrorCategory.SERVER_ERROR, "Request timed out") from None
        except httpx.ConnectError:
            raise RedmineError(ErrorCategory.SERVER_ERROR, "Failed to connect to Redmine") from None
        self._raise_for_status(response)
        result: dict[str, Any] = response.json()
        return result

    async def post(
        self,
        path: str,
        json: dict[str, Any],
    ) -> dict[str, Any]:
        """POSTリクエストを送信してJSONレスポンスを返す。

        Args:
            path: APIパス（例: ``/issues.json``）。
            json: リクエストボディ（dictとして渡すとJSON直列化される）。

        Returns:
            JSONレスポンスをdict型で返す。

        Raises:
            RedmineError: HTTPエラーまたはネットワークエラーが発生した場合。
        """
        try:
            response: httpx.Response = await self._http.post(path, json=json)
        except httpx.TimeoutException:
            raise RedmineError(ErrorCategory.SERVER_ERROR, "Request timed out") from None
        except httpx.ConnectError:
            raise RedmineError(ErrorCategory.SERVER_ERROR, "Failed to connect to Redmine") from None
        self._raise_for_status(response)
        result: dict[str, Any] = response.json()
        return result

    async def put(
        self,
        path: str,
        json: dict[str, Any],
    ) -> dict[str, Any]:
        """PUTリクエストを送信してJSONレスポンスを返す。

        Redmineの更新系APIは成功時に204 No Contentを返す場合がある。
        その場合は空dictを返す。

        Args:
            path: APIパス（例: ``/issues/1.json``）。
            json: リクエストボディ。

        Returns:
            JSONレスポンス（Redmineが204を返す場合は空dict）。

        Raises:
            RedmineError: HTTPエラーまたはネットワークエラーが発生した場合。
        """
        try:
            response: httpx.Response = await self._http.put(path, json=json)
        except httpx.TimeoutException:
            raise RedmineError(ErrorCategory.SERVER_ERROR, "Request timed out") from None
        except httpx.ConnectError:
            raise RedmineError(ErrorCategory.SERVER_ERROR, "Failed to connect to Redmine") from None
        self._raise_for_status(response)
        if response.status_code == 204 or not response.content:
            return {}
        result: dict[str, Any] = response.json()
        return result

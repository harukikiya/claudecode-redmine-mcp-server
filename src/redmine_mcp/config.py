"""Redmine MCP server の設定管理モジュール。

環境変数（またはオプションの .env ファイル）から設定を読み込む。
ADR-0005 (pydantic-settings) および ADR-0006 (API key auth) に従う。
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedmineConfig(BaseSettings):
    """Redmine接続設定。

    環境変数プレフィックス ``REDMINE_`` で読み込む。
    ``.env`` ファイルも自動的に読み込む（存在する場合のみ）。

    Attributes:
        url: RedmineサーバーのベースURL（末尾スラッシュなし）。
        api_key: RedmineのAPIキー（X-Redmine-API-Keyヘッダーで使用）。
        timeout: HTTPリクエストのタイムアウト秒数。

    Example:
        >>> import os
        >>> os.environ["REDMINE_URL"] = "http://localhost:3000"
        >>> os.environ["REDMINE_API_KEY"] = "secret"
        >>> config = RedmineConfig()
        >>> config.url
        'http://localhost:3000'
    """

    model_config = SettingsConfigDict(
        env_prefix="REDMINE_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    url: str = Field(
        ...,
        description="RedmineサーバーのベースURL（例: http://localhost:3000）",
    )
    api_key: str = Field(
        ...,
        description="Redmine APIキー（X-Redmine-API-Keyヘッダーに付与）",
    )
    timeout: float = Field(
        default=30.0,
        description="HTTPリクエストのタイムアウト秒数",
        gt=0,
    )

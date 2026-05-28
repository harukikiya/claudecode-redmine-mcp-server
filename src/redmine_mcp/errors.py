"""Redmine MCP server のエラー分類モジュール。

ADR-0008 (Categorized error response) に従い、Redmine APIから返るエラーを
LLMが判断しやすいカテゴリに分類する。HTTP→エラーマッピングはM2でclientに実装する。
"""

from __future__ import annotations

from enum import StrEnum


class ErrorCategory(StrEnum):
    """Redmineエラーのカテゴリ分類。

    LLMがエラー種別に応じた次のアクションを判断できるように分類する。
    ``str`` を継承しているため、そのままJSON serializable。
    """

    NOT_FOUND = "NotFound"
    AUTH_FAILED = "AuthFailed"
    VALIDATION = "Validation"
    RATE_LIMITED = "RateLimited"
    SERVER_ERROR = "ServerError"


class RedmineError(Exception):
    """Redmine API呼び出し時に発生するエラーの基底クラス。

    ADR-0008のcategorized error responseで使用する。
    tool handlerがこの例外をcatchしてMCP isError responseに変換する。

    Args:
        category: エラーのカテゴリ。
        message: 人間・LLM向けのエラーメッセージ。

    Example:
        >>> raise RedmineError(ErrorCategory.NOT_FOUND, "Issue #42 not found")
    """

    def __init__(self, category: ErrorCategory, message: str) -> None:
        """RedmineErrorを初期化する。

        Args:
            category: エラーのカテゴリ（LLMがnext actionを判断するために使用）。
            message: エラーの詳細メッセージ。
        """
        super().__init__(message)
        self.category: ErrorCategory = category
        self.message: str = message

    def __repr__(self) -> str:
        """デバッグ用文字列表現を返す。

        Returns:
            カテゴリとメッセージを含む文字列。
        """
        return f"RedmineError(category={self.category!r}, message={self.message!r})"

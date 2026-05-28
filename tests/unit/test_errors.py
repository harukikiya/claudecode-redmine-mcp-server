"""RedmineError / ErrorCategory の単体テスト。"""

from __future__ import annotations

import pytest

from redmine_mcp.errors import ErrorCategory, RedmineError


def test_error_category_values() -> None:
    """ErrorCategory の各値が期待する文字列であること。"""
    assert ErrorCategory.NOT_FOUND.value == "NotFound"
    assert ErrorCategory.AUTH_FAILED.value == "AuthFailed"
    assert ErrorCategory.VALIDATION.value == "Validation"
    assert ErrorCategory.RATE_LIMITED.value == "RateLimited"
    assert ErrorCategory.SERVER_ERROR.value == "ServerError"


def test_redmine_error_attributes() -> None:
    """RedmineError が category と message を保持すること。"""
    error: RedmineError = RedmineError(ErrorCategory.NOT_FOUND, "Issue #42 not found")

    assert error.category == ErrorCategory.NOT_FOUND
    assert error.message == "Issue #42 not found"
    assert str(error) == "Issue #42 not found"


@pytest.mark.parametrize("category", list(ErrorCategory))
def test_redmine_error_all_categories(category: ErrorCategory) -> None:
    """全カテゴリで RedmineError を生成できること。"""
    error: RedmineError = RedmineError(category, f"test error for {category}")

    assert error.category == category


def test_redmine_error_is_exception() -> None:
    """RedmineError が Exception のサブクラスであること。"""
    error: RedmineError = RedmineError(ErrorCategory.SERVER_ERROR, "internal error")

    assert isinstance(error, Exception)


def test_redmine_error_repr() -> None:
    """__repr__ が category と message を含む文字列を返すこと。"""
    error: RedmineError = RedmineError(ErrorCategory.AUTH_FAILED, "invalid key")
    r: str = repr(error)

    assert "AuthFailed" in r
    assert "invalid key" in r


def test_redmine_error_can_be_raised() -> None:
    """RedmineError を raise できること。"""
    with pytest.raises(RedmineError) as exc_info:
        raise RedmineError(ErrorCategory.VALIDATION, "field required")

    assert exc_info.value.category == ErrorCategory.VALIDATION

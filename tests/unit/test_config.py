"""RedmineConfig の単体テスト。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from redmine_mcp.config import RedmineConfig


def test_config_reads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """環境変数から正しく設定を読み込めること。"""
    monkeypatch.setenv("REDMINE_URL", "http://redmine.example.com")
    monkeypatch.setenv("REDMINE_API_KEY", "my-api-key")

    config: RedmineConfig = RedmineConfig()  # type: ignore[call-arg]

    assert config.url == "http://redmine.example.com"
    assert config.api_key == "my-api-key"
    assert config.timeout == 30.0


def test_config_custom_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """REDMINE_TIMEOUT 環境変数でタイムアウトを変更できること。"""
    monkeypatch.setenv("REDMINE_URL", "http://redmine.example.com")
    monkeypatch.setenv("REDMINE_API_KEY", "key")
    monkeypatch.setenv("REDMINE_TIMEOUT", "60.0")

    config: RedmineConfig = RedmineConfig()  # type: ignore[call-arg]

    assert config.timeout == 60.0


def test_config_missing_required_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """必須フィールドが欠けていると ValidationError が発生すること。"""
    monkeypatch.delenv("REDMINE_URL", raising=False)
    monkeypatch.delenv("REDMINE_API_KEY", raising=False)

    with pytest.raises(ValidationError):
        RedmineConfig()  # type: ignore[call-arg]


def test_config_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """REDMINE_API_KEY が欠けていると ValidationError が発生すること。"""
    monkeypatch.setenv("REDMINE_URL", "http://redmine.example.com")
    monkeypatch.delenv("REDMINE_API_KEY", raising=False)

    with pytest.raises(ValidationError):
        RedmineConfig()  # type: ignore[call-arg]

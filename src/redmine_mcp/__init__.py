"""Redmine MCP server package.

Claude Code等のMCP clientからRedmineへ低摩擦で記録・参照するためのMCP server。
stdio transportで動作し、Redmine REST APIをMCP toolとして公開する。
"""

from __future__ import annotations

__version__: str = "0.1.0"

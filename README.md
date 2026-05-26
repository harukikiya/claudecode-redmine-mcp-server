# Redmine MCP Server

[![CI](https://github.com/harukikiya/claudecode-redmine-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/harukikiya/claudecode-redmine-mcp-server/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/harukikiya/claudecode-redmine-mcp-server/branch/main/graph/badge.svg)](https://codecov.io/gh/harukikiya/claudecode-redmine-mcp-server)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

Personal Redmine MCP server。他プロジェクトのClaude / Claude Code agentからRedmineへ低摩擦で記録・参照するために作る。

## 概要

- Redmine REST APIをwrapする [Model Context Protocol](https://modelcontextprotocol.io/) server
- Python + 公式 low-level `mcp` SDK
- 自宅Raspberry Piで運用想定

## ステータス

開発中。詳細は [Milestones](../../milestones) を参照。

- **M0** 設計・調査 — done
- **M1** Skeleton — in progress
- **M2** Core tools (12) — pending
- **M3** Extended tools (13) — pending
- **M4** 品質・CI — pending

## 公開する tools

合計25 tools（issue / time entry / project / wiki / search 等）。
仕様: [`docs/tools.md`](docs/tools.md)

## ドキュメント

| ファイル | 内容 |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Claude Codeへのコラボ契約・規約 |
| [`docs/tools.md`](docs/tools.md) | 公開する25 toolsの仕様 |
| [`docs/adr/`](docs/adr/) | 設計判断記録（MADR v4） |
| [`docs/branch-protection.md`](docs/branch-protection.md) | branch protectionの推奨設定 |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | 開発フロー |
| [`SECURITY.md`](SECURITY.md) | 脆弱性報告 |

## 開発

(M1完了後に追記予定。当面は CONTRIBUTING.md を参照)

## License

MIT — see [`LICENSE`](LICENSE)

# Roadmap

このプロジェクトの全体方針とマイルストーン構成。
**Claude Codeはタスクに着手する前にこのドキュメントで「自分が今どこにいるか」を確認する。**

## ビジョン

他プロジェクトのClaude / Claude Code agentから、Redmineへ低摩擦で記録・参照できるMCP serverを作る。個人用途、自宅Raspberry Piで運用。

## 全体マイルストーン

| M# | 名前 | 状態 | 目的 |
|---|---|---|---|
| M0 | 設計・調査 | ✅ done | ADR・docs・規約・GitHub基盤の確立 |
| M1 | Skeleton | 🚧 in progress | 動く最小のMCP server（hello world + auth疎通） |
| M2 | Core Tools (Tier 1) | pending | 12 tools — issue CRUD + 工数 + 解決系 |
| M3 | Extended Tools (Tier 2 + 3) | pending | 13 tools — wiki / attachment / search / queries 等 |
| M4 | 品質・CI | pending | release process / packaging / polish |

---

## M0: 設計・調査 ✅

**Goal**: 実装可能な設計合意とdev基盤の整備

**Delivered**:
- ADR-0001 〜 ADR-0008（言語 / SDK / 依存 / auth / tool粒度 / error handling）
- `docs/tools.md` — 25 toolsの仕様
- `CLAUDE.md` + `.claude/` — Claude Codeとのコラボ契約
- `.github/` — CI / Issue Forms / Dependabot / release-please / labels
- `docs/review-checklist.md` — pre-push self-review観点

---

## M1: Skeleton 🚧

**Goal**: 動く最小のMCP serverで「auth疎通 + protocol動作」が確認できる状態

**Deliverables**:
- `pyproject.toml`（uv管理、Python 3.11+）
- `src/redmine_mcp/` フォルダ構造
  - `__init__.py`
  - `__main__.py` または `server.py` — stdio transport entry point
  - `config.py` — pydantic-settings (`RedmineConfig`)
  - `redmine/client.py` — httpxベースの最小Redmine client（auth付きGET確認）
  - `errors.py` — ADR-0008のcategorized error type定義
- `tests/` フォルダ初期化
- `.gitignore`, `.env.example`

**Acceptance Criteria**:
- [ ] `uv run python -m redmine_mcp` でMCP serverがstdio上で起動
- [ ] Claude Desktop / Claude Code から接続できる（`initialize` / `tools/list` が応答、toolはまだ無くてOK）
- [ ] Redmine APIへの認証付きrequestが1本通る（`GET /users/current.json` を内部で叩いて疎通確認）
- [ ] CIが `ruff` / `mypy --strict` / `pytest` でgreen

**Dependencies**: M0 ✅

**注意点**:
- このマイルストーンではMCP toolは1つも実装しない（次のM2で乗せる）
- `RedmineConfig`は最低限 `url` と `api_key` だけで起動できること

---

## M2: Core Tools (Tier 1) — 12 tools

**Goal**: 「Redmineに記録する」基本ループが完成

**Deliverables**: `docs/tools.md` Tier 1の12 toolsを以下の実装順で:

1. `get_current_user`
2. `list_projects`
3. `list_issue_statuses` / `list_trackers` / `list_priorities`
4. `list_issues` / `get_issue`
5. `create_issue`
6. `update_issue`
7. `list_time_entries`
8. `create_time_entry`
9. `update_time_entry`

各toolごとに:
- input / output Pydantic schema
- integration test（success + 主要error category）
- 日本語Google style docstring
- `implement-redmine-tool` skill 準拠

**Acceptance Criteria**:
- [ ] 12 toolsすべてが `tools/list` で公開される
- [ ] 各toolにつき integration test が1つ以上、success + 1つ以上のerror categoryをカバー
- [ ] 実際にClaude / Claude CodeからRedmineへの記録ループ（`list_projects` → `create_issue` → `create_time_entry`）が動く

**Dependencies**: M1

---

## M3: Extended Tools (Tier 2 + 3) — 13 tools

**Goal**: Tier 1で記録した内容の周辺操作（wiki / attachment / search / queries / relations / watchers）

### Tier 2（M3 前半）— 8 tools

- `list_versions`, `list_issue_categories`, `list_users`
- `get_wiki_page`, `create_or_update_wiki_page`
- `upload_attachment`, `attach_to_issue`
- `search`

### Tier 3（M3 後半）— 5 tools（優先順位順）

- `list_queries` + `list_issues` の `query_id` param拡張
- `list_issue_relations`, `create_issue_relation`
- `add_watcher`, `remove_watcher`

**Acceptance Criteria**:
- [ ] 全25 tools（Tier 1 + 2 + 3）が公開される
- [ ] Tier 2 / 3 各toolにintegration test
- [ ] サンプル用法（README または `examples/`）に主要な使い方が記載

**Dependencies**: M2

---

## M4: 品質・CI

**Goal**: 運用に乗せられる品質まで仕上げ、release-please で v0.1.0 を切る

**Deliverables**:
- README拡充（install手順 / 使い方 / Claude Desktop連携 / Claude Code連携）
- Claude Desktop / Claude Code用の `mcp.json` または設定例
- packaging確認（`uv build`、wheel生成）
- coverage 80%以上達成
- 初回release（release-please による v0.1.0）
- 必要なら追加ADR（運用課題への対応）

**Acceptance Criteria**:
- [ ] release v0.1.0 がpublishされる
- [ ] 別マシン（or freshなコンテナ）でinstall → 動作確認できる
- [ ] README だけで初期セットアップが完結する

**Dependencies**: M3

---

## Out of Scope（プロジェクト全体）

意図的にスコープから外しているもの:

- 破壊的操作（`delete_issue`, `delete_project` 等のentity削除）
- Custom Field定義の変更
- User / Group / Role管理（admin系操作）
- News（プロジェクトアナウンス機能）
- Lychee Redmine 拡張 API（v1では扱わない）
- production hardening（rate limit回避の作り込み、retry戦略の高度化 等）

「やらないこと」を明示する目的は、Claude Codeが良かれと思って勝手に機能追加するのを防ぐため。

---

## マイルストーン間の依存

```
M0 ─→ M1 ─→ M2 ─→ M3 ─→ M4
```

並行作業は基本やらない。M1完成までM2 toolの実装には着手しない、等。
ただしdocs改善やADRの新規追加・bug fixは任意のタイミングで実施可。

---

## このドキュメントの位置付け

Claude Codeが「次に何をすべきか」迷ったら、まずここを読む。

| 種類 | 場所 |
|---|---|
| **今どこにいて次にどこへ** | このファイル（roadmap） |
| **個別tasksの詳細** | GitHub Issues |
| **設計判断の理由** | `docs/adr/` |
| **tool spec** | `docs/tools.md` |
| **コラボ契約** | `CLAUDE.md` |

# CLAUDE.md

Redmine MCP server。Claude Codeへのコラボ契約と作業規約。

## Project Overview

Personal Redmine MCP server。他プロジェクトのClaude/Claude Code agentからRedmineへ低摩擦で記録・参照するために作る。

- **用途**: 個人用、自宅Raspberry Piで運用
- **利用者**: 主に晴貴本人 + Claude/Claude Codeから呼ばれるMCP client
- **スコープ**: [`docs/tools.md`](docs/tools.md) を参照（Tier 1–3、合計25 tools）

## Session Start Checklist

セッション開始時に必ず:

1. このCLAUDE.mdを読む
2. 担当するGitHub issueの内容を読む
3. 関連ADR（`docs/adr/`）を読む
4. tool実装ならば `docs/tools.md` の該当箇所を読む
5. 必要なら `.claude/rules/python-conventions.md` を読む
6. 既存コードの規約を読み取る

## Model Selection

品質とコストの両立のため、タスクに合わせてmodelを切り替える:

| 場面 | コマンド | model |
|---|---|---|
| 設計 / ADR起草 / 大規模refactoring / 複雑debug | `/model opus` | Opus |
| Tool実装 / test / 通常のコード編集 | `/model sonnet`（default） | Sonnet |
| Mechanical work（rename, format, type fix等） | `/model haiku` | Haiku |
| 設計→実装が混在するタスク | `/model opusplan` | hybrid（plan: Opus, 実装: Sonnet） |

迷ったらsonnet、困ったらopus、雑用はhaiku。
default modelは `.claude/settings.json` で`sonnet`に固定。

## Collaboration Contract

このプロジェクトの大原則:

- **意思決定はユーザー**。Claude Codeは決定を下さない。
- **Claude Codeは設計提案と実装を担当**する。
- 設計判断（API設計、auth、error handling、依存追加、folder構造変更、tool分割、ADR変更等）は**必ずproposalを先に出す**。ユーザー承認が出るまで実装に入らない。
- 承認の有無が不明な場合、デフォルトは「未承認」。確認を求める。
- 「とりあえず動くもの」を勢いで作って既成事実化することは厳禁。

### Communication Style

- 単にコードを納品するのではなく、**なぜそうしたか**の理由を添える（メンタリングスタイル）
- 複数案があるときは推奨を出してよいが、決定は押し付けない
- 不明点・前提の曖昧さは黙って埋めず、ユーザーに確認する
- 既存ADRと矛盾する判断が必要になったら、新規ADRを提案する

### Settled Decisions

[`docs/adr/`](docs/adr/) に記録済みの確定事項。変更には新規ADRが必要:

- **ADR-0001**: Programming Language → Python
- **ADR-0002**: MCP SDK → 公式 low-level `mcp` package
- **ADR-0003**: Packaging → uv
- **ADR-0004**: HTTP Client → httpx
- **ADR-0005**: Config → pydantic-settings
- **ADR-0006**: Auth → API key (X-Redmine-API-Key header)
- **ADR-0007**: Tool粒度 → fine-grained
- **ADR-0008**: Error handling → categorized error response

## Prompting Style

複雑な提案や指示はXML tagsで構造化する。Claudeはこの形式に最適化されている。

例:

```
<task>
  list_issuesで、limit未指定時のRedmine既定（25件）を維持しつつ、all=true指定時のみ自動pagination
</task>
<context>
  - ADR-0008: error handlingはcategorized
  - docs/tools.md: list_issues spec
</context>
<success_criteria>
  - all=trueで全件取得
  - error caseでNotFound/Validation等の適切な分類
  - integration testでpagination境界を検証
</success_criteria>
```

長い参考資料（spec、log、code抜粋）は**プロンプトの先頭**に置き、その後にtask/instructionsを書く（long-context性能向上のため）。

## Proposal Format

短いものはPR description、大きいものは `docs/proposals/NNNN-title.md` に書く。

### 構造

1. **Context**: 何を解決したいか、背景
2. **Options**: 最低2つの選択肢
3. **Trade-offs**: 各選択肢のpros/cons
4. **Recommendation**: 推奨と理由
5. **Impact**: 影響範囲（既存コード、ADR、他tool等）

### ADR化が必要なケース

以下は確定後に新規ADRを書く（`docs/adr/TEMPLATE.md` を使用）:

- 言語・SDK・主要依存の変更
- auth方式・error handling方針の変更
- folder構造の根本的変更
- セキュリティ・運用に関する判断

通常のtool実装はADR不要、PR descriptionの提案で十分。

## Code Style

### Python全般

- **Python 3.11+**（`pyproject.toml` の `requires-python` で固定）
- async/awaitベース（MCP SDK・httpxとの整合）

### Type annotations / Docstrings

**全関数の引数・戻り値、全変数に型注釈必須**。**全public moduleにdocstring必須**。詳細ルールは [`.claude/rules/python-conventions.md`](.claude/rules/python-conventions.md) を参照。

### Lint / Format / Type check

- **`ruff check` / `ruff format`** で lint + format
- **`mypy --strict`** をpassすること
- 設定は `pyproject.toml` に集約

### 命名

- Tool関数名は `docs/tools.md` の命名に従う
- Module名はsnake_case、Class名はPascalCase
- 内部関数は `_leading_underscore`

## Testing

- **`pytest`** を使用
- ディレクトリ:
  - `tests/unit/` — 単体テスト
  - `tests/integration/` — Redmine API呼び出しを伴うテスト（mock使用）
- Redmine API mock: **`pytest-httpx`** を第一候補
- 各toolにつき最低: success caseと主要なerror category caseのテスト
- coverage目標: 80%以上

## Commits & PRs

### Commits

- **Conventional Commits**形式 (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:` 等)
- 例: `feat(tools): add create_issue tool`
- 1コミット = 1論理変更

### PRs

- 1 issue = 1 PR を基本
- PR description:
  - 関連issue (`Closes #N`)
  - 変更概要
  - proposalがあった場合はそのリンクまたは要約
  - test結果（`pytest`/`ruff`/`mypy` の出力概要）
- ブランチ命名: `feat/N-short-description`, `fix/N-short-description`

### Workflow

1. issueまたはPR descriptionにproposalを書く
2. ユーザーレビュー・承認
3. 実装ブランチを作成、commit
4. PR作成（draftで開始可）
5. CI green、ユーザーレビュー
6. merge

## Sensitive Areas — 必ずユーザー確認

以下に触れる場合、proposal経由でないと進めない:

- **Secrets**: API key・credentialのコード/コミット混入は絶対NG。env var経由のみ。`.env` は `.gitignore` 必須
- **依存追加**: `pyproject.toml` の `dependencies` への追加は、理由とlicense確認をproposalに記載
- **`pyproject.toml`の構造変更**: build system、project metadata、tool設定セクション
- **CI設定**（`.github/workflows/`）
- **ADR / `docs/tools.md`**: 設計の合意記録。変更時は新規ADRまたは既存ADRの `status: superseded` を提案
- **MCP protocol層への干渉**: low-level SDKの内部に手を入れる、独自transport実装等

## Key References

- **ADR**: [`docs/adr/`](docs/adr/) ([README](docs/adr/README.md))
- **Tool spec**: [`docs/tools.md`](docs/tools.md)
- **Python conventions**: [`.claude/rules/python-conventions.md`](.claude/rules/python-conventions.md)
- **Pre-push review checklist**: [`docs/review-checklist.md`](docs/review-checklist.md)
- **Skills**:
  - `implement-redmine-tool` ([`.claude/skills/implement-redmine-tool/SKILL.md`](.claude/skills/implement-redmine-tool/SKILL.md))
  - `pre-push-review` ([`.claude/skills/pre-push-review/SKILL.md`](.claude/skills/pre-push-review/SKILL.md))
- **WBS**: GitHub Milestones M0–M4
- **MCP公式SDK**: https://github.com/modelcontextprotocol/python-sdk
- **Redmine REST API**: https://www.redmine.org/projects/redmine/wiki/Rest_api

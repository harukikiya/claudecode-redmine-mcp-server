# Contributing

このプロジェクトは個人運用ですが、構造としてはOSS的な規約に従っています。Claude Codeも基本的にこのドキュメント + [`CLAUDE.md`](CLAUDE.md) に沿って動作します。

## 開発フロー

詳細は [`CLAUDE.md`](CLAUDE.md) を参照。要約:

1. **issue起票** — Issue Forms から該当typeを選択
2. **proposal** が必要な場合は PR description または `docs/proposals/` に書く
3. **owner承認** を得る
4. **ブランチを切る** — `feat/N-...`, `fix/N-...` 等
5. **実装 + test**
6. **PR作成** — `Closes #N`、CI green が前提
7. **レビュー** → merge

## Commits

[Conventional Commits](https://www.conventionalcommits.org/) 形式:

- `feat:` 新機能
- `fix:` バグ修正
- `docs:` ドキュメント
- `chore:` 雑務（dependabot等）
- `refactor:` リファクタ
- `test:` テスト追加・修正
- `ci:` CI設定変更
- `build:` ビルド設定変更

release-pleaseがこの形式を解析してCHANGELOGとversion bumpを自動生成するため、形式厳守。

## コード規約

- **Python**: [`.claude/rules/python-conventions.md`](.claude/rules/python-conventions.md)
- **ADR**: MADR v4形式。[`docs/adr/TEMPLATE.md`](docs/adr/TEMPLATE.md) を雛形に
- **Tool**: [`docs/tools.md`](docs/tools.md) の命名・schemaに従う

## ローカル検証

PR前に必ず実行:

```sh
# 依存セットアップ
uv sync --all-extras --dev

# lint + format
uv run ruff check
uv run ruff format --check

# type check
uv run mypy --strict

# test
uv run pytest
```

CIで同じことを再実行する。CI green でなければmergeできない。

## Labels

Issue/PRのラベルは [`labels.yml`](.github/labels.yml) で定義。Issue Form / Dependabot / auto-label workflow が自動付与する。
手動で `.github/labels.yml` を編集してpushすると、`labels-sync` workflow が GitHub上のラベルに反映する。

## Branch Protection

`main` への直push禁止・CI green必須。詳細は [`docs/branch-protection.md`](docs/branch-protection.md)。

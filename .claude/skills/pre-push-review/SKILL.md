---
name: pre-push-review
description: Self-review checklist that Claude Code runs before pushing a PR or opening it on GitHub. Use after local CI (ruff/mypy/pytest) passes and implementation is complete. Catches design quality, documentation drift, LLM-friendliness, security, and operational concerns that CI cannot detect.
---

# Pre-Push Review

PRをpushする直前（CIを回す前）にClaude Codeが自己レビューする手順。
CIが検出できない品質側面（設計 / docs整合 / LLM-friendliness / security / 運用）をカバーする。

## When to run

- 実装 + local CI（`ruff` / `mypy` / `pytest`）が通った直後
- PR descriptionを書く前
- 大きめのrefactoring後

## How to run

1. 詳細チェックリスト [`docs/review-checklist.md`](../../../docs/review-checklist.md) を読む
2. 6つのbucket（A〜F）を順に確認:
   - **A. Code quality** — Python構成 / Tool API LLM-friendliness / Idempotency / Backward compatibility
   - **B. Documentation** — Docstring quality / Doc consistency
   - **C. Test quality** — 観点・テスト品質・N+1
   - **D. Error handling & Security** — error completeness / Logging / Security
   - **E. Domain perspectives** — LLM caller / Manager / Worker / Self-hosting
   - **F. Process compliance** — Proposal alignment / Sensitive Areas
3. 引っかかった点は (a) その場で修正 / (b) 後続issueとして起票 / (c) 既知の制限としてdocsに記録 のいずれか
4. PR descriptionの `## Self-Review Summary` セクションに結果を記入

## Output template

PR description末尾に追加するreview summary:

```markdown
## Self-Review Summary

[詳細チェックリスト](docs/review-checklist.md) を確認。

- [x] A. Code quality
- [x] B. Documentation
- [x] C. Test quality
- [x] D. Error handling & Security
- [x] E. Domain perspectives
- [x] F. Process compliance

### 特記事項
- （気づき・残課題・既知の制限を箇条書き。なければ「なし」）
```

## Anti-patterns

- 「全項目確認した」と書きつつ実際は流し読み
- 引っかかった点を黙って修正し、self-review summaryに残さない
- proposalに無い変更を「軽微」として勝手に追加する
- E (Domain perspectives) を省略する。**MCP toolはLLM ergonomicsが製品の質そのもの**

## Model selection hint

review作業はOpus推奨（設計・docs整合性・API ergonomicsの観点は推論深度が効く）。
`/model opus` で実行。

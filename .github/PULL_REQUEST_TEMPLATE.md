## 概要

<!-- 何を変えたか、なぜ変えたかを簡潔に -->

## 関連 issue

Closes #

## 種別

<!-- 該当するものに [x] を入れる -->

- [ ] tool実装
- [ ] bug fix
- [ ] refactor
- [ ] docs
- [ ] infra / CI
- [ ] ADR / design

## Proposal

<!-- proposal経由の場合、proposalへのリンクまたは要約。proposal不要な変更ならN/A -->

## チェックリスト

- [ ] `ruff check` pass
- [ ] `ruff format --check` pass
- [ ] `mypy --strict` pass
- [ ] `pytest` pass
- [ ] 必要なdocstring・型注釈を付けた
- [ ] CLAUDE.md / `docs/tools.md` / ADR等の関連docを必要に応じて更新
- [ ] Conventional Commits形式でcommit

## test結果

<!-- pytest出力の関連部分を貼る -->

```
```

## Self-Review Summary

<!--
pre-push-review skill ( .claude/skills/pre-push-review/SKILL.md ) を実行。
詳細チェックリストは docs/review-checklist.md 。
-->

- [ ] A. Code quality（Python構成 / Tool API LLM-friendliness / Idempotency / Backward compat）
- [ ] B. Documentation（Docstring / Doc consistency）
- [ ] C. Test quality（観点 / 品質 / N+1）
- [ ] D. Error handling & Security
- [ ] E. Domain perspectives（LLM caller / Manager / Worker / Self-hosting）
- [ ] F. Process compliance（Proposal alignment / Sensitive Areas）

### 特記事項

<!-- self-reviewで気づいた点・残課題・既知の制限を箇条書き。なければ「なし」 -->

## 補足

<!-- レビュアーに伝えるべき注意点・前提があれば -->
---
name: implement-redmine-tool
description: Standard workflow for implementing a new Redmine MCP tool. Use when adding any tool defined in docs/tools.md (e.g., create_issue, list_time_entries). Covers branch creation, schema design, error mapping, testing, and PR submission.
---

# Implement Redmine Tool

`docs/tools.md` に定義されているtoolを実装するときの標準workflow。

## Steps

1. **GitHub issueを確認**: tool名、tier、関連リンク、acceptance criteriaを把握
2. **`docs/tools.md` の該当セクションを読む**: endpoint、required/optional params、注意事項
3. **既存の似たtoolの実装を読む**（あれば）: 命名・schema・error mappingのパターンを揃える
4. **proposalが必要か判断**: 以下のいずれかに該当する場合は実装前にproposal:
   - schema設計に複数案がある
   - 既存コードへの広い影響がある
   - ADRと矛盾する判断が必要
   - 新規依存が必要
5. **ブランチ作成**: `feat/N-tool-name`
6. **実装**:
   - tool function in `src/tools/<resource>.py`
   - Pydantic input/output schemas
   - error categorizationはADR-0008に従う
   - registration in `src/server.py`
7. **Docstring**: `docs/tools.md` の内容をdocstringに反映（Args / Returns / Raises / Example）
   - Google style、詳細は `.claude/rules/python-conventions.md`
8. **テスト** in `tests/integration/test_<resource>.py`:
   - success case
   - error caseは各categoryをカバー（NotFound / Validation / AuthFailed等）
   - `pytest-httpx` でRedmine APIをmock
9. **ローカル確認**: 全部greenまで進めない
   - `ruff check`
   - `ruff format --check`
   - `mypy --strict`
   - `pytest`
10. **Pre-push self-review**: `pre-push-review` skill を実行（[`.claude/skills/pre-push-review/SKILL.md`](../pre-push-review/SKILL.md)）。`docs/review-checklist.md` の6 bucket（A〜F）を確認
11. **PR作成**: `Closes #N`、変更概要、test結果、self-review summary を記載

## Checklist

- [ ] tool名は `docs/tools.md` と一致
- [ ] 全引数・戻り値に型注釈
- [ ] Google style docstring（Args / Returns / Raises / Example）
- [ ] errorはADR-0008のcategoryに分類
- [ ] integration testでhttpx mockを使い、API call内容をassert
- [ ] `mypy --strict` がpass
- [ ] `ruff check` / `ruff format --check` がpass
- [ ] PR descriptionに `Closes #N` を記載

## Anti-patterns

- 提案なくschemaを変更する（特に既存toolと整合性を崩す変更）
- error messageを素の例外文字列のまま返す（categorizationなし）
- async関数の中で同期blocking I/O（`requests`、`time.sleep` 等）
- docstringを `"""TODO"""` のまま放置
- `mypy --strict` のwarningを `# type: ignore` で雑に消す（error code明示せず）

## Model Selection Hint

- **新規tool設計でschema迷う**: `/model opus` で議論
- **既存パターンに沿った実装**: `sonnet`（default）で十分
- **既存コードのrename・format等のmechanical fix**: `/model haiku`

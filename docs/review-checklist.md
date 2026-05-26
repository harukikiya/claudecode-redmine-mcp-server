# Pre-Push Review Checklist

`.claude/skills/pre-push-review/SKILL.md` が参照する詳細チェックリスト。
PRをpushする直前に、Claude Code（または人間）が以下の観点で自己レビューする。

**CI (`ruff` / `mypy` / `pytest`) が検出する観点はここに含めない。**
CIで自動検出できない品質側面のみ扱う。

---

## A. Code quality

### A1. Python構成

- [ ] module分割が責務に沿っているか（`src/tools/issues.py` / `src/redmine/client.py` 等の境界）
- [ ] 循環importが発生していないか
- [ ] async関数の中で同期blocking I/O（`requests`、`time.sleep` 等）を使っていないか
- [ ] resource cleanup（httpx clientのclose、fileのclose）が `async with` / `try-finally` で確実か
- [ ] Pydantic modelをDTOとして使えているか（`dict` / `Any` の泥沼を避けているか）

### A2. Tool API LLM-friendliness（特に重要）

MCP toolは LLMが docstring / input schema を読んで「どれを呼ぶか」「どう引数を埋めるか」を判断する。LLM側の精度に直結する。

- [ ] tool名が `docs/tools.md` と一致、`verb_resource[_qualifier]` 形式
- [ ] tool descriptionが「いつこのtoolを使うべきか」をLLMに伝えている
- [ ] 引数の意味が param description だけで自己完結している
- [ ] required引数を最小限に絞れている
- [ ] enum型（status, priority等）を生のstringではなく `Literal` / `Enum` で表現
- [ ] 似たtool（`list_issues` vs `search` 等）の使い分けが docstring から明確

### A3. Idempotency / Side effects

- [ ] 同じ引数で2回呼ぶと副作用が累積するtoolなら、docstringに明記
- [ ] create系は重複検出する余地があるか考慮（同名issueを複数作るリスク）
- [ ] retry安全性が docstring か code comment に記載

### A4. Backward compatibility

- [ ] 既存toolのrequired param追加・削除をしていないか
- [ ] Pydantic modelからfield削除・名前変更していないか
- [ ] 互換性を壊す場合、deprecation policyをADRで定義

---

## B. Documentation

### B1. Docstring quality

- [ ] 全public関数 / class / method に docstring（日本語、Google style）
- [ ] Args / Returns / Raises / Example が揃っている
- [ ] toolの場合、Exampleが実用的な呼び出し例になっている
- [ ] 内部関数（`_leading_underscore`）でもロジック複雑なら docstring を書いた

### B2. Documentation consistency

- [ ] docstringのspecが `docs/tools.md` と矛盾していない（param名・default値・description）
- [ ] 関連ADRが今も妥当か（ADR記載と異なる方針で実装していないか）
- [ ] 影響を受ける可能性のあるADRへのcross-referenceを更新
- [ ] README / CONTRIBUTING の記述が古くなっていないか

---

## C. Test quality

### C1. Test観点

- [ ] success case
- [ ] error category each（NotFound / Validation / AuthFailed / RateLimited / ServerError）
- [ ] boundary case（limit境界、empty result、Redmine pagination境界の100件超え）
- [ ] auth failure（401 / 403）
- [ ] network failure（timeout / connection error）
- [ ] malformed Redmine response（JSON parse失敗、想定外のfield欠落）

### C2. Test品質（coverage数字以外）

- [ ] test名が「何を確認しているか」を表している
- [ ] test同士に順序依存がない（独立で動く）
- [ ] mockがRedmine実応答のshapeに忠実（fixtureは公式docsかreal response由来）
- [ ] integration testでhttpx mockが受け取ったrequest内容（URL / header / body）をassertしている

### C3. N+1 / pagination

- [ ] list系toolで全件取得時のbehaviorを意識
- [ ] Redmineの100件/request制限を超える場合の挙動（自動pagination？ erroring out？）
- [ ] 関連resource取得（issue + watchers + relations）で都度API callにならない設計

---

## D. Error handling & Security

### D1. Error handling completeness

- [ ] ADR-0008の全error categoryをハンドル
- [ ] network層のerror（`httpx.TimeoutException` / `ConnectError` / `RemoteProtocolError`）をcategorized errorに変換
- [ ] error messageに「次に何をすべきか」のヒントが含まれる（LLMが次のaction判断できる）
- [ ] error messageに過度に内部実装の詳細を出していない（内部URL、token値等）

### D2. Logging quality

- [ ] debug時に追跡可能なcontext（tool名 / request_id / issue_id等）がlogに残る
- [ ] secrets（API key / password）が log に絶対出ていない
- [ ] log levelが妥当（DEBUG / INFO / WARNING / ERROR）
- [ ] 例外発生時、stack traceを捨てずに `logger.exception` で残す

### D3. Security

- [ ] API key / token がコード / log / error message / test fixtureに直書きされていない
- [ ] URL path組み立てで user入力がそのまま format string に入っていない（path traversalの余地）
- [ ] Redmine permission scopeの想定が docstring に書かれている（admin requiredなtoolはその旨明記）

---

## E. Domain perspectives

### E1. LLM caller視点（このtoolをClaude/Claude Codeから呼ぶ側）

- [ ] 自然言語の曖昧依頼（「RP2040にメモして」「あれの工数つけて」）から正しいtoolを選べる手がかりが description にある
- [ ] tool chainが組みやすい（`list_projects` → `create_issue` のように引数を引き渡せる）
- [ ] return valueから次のactionに使うid / keyが取り出しやすい

### E2. Manager視点（Redmine上司側 / 進捗管理）

- [ ] issue title / descriptionが「誰が見ても何のタスクか分かる」内容になるよう促す param設計
- [ ] `assignee` / `priority` / `due_date` / `estimated_hours` を渡せる
- [ ] 状態遷移（status変更）がRedmine journalに残る
- [ ] milestone（version）との紐付けが可能
- [ ] subjectやdescriptionに含まれるwordから検索しやすい

### E3. Worker視点（Redmine作業者側 / 進捗記入）

- [ ] 工数記録（time entry）が低摩擦（issue_idだけで最小入力可）
- [ ] 状態更新が1 tool呼びで完結
- [ ] note追加が `update_issue` から自然にできる
- [ ] よく使うfilter（「自分にassignされた open」）が短い引数で表現できる

### E4. Self-hosting operational視点

- [ ] memory / CPU heavyな処理（大量list / 巨大attachment）のboundary考慮
- [ ] 長時間稼働でのconnection leak防止（httpx client lifecycle）
- [ ] 再起動時のstate依存がないか（stdio MCP serverは再起動安全か）
- [ ] Raspberry Piのリソース制約を想定（過剰なin-memory cacheを避ける等）

---

## F. Process compliance

### F1. Proposal-implementation alignment

- [ ] 承認されたproposalから逸脱した変更を含んでいないか
- [ ] proposalで「out of scope」とした項目を勝手に追加していないか
- [ ] proposal時のschemaから乖離していないか

### F2. Sensitive Areas侵犯

CLAUDE.mdに記載の以下に該当する変更があれば、別proposalを通した上でPRに含めること:

- [ ] secrets handling
- [ ] 新規依存追加（pyproject.toml `dependencies`）
- [ ] pyproject.tomlの構造変更（build system / metadata / tool config）
- [ ] CI設定（`.github/workflows/`）
- [ ] ADR / `docs/tools.md`
- [ ] MCP protocol層への干渉（low-level SDK内部 / 独自transport等）

---

## 使い方

1. PRをpushする直前にこのファイルを開き、該当セクションを上から確認する
2. 引っかかった項目があれば:
   - その場で修正可能 → 修正してからpush
   - 別issueに切り出せる → issue起票してPR descriptionで参照
   - 既知の制限として受容 → README / CHANGELOG の Known Limitations に明記
3. PR descriptionの `## Self-Review Summary` セクションに各bucket（A〜F）のチェック結果と特記事項を記入

## メンテナンス

このchecklistは「育てる」前提:

- 実装中に発見した観点を追加する
- 運用上ほぼ引っかからない過剰な項目は削除する
- 大きな構造変更はADR proposalを経る

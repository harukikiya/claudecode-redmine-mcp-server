---
status: accepted
date: 2026-05-25
decision-makers: [haruki]
---

# ADR-0008: Error Handling Strategy

## Context and Problem Statement

<!-- TBD: tool実行中に発生したエラーをMCP responseとしてLLMに返す方式を決める。
MCP SDKでは `CallToolResult` の `isError: true` フラグとcontent blockでエラーを表現する -->

## Decision Drivers

* LLMが次のactionを判断しやすい構造化
* debug容易さ
* 実装の複雑さ

## Considered Options

* A. Exception bubbling — tool関数で例外をraiseし、SDKがisErrorに変換
* B. Categorized error response — `NotFound / AuthFailed / Validation / RateLimited / ServerError` 等に分類して構造化contentで返す
* C. Result型風 — `SuccessResult | ErrorResult` のUnion型でtoolが返す
* D. ハイブリッド — B + 人間向け1文の説明 + raw details (debug用)

## Decision Outcome

Chosen option: **B. Categorized error response**

<!-- TBD: LLMが「これは404だから別のtoolを試そう」のような判断がしやすい。categorizationを書く過程でRedmineエラーパターンが体に入る（学習目的との相性） -->

### Consequences

* Good, because <!-- TBD -->
* Bad, because <!-- TBD -->

### Confirmation

<!-- TBD: 各toolが返すerror responseがcategory enumに従っていることをtestで確認 -->

## Pros and Cons of the Options

### A. Exception bubbling

* <!-- TBD -->

### B. Categorized

* <!-- TBD -->

### C. Result型

* <!-- TBD -->

### D. ハイブリッド

* <!-- TBD -->

## More Information

<!-- TBD -->

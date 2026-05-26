---
status: accepted
date: 2026-05-25
decision-makers: [haruki]
---

# ADR-0004: HTTP Client

## Context and Problem Statement

<!-- TBD: Redmine REST APIを呼び出すHTTPクライアントを選定する -->

## Decision Drivers

* MCP SDKがasyncベースのためasync対応必須
* <!-- TBD: API設計、成熟度、HTTP/2サポート等 -->

## Considered Options

* httpx
* requests
* aiohttp

## Decision Outcome

Chosen option: **httpx**

<!-- TBD: 選定理由 -->

### Consequences

* Good, because <!-- TBD -->
* Bad, because <!-- TBD -->

### Confirmation

<!-- TBD -->

## Pros and Cons of the Options

### httpx

* <!-- TBD -->

### requests

* <!-- TBD -->

### aiohttp

* <!-- TBD -->

## More Information

* 関連ADR: 0002 (MCP SDK Selection)

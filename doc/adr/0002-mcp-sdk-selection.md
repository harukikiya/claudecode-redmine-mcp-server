---
status: accepted
date: 2026-05-25
decision-makers: [haruki]
---

# ADR-0002: MCP SDK Selection

## Context and Problem Statement

Redmine MCP server実装のためのPython側SDKを選定する。MCPの仕組みを理解しながら作りたい一方、ボイラープレートに時間を取られすぎたくない。

## Decision Drivers

* MCP protocolの動作を理解できること（学習目的）
* SDKの成熟度・docs・exampleの量
* 個人プロジェクトとして開発負担が現実的であること
* httpx / pydantic-settingsとの相性

## Considered Options

* 公式 low-level SDK (`mcp` package)
* FastMCP（高レベルdecorator API）

## Decision Outcome

Chosen option: **公式 low-level SDK (`mcp` package)**, because protocolの動作（`initialize`, `tools/list`, `tools/call` 等）を直接書くことで学習目的を満たせる。公式で最も成熟、async対応がhttpxと自然に組み合わせられる。

### Consequences

* Good, because protocolが見えるのでMCPの理解が深まる
* Good, because 公式SDKで長期メンテナンスが期待できる
* Good, because async/awaitベース、httpxと自然に統合
* Bad, because FastMCPと比べてtool登録等の記述量が多い
* Bad, because boilerplateを自分で管理する必要がある

### Confirmation

`mcp` packageを依存に追加し、M1 (Skeleton) でstdio transportのhello world serverを動作させることで確認する。

## Pros and Cons of the Options

### 公式 low-level SDK (`mcp` package)

* Good, because protocol層が露出していて挙動が追える
* Good, because 公式・最も成熟
* Good, because asyncネイティブ
* Bad, because tool定義時にschemaを手書きする部分がある

### FastMCP

* Good, because decoratorで簡潔に書ける
* Good, because schemaが関数signatureから自動生成
* Bad, because protocol層が隠蔽されて学習目的に合わない
* Bad, because 内部の挙動を追うときに抽象化レイヤーを越える必要がある

## More Information

* MCP公式SDK: https://github.com/modelcontextprotocol/python-sdk
* 関連ADR: 0001 (Programming Language), 0004 (HTTP Client)

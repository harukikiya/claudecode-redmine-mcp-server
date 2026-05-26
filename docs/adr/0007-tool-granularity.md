---
status: accepted
date: 2026-05-25
decision-makers: [haruki]
---

# ADR-0007: Tool Granularity

## Context and Problem Statement

<!-- TBD: Redmineの操作をMCP toolにマッピングする粒度を決める -->

## Decision Drivers

* LLMからのtool discoverability（toolの選択判断のしやすさ）
* 各toolのschema/inputの明瞭さ
* tool数の増加に対するメンテナンス性

## Considered Options

* Fine-grained: 1操作1tool (`create_issue`, `update_issue`, `list_issues`, ...)
* Coarse-grained: 1tool + action param (`manage_issue` with `action: create | update | list`)
* Hybrid: 主要操作はfine-grained、補助操作は集約

## Decision Outcome

Chosen option: **Fine-grained (1操作1tool)**

<!-- TBD: LLMがtoolを選ぶ判断が単純になる。schemaが各toolで明確 -->

### Consequences

* Good, because <!-- TBD -->
* Bad, because <!-- TBD -->

### Confirmation

<!-- TBD: tool一覧と命名規則をdocs/tools.md等で管理し、PR時にレビュー -->

## Pros and Cons of the Options

### Fine-grained

* <!-- TBD -->

### Coarse-grained

* <!-- TBD -->

### Hybrid

* <!-- TBD -->

## More Information

<!-- TBD -->

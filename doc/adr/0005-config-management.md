---
status: accepted
date: 2026-05-25
decision-makers: [haruki]
---

# ADR-0005: Config Management

## Context and Problem Statement

<!-- TBD: Redmine URL、API key等のconfigurationを読み込み・検証する方式を選定する -->

## Decision Drivers

* 型安全性
* environment variableからの読み込み
* 実装のシンプルさ

## Considered Options

* pydantic-settings
* 素のos.environ + 手動validation
* dynaconf

## Decision Outcome

Chosen option: **pydantic-settings**

<!-- TBD: 選定理由 -->

### Consequences

* Good, because <!-- TBD -->
* Bad, because <!-- TBD -->

### Confirmation

<!-- TBD -->

## Pros and Cons of the Options

### pydantic-settings

* <!-- TBD -->

### os.environ + 手動validation

* <!-- TBD -->

### dynaconf

* <!-- TBD -->

## More Information

* pydantic-settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/

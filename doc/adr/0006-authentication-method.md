---
status: accepted
date: 2026-05-25
decision-makers: [haruki]
---

# ADR-0006: Authentication Method

## Context and Problem Statement

<!-- TBD: Redmine APIへの認証方式を選定する。
RedmineはAPI key (X-Redmine-API-Key header) とBasic auth (username:password または username:api_key) の両方をサポートする -->

## Decision Drivers

* bot/automation用途への適性
* 認証情報管理のシンプルさ
* Redmine側の運用との整合性

## Considered Options

* API key (X-Redmine-API-Key header)
* Basic auth (username:api_key or username:password)

## Decision Outcome

Chosen option: **API key (X-Redmine-API-Key header)**

<!-- TBD: bot/automation向けに作られた素直な方式。専用headerで扱いがclean -->

### Consequences

* Good, because <!-- TBD -->
* Bad, because <!-- TBD -->

### Confirmation

<!-- TBD: HTTP clientの全リクエストに `X-Redmine-API-Key` headerが付与されることをintegration testで確認 -->

## Pros and Cons of the Options

### API key (header)

* <!-- TBD -->

### Basic auth

* <!-- TBD -->

## More Information

* Redmine REST API auth: https://www.redmine.org/projects/redmine/wiki/Rest_api#Authentication

# Security Policy

## 脆弱性報告

セキュリティ問題を発見した場合は、**公開issueではなく**プライベートに報告してください:

- **GitHub Security Advisory**: repo > Security > "Report a vulnerability"
- 公開issueには書かないこと（exploitが対応前に拡散するリスクがあるため）

## サポート対象

- 最新の `main` ブランチのみ
- リリース済みのtaggedバージョンも最新のもののみ

## 既知の制約・運用上の前提

- 本projectは**個人用途**を想定。production deploymentは想定外
- secrets管理は**環境変数前提**。リポジトリにcredentialを混入させないこと
- `.env` は `.gitignore` 必須
- Redmine APIキーは権限を必要最小限に絞ることを推奨

## 依存パッケージの脆弱性

- Dependabotが週1で依存をチェック・更新PRを作成する
- 脆弱性パッチは優先的にmerge

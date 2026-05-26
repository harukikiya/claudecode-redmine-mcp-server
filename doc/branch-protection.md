# Branch Protection Rules

GitHub UI上で設定する内容のドキュメント。コードで管理できないため、ここに記録して再現可能にしておく。

## 目的

- `main` ブランチへの直push禁止 → 変更は必ずPR経由
- CI green でなければmergeできない
- 設計合意（ADR）と整合しない変更を防ぐ

## 設定箇所

GitHub > Settings > Branches > **Add classic branch protection rule**
（または Settings > Rules > Rulesets でnewer rulesetとして設定）

Branch name pattern: `main`

## 推奨設定

### 必須 (Required)

- [x] **Require a pull request before merging**
  - [ ] Require approvals — 0（個人運用なら不要、自己レビュー徹底するなら 1）
  - [x] Dismiss stale pull request approvals when new commits are pushed
- [x] **Require status checks to pass before merging**
  - [x] Require branches to be up to date before merging
  - 必須statuses:
    - `test` (CI workflow から)
- [x] **Require conversation resolution before merging**
- [x] **Do not allow bypassing the above settings**（adminも例外なし）

### 推奨（必須ではない）

- [x] **Require linear history** — merge commitを禁止、squash or rebase merge のみ
- [ ] Require signed commits — GPG/SSH署名強制。個人開発では運用負担増のため一旦off
- [x] **Restrict who can push to matching branches** — adminのみ

### 不要

- Restrict pushes that create matching files patterns — 個人プロジェクトでは過剰

## merge方式

repo > Settings > General > Pull Requests:

- [ ] Allow merge commits — off（履歴をlinearに保つ）
- [x] Allow squash merging — on
- [ ] Allow rebase merging — お好みで
- [x] Automatically delete head branches — on（mergeされたbranchを自動削除）

## main以外のブランチ

`feat/*`, `fix/*` 等の作業ブランチには保護不要。

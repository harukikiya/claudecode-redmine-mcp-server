# Tool Catalog

このドキュメントはRedmine MCP serverが公開するtoolの一覧と仕様を定義する。

## Conventions

- Tool命名: `verb_resource[_qualifier]` (snake_case)
- 全toolはasync
- Errorは [ADR-0008](adr/0008-error-handling-strategy.md) に従いcategorized error responseで返す
- 破壊的操作（`delete_*`）はscope外（[ADR-0007](adr/0007-tool-granularity.md) 関連）
- Custom Fieldsはscope外。create/update系toolはCF入力を受け付けない
- Redmine APIは `?include=...` で関連resourceを埋め込める。各get/list系toolで `include` をoptional paramとして受け付ける

## 認証

全toolは `X-Redmine-API-Key` headerを付けてRedmineにアクセスする（[ADR-0006](adr/0006-authentication-method.md)）。

---

## Tier 1 (M2) — Core: 12 tools

### Issues

#### `list_issues`
- Purpose: filter付きでissue一覧を取得
- Endpoint: `GET /issues.json`
- Key params: `project_id`, `status_id`, `assigned_to_id`, `tracker_id`, `priority_id`, `subject` (検索), `limit`, `offset`, `sort`, `include`
- Note: `query_id` paramはTier 3で追加

#### `get_issue`
- Purpose: 単一issue取得
- Endpoint: `GET /issues/:id.json`
- Required: `id`
- Optional: `include` (e.g., `journals`, `attachments`, `relations`, `watchers`, `children`)

#### `create_issue`
- Purpose: issue起票
- Endpoint: `POST /issues.json`
- Required: `project_id`, `subject`
- Optional: `tracker_id`, `status_id`, `priority_id`, `description`, `assigned_to_id`, `category_id`, `fixed_version_id`, `parent_issue_id`, `start_date`, `due_date`, `estimated_hours`, `done_ratio`, `watcher_user_ids`

#### `update_issue`
- Purpose: issue更新（status遷移・note追加含む）
- Endpoint: `PUT /issues/:id.json`
- Required: `id`
- Optional: create_issueのoptional全て + `notes` (コメント追加), `private_notes`

### Resolution

#### `list_projects`
- Purpose: 自分が見えるproject一覧
- Endpoint: `GET /projects.json`
- Optional: `include` (`trackers`, `issue_categories`等)

#### `get_current_user`
- Purpose: 現在の認証userの情報取得（自分のid解決用）
- Endpoint: `GET /users/current.json`

### Enums（起票時に必要）

#### `list_issue_statuses`
- Endpoint: `GET /issue_statuses.json`

#### `list_trackers`
- Endpoint: `GET /trackers.json`

#### `list_priorities`
- Endpoint: `GET /enumerations/issue_priorities.json`

### Time Entries

#### `list_time_entries`
- Purpose: 工数記録一覧
- Endpoint: `GET /time_entries.json`
- Key params: `issue_id`, `project_id`, `user_id`, `spent_on`, `from`, `to`, `limit`, `offset`

#### `create_time_entry`
- Purpose: 工数記録
- Endpoint: `POST /time_entries.json`
- Required: `hours`, AND (`issue_id` OR `project_id`)
- Optional: `spent_on` (default: today), `activity_id`, `comments`

#### `update_time_entry`
- Purpose: 工数記録の修正
- Endpoint: `PUT /time_entries/:id.json`
- Required: `id`
- Optional: `hours`, `spent_on`, `activity_id`, `comments`, `issue_id`, `project_id`

### Tier 1 実装順

1. `get_current_user` — 最もシンプル、auth疎通確認に使える
2. `list_projects`
3. `list_issue_statuses` / `list_trackers` / `list_priorities`
4. `list_issues` / `get_issue`
5. `create_issue`
6. `update_issue`
7. `list_time_entries`
8. `create_time_entry`
9. `update_time_entry`

---

## Tier 2 (M3前半) — Extended: 8 tools

### Project Resources

#### `list_versions`
- Purpose: project内のversion（milestone）一覧
- Endpoint: `GET /projects/:project_id/versions.json`
- Required: `project_id`

#### `list_issue_categories`
- Purpose: project内のissue category一覧
- Endpoint: `GET /projects/:project_id/issue_categories.json`
- Required: `project_id`

### Users

#### `list_users`
- Purpose: user一覧（assignee検索用）
- Endpoint: `GET /users.json`
- **Note**: admin権限が必要。個人運用ではadmin keyを使うため通常は問題ないが、運用前提として注意
- Optional: `name`, `status`, `limit`, `offset`

### Wiki

#### `get_wiki_page`
- Purpose: wiki page取得
- Endpoint: `GET /projects/:project_id/wiki/:title.json`
- Required: `project_id`, `title`
- Optional: `include` (`attachments`等)

#### `create_or_update_wiki_page`
- Purpose: wiki page作成または更新（Redmineは同じPUTで両方扱う）
- Endpoint: `PUT /projects/:project_id/wiki/:title.json`
- Required: `project_id`, `title`, `text`
- Optional: `comments`, `version` (更新時のconflict検出)

### Attachments

#### `upload_attachment`
- Purpose: ファイルをuploadしてtokenを取得
- Endpoint: `POST /uploads.json` (Content-Type: application/octet-stream)
- Required: `file_path` または `file_content` (bytes), `filename`
- Returns: `token` (attachに使う)

#### `attach_to_issue`
- Purpose: upload済みtokenを使ってissueに添付
- Endpoint: `PUT /issues/:id.json` with `uploads: [{token, filename, content_type}]`
- Required: `id` (issue id), `token`, `filename`
- Optional: `content_type`, `description`

### Search

#### `search`
- Purpose: 横断free text search (issues / wiki / documents / messages等)
- Endpoint: `GET /search.json`
- Required: `q` (query string)
- Optional: `scope`, `all_words`, `titles_only`, `issues`, `wiki_pages`, `documents`, `messages`, `limit`, `offset`

### Tier 2 実装順

1. `list_versions` / `list_issue_categories` (Tier 1のenum延長)
2. `list_users`
3. `search` (read-only, 独立)
4. `get_wiki_page`
5. `create_or_update_wiki_page`
6. `upload_attachment` (binary uploadの基盤)
7. `attach_to_issue`

---

## Tier 3 (M3後半) — Nice to Have: 5 tools

優先順位順:

### Queries（Tier 3 最優先）

#### `list_queries`
- Purpose: 保存済みクエリ一覧
- Endpoint: `GET /queries.json`

#### `list_issues` の拡張
- Tier 3で `query_id` paramを追加
- 動作: query_id指定時はそのfilterでissue取得

### Issue Relations

#### `list_issue_relations`
- Purpose: あるissueに紐づくrelation一覧
- Endpoint: `GET /issues/:id/relations.json`
- Required: `id` (issue id)

#### `create_issue_relation`
- Purpose: issue間のrelation作成
- Endpoint: `POST /issues/:id/relations.json`
- Required: `id`, `issue_to_id`, `relation_type` (`relates`, `duplicates`, `blocks`, `precedes`, etc.)
- Optional: `delay` (precedes/follows用)

### Watchers

#### `add_watcher`
- Purpose: issueにwatcherを追加
- Endpoint: `POST /issues/:id/watchers.json`
- Required: `id` (issue id), `user_id`

#### `remove_watcher`
- Purpose: issueからwatcher削除
- Endpoint: `DELETE /issues/:id/watchers/:user_id.json`
- Required: `id` (issue id), `user_id`
- Note: HTTP DELETEを使うが、issueやuserそのものではなく「watch関係」を解除するだけ。データロスを伴わないためscope内とする

### Tier 3 実装順

1. `list_queries` + `list_issues` の `query_id` 拡張
2. `list_issue_relations`
3. `create_issue_relation`
4. `add_watcher`
5. `remove_watcher`

---

## 合計

| Tier | Tools | Milestone |
|---|---|---|
| 1 | 12 | M2 |
| 2 | 8 | M3前半 |
| 3 | 5 | M3後半 |
| **合計** | **25** | |

## Out of Scope

- 破壊的操作 (`delete_issue`, `delete_project`, `delete_time_entry`, `delete_wiki_page` 等のentity削除)
- Custom Field定義変更
- User / Group / Role管理（admin操作）
- News（プロジェクトアナウンス機能）
- Project / Membership作成・更新

破壊的操作の扱いに例外あり: `remove_watcher` と（将来必要なら）`delete_issue_relation` は「関係性の解除」であってentityを消さないため許容する方針。

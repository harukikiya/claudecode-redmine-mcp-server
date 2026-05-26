# Setup Guide

Redmine MCP serverをGitHubで運用開始するための手順。一度きりのsetupだが、別環境で再現する場合のために残す。

## 前提

- GitHubアカウントと配置先repository（既存のscaffoldingがある想定）
- ローカルにgit / uv / Python 3.11+
- 後でCodecovアカウント（無料、GitHubログイン可）

---

## Phase 0: 既存scaffoldingとの統合

既にrepoに scaffolding（setup scripts等）がある前提。

1. backup branchを切る: `git checkout -b backup/pre-m0`
2. 競合する可能性のあるファイルを確認:
   - `CLAUDE.md` / `README.md` / `LICENSE` / `pyproject.toml`
   - `.github/` 配下の既存ファイル
3. 必要なら手動マージ。既存のsetup scriptsは活かす方針で

---

## Phase 1: ファイル配置

### 1-1. 配置するもの

M0で生成した以下を repo root に配置:

```
.claude/
├── rules/python-conventions.md
├── settings.json
└── skills/
    ├── implement-redmine-tool/SKILL.md
    └── pre-push-review/SKILL.md
.github/
├── ISSUE_TEMPLATE/{config,01_bug,02_tool,03_adr,04_feature,05_question}.yml
├── workflows/{ci,auto-add-to-project,auto-label,labels-sync,release-please,stale}.yml
├── dependabot.yml
├── labeler.yml
├── labels.yml
└── PULL_REQUEST_TEMPLATE.md
docs/
├── adr/{0001..0008}-*.md, README.md, TEMPLATE.md
├── branch-protection.md
├── review-checklist.md
├── setup-guide.md  (このファイル)
└── tools.md
CLAUDE.md
CONTRIBUTING.md
LICENSE
README.md
SECURITY.md
```

### 1-2. placeholder の置換

`grep` で検索して、自分のrepoの実値に置換:

| placeholder | 置換先 | 例 |
|---|---|---|
| `harukikiya/claudecode-redmine-mcp-server` | GitHub owner/repo | `mygithub-user/redmine-mcp-server` |
| `harukikiya` | GitHub username単独 | `mygithub-user` |
| `PROJECT_NUMBER` | Projects boardの番号 | `1`（Phase 2-2で確定） |
| `[OWNER]` | LICENSE の著作権者名 | GitHub username等で可 |

検索コマンド:

```sh
grep -rn "harukikiya/claudecode-redmine-mcp-server\|harukikiya\|PROJECT_NUMBER\|\[OWNER\]" . \
  --exclude-dir=.git --exclude-dir=node_modules
```

### 1-3. pyproject.toml

M0段階では未作成。M1で作る。

---

## Phase 2: GitHub repo の設定

### 2-1. Discussions 有効化

`Settings > General > Features` → `Discussions` を on。
確認: repo top に `Discussions` tab が出る。

### 2-2. Projects board 作成

1. Profile（personal account）→ `Projects` (`https://github.com/users/harukikiya/projects`)
2. `New project` → Template `Board`
3. プロジェクト名: 「Redmine MCP Server」等
4. URL末尾の数字 `N` を控える: `https://github.com/users/harukikiya/projects/N`
5. `.github/workflows/auto-add-to-project.yml` の `PROJECT_NUMBER` を `N` に置換

### 2-3. Milestone の作成

`Issues > Milestones > New milestone` で5つ:

- M0: 設計・調査（completedで作成 → 即closeでも可）
- M1: Skeleton
- M2: Core tools (Tier 1)
- M3: Extended tools (Tier 2 + 3)
- M4: 品質・CI

既に作成済みのscaffoldingがあるなら確認のみ。

---

## Phase 3: 外部連携 / Secrets

### 3-1. Codecov 連携

1. https://about.codecov.io/ にGitHubでログイン
2. `+ Setup repo` でこのrepoを選択
3. GitHub Appをinstall（無料）
4. repository upload token をコピー
5. GitHub repo `Settings > Secrets and variables > Actions > New repository secret`
   - Name: `CODECOV_TOKEN`
   - Value: コピーしたtoken

### 3-2. PROJECT_TOKEN 作成

Projects操作には `GITHUB_TOKEN` では権限不足なのでPersonal Access Tokenが必要:

1. `Settings > Developer settings > Personal access tokens > Tokens (classic) > Generate new token`
2. Note: `redmine-mcp-projects`
3. Expiration: 1年（カレンダーにrenew予定を入れておくと安全）
4. Scopes:
   - [x] `repo` (full control)
   - [x] `project`
5. `Generate token` → 即コピー（再表示不可）
6. repo `Settings > Secrets > Actions > New repository secret`:
   - Name: `PROJECT_TOKEN`
   - Value: コピーしたtoken

---

## Phase 4: 初回push

### 4-1. commit & push

直mainでもいいが、初回PRにするとworkflowの動作確認になる:

```sh
git checkout -b chore/m0-setup
git add .
git commit -m "chore: add M0 docs and GitHub workflows"
git push origin chore/m0-setup
```

そのままPR作成（template が表示されることを確認）。

### 4-2. workflow の確認

repo `Actions` tab:

- ✓ `CI` — まだソースファイル無いのでpytest/ruff/mypy は no-op で pass する想定
- ✓ `Sync Labels` — `.github/labels.yml` の内容でGitHubラベルが作成される
- `Auto Add to Project` は issue 作成時のみ動く
- `Auto Label` は path-based、PR時に動く

初回のActions実行は手動承認待ちで pending になることがある → `Actions` tabの「I understand my workflows, go ahead and enable them」をクリック。

### 4-3. main へ merge

CI green を確認 → squash merge。

---

## Phase 5: Branch protection

**Phase 4 が完了した後で**設定する（早く有効化するとPRがmergeできなくなる）。

`Settings > Branches > Add classic branch protection rule`:

- Branch name pattern: `main`
- 設定: [`branch-protection.md`](branch-protection.md) に従う

必須:

- [x] Require a pull request before merging
- [x] Require status checks to pass before merging
  - Required statuses: `test`（CI workflow のjob名）
- [x] Do not allow bypassing the above settings

---

## Phase 6: 動作確認

### 6-1. Labelの存在確認

`Issues > Labels` で `labels.yml` の全ラベルが揃っていることを確認。
無ければ `Actions > Sync Labels > Run workflow` で手動実行。

### 6-2. テストissue起票

`Issues > New issue` で Forms picker が出る。5種類のtemplateが選べることを確認。

🔧 Tool Implementation で `get_current_user` のissueを試しに起票（M1で実際に使う）。

確認項目:

- [ ] ラベルが自動付与（`type: tool`, `status: ready`）
- [ ] Projects boardに自動追加された
- [ ] picker画面に Discussions リンクが出ている

### 6-3. テストPR

軽微な変更（typo修正等）で動作確認:

- [ ] CI が走る
- [ ] auto-label が path-based で動く
- [ ] PR template が表示される
- [ ] Codecov コメントが付く（test実行があれば）

### 6-4. Claude Code 起動確認

repo root で Claude Code 起動:

- [ ] `CLAUDE.md` が読まれている（Model Selectionの内容に従っているか確認）
- [ ] `.claude/settings.json` の `model: sonnet` がdefaultとして効いているか
- [ ] tool実装のお願いで `implement-redmine-tool` skill が発動するか

---

## Troubleshooting

### CI が無限に「pending」のまま

初回起動時、Actionsが手動承認待ち。`Actions` tabで「I understand my workflows, go ahead and enable them」をクリック。

### `release-please` が release PRを作らない

`feat:` / `fix:` 形式のcommitがmainに入って初めて生成される。初回は手動で `pyproject.toml` の version設定が必要なこともある。

### Codecov upload で `token missing`

- repo Secrets に `CODECOV_TOKEN` が登録されているか確認
- repoがprivateの場合token必須、publicでも明示的に登録した方が安定

### `auto-add-to-project` が permission denied

- `PROJECT_TOKEN` の scope を確認（`project` + `repo`）
- expired してたら再発行

### `labels-sync` で resource not accessible

- repo > Settings > Actions > General > Workflow permissions が `Read and write permissions` になっているか確認

### Dependabot がPRを作らない

- 初回は1週間（schedule weekly）待つか、Settings > Code security and analysis > Dependabot version updates が enabled か確認

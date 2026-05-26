# Architecture Decision Records

このディレクトリはRedmine MCP serverの設計判断を記録します。
形式は[MADR (Markdown Any Decision Records)](https://adr.github.io/madr/) v4 を採用しています。

## ファイル命名規則

`NNNN-kebab-case-title.md` (zero-padded 4桁)

## ステータス

- `proposed`: 提案中、レビュー前
- `accepted`: 承認済み、有効
- `deprecated`: 非推奨、新規参照しないこと
- `superseded by ADR-NNNN`: 別ADRで置き換え

## ADR一覧

| ID | Title | Status | Date |
|---|---|---|---|
| 0001 | Programming Language | accepted | 2026-05-25 |
| 0002 | MCP SDK Selection | accepted | 2026-05-25 |
| 0003 | Packaging Tool | accepted | 2026-05-25 |
| 0004 | HTTP Client | accepted | 2026-05-25 |
| 0005 | Config Management | accepted | 2026-05-25 |
| 0006 | Authentication Method | accepted | 2026-05-25 |
| 0007 | Tool Granularity | accepted | 2026-05-25 |
| 0008 | Error Handling Strategy | accepted | 2026-05-25 |

ADR-0002はチャット中で議論したMADR sampleをそのまま採用しています。他7本はskeleton状態（Decision Outcomeのみ確定、残りは `<!-- TBD -->`）なので、Claude Codeで肉付けする想定です。

## 新規ADRを書くとき

1. `TEMPLATE.md`をコピーして`NNNN-title.md`にrename
2. Claude Codeに提案させる場合は `status: proposed` で開始
3. ユーザーレビュー・承認後に `status: accepted` に変更してmerge
4. このREADMEのADR一覧テーブルを更新

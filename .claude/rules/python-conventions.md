# Python Conventions

Redmine MCP serverのPythonコード規約。CLAUDE.mdから参照される詳細ルール。

## Language Policy

- **コメント・docstringは日本語で書く**。技術用語は英語のまま（例: `MCP tool`, `Pydantic model`, `async function` 等は無理に和訳しない）
- 識別子（変数名・関数名・クラス名）は英語
- ログ・エラーメッセージは原則英語（systemログとの整合のため。ユーザー向け表示が日本語の場合のみ日本語）

---

## Type Annotations

### 必須

- **全関数の引数と戻り値**に型注釈
- **全モジュール / 全クラスのattribute**に型注釈
- **全ローカル変数**にも型注釈を付ける（プロジェクト方針）

> NOTE: Pythonの慣習ではローカル変数の型注釈は推論に任せるのが一般的だが、本プロジェクトでは可読性と意図明示を優先し、明示する方針。
> ただし、リテラルから明らかに型が決まる場合（`x = 0`, `name = "foo"` 等）は例外として省略可。複雑な式・空コレクション・`None`初期値・public APIから受け取った値は必須。

### `Any` の扱い

`Any` は **逃げ道として最終手段**。使う場合:

- 理由をコメントに残す: `x: Any  # Redmineが返すJSON。versionにより構造が変わるためAny`
- 可能なら `object` / `TypedDict` / Union型 / Protocol で代替を検討

### Forward references

- `from __future__ import annotations` を全ファイルで有効化
- circular import回避のため、`TYPE_CHECKING` ガード内のimportを活用

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 実行時にはimportされない。型注釈でのみ使う
    from .redmine.client import RedmineClient
```

### mypy

- `mypy --strict` をpassすること
- 個別suppressionは `# type: ignore[error-code]` の形式で、error code指定必須
- file-level / module-level suppressionは原則禁止

---

## Docstrings

### 必須

- **全public module / class / function / method**にdocstring必須
- スタイルは **Google style** に統一
- **本文は日本語**で書く（技術用語は英語のまま）

### 含めるべき要素

| 要素 | 必須 / 推奨 | 説明 |
|---|---|---|
| 1行summary | 必須 | 「動詞 + 目的語」で簡潔に |
| 詳細description | 推奨 | summary後に空行、続けて段落で背景・挙動補足 |
| `Args:` | 必須（引数があれば） | 各引数の名前、型、説明 |
| `Returns:` | 必須（戻り値があれば） | 戻り値の型と意味 |
| `Raises:` | 推奨 | 明示的に発生させる例外を列挙 |
| `Example:` | toolは強く推奨 | 使用例。MCP toolはLLMがhintとして読むので特に重要 |

### 例

```python
async def list_issues(
    project_id: str | None = None,
    status_id: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> ListIssuesResult:
    """Redmineのissue一覧を取得する。

    Redmineの ``GET /issues.json`` をwrapする。project / status / paginationの
    filterに対応する。全filter optionは ``docs/tools.md`` を参照。

    Args:
        project_id: project identifier（数値ID または shortname）でfilterする。
        status_id: issue statusでfilterする。特殊値: ``open``, ``closed``, ``*``。
        limit: 返却するissueの最大数（default 25、max 100）。
        offset: pagination offset。

    Returns:
        マッチしたissueとpaginationメタデータを含む ``ListIssuesResult``。

    Raises:
        RedmineAuthError: API keyが不正な場合。
        RedmineNotFoundError: 指定したproject_idが存在しない場合。

    Example:
        >>> await list_issues(project_id="rp2040", status_id="open", limit=10)
        ListIssuesResult(issues=[...], total_count=42, offset=0, limit=10)
    """
    # まずRedmineに渡すparam dictを組み立てる
    params: dict[str, str | int] = {"limit": limit, "offset": offset}
    if project_id is not None:
        params["project_id"] = project_id
    if status_id is not None:
        params["status_id"] = status_id
    # ... 実装続く
```

### 内部関数

`_leading_underscore` で始まる内部関数は1行summaryのみで可。
ロジックが複雑な場合は通常のdocstringを書く。

### Module-level docstring

全moduleの先頭に1段落のdocstringを置く。何を提供するmoduleかが分かること。

```python
"""Redmine issue tools.

このmoduleはissueのCRUD操作（list, get, create, update）をMCP toolとして
公開する。各toolはRedmine REST API endpointをwrapし、失敗時はADR-0008に従った
categorized errorを返す。
"""
```

---

## Comments

- **日本語で書く**（技術用語は英語のまま）
- コメントは「なぜ」を説明する。「何を」はコードから読めるので不要
- 良い例: `# Redmineは offset=0 で最初の25件を返す。limitなしのときは全件取得が必要なのでloopする`
- 悪い例: `# i に 1 を足す`

---

## Async

- I/Oは全て `async def` + `await`
- async関数の中で同期blocking I/O（`requests`、`time.sleep` 等）は禁止
- 同期的に書きたいCPUバウンド処理は `asyncio.to_thread` を使う

## Imports

- 順序: 標準ライブラリ → サードパーティ → ローカル（`ruff` が自動整形）
- 各グループ間は空行1つ
- relative importはpackage内のみ

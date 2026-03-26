---
name: auto-wiki-sync
description: Rebuild and reconcile Auto-Wiki state files. Use after article, template, feedback, or expansion changes to rescan articles/, rebuild links_to and linked_from, regenerate db/graph.json, refresh index.html, and update db/session.json.
---

# Auto-Wiki: DB同期・再生成

全データベースファイルとindex.htmlの整合性を検証・再構築するスキル。他のスキルの操作後に呼び出される。

## 入力

なし（現在のDB状態から自動判定）

## 実行手順

### 1. CLI一括同期

以下のコマンドで整合性チェック・再構築・クリーンアップを一括実行:

```bash
uv run awiki sync
```

このコマンドは以下を自動実行:
- `articles/` ディレクトリとDBの照合（孤立ファイル・孤立エントリの検出）
- `linked_from` の全再構築
- `graph.json` の再生成
- `brainstorm.json` のクリーンアップ（既存記事の除去、重複削除、履歴100件制限）
- `session.json` の更新（`last_phase: "sync"`）

結果はJSON形式で返される:
```json
{
  "articles_count": N,
  "orphan_db_entries": [],
  "untracked_html_files": [],
  "graph_nodes": N,
  "graph_links": N,
  "brainstorm_cleaned": N
}
```

### 2. リンク整合性検証（HTMLベース）

CLIの `sync` はDB内の `links_to` からの再構築を行う。
HTMLから実際のリンクを抽出して `links_to` を更新する必要がある場合は、各記事について:

1. 記事HTMLから `<a href="...html">` を抽出
2. `uv run awiki article set-links {slug} --links "{link1},{link2}"` で更新

### 3. index.html 再生成

`templates/index.html` テンプレートを読み込み、プレースホルダーを置換:

| プレースホルダー | 内容 |
|---|---|
| `{{LANG}}` | 言語コード（デフォルト "ja"） |
| `{{TOTAL_COUNT}}` | `uv run awiki article list` の `total_count` |
| `{{LINK_COUNT}}` | `uv run awiki graph rebuild` の links 配列長 |
| `{{ARTICLE_ROWS}}` | 記事一覧テーブル行（下記形式） |

記事行の形式:
```html
<tr>
  <td><a href="articles/{slug}.html">{title}</a></td>
  <td>{summary}</td>
  <td>{updated_at}</td>
  <td>{links_to.length + linked_from.length}</td>
</tr>
```

記事は `updated_at` 降順でソート。

### 4. 完了報告

- 総記事数
- 総リンク数
- 修正があった場合はその詳細
- キュー内候補数

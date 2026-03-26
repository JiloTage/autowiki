---
name: auto-wiki-sync
description: Rebuild and reconcile Auto-Wiki state files for a specific wiki. Use after article, template, feedback, or expansion changes to rescan the wiki's articles/, rebuild links, regenerate graph.json, refresh the wiki index.html, and update session.json.
---

# Auto-Wiki: DB同期・再生成 (Multi-Wiki)

特定wikiの全データベースファイルとindex.htmlの整合性を検証・再構築するスキル。

## 入力

```
--wiki WIKI_ID
```

- `--wiki`: 対象wiki ID（省略時: 自動解決）

## 実行手順

### 1. CLI一括同期

```bash
uv run awiki sync --wiki {wiki-id}
```

このコマンドは以下を自動実行:
- `wikis/{wiki-id}/articles/` とDBの照合
- `linked_from` の全再構築
- `graph.json` の再生成
- `brainstorm.json` のクリーンアップ
- `session.json` の更新

### 2. リンク整合性検証（HTMLベース）

HTMLから実際のリンクを抽出して更新する必要がある場合:

1. 記事HTMLから `<a href="...html">` を抽出
2. `uv run awiki article set-links --wiki {wiki-id} {slug} --links "{link1},{link2}"`

### 3. wiki index.html 再生成

`templates/wiki-index.html` テンプレートを読み込み、プレースホルダーを置換:

| プレースホルダー | 内容 |
|---|---|
| `{{WIKI_TITLE}}` | wiki名 |
| `{{WIKI_DESCRIPTION}}` | wikiの説明文 |
| `{{LANG}}` | 言語コード（デフォルト "ja"） |
| `{{TOTAL_COUNT}}` | 総記事数 |
| `{{LINK_COUNT}}` | graph.json の links 配列長 |
| `{{ARTICLE_ROWS}}` | 記事一覧テーブル行 |

記事行: `<td><a href="articles/{slug}.html">{title}</a></td>`

出力先: `wikis/{wiki-id}/index.html`

### 4. 完了報告

- wiki名と総記事数
- 総リンク数
- 修正があった場合はその詳細
- キュー内候補数

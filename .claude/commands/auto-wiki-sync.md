---
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Skill
description: "Auto-Wiki: Synchronize databases, rebuild graph, regenerate wiki index from current state"
---

# Auto-Wiki: DB同期・再生成 (Multi-Wiki)

特定wikiの全データベースファイルとindex.htmlの整合性を検証・再構築するskill。

## 入力

$ARGUMENTS:
```
--wiki WIKI_ID
```

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

HTMLから実際のリンクを抽出して `links_to` を更新する必要がある場合は、各記事について:

1. 記事HTMLから `<a href="...html">` を抽出
2. `uv run awiki article set-links --wiki {wiki-id} {slug} --links "{link1},{link2}"`

### 3. wiki index.html 再生成

`templates/wiki-index.html` テンプレートを読み込み、プレースホルダーを置換:

| プレースホルダー | 内容 |
|---|---|
| `{{WIKI_TITLE}}` | `uv run awiki wiki get {wiki-id}` の title |
| `{{WIKI_DESCRIPTION}}` | wikiの説明文 |
| `{{LANG}}` | 言語コード（デフォルト "ja"） |
| `{{TOTAL_COUNT}}` | 総記事数 |
| `{{LINK_COUNT}}` | graph.json の links 配列長 |
| `{{ARTICLE_ROWS}}` | 記事一覧テーブル行 |

記事行の形式:
```html
<tr>
  <td><a href="articles/{slug}.html">{title}</a></td>
  <td>{summary}</td>
  <td>{updated_at}</td>
  <td>{links_to.length + linked_from.length}</td>
</tr>
```

出力先: `wikis/{wiki-id}/index.html`

### 4. ポータル再生成

`/auto-wiki-portal` を `Skill` で呼び出し、ルートの `index.html` を最新状態に更新する。

### 5. 完了報告

- wiki名と総記事数
- 総リンク数
- 修正があった場合はその詳細
- キュー内候補数

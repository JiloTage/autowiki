---
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
description: "Auto-Wiki: Synchronize databases, rebuild graph, regenerate index.html from current state"
---

# Auto-Wiki: DB同期・再生成

全データベースファイルとindex.htmlの整合性を検証・再構築するskill。他のskillの操作後に呼び出される。

## 入力

$ARGUMENTS: なし（現在のDB状態から自動判定）

## 実行手順

### 1. 現状スキャン

1. `articles/` ディレクトリ内の全HTMLファイルをスキャン
2. `db/articles.json` を読み込む
3. `db/brainstorm.json` を読み込む
4. `db/graph.json` を読み込む

### 2. articles.json 整合性検証

1. **ファイル→DB照合**: `articles/` 内の各HTMLファイルが `db/articles.json` にエントリを持つか確認
   - 無ければ警告を表示（孤立ファイル）
2. **DB→ファイル照合**: `db/articles.json` の各エントリが `articles/` に実体ファイルを持つか確認
   - 無ければDBから削除
3. **total_count** を実際のエントリ数で更新

### 3. リンク整合性検証

各記事HTMLファイルから `<a href="...html">` を抽出し:

1. `links_to` の再構築: HTMLから実際に抽出されたリンク先で上書き
2. `linked_from` の再構築: 全記事を走査して被リンクを再計算
3. 双方向リンクの一致を検証

### 4. graph.json 再生成

`db/articles.json` から完全に再生成:

```json
{
  "nodes": [
    {
      "id": "slug",
      "title": "タイトル",
      "url": "articles/slug.html",
      "summary": "要約",
      "is_root": true|false
    }
  ],
  "links": [
    {"source": "slug-a", "target": "slug-b"}
  ]
}
```

- `is_root`: `origin === "root"` の記事のみtrue
- `links`: 全記事の `links_to` からリンクが実在する（双方のノードが存在する）もののみ

### 5. index.html 再生成

`templates/index.html` テンプレートを読み込み、プレースホルダーを置換:

| プレースホルダー | 内容 |
|---|---|
| `{{LANG}}` | 言語コード（デフォルト "ja"） |
| `{{TOTAL_COUNT}}` | `db/articles.json` の総記事数 |
| `{{LINK_COUNT}}` | `db/graph.json` のlinks配列長 |
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

### 6. brainstorm.json クリーンアップ

1. queueから既に記事が存在するslugの候補を削除
2. queueから重複候補を削除（同一slug）
3. historyが100件を超えたら古い順に切り詰め

### 7. session.json 更新

```json
{
  "last_phase": "sync",
  "last_run": "ISO8601",
  "total_articles": N,
  "queue_size": N,
  "max_agents": 3,
  "max_total_articles": 50
}
```

### 8. 完了報告

- 総記事数
- 総リンク数
- 修正があった場合はその詳細
- キュー内候補数

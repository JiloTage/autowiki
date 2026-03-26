---
name: auto-wiki-feedback
description: Apply user feedback to an existing Auto-Wiki article within a specific wiki while preserving link consistency. Use when an article needs edits and the wiki's databases must stay synchronized.
---

# Auto-Wiki: フィードバック適用 (Multi-Wiki)

特定wiki内の既存記事にユーザーのフィードバックを適用し、リンク整合性を維持するスキル。

## 入力

```
--wiki WIKI_ID "記事slug" フィードバック内容...
```

- `--wiki`: 対象wiki ID（省略時: 自動解決）

## 実行手順

### 1. 記事特定

1. `uv run awiki article list --wiki {wiki-id}` で全記事を取得
2. 指定された文字列でslugまたはタイトルを検索
3. 該当記事が見つからない場合は部分一致で候補を提示

### 2. 記事読み込み

1. `wikis/{wiki-id}/articles/{slug}.html` を読み込む
2. `uv run awiki article get --wiki {wiki-id} {slug}` で記事メタデータを取得
3. 現在の `links_to` と `linked_from` を記録

### 3. フィードバック適用

ユーザーのフィードバックに従って記事を修正。

### 4. リンク整合性検証

修正後のHTMLから全 `<a href="...html">` を抽出し:

1. リンクの一括更新:
   ```bash
   uv run awiki article set-links --wiki {wiki-id} {slug} --links "{link1},{link2}"
   ```

2. 存在しないリンク先の候補追加:
   ```bash
   uv run awiki brainstorm add --wiki {wiki-id} --slug "{new-slug}" --title "{title}" --source-id "{slug}" --rationale "フィードバックによる追加リンク" --score 0.7
   ```

### 5. DB更新

1. グラフ再構築: `uv run awiki graph rebuild --wiki {wiki-id}`
2. wiki index.html を再生成（出力先: `wikis/{wiki-id}/index.html`）

### 6. 完了報告

- 修正内容のサマリー
- リンク変更の詳細
- 新たにqueueに追加された候補

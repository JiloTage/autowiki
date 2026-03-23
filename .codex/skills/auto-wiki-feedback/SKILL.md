---
name: auto-wiki-feedback
description: Apply user feedback to an existing Auto-Wiki article while preserving link consistency. Use when an article needs content, section, diagram, or link edits and db/articles.json, db/brainstorm.json, db/graph.json, and index.html must stay synchronized.
---

# Auto-Wiki: フィードバック適用

既存記事にユーザーのフィードバックを適用し、リンク整合性を維持するスキル。

## 入力

```
"記事slug" フィードバック内容...
```

- 最初の引用文字列またはスペースまでの文字列が記事slugまたはタイトル
- それ以降がフィードバック内容

## 実行手順

### 1. 記事特定

1. `db/articles.json` を読み込む
2. 指定された文字列でslugまたはタイトルを検索
3. 該当記事が見つからない場合:
   - 部分一致で候補を提示
   - ユーザーに確認

### 2. 記事読み込み

1. `articles/{slug}.html` を読み込む
2. `db/articles.json` から記事メタデータを取得
3. 現在の `links_to` と `linked_from` を記録

### 3. フィードバック適用

ユーザーのフィードバックに従って記事を修正:
- 内容の修正・追加・削除
- セクション構造の変更
- インラインSVGダイアグラムの修正
- リンクの追加・削除

### 4. リンク整合性検証

修正後のHTMLから全 `<a href="...html">` を抽出し:

1. **新しいリンクの検出**:
   - 修正前に無かったリンク先を特定
   - リンク先が `db/articles.json` に存在する場合:
     - リンク先記事の `linked_from` にこの記事slugを追加
   - リンク先が存在しない場合:
     - `db/brainstorm.json` のqueueに候補として追加
     ```json
     {
       "proposed_slug": "new-slug",
       "proposed_title": "リンクテキストから推定",
       "source_id": "this-article-slug",
       "rationale": "フィードバックによる追加リンク",
       "interestingness_score": 0.7,
       "status": "queued"
     }
     ```

2. **削除されたリンクの検出**:
   - 修正前にあったが修正後に無いリンク先を特定
   - リンク先記事の `linked_from` からこの記事slugを削除

3. **`links_to` 更新**:
   - 修正後のHTMLから抽出したリンク先で `links_to` を再構築

### 5. DB更新

1. `db/articles.json`:
   - `updated_at` を更新
   - `links_to` を更新
   - 影響を受けた他記事の `linked_from` を更新
2. `db/brainstorm.json`: 新候補があれば追加
3. `db/graph.json` を再生成（全ノード・全リンク）
4. `index.html` を再生成（`templates/index.html` テンプレートから）

### 6. 完了報告

- 修正内容のサマリー
- リンク変更の詳細（追加/削除）
- 新たにqueueに追加された候補があれば報告

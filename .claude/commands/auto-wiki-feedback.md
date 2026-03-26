---
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
description: "Auto-Wiki: Apply user feedback to an existing article and maintain link integrity"
---

# Auto-Wiki: フィードバック適用

既存記事にユーザーのフィードバックを適用し、リンク整合性を維持するskill。

## 入力

$ARGUMENTS:
```
"記事slug" フィードバック内容...
```

- 最初の引用文字列またはスペースまでの文字列が記事slugまたはタイトル
- それ以降がフィードバック内容

## 実行手順

### 1. 記事特定

1. `uv run awiki article list` で全記事を取得
2. 指定された文字列でslugまたはタイトルを検索（JSONの出力から判定）
3. 該当記事が見つからない場合:
   - 部分一致で候補を提示
   - ユーザーに確認

### 2. 記事読み込み

1. `articles/{slug}.html` を読み込む
2. `uv run awiki article get {slug}` で記事メタデータを取得
3. 現在の `links_to` と `linked_from` を記録

### 3. フィードバック適用

ユーザーのフィードバックに従って記事を修正:
- 内容の修正・追加・削除
- セクション構造の変更
- インラインSVGダイアグラムの修正
- リンクの追加・削除

### 4. リンク整合性検証

修正後のHTMLから全 `<a href="...html">` を抽出し:

1. **リンクの一括更新**: 修正後のHTMLから全 `<a href="...html">` を抽出し、CLIで更新:
   ```bash
   uv run awiki article set-links {slug} --links "{link1},{link2},{link3}"
   ```
   これにより `links_to` の更新と、関連記事の `linked_from` の追加・削除が自動で行われる。

2. **存在しないリンク先の候補追加**: リンク先が既存記事に無い場合:
   ```bash
   uv run awiki brainstorm add --slug "{new-slug}" --title "{リンクテキストから推定}" --source-id "{this-article-slug}" --rationale "フィードバックによる追加リンク" --score 0.7
   ```

### 5. DB更新

Step 4で `article set-links` と `brainstorm add` を実行済み。残りの更新:

1. グラフ再構築: `uv run awiki graph rebuild`
2. `index.html` を再生成（`templates/index.html` テンプレートから）:
   - `{{TOTAL_COUNT}}`, `{{LINK_COUNT}}`, `{{ARTICLE_ROWS}}` を更新

### 6. 完了報告

- 修正内容のサマリー
- リンク変更の詳細（追加/削除）
- 新たにqueueに追加された候補があれば報告

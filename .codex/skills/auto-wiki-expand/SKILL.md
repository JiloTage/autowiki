---
name: auto-wiki-expand
description: Run an Auto-Wiki expansion cycle within a specific wiki. Use when pending articles should brainstorm follow-up topics, prioritize queued candidates, generate new articles, and update the wiki's db/ plus index.html.
---

# Auto-Wiki: 拡張オーケストレーション (Multi-Wiki)

特定wiki内の記事の拡張サイクルを管理するスキル。ブレスト → 優先度ソート → 並列記事作成 → 結果収集を行う。

## 入力

```
--wiki WIKI_ID
```

- `--wiki`: 対象wiki ID（省略時: 自動解決）

## 実行手順

### 1. DB読み込み

以下のコマンドでDB状態を取得:
1. `uv run awiki article list --wiki {wiki-id}`
2. `uv run awiki brainstorm list --wiki {wiki-id}`
3. `uv run awiki session get --wiki {wiki-id}`
4. `uv run awiki wiki get {wiki-id}`（wiki名・色情報取得）

### 2. 設定確認

- `max_total_articles`: デフォルト50

### 3. 上限チェック

`total_count >= max_total_articles` なら終了メッセージを表示して終了。

### 4. ブレスト

`expansion_status` が `"pending"` の記事それぞれについて:

1. `wikis/{wiki-id}/articles/{slug}.html` の内容を読み込む
2. その記事から派生する3〜5個の記事候補をブレスト
3. 各候補に面白さスコア（0.0〜1.0）を付与
4. スコア0.5未満は却下
5. 重複チェック
6. queueに追加:
   ```bash
   uv run awiki brainstorm add-batch --wiki {wiki-id} --json '[...]'
   ```
7. その記事の `expansion_status` を `"done"` に更新:
   ```bash
   uv run awiki article update --wiki {wiki-id} {slug} --expansion-status done
   ```

### 5. 記事作成

queueの全候補を `uv run awiki brainstorm pop --wiki {wiki-id}` で取り出し、各候補について `auto-wiki-create` スキルの手順に従い記事を作成する。

### 6. 結果収集・DB更新

各記事の作成結果を収集し、以下のCLIコマンドで一括更新:

1. 新記事をDBに登録:
   ```bash
   uv run awiki article add --wiki {wiki-id} --slug {slug} --title "{title}" --filename "wikis/{wiki-id}/articles/{slug}.html" --summary "{summary}" --links-to "{link1},{link2}" --origin expanded --source-id {source_slug}
   ```

2. 提案元記事のリンクを更新:
   ```bash
   uv run awiki article set-links --wiki {wiki-id} {source_slug} --links "{既存links},{new_slug}"
   ```

3. 新候補をqueueに追加:
   ```bash
   uv run awiki brainstorm add-batch --wiki {wiki-id} --json '[...]'
   ```

4. グラフを再構築:
   ```bash
   uv run awiki graph rebuild --wiki {wiki-id}
   ```

5. wiki index.html を再生成（`templates/wiki-index.html` テンプレートから）:
   - `{{WIKI_TITLE}}`: wiki名
   - `{{WIKI_DESCRIPTION}}`: wikiの説明
   - `{{TOTAL_COUNT}}`, `{{LINK_COUNT}}`, `{{ARTICLE_ROWS}}`
   - 記事行: `<td><a href="articles/{slug}.html">{title}</a></td>`
   - 出力先: `wikis/{wiki-id}/index.html`

6. セッション状態を更新:
   ```bash
   uv run awiki session update --wiki {wiki-id} --phase phase_2
   ```

### 7. 継続判定

1. 残りキュー表示（候補数、トップ5）
2. 次サイクルの候補を提示
3. ユーザーに続行するか確認
4. 続行する場合、Step 3から再実行

---
name: auto-wiki-expand
description: Run an Auto-Wiki expansion cycle. Use when pending articles should brainstorm follow-up topics, prioritize queued candidates, generate up to max_agents new articles, and update db/*.json plus index.html.
---

# Auto-Wiki: 拡張オーケストレーション

記事の拡張サイクルを管理するスキル。ブレスト → 優先度ソート → 並列記事作成 → 結果収集を行う。

## 入力

```
--max-agents N    # 同時作成記事数上限（デフォルト: 3）
```

## 実行手順

### 1. DB読み込み

1. `db/articles.json` を読み込む
2. `db/brainstorm.json` を読み込む
3. `db/session.json` を読み込む

### 2. 設定確認

- `max_agents`: デフォルト3（引数で上書き可能）
- `max_total_articles`: デフォルト50

### 3. 上限チェック

`total_count >= max_total_articles` なら終了メッセージを表示して終了。

### 4. ブレスト

`expansion_status` が `"pending"` の記事それぞれについて:

1. `articles/{slug}.html` の内容を読み込む
2. その記事から派生する3〜5個の記事候補をブレスト
3. 各候補に面白さスコア（0.0〜1.0）を付与:
   - 読者が「この先も知りたい」と思うか
   - 既存記事との差別化が十分か
   - wiki全体の知識グラフに深みを加えるか
4. スコア0.5未満は却下
5. 重複チェック:
   - 同一slugが `db/articles.json` に存在 → 却下
   - 同一slugが `db/brainstorm.json` のqueueに存在 → 却下
   - 既存記事と意味的に重複するタイトル → 却下
6. `db/brainstorm.json` のqueueに追加:
   ```json
   {
     "proposed_slug": "candidate-slug",
     "proposed_title": "候補タイトル",
     "source_id": "parent-slug",
     "rationale": "なぜこの記事が面白いか",
     "interestingness_score": 0.85,
     "status": "queued"
   }
   ```
7. その記事の `expansion_status` を `"done"` に更新

### 5. 優先度ソート

queue全体を `interestingness_score` 降順でソート。

### 6. 記事作成

queueの上位 `max_agents` 件を取り出す。各候補について `auto-wiki-create` スキルの手順に従い記事を作成する。

各記事の作成指示:
- タイトル: `proposed_title`
- slug: `proposed_slug`
- origin: `"expanded"`
- source: `source_id`
- 提案元記事を読み込んで文脈を理解した上で作成
- 既存記事への相互リンクを積極的に行う（フラット構造）
- 新規候補記事へのリンクも3〜5個含める

### 7. 結果収集・DB更新

各記事の作成結果を収集し:

1. `db/articles.json` に新記事を追加:
   ```json
   {
     "id": "slug",
     "title": "記事タイトル",
     "filename": "articles/slug.html",
     "created_at": "ISO8601",
     "updated_at": "ISO8601",
     "links_to": ["linked-slug-1"],
     "linked_from": ["source-slug"],
     "summary": "要約",
     "expansion_status": "pending",
     "origin": "expanded"
   }
   ```
2. 提案元記事の `links_to` に新記事slugを追加（未含なら）
3. 提案元記事HTMLの被リンクセクション（`{{LINKED_FROM}}`部分）を更新
4. 新記事から提案された候補を `db/brainstorm.json` のqueueに追加
5. 処理済み候補を `db/brainstorm.json` の `history` に移動
6. `db/graph.json` を再生成:
   ```json
   {
     "nodes": [
       {"id": "slug", "title": "タイトル", "url": "articles/slug.html", "summary": "要約", "is_root": false}
     ],
     "links": [
       {"source": "slug-a", "target": "slug-b"}
     ]
   }
   ```
7. `index.html` を再生成（`templates/index.html` テンプレートから）:
   - `{{LANG}}`: 言語コード
   - `{{TOTAL_COUNT}}`: 総記事数
   - `{{LINK_COUNT}}`: 総リンク数
   - `{{ARTICLE_ROWS}}`: 記事一覧テーブル行
8. `db/session.json` を更新

### 8. 継続判定

1. 残りキュー表示（候補数、トップ5）
2. 次サイクルの候補を提示
3. ユーザーに続行するか確認
4. 続行する場合、Step 3から再実行

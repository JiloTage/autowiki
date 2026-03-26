---
name: auto-wiki-request
description: Create a new requested Auto-Wiki article and connect it to the existing wiki. Use when the user asks for a new topic outside the current queue and related articles should receive reciprocal links.
---

# Auto-Wiki: 新規記事リクエスト

ユーザーが指定した新トピックの記事を作成し、既存記事と相互リンクするスキル。

## 入力

```
"新トピック名"
```

## 実行手順

### 1. コンテキスト把握

1. `uv run awiki article list` で全既存記事を取得
2. 新トピックからslugを生成（日本語はローマ字変換、英語はkebab-case）
3. 重複チェック: `uv run awiki article exists {slug}` で確認。存在する場合はエラー

### 2. 関連記事分析

1. 新トピックと関連性が高い既存記事をリストアップ（最大5件）
2. 関連度の判定基準:
   - トピックの意味的類似性
   - 既存記事のリンク先との関連
   - wiki全体の知識グラフ上の位置づけ
3. 接続候補をユーザーに提示

### 3. 記事作成

`auto-wiki-create` スキルと同様の手順で記事を作成:

1. `templates/article.html` テンプレートを読み込む
2. 記事本文を作成:
   - 冒頭段落にトピックの定義（タイトルを `<b>` 強調）
   - 3〜6セクション（H2）、必要に応じてH3
   - インラインSVGダイアグラム最低1つ（`<div class="diagram-container"><svg>...</svg></div>` 形式）
   - 関連既存記事への積極的なリンク
   - 新規候補記事へのリンク3〜5個
3. テンプレートプレースホルダーを置換
4. `articles/{slug}.html` に書き出す

### 4. 既存記事への逆リンク追加

関連性の高い既存記事（Step 2で特定したもの）に対して:

1. `articles/{existing-slug}.html` を読み込む
2. 本文の適切な箇所に新記事へのリンクを追加（文脈に自然に組み込む）
3. フッター（関連記事セクション）にもリンクを追加
4. `db/articles.json` の該当記事の `links_to` に新記事slugを追加

### 5. DB更新

CLIコマンドで一括更新:

1. 新記事をDBに登録:
   ```bash
   uv run awiki article add --slug {slug} --title "{title}" --filename "articles/{slug}.html" --summary "{summary}" --links-to "{link1},{link2}" --origin requested
   ```
2. 新規候補記事をqueueに追加:
   ```bash
   uv run awiki brainstorm add-batch --json '[{"proposed_slug":"...","proposed_title":"...","source_id":"{slug}","rationale":"...","interestingness_score":0.8}]'
   ```
3. グラフ再構築: `uv run awiki graph rebuild`
4. `index.html` を再生成

### 6. 完了報告

- 新記事のタイトルとslug
- 相互リンクされた既存記事一覧
- 新たに追加された拡張候補
- `expansion_status: "pending"` → 次のexpandサイクルで派生対象になることを通知

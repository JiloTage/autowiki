---
name: auto-wiki-create
description: Create a single Wikipedia-style HTML article within a specific wiki. Use when a root article, expanded article, or requested article needs to be generated from templates/article.html and linked into the wiki graph.
---

# Auto-Wiki: 記事作成 (Multi-Wiki)

特定wiki内に単一のWikipedia風HTML記事を作成するスキル。

## 入力

```
[topic] --wiki [wiki-id] --slug [slug] --origin [root|expanded|requested] --source [source-slug]
```

- `topic`: 記事トピック（必須）
- `--wiki`: 対象wiki ID（必須、CLIは自動解決可）
- `--slug`: slug指定（省略時は自動生成）
- `--origin`: 作成起源（デフォルト: "root"）
- `--source`: 提案元記事slug（expanded/requestedの場合）

## 実行手順

### 1. 準備

1. `uv run awiki article list --wiki {wiki-id}` で既存記事を把握
2. `uv run awiki wiki get {wiki-id}` でwiki情報（title, color等）を取得
3. slugを決定:
   - 指定がある場合はそのまま使用
   - 日本語トピックはローマ字変換 → kebab-case
   - 英語トピックはkebab-case
4. 重複チェック: `uv run awiki article exists --wiki {wiki-id} {slug}`

### 2. テンプレート読み込み

`templates/article.html` テンプレートを読み込む。

### 3. コンテキスト把握

- `--source` がある場合: `wikis/{wiki-id}/articles/{source-slug}.html` を読み込んで文脈を理解
- 既存記事一覧から、関連性の高い記事を特定

### 4. 記事本文作成

以下の構造でHTML本文を作成:

- **冒頭段落**: トピックの定義。タイトルを `<b>` で強調
- **H2セクション**: 3〜6個。各セクションに `id` 属性を付与
- **H3サブセクション**: 必要に応じて
- **インラインSVGダイアグラム**: 最低1つ。以下の形式:
  ```html
  <div class="diagram-container">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 [幅] [高さ]" width="[幅]" height="[高さ]">
      <!-- SVG要素 -->
    </svg>
    <div class="diagram-caption">図の説明</div>
  </div>
  ```
  - Mermaidは使用しない。インラインSVGで直接描画
  - 色: 背景 `#f8f9fa`, 枠線 `#a2a9b1`, テキスト `#202122`, アクセント `#36c`
- **内部リンク**:
  - 同一wiki内: `<a href="{slug}.html">{タイトル}</a>`
  - 他wikiへのクロスリンク: `<a href="../../{other-wiki-id}/articles/{slug}.html">{タイトル}</a>`
  - 既存記事へは積極的にリンク
  - 未作成の関連記事へのリンク: 3〜5個
- **外部リンクは含めない**（自己完結wiki）

### 5. テンプレート適用

プレースホルダーを置換:

| プレースホルダー | 内容 |
|---|---|
| `{{TITLE}}` | 記事タイトル |
| `{{WIKI_TITLE}}` | wiki名 |
| `{{LANG}}` | 言語コード（デフォルト "ja"） |
| `{{UPDATED_AT}}` | 現在日時 |
| `{{SUMMARY}}` | 1-2文の要約 |
| `{{CONTENT}}` | 本文HTML |
| `{{TOC}}` | H2/H3から自動生成する目次 |
| `{{RELATED_ARTICLES}}` | リンク先記事リスト |
| `{{LINKS_TO}}` | リンク先一覧 |
| `{{LINKED_FROM}}` | 被リンク一覧 |

### 6. TOC生成

H2, H3要素から目次を自動生成:
```html
<li><a href="#section-id">セクション名</a></li>
<li class="toc-h3"><a href="#subsection-id">サブセクション名</a></li>
```

### 7. ファイル書き出し

`wikis/{wiki-id}/articles/{slug}.html` に書き出す。

### 8. DB登録

```bash
uv run awiki article add --wiki {wiki-id} --slug {slug} --title "{title}" --filename "wikis/{wiki-id}/articles/{slug}.html" --summary "{summary}" --links-to "{link1},{link2}" --origin {origin} --source-id {source}
```

### 9. 結果報告

以下のJSON形式で結果を返す:
```json
{
  "wiki": "wiki-id",
  "slug": "article-slug",
  "title": "記事タイトル",
  "filename": "wikis/wiki-id/articles/slug.html",
  "summary": "要約テキスト",
  "links_to": ["existing-slug-1", "new-slug-1"],
  "origin": "root|expanded|requested",
  "source_id": "source-slug-or-null",
  "new_candidates": [
    {
      "proposed_slug": "candidate-slug",
      "proposed_title": "候補タイトル",
      "rationale": "なぜこの記事が面白いか",
      "interestingness_score": 0.85
    }
  ]
}
```

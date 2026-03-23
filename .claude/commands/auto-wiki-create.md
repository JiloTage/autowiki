---
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
description: "Auto-Wiki: Create a single article from a topic with template, links, and Mermaid diagrams"
---

# Auto-Wiki: 記事作成

単一のWikipedia風HTML記事を作成するskill。オーケストレータまたは他のskillから呼び出される。

## 入力

$ARGUMENTS は以下の形式:
```
[topic] --slug [slug] --origin [root|expanded|requested] --source [source-slug]
```

- `topic`: 記事トピック（必須）
- `--slug`: slug指定（省略時は自動生成）
- `--origin`: 作成起源（デフォルト: "root"）
- `--source`: 提案元記事slug（expanded/requestedの場合）

## 実行手順

### 1. 準備

1. プロジェクトルート: `/Users/toshihideyukitake/Project/autowiki/`
2. `db/articles.json` を読み込み、既存記事を把握
3. slugを決定:
   - 指定がある場合はそのまま使用
   - 日本語トピックはローマ字変換 → kebab-case
   - 英語トピックはkebab-case
4. 重複チェック: 同一slugが存在する場合はエラーを返す

### 2. テンプレート読み込み

`templates/article.html` テンプレートを読み込む。

### 3. コンテキスト把握

- `--source` がある場合: `articles/{source-slug}.html` を読み込んで文脈を理解
- 既存記事一覧から、関連性の高い記事を特定

### 4. 記事本文作成

以下の構造でHTML本文を作成:

- **冒頭段落**: トピックの定義。タイトルを `<b>` で強調
- **H2セクション**: 3〜6個。各セクションに `id` 属性を付与（例: `id="history"`）
- **H3サブセクション**: 必要に応じて
- **Mermaidダイアグラム**: 最低1つ。以下の形式:
  ```html
  <div class="mermaid-container"><pre class="mermaid">...</pre></div>
  ```
- **内部リンク**: `<a href="{slug}.html">{タイトル}</a>` 形式
  - 既存記事へのリンク: 積極的に相互リンク（フラット構造）
  - 未作成の関連記事へのリンク: 3〜5個（今後の拡張候補）
  - リンクは記事内の文脈に自然に組み込む
- **外部リンクは含めない**（自己完結wiki）

### 5. テンプレート適用

プレースホルダーを置換:

| プレースホルダー | 内容 |
|---|---|
| `{{TITLE}}` | 記事タイトル |
| `{{LANG}}` | 言語コード（デフォルト "ja"） |
| `{{UPDATED_AT}}` | 現在日時 |
| `{{SUMMARY}}` | 1-2文の要約 |
| `{{CONTENT}}` | 本文HTML |
| `{{TOC}}` | H2/H3から自動生成する目次 |
| `{{RELATED_ARTICLES}}` | リンク先記事リスト |
| `{{LINKS_TO}}` | リンク先一覧 |
| `{{LINKED_FROM}}` | 被リンク一覧（新規は空、requestedの場合は提案元） |

### 6. TOC生成

H2, H3要素から目次を自動生成:
```html
<li><a href="#section-id">セクション名</a></li>
<li class="toc-h3"><a href="#subsection-id">サブセクション名</a></li>
```

### 7. ファイル書き出し

`articles/{slug}.html` に書き出す。

### 8. 結果報告

以下のJSON形式で結果を返す:
```json
{
  "slug": "article-slug",
  "title": "記事タイトル",
  "filename": "articles/slug.html",
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

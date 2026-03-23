---
name: auto-wiki-layout
description: Change the Auto-Wiki page layout and template structure. Use when the user wants header, sidebar, footer, search, article list, responsive behavior, or other structural changes that affect templates, CSS, JS, and possibly existing articles.
---

# Auto-Wiki: レイアウト・テンプレート変更

wikiのレイアウト構造（ヘッダー、サイドバー、フッター、ナビゲーション、レスポンシブ設計）を変更するスキル。

## 入力

自然言語でレイアウト変更を指示:
- `サイドバーを左に移動して`
- `ヘッダーに検索バーを追加して`
- `フッターにタグクラウドを表示して`
- `サイドバーを削除してシンプルにして`
- `index.htmlにカード形式の記事一覧を追加して`
- `モバイルでサイドバーをアコーディオンにして`

## 対象ファイル

| ファイル | 責務 |
|---|---|
| `templates/article.html` | 記事ページのHTML構造 |
| `templates/index.html` | トップページのHTML構造 |
| `assets/css/wiki.css` | レイアウト関連CSS |
| `assets/js/graph.js` | グラフコンテナのサイズ・振る舞い |
| `assets/js/search.js` | 検索UIの配置変更時 |
| 既存の `articles/*.html` | テンプレート構造変更時の一括更新 |

## 実行手順

### 1. 現状把握

1. `templates/article.html` を読み込む → 現在の記事ページ構造を把握
2. `templates/index.html` を読み込む → 現在のトップページ構造を把握
3. `assets/css/wiki.css` を読み込む → レイアウト関連CSSを把握
4. 既存記事があれば `articles/` の件数を確認

### 2. 変更影響分析

| 変更種別 | 影響ファイル | 既存記事更新 |
|---|---|---|
| テンプレートHTML構造変更 | template + CSS | 必要（全記事） |
| CSSのみの変更 | CSSのみ | 不要 |
| JSの変更 | JS + 必要ならCSS | 不要 |
| プレースホルダーの追加 | template + 各skill | 必要（全記事） |

**既存記事の更新が必要な場合は、ユーザーに影響範囲を明示して確認を取る。**

### 3. テンプレート変更

#### 記事テンプレート（`templates/article.html`）の構造:

```
┌─────────────────────────────┐
│ wiki-header                  │ ← ヘッダー（サイトタイトル + ナビ）
├─────────────────────────────┤
│ breadcrumb                   │ ← パンくずリスト
├───────────────┬─────────────┤
│  wiki-main    │ wiki-sidebar│ ← メイン + サイドバー
│  - title      │  - TOC      │
│  - meta       │  - 関連記事 │
│  - summary    │             │
│  - content    │             │
├───────────────┴─────────────┤
│ wiki-footer                  │ ← フッター
└─────────────────────────────┘
```

#### トップページテンプレート（`templates/index.html`）の構造:

```
┌─────────────────────────────┐
│ wiki-header                  │
├─────────────────────────────┤
│ index-header                 │ ← タイトル + 説明
├─────────────────────────────┤
│ stats-bar                    │ ← 統計
├─────────────────────────────┤
│ search-container             │ ← 検索バー
├─────────────────────────────┤
│ graph-container              │ ← D3グラフ
├─────────────────────────────┤
│ article-list                 │ ← 記事一覧テーブル
├─────────────────────────────┤
│ wiki-footer                  │
└─────────────────────────────┘
```

### 4. レイアウトパターン

#### サイドバー位置
- **右サイドバー**（デフォルト）: `.wiki-content { flex-direction: row; }`
- **左サイドバー**: `.wiki-content { flex-direction: row-reverse; }` + ボーダー調整
- **サイドバーなし**: サイドバーをメイン下部に統合

#### ヘッダースタイル
- **シンプル**（デフォルト）: タイトル + ナビリンク
- **検索付き**: ヘッダーに検索バーを統合
- **固定ヘッダー**: `position: sticky; top: 0;`

#### 記事一覧形式（index.html）
- **テーブル形式**（デフォルト）
- **カード形式**: グリッドレイアウト
- **リスト形式**: コンパクト

### 5. 既存記事の一括更新

テンプレート構造が変わった場合:

1. `articles/` 内の全HTMLファイルを走査
2. 各記事から本文コンテンツとメタデータを抽出
3. 新しいテンプレートで再生成
4. `db/articles.json` のメタデータを保持

抽出対象:
- `<h1>` からタイトル
- `.article-meta` から更新日時
- `.article-summary` からサマリー
- `.wiki-main` の本文（H2以降）
- `.toc-list` からTOC
- `.footer-links` からリンク先/被リンク

### 6. レスポンシブ調整

レイアウト変更時は必ずレスポンシブ対応を確認:

- **768px以下**: サイドバー → コンテンツ下に配置
- **480px以下**: フォントサイズ・パディング調整
- グラフコンテナの高さ調整
- テーブルの横スクロール対応

### 7. 完了報告

- 変更したファイル一覧と変更内容
- 更新された既存記事数
- ブラウザで確認するよう案内

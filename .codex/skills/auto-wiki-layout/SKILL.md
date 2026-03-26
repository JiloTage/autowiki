---
name: auto-wiki-layout
description: Change the Auto-Wiki page layout and template structure. Use when the user wants header, sidebar, footer, search, article list, responsive behavior, or other structural changes that affect templates, CSS, JS, and possibly existing articles.
---

# Auto-Wiki: レイアウト・テンプレート変更 (Multi-Wiki)

wikiのレイアウト構造（ヘッダー、サイドバー、フッター、ナビゲーション、レスポンシブ設計）を変更するスキル。

## 入力

自然言語でレイアウト変更を指示:
- `サイドバーを左に移動して`
- `ヘッダーに検索バーを追加して`
- `モバイルでサイドバーをアコーディオンにして`

## 対象ファイル

| ファイル | 責務 |
|---|---|
| `templates/article.html` | 記事ページのHTML構造 |
| `templates/wiki-index.html` | wiki個別トップページのHTML構造 |
| `templates/portal.html` | 全wikiポータルのHTML構造 |
| `assets/css/wiki.css` | レイアウト関連CSS |
| `assets/js/graph.js` | グラフコンテナのサイズ・振る舞い |
| `assets/js/search.js` | 検索UIの配置変更時 |
| 既存の `wikis/*/articles/*.html` | テンプレート構造変更時の一括更新 |

## 実行手順

### 1. 現状把握

1. `templates/article.html` を読み込む
2. `templates/wiki-index.html` を読み込む
3. `templates/portal.html` を読み込む
4. `assets/css/wiki.css` を読み込む
5. 既存記事があれば `wikis/*/articles/` の件数を確認

### 2. 変更影響分析

| 変更種別 | 影響ファイル | 既存記事更新 |
|---|---|---|
| テンプレートHTML構造変更 | template + CSS | 必要（全記事） |
| CSSのみの変更 | CSSのみ | 不要 |
| JSの変更 | JS + 必要ならCSS | 不要 |

**既存記事の更新が必要な場合は、ユーザーに確認を取る。**

### 3. テンプレート変更

記事テンプレート（`templates/article.html`）の構造:
```
wiki-header → breadcrumb → wiki-main + wiki-sidebar → wiki-footer
```

### 4. 既存記事の一括更新

テンプレート構造が変わった場合:
1. `wikis/*/articles/` 内の全HTMLファイルを走査
2. 各記事から本文コンテンツとメタデータを抽出
3. 新しいテンプレートで再生成

### 5. レスポンシブ調整

- **768px以下**: サイドバー → コンテンツ下に配置
- **480px以下**: フォントサイズ・パディング調整

### 6. 完了報告

- 変更したファイル一覧
- 更新された既存記事数
- ブラウザで確認するよう案内

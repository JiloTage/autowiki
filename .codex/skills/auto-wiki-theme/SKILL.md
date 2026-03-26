---
name: auto-wiki-theme
description: Customize the Auto-Wiki visual theme. Use when the user wants color, font, dark mode, SVG diagram styling, or graph styling changes across assets/css/wiki.css, assets/js/graph.js, templates, and existing articles when required.
---

# Auto-Wiki: テーマカスタマイズ (Multi-Wiki)

wikiのビジュアルテーマ（カラースキーム、フォント、ダークモード、グラフスタイル等）を変更するスキル。

## 入力

自然言語でテーマ変更を指示:
- `ダークモードにして`
- `アクセントカラーを緑にして`
- `グラフのノードを大きくして`

## 対象ファイル

| ファイル | 変更内容 |
|---|---|
| `assets/css/wiki.css` | CSS変数、色、フォント、スペーシング |
| `assets/js/graph.js` | グラフのノード色・サイズ・リンク色 |
| `templates/wiki-index.html` | （テーマ依存の変更があれば） |
| `templates/portal.html` | （テーマ依存の変更があれば） |
| 既存の `wikis/*/articles/*.html` | SVGダイアグラムの色変更時に一括更新 |

## 実行手順

### 1. 現状把握

1. `assets/css/wiki.css` を読み込む（`:root` のCSS変数セクション）
2. `assets/js/graph.js` を読み込む（ノード・リンクのスタイル定数）
3. 既存記事があれば1件サンプルとして読み込み

### 2. 変更計画の提示

ユーザー確認を得てから実行する。

### 3. CSS変数の変更

`:root` セクションのCSS変数を更新。主な変数:

| 変数 | 用途 | デフォルト |
|---|---|---|
| `--bg-primary` | メイン背景 | `#fff` |
| `--bg-secondary` | サイドバー・フッター背景 | `#f8f9fa` |
| `--text-primary` | メインテキスト | `#202122` |
| `--link-color` | リンク色 | `#0645ad` |
| `--accent` | アクセントカラー | `#36c` |

### 4. グラフスタイルの変更

`assets/js/graph.js` のノード色・サイズ・リンク色等を更新。

### 5. インラインSVGダイアグラムのスタイル変更

1. `wikis/*/articles/` 内の全HTMLファイルを走査
2. SVG内の色属性を置換

### 6. プリセットテーマ

| キーワード | 説明 |
|---|---|
| `wikipedia` | デフォルト |
| `dark` | ダークモード |
| `sepia` | セピア調 |
| `minimal` | ミニマル |
| `ocean` | ブルー系 |
| `forest` | グリーン系 |

### 7. 完了報告

- 変更したファイル一覧
- 変更前後のCSS変数値
- 更新された記事数（SVG変更時）

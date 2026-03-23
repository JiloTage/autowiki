---
name: auto-wiki-theme
description: Customize the Auto-Wiki visual theme. Use when the user wants color, font, dark mode, SVG diagram styling, or graph styling changes across assets/css/wiki.css, assets/js/graph.js, templates, and existing articles when required.
---

# Auto-Wiki: テーマカスタマイズ

wikiのビジュアルテーマ（カラースキーム、フォント、ダークモード、グラフスタイル等）を変更するスキル。

## 入力

自然言語でテーマ変更を指示:
- `ダークモードにして`
- `アクセントカラーを緑にして`
- `モダンなサンセリフフォントに変えて`
- `グラフのノードを大きくして`
- `全体的にもっとコンパクトにして`
- `SVGダイアグラムの色を変えて`

## 対象ファイル

| ファイル | 変更内容 |
|---|---|
| `assets/css/wiki.css` | CSS変数、色、フォント、スペーシング、SVGダイアグラムスタイル |
| `assets/js/graph.js` | グラフのノード色・サイズ・リンク色 |
| `templates/index.html` | （テーマ依存の変更があれば） |
| 既存の `articles/*.html` | SVGダイアグラムの色変更時に一括更新 |

## 実行手順

### 1. 現状把握

1. `assets/css/wiki.css` を読み込む（特に `:root` のCSS変数セクション）
2. `assets/js/graph.js` を読み込む（ノード・リンクのスタイル定数）
3. 既存記事のインラインSVGダイアグラムのスタイルを確認
4. 既存記事があれば1件サンプルとして読み込み

### 2. 変更計画の提示

ユーザーの指示を解釈し、変更内容を一覧で提示:

```
変更計画:
- [wiki.css] --bg-primary: #fff → #1a1a2e
- [wiki.css] --text-primary: #202122 → #e0e0e0
- [graph.js] ノード色: #0645ad → #4cc9f0
- ...
```

**ユーザー確認を得てから実行する。**

### 3. CSS変数の変更

`:root` セクションのCSS変数を更新。変更可能な変数:

#### カラー変数
| 変数 | 用途 | デフォルト |
|---|---|---|
| `--bg-primary` | メイン背景 | `#fff` |
| `--bg-secondary` | サイドバー・フッター背景 | `#f8f9fa` |
| `--bg-tertiary` | テーブルヘッダー等 | `#eaecf0` |
| `--text-primary` | メインテキスト | `#202122` |
| `--text-secondary` | 補助テキスト | `#54595d` |
| `--text-muted` | 薄いテキスト | `#72777d` |
| `--link-color` | リンク色 | `#0645ad` |
| `--link-visited` | 訪問済みリンク | `#0b0080` |
| `--link-hover` | ホバー時リンク | `#3366cc` |
| `--link-red` | 未作成記事リンク | `#ba0000` |
| `--border-color` | ボーダー | `#a2a9b1` |
| `--border-light` | 薄いボーダー | `#c8ccd1` |
| `--accent` | アクセントカラー | `#36c` |

#### フォント変数
| 変数 | 用途 | デフォルト |
|---|---|---|
| `--font-serif` | 見出し | `'Linux Libertine', 'Georgia', 'Times', serif` |
| `--font-sans` | 本文 | `-apple-system, 'Segoe UI', 'Helvetica Neue', sans-serif` |
| `--font-mono` | コード | `'Menlo', 'Consolas', 'Liberation Mono', monospace` |

#### レイアウト変数
| 変数 | 用途 | デフォルト |
|---|---|---|
| `--max-width` | コンテンツ最大幅 | `960px` |
| `--sidebar-width` | サイドバー幅 | `220px` |

### 4. グラフスタイルの変更

`assets/js/graph.js` の以下の値を更新:

| 対象 | デフォルト |
|---|---|
| ルートノード色 | `#0645ad` |
| 通常ノード色 | `#36c` |
| ルートノードサイズ | `12` |
| 通常ノードサイズ | `8` |
| ノードストローク | `#fff` |
| リンク色 | `#c8ccd1` |
| 矢印色 | `#a2a9b1` |
| ラベルフォントサイズ | `11px` |
| ラベルテキスト色 | `#202122` |
| リンク距離 | `100` |
| 反発力 | `-300` |
| 衝突半径 | `30` |

### 5. インラインSVGダイアグラムのスタイル変更

ダイアグラムはインラインSVGで記述されている。テーマ変更時は既存記事のSVG内の色を一括更新:
1. `articles/` 内の全HTMLファイルを走査
2. SVG内の `fill`, `stroke`, `font-family` 等の属性値を置換
3. `.diagram-container` のCSS（`wiki.css`内）も更新

### 6. プリセットテーマ

| キーワード | 説明 |
|---|---|
| `wikipedia` | デフォルトのWikipedia風（初期値に戻す） |
| `dark` | ダークモード |
| `sepia` | セピア調（読書向き） |
| `minimal` | ミニマルモノクロ |
| `ocean` | ブルー系マリンテーマ |
| `forest` | グリーン系ナチュラルテーマ |

ダークモード推奨カラーパレット:
```css
--bg-primary: #1a1a2e;
--bg-secondary: #16213e;
--bg-tertiary: #0f3460;
--text-primary: #e0e0e0;
--text-secondary: #b0b0b0;
--text-muted: #808080;
--link-color: #4cc9f0;
--link-visited: #7b68ee;
--link-hover: #72efdd;
--border-color: #2a2a4a;
--border-light: #1e1e3e;
--accent: #4cc9f0;
```

### 7. 完了報告

- 変更したファイル一覧
- 変更前後のCSS変数値
- 更新された記事数（SVG変更時）
- ブラウザで確認するよう案内

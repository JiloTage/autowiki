---
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
description: "Auto-Wiki: Customize visual theme - colors, fonts, dark mode, spacing, and graph styling"
---

# Auto-Wiki: テーマカスタマイズ

wikiのビジュアルテーマ（カラースキーム、フォント、ダークモード、グラフスタイル等）を変更するskill。

## Usage

```
/auto-wiki-theme [指示]
```

指示の例:
- `ダークモードにして`
- `アクセントカラーを緑にして`
- `モダンなサンセリフフォントに変えて`
- `グラフのノードを大きくして`
- `全体的にもっとコンパクトにして`
- `Mermaidのテーマをdarkに変えて`

## 対象ファイル

| ファイル | 変更内容 |
|---|---|
| `assets/css/wiki.css` | CSS変数、色、フォント、スペーシング |
| `assets/js/graph.js` | グラフのノード色・サイズ・リンク色 |
| `templates/article.html` | Mermaidテーマ設定 |
| `templates/index.html` | （テーマ依存の変更があれば） |
| 既存の `articles/*.html` | Mermaidテーマ変更時のみ一括更新 |

## 実行手順

ユーザー入力: $ARGUMENTS

### 1. 現状把握

1. `assets/css/wiki.css` を読み込む（特に `:root` のCSS変数セクション）
2. `assets/js/graph.js` を読み込む（ノード・リンクのスタイル定数）
3. `templates/article.html` を読み込む（Mermaid設定）
4. 既存記事があれば1件サンプルとして読み込み、現在の見た目を把握

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

`:root` セクションのCSS変数を更新。変更可能な変数一覧:

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

| 対象 | 場所 | デフォルト |
|---|---|---|
| ルートノード色 | `node.append('circle') ... fill` | `#0645ad` |
| 通常ノード色 | 同上 | `#36c` |
| ルートノードサイズ | `attr('r', ...)` | `12` |
| 通常ノードサイズ | 同上 | `8` |
| ノードストローク | `attr('stroke', ...)` | `#fff` |
| リンク色 | `link ... stroke` | `#c8ccd1` |
| 矢印色 | `marker ... fill` | `#a2a9b1` |
| ラベルフォントサイズ | `attr('font-size', ...)` | `11px` |
| ラベルテキスト色 | `attr('fill', ...)` | `#202122` |
| リンク距離 | `forceLink().distance()` | `100` |
| 反発力 | `forceManyBody().strength()` | `-300` |
| 衝突半径 | `forceCollide().radius()` | `30` |

### 5. Mermaidテーマの変更

`templates/article.html` の `mermaid.initialize()` 内:
```javascript
mermaid.initialize({startOnLoad: true, theme: 'neutral'});
```

利用可能なテーマ: `default`, `neutral`, `dark`, `forest`, `base`

Mermaidテーマ変更時は既存の `articles/*.html` も一括更新:
1. `articles/` 内の全HTMLファイルを走査
2. `mermaid.initialize` の `theme` 値を置換

### 6. ダークモード対応

ダークモード要求時は以下を実施:

1. `:root` のカラー変数をダーク系に変更
2. グラフのノード・リンク色をダーク背景に合うように調整
3. Mermaidテーマを `'dark'` に変更
4. `body` の `background` を暗色に変更
5. ボーダー色をダーク系に変更
6. ツールチップ・検索結果等の背景も調整

推奨ダークカラーパレット:
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

### 7. プリセットテーマ

以下のキーワードで即座にテーマを適用可能:

| キーワード | 説明 |
|---|---|
| `wikipedia` | デフォルトのWikipedia風（初期値に戻す） |
| `dark` | ダークモード |
| `sepia` | セピア調（読書向き） |
| `minimal` | ミニマルモノクロ |
| `ocean` | ブルー系マリンテーマ |
| `forest` | グリーン系ナチュラルテーマ |

### 8. 既存記事への反映

CSSの変更は自動的に全記事に反映される（共通CSS読み込みのため）。
以下の場合のみ記事HTMLの更新が必要:
- Mermaidテーマ変更 → 全記事の `mermaid.initialize` を更新
- インラインスタイルの変更 → 該当箇所を一括置換

### 9. 完了報告

- 変更したファイル一覧
- 変更前後のCSS変数値
- 更新された記事数（Mermaid変更時）
- ブラウザで確認するよう案内

---
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
description: "Auto-Wiki: Rebuild the portal page with unified graph, wiki cards, and reaction log"
---

# Auto-Wiki: ポータル再生成

全wikiの統合ポータルページを再生成するskill。

## Usage

```
/auto-wiki-portal
```

## 実行手順

### 1. データ収集

以下のコマンドで全体状態を収集:

```bash
uv run awiki wiki list                # 全wiki一覧
uv run awiki reaction list            # 全反応一覧
uv run awiki portal rebuild           # cross-graph.json再構築
```

### 2. index.html 生成

`templates/portal.html` テンプレートを読み込み、プレースホルダーを置換:

| プレースホルダー | 内容 |
|---|---|
| `{{LANG}}` | 言語コード（デフォルト "ja"） |
| `{{WIKI_COUNT}}` | アクティブwiki数 |
| `{{TOTAL_ARTICLES}}` | 全wikiの総記事数 |
| `{{REACTION_COUNT}}` | 反応数 |
| `{{WIKI_CARDS}}` | wikiカード一覧 |
| `{{REACTION_LOG}}` | 反応ログ |

### 3. Wikiカード生成

各wikiについて以下のHTML形式で生成:

```html
<div class="wiki-card" style="border-left: 4px solid {color}">
  <h3><a href="wikis/{wiki-id}/index.html">{title}</a></h3>
  <p class="wiki-topic">{root_topic}</p>
  <div class="wiki-stats">
    <span>記事数: {article_count}</span>
    <span>ステータス: {status}</span>
  </div>
</div>
```

### 4. 反応ログ生成

各反応について以下のHTML形式で生成:

```html
<div class="reaction-entry">
  <span class="reaction-type reaction-{type}">{type}</span>
  <span class="reaction-reagents">
    <a href="wikis/{wiki-a}/articles/{slug-a}.html">{title-a}</a>
    <span class="reaction-arrow">+</span>
    <a href="wikis/{wiki-b}/articles/{slug-b}.html">{title-b}</a>
  </span>
  <span class="reaction-arrow">→</span>
  <a href="wikis/{product-wiki}/articles/{product-slug}.html" class="reaction-product">{product-title}</a>
  <div class="reaction-catalyst">{catalyst}</div>
</div>
```

反応がない場合: `<p>まだ化学反応は発生していません。/auto-wiki-react で反応を起こしましょう。</p>`

### 5. ファイル出力

`index.html`（プロジェクトルート）に書き出す。

### 6. CSS追加

`assets/css/wiki.css` に以下のスタイルが無ければ追加:

```css
/* Portal styles */
.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin: 16px 0; }
.wiki-card { background: var(--bg-secondary); border-radius: 4px; padding: 16px; }
.wiki-card h3 { margin: 0 0 8px; }
.wiki-topic { color: var(--text-secondary); margin: 0 0 8px; }
.wiki-stats { font-size: 0.9em; color: var(--text-muted); }
.reaction-log { margin: 16px 0; }
.reaction-entry { display: flex; align-items: center; gap: 8px; padding: 8px 0; border-bottom: 1px solid var(--border-light); flex-wrap: wrap; }
.reaction-type { font-size: 0.8em; padding: 2px 8px; border-radius: 3px; font-weight: bold; }
.reaction-bridge { background: #d4edda; color: #155724; }
.reaction-synthesis { background: #cce5ff; color: #004085; }
.reaction-debate { background: #f8d7da; color: #721c24; }
.reaction-analogy { background: #fff3cd; color: #856404; }
.reaction-arrow { color: var(--text-muted); }
.reaction-catalyst { font-size: 0.85em; color: var(--text-secondary); width: 100%; margin-top: 4px; }
```

### 7. 完了報告

- wiki数と総記事数
- 反応数
- ポータルのパス

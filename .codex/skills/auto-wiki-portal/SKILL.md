---
name: auto-wiki-portal
description: Rebuild the Auto-Wiki portal page with unified graph, wiki cards, cross-wiki search, and reaction log. Use after wiki changes or reactions to update the portal.
---

# Auto-Wiki: ポータル再生成

全wikiの統合ポータルページを再生成するスキル。

## Usage

```
auto-wiki-portal
```

## 実行手順

### 1. データ収集

```bash
uv run awiki wiki list                # 全wiki一覧
uv run awiki reaction list            # 全反応一覧
uv run awiki portal rebuild           # cross-graph.json再構築
```

### 2. portal.html 生成

`templates/portal.html` テンプレートのプレースホルダーを置換:

| プレースホルダー | 内容 |
|---|---|
| `{{LANG}}` | 言語コード |
| `{{WIKI_COUNT}}` | アクティブwiki数 |
| `{{TOTAL_ARTICLES}}` | 全wikiの総記事数 |
| `{{REACTION_COUNT}}` | 反応数 |
| `{{WIKI_CARDS}}` | wikiカード一覧HTML |
| `{{REACTION_LOG}}` | 反応ログHTML |

### 3. Wikiカード生成

```html
<div class="wiki-card" style="border-left: 4px solid {color}">
  <h3><a href="wikis/{wiki-id}/index.html">{title}</a></h3>
  <p class="wiki-topic">{root_topic}</p>
  <div class="wiki-stats">記事数: {article_count}</div>
</div>
```

### 4. 反応ログ生成

各反応をタイプ別に色分け表示（bridge/synthesis/debate/analogy）。

### 5. ファイル出力

`portal.html`（プロジェクトルート）に書き出す。

### 6. 完了報告

- wiki数と総記事数
- 反応数
- ポータルのパス

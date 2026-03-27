# Multi-Wiki Same-Repo Design

## Overview

同一リポジトリ内で複数のwikiを管理し、各wikiは独立して拡張しつつ、明示的な操作でwiki間の「化学反応」を起こす。

## Design Decisions

| 項目 | 決定 |
|------|------|
| 後方互換 | 不要。`wikis/{id}/` がデフォルト構造 |
| 反応トリガー | 明示的（`/auto-wiki-react`） |
| 反応記事の所属 | どちらかのwikiに帰属 |
| wiki間リンク | 通常リンクと同じ扱い |
| ポータルグラフ | 全ノード表示（wiki別色分け） |

## Directory Structure

```
autowiki/
├── wikis/
│   └── {wiki-id}/
│       ├── articles/
│       ├── db/
│       │   ├── articles.json
│       │   ├── brainstorm.json
│       │   ├── graph.json
│       │   └── session.json
│       └── index.html
│
├── db/
│   ├── registry.json        # wiki一覧
│   └── reactions.json       # 反応レジストリ
│
├── assets/                  # 共有アセット
│   ├── css/wiki.css
│   └── js/
│       ├── graph.js
│       └── search.js
│
├── templates/               # 共有テンプレート
│   ├── article.html
│   ├── wiki-index.html      # 個別wikiトップ
│   └── portal.html          # 全wiki統合ポータル
│
├── tools/
│   ├── db.py
│   └── cli.py
│
└── index.html               # 生成済みポータル
```

## Data Models

### `db/registry.json` — Wiki Registry

```json
{
  "wikis": {
    "quantum-physics": {
      "id": "quantum-physics",
      "title": "量子物理学",
      "root_topic": "量子力学",
      "created_at": "2026-03-26T00:00:00+00:00",
      "article_count": 12,
      "color": "#0645ad",
      "status": "active"
    }
  }
}
```

### `db/reactions.json` — Reaction Registry

```json
{
  "reactions": [
    {
      "id": "r-001",
      "type": "bridge",
      "reagents": [
        {"wiki": "quantum-physics", "article": "measurement-problem"},
        {"wiki": "philosophy-of-mind", "article": "hard-problem"}
      ],
      "product": {
        "wiki": "philosophy-of-mind",
        "slug": "quantum-consciousness-bridge",
        "title": "量子測定と意識のハードプロブレム"
      },
      "catalyst": "概念的重複: 観測者問題",
      "affinity_score": 0.82,
      "created_at": "2026-03-26T00:00:00+00:00"
    }
  ],
  "pending_affinities": [
    {
      "wiki_a": "quantum-physics",
      "article_a": "decoherence",
      "wiki_b": "philosophy-of-mind",
      "article_b": "emergence",
      "affinity_score": 0.71,
      "suggested_type": "analogy",
      "rationale": "量子デコヒーレンスと意識の創発は情報統合の観点で類似"
    }
  ]
}
```

### Wiki-local DB files

Each wiki has its own `db/` with the same schema as the current single-wiki design:
- `articles.json` — same schema, but `filename` becomes `wikis/{wiki-id}/articles/{slug}.html`
- `brainstorm.json` — same schema
- `graph.json` — same schema, but node `url` includes wiki prefix
- `session.json` — same schema

### Cross-wiki Article References

DB内のリンク表現:
- **同一wiki内**: `"slug"` (従来通り)
- **他wiki**: `"{wiki-id}:{slug}"` (コロン区切り)

HTML内のリンク:
- **同一wiki内**: `href="{slug}.html"` (従来通り)
- **他wiki**: `href="../../{wiki-id}/articles/{slug}.html"` (articlesディレクトリ基準の相対パス)

## Reaction Types

| Type | Description | Example |
|------|-------------|---------|
| `bridge` | 2つの概念を接続 | 量子測定↔意識のハードプロブレム |
| `synthesis` | 2分野を統合した新概念 | 自然選択+市場競争→進化経済学 |
| `debate` | 対立する見解を整理 | 自由意志⇔決定論 |
| `analogy` | 構造的類似性を論じる | トポロジー≈音韻変化 |

## Reaction Flow

```
/auto-wiki-react [--wikis A,B]
    │
    ├─ 1. 全wiki（or指定wiki）の記事サマリ収集
    │     uv run awiki article list --wiki A
    │     uv run awiki article list --wiki B
    │
    ├─ 2. 親和性スキャン
    │     - タイトル・サマリの意味的近接
    │     - 共通キーワード検出
    │     - LLMによるペア評価 → affinity_score
    │
    ├─ 3. pending_affinities に追加
    │     uv run awiki reaction add-affinity ...
    │
    ├─ 4. ユーザーに候補提示 → 承認
    │
    ├─ 5. 反応記事生成
    │     - 帰属先wikiを決定
    │     - /auto-wiki-create --wiki {wiki} --reaction-type {type}
    │     - 双方のwiki記事にクロスリンク挿入
    │
    └─ 6. 反応登録 + 統合グラフ更新
          uv run awiki reaction create ...
          uv run awiki portal rebuild
```

## CLI Extensions

```bash
# Wiki management
uv run awiki wiki create --id ID --title T --root-topic TOPIC [--color C]
uv run awiki wiki list
uv run awiki wiki get {wiki-id}
uv run awiki wiki delete {wiki-id}    # soft-delete (status: archived)

# All existing commands gain --wiki flag
uv run awiki article list --wiki quantum-physics
uv run awiki article add --wiki quantum-physics --slug S --title T ...
uv run awiki brainstorm pop --wiki quantum-physics --n 3
uv run awiki sync --wiki quantum-physics
uv run awiki session get --wiki quantum-physics

# Reaction commands
uv run awiki reaction scan [--wikis A,B]
uv run awiki reaction list
uv run awiki reaction add-affinity --wiki-a A --article-a SA --wiki-b B --article-b SB --score 0.8 --type bridge --rationale R
uv run awiki reaction create --id ID --type TYPE --reagent-a A:slug --reagent-b B:slug --product-wiki W --product-slug S --product-title T --catalyst C --score 0.8
uv run awiki reaction get {id}

# Portal
uv run awiki portal rebuild    # index.html + cross-graph
```

## Skill Commands

| Command | Description |
|---------|-------------|
| `/auto-wiki [topic] --wiki ID` | Create/expand a specific wiki |
| `/auto-wiki-create [topic] --wiki ID` | Create article in a wiki |
| `/auto-wiki-expand --wiki ID` | Expand a specific wiki |
| `/auto-wiki-sync --wiki ID` | Sync a specific wiki |
| `/auto-wiki-react [--wikis A,B]` | **NEW**: Scan for affinities, create reaction articles |
| `/auto-wiki-portal` | **NEW**: Rebuild portal page |

## Portal (index.html)

- 全wikiカード一覧（色分け、記事数、最終更新）
- 統合グラフ: 全wikiの全ノード表示、wiki別色分け、反応リンクは太線
- 横断検索: 全wikiの articles.json を統合してクライアントサイド検索
- 反応ログ: 最近の化学反応一覧

## Graph Visualization

### Wiki-local graph (wiki index page)
- 従来通り、そのwiki内のノードとリンクのみ
- 他wikiへのクロスリンクは点線で表示、ノードは半透明

### Portal unified graph
- 全wikiの全ノードを表示
- ノード色はwikiの `color` で着色
- 通常リンクは細線、反応リンクは太い赤線
- wiki名ラベルをクラスタ中心に表示
- クリックで記事ページへ遷移

### `cross-graph.json` schema
```json
{
  "nodes": [
    {
      "id": "quantum-physics:measurement-problem",
      "wiki": "quantum-physics",
      "title": "測定問題",
      "url": "wikis/quantum-physics/articles/measurement-problem.html",
      "color": "#0645ad",
      "is_root": true
    }
  ],
  "links": [
    {
      "source": "quantum-physics:measurement-problem",
      "target": "quantum-physics:wave-function",
      "type": "internal"
    },
    {
      "source": "quantum-physics:measurement-problem",
      "target": "philosophy-of-mind:hard-problem",
      "type": "reaction",
      "reaction_id": "r-001"
    }
  ]
}
```

## Path Resolution

| Context | Same wiki | Cross-wiki |
|---------|-----------|------------|
| DB `links_to` | `"slug"` | `"wiki-id:slug"` |
| Article HTML | `href="{slug}.html"` | `href="../../{wiki-id}/articles/{slug}.html"` |
| Wiki index | `href="articles/{slug}.html"` | `href="../{wiki-id}/articles/{slug}.html"` |
| Portal | `href="wikis/{wiki-id}/articles/{slug}.html"` | same |
| graph.json node url | `articles/{slug}.html` | (local graph only) |
| cross-graph.json url | `wikis/{wiki-id}/articles/{slug}.html` | same |

## Migration

No migration needed. The system starts fresh with `wikis/` structure.
Old flat-structure repos are not supported.

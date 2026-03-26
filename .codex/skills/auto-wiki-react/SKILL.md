---
name: auto-wiki-react
description: Scan for conceptual affinities between wikis and create cross-wiki reaction articles (bridge, synthesis, debate, analogy). Use when the user wants to trigger "chemical reactions" between multiple wikis.
---

# Auto-Wiki: 化学反応 (Cross-Wiki Reaction)

複数のwiki間で概念的親和性をスキャンし、ブリッジ記事・合成記事を生成するスキル。

## Usage

```
auto-wiki-react                    # 全wiki間をスキャン
auto-wiki-react --wikis A,B        # 特定wiki間のみ
```

## 反応タイプ

| Type | 説明 | 例 |
|------|------|---|
| `bridge` | 2つの概念を接続 | 量子測定 ↔ 意識のハードプロブレム |
| `synthesis` | 2分野を統合した新概念 | 自然選択 + 市場競争 → 進化経済学 |
| `debate` | 対立する見解を整理 | 自由意志 ⇔ 決定論 |
| `analogy` | 構造的類似性を論じる | トポロジー ≈ 音韻変化 |

## 実行手順

### 1. wiki一覧取得

```bash
uv run awiki wiki list
```

`--wikis A,B` 指定があればそのペアのみ対象。

### 2. 記事サマリ収集

対象wikiそれぞれについて:
```bash
uv run awiki article list --wiki {wiki-id}
```

### 3. 親和性スキャン

wiki間の記事ペアについて親和性を評価（0.0〜1.0）。0.6以上を候補とする。

### 4. 候補提示

親和性スコアが高い順にペアを提示し、ユーザーに選択を促す。

### 5. 反応記事生成

1. 帰属先wikiを決定
2. 両方の元記事を読み込む
3. 反応タイプに応じた記事を作成
4. DB登録:
   ```bash
   uv run awiki article add --wiki {product-wiki} --slug {slug} --title "{title}" --filename "wikis/{product-wiki}/articles/{slug}.html" --summary "{summary}" --links-to "{links}" --origin expanded
   ```
5. 元記事にクロスリンク追加
6. 反応登録:
   ```bash
   uv run awiki reaction create --type {type} --reagent-a {wiki-a}:{slug-a} --reagent-b {wiki-b}:{slug-b} --product-wiki {product-wiki} --product-slug {slug} --product-title "{title}" --catalyst "{理由}" --score {score}
   ```

### 6. 統合グラフ・ポータル更新

```bash
uv run awiki graph rebuild --wiki {product-wiki}
uv run awiki portal rebuild
```

### 7. 完了報告

- 生成された反応記事一覧
- 各反応のタイプと帰属先wiki
- クロスリンクが追加された記事

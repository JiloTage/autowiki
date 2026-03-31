---
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - WebSearch
  - WebFetch
  - Agent
  - Skill
description: "Auto-Wiki: Cross-wiki reaction - scan for affinities between wikis and create bridge/synthesis articles"
---

# Auto-Wiki: 化学反応 (Cross-Wiki Reaction)

複数のwiki間で概念的親和性をスキャンし、ブリッジ記事・合成記事を生成するskill。

## Usage

```
/auto-wiki-react                    # 全wiki間をスキャン
/auto-wiki-react --wikis A,B        # 特定wiki間のみ
```

## 反応タイプ

| Type | 説明 | 例 |
|------|------|---|
| `bridge` | 2つの概念を接続する解説 | 量子測定↔意識のハードプロブレム |
| `synthesis` | 2分野を統合した新概念 | 自然選択+市場競争→進化経済学 |
| `debate` | 対立する見解を整理 | 自由意志⇔決定論 |
| `analogy` | 構造的類似性を論じる | トポロジー≈音韻変化 |

## 実行手順

ユーザー入力: $ARGUMENTS

### 1. wiki一覧取得

```bash
uv run awiki wiki list
```

`--wikis A,B` 指定があればそのwikiペアのみ対象。指定がなければ全activeなwikiの全組み合わせを対象。

### 2. 記事サマリ収集

対象wikiそれぞれについて:
```bash
uv run awiki article list --wiki {wiki-id}
```

各記事の `title` と `summary` を収集する。

### 3. 親和性スキャン

wiki間の全記事ペアについて、以下の観点で親和性を評価:

- **概念的重複**: タイトル・サマリの意味的近接
- **用語共有**: 同一キーワードの出現
- **構造的類似**: 似た問題構造・フレームワーク
- **対立・補完**: 反対の立場や補完的な知見

各ペアに `affinity_score` (0.0〜1.0) を付与。0.6以上を候補とする。

### 4. 候補提示

親和性スコアが高い順にペアを提示:

```
検出された親和性:

1. [0.85] quantum-physics:measurement-problem ↔ philosophy-of-mind:hard-problem
   推奨タイプ: bridge
   理由: 観測者の役割が両分野で中心的な問題

2. [0.72] biology:natural-selection ↔ economics:market-competition
   推奨タイプ: synthesis
   理由: 適応と最適化の類似メカニズム

どのペアで反応を起こしますか？（番号で選択、または 'all' で全件）
```

### 5. 反応記事生成

ユーザーが選択したペアについて:

1. **帰属先wiki決定**: より関連度の高い方、または記事数の少ない方に配置
2. **両方の元記事を読み込む**:
   ```
   wikis/{wiki-a}/articles/{slug-a}.html
   wikis/{wiki-b}/articles/{slug-b}.html
   ```
3. **反応記事を作成**: `/auto-wiki-create` と同じ手順で記事生成
   - 反応タイプに応じた構成:
     - bridge: 両概念の解説→接点の分析→統合的視座
     - synthesis: 各分野の知見→統合フレームワーク→新たな洞察
     - debate: 各立場の整理→対立点の分析→メタ的考察
     - analogy: 各構造の説明→対応関係の分析→類推の限界と価値
   - 両wikiの元記事へのクロスリンクを含む
   - 同一wikiリンク: `<a href="{slug}.html">`
   - 他wikiリンク: `<a href="../../{other-wiki}/articles/{slug}.html">`

4. **DB登録**:
   ```bash
   uv run awiki article add --wiki {product-wiki} --slug {slug} --title "{title}" --filename "wikis/{product-wiki}/articles/{slug}.html" --summary "{summary}" --links-to "{local-links},{wiki-b:slug-b}" --origin expanded --source-id {source}
   ```

5. **元記事にクロスリンク追加**:
   - 帰属先wikiの元記事: 通常リンクを追加
   - 他wikiの元記事: クロスリンクを `links_to` に追加（`{product-wiki}:{product-slug}` 形式）
   - 元記事HTMLにもリンクを挿入

6. **反応登録**:
   ```bash
   uv run awiki reaction create --type {type} --reagent-a {wiki-a}:{slug-a} --reagent-b {wiki-b}:{slug-b} --product-wiki {product-wiki} --product-slug {product-slug} --product-title "{title}" --catalyst "{理由}" --score {affinity_score}
   ```

### 6. 統合グラフ・ポータル更新

```bash
uv run awiki graph rebuild --wiki {product-wiki}
uv run awiki portal rebuild
```

wiki index.html とルートの index.html（ポータル）を再生成。

### 7. 反応チェックポイント記録

反応完了後、次回の自動発火判定のためにチェックポイントを記録:
```bash
uv run awiki reaction mark-reacted
```

### 8. ポータル更新

`/auto-wiki-portal` skillを呼び出して、統合ポータルページを再生成する。

### 9. 完了報告

- 生成された反応記事一覧
- 各反応のタイプと帰属先wiki
- クロスリンクが追加された記事
- 統合グラフの更新状況
- ポータル更新完了

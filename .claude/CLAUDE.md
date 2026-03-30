# Auto-Wiki Project

同一リポジトリ内で複数の自己増殖wikiを管理し、wiki間の化学反応を起こすClaude Code Skillプロジェクト。

## プロジェクト構造

- `wikis/{wiki-id}/` - 各wiki独立空間
  - `articles/` - 生成されたHTML記事
  - `db/` - wiki固有JSONデータベース（articles.json, brainstorm.json, graph.json, session.json）
  - `index.html` - wiki個別トップページ
- `db/` - グローバルデータベース
  - `registry.json` - wiki一覧
  - `reactions.json` - wiki間反応レジストリ
  - `cross-graph.json` - 全wiki統合グラフ
- `assets/css/wiki.css` - Wikipedia風テーマ（共有）
- `assets/js/graph.js` - D3.js力指向グラフ（wiki個別＋ポータル統合対応）
- `assets/js/search.js` - クライアントサイド検索（wiki個別＋ポータル横断対応）
- `templates/` - HTML テンプレート（共有）
  - `article.html` - 記事ページ
  - `wiki-index.html` - wiki個別トップ
  - `portal.html` - 全wiki統合ポータルテンプレート
- `tools/` - Python CLIツール（uv管理）
  - `tools/db.py` - JSON DB操作ライブラリ
  - `tools/cli.py` - CLIエントリポイント（`awiki` コマンド）
- `index.html` - 全wiki統合ポータル（`/auto-wiki-sync` で毎回再生成）
- `docs/multi-wiki-design.md` - 設計ドキュメント
- `.claude/commands/` - Skillコマンド
  - `auto-wiki.md` - オーケストレータ（メインエントリポイント）
  - `auto-wiki-create.md` - 記事作成skill
  - `auto-wiki-expand.md` - 拡張オーケストレーションskill
  - `auto-wiki-feedback.md` - フィードバック適用skill
  - `auto-wiki-request.md` - 新規記事リクエストskill
  - `auto-wiki-sync.md` - DB同期・再生成skill
  - `auto-wiki-react.md` - wiki間化学反応skill
  - `auto-wiki-portal.md` - ポータル再生成skill
  - `auto-wiki-theme.md` - テーマカスタマイズskill
  - `auto-wiki-layout.md` - レイアウト変更skill

## JSON DB操作 CLI (`awiki`)

**JSONデータベースの操作はPython CLIツール経由で行う。** JSONファイルを直接Read/Write/Editしない。

```bash
# Wiki管理
uv run awiki wiki create --id ID --title T --root-topic TOPIC [--color C]
uv run awiki wiki list
uv run awiki wiki get {wiki-id}
uv run awiki wiki delete {wiki-id}

# 記事操作（--wiki 必須）
uv run awiki article list --wiki W
uv run awiki article get --wiki W {slug}
uv run awiki article exists --wiki W {slug}
uv run awiki article add --wiki W --slug S --title T --filename F --summary S [--links-to L1,L2] [--origin O] [--source-id ID]
uv run awiki article update --wiki W {slug} [--title T] [--summary S] [--expansion-status S] [--links-to L1,L2]
uv run awiki article set-links --wiki W {slug} --links L1,L2
uv run awiki article rebuild-linked-from --wiki W

# グラフ
uv run awiki graph rebuild --wiki W

# ブレスト
uv run awiki brainstorm list --wiki W
uv run awiki brainstorm add --wiki W --slug S --title T --source-id ID --rationale R --score 0.8
uv run awiki brainstorm add-batch --wiki W --json '[...]'
uv run awiki brainstorm pop --wiki W [--n N] [--min-score 0.5]
uv run awiki brainstorm cleanup --wiki W [--max-history 100]

# セッション
uv run awiki session get --wiki W
uv run awiki session update --wiki W --phase P [--setting key=value ...]
uv run awiki session frontier-add --wiki W {slug}
uv run awiki session frontier-remove --wiki W {slug}

# 一括同期
uv run awiki sync --wiki W

# 反応（wiki間）
uv run awiki reaction add-affinity --wiki-a A --article-a SA --wiki-b B --article-b SB --score 0.8 --type TYPE --rationale R
uv run awiki reaction create --type TYPE --reagent-a A:slug --reagent-b B:slug --product-wiki W --product-slug S --product-title T --catalyst C --score 0.8
uv run awiki reaction should-react [--threshold N]
uv run awiki reaction mark-reacted
uv run awiki reaction list
uv run awiki reaction get {id}

# ポータル
uv run awiki portal rebuild
```

全コマンドはJSON形式で結果を出力する。

## クロスwikiリンク表現

- DB内: 同一wiki `"slug"` / 他wiki `"wiki-id:slug"`
- HTML: 同一wiki `href="{slug}.html"` / 他wiki `href="../../{wiki-id}/articles/{slug}.html"`

## 運用ルール

1. 記事は必ず `templates/article.html` テンプレートベースで生成する
2. 記事作成・修正時は必ず `uv run awiki` コマンドでDB更新する（JSONファイル直接編集禁止）
3. リンク整合性を常に維持する（`article set-links` が `linked_from` を自動同期）
4. サブエージェントは `max_agents` 上限を超えない
5. `uv run awiki session update --wiki W` でセッション状態を永続化する
6. wiki間の化学反応は `/auto-wiki-react` で明示的に実行する
7. 反応記事はどちらかのwikiに帰属させる（独立した反応記事ディレクトリは無い）

## Wiki ID自動解決

CLIの `--wiki` は省略可能:
- **wikiが1つだけ**: 自動選択（stderrに `auto_selected_wiki` を出力）
- **wikiが0個**: エラー（作成を促す）
- **wikiが複数**: エラー（ID一覧を表示）

オーケストレータ（`/auto-wiki`）では:
- **新規作成時**: トピックからIDを自動生成（`--wiki` 省略可）
- **既存操作時**: wikiが1つなら自動選択、複数なら選択を促す

## 現在の状態

- マルチwiki対応済み（wiki未作成）
- `/auto-wiki [トピック]` でwikiを作成してください（IDは自動生成）
- 複数wiki作成後、`/auto-wiki-react` でwiki間の化学反応を起こせます

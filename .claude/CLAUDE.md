# Auto-Wiki Project

自己増殖するwikiを生成するClaude Code Skillプロジェクト。

## プロジェクト構造

- `articles/` - 生成されたHTML記事
- `assets/css/wiki.css` - Wikipedia風テーマ
- `assets/js/graph.js` - D3.js力指向グラフ
- `assets/js/search.js` - クライアントサイド検索
- `templates/` - HTML テンプレート
- `db/` - JSONデータベース（articles.json, brainstorm.json, graph.json, session.json）
- `tools/` - Python CLIツール（uv管理）
  - `tools/db.py` - JSON DB操作ライブラリ
  - `tools/cli.py` - CLIエントリポイント（`awiki` コマンド）
- `.claude/commands/auto-wiki.md` - オーケストレータ（メインエントリポイント）
- `.claude/commands/auto-wiki-create.md` - 記事作成skill
- `.claude/commands/auto-wiki-expand.md` - 拡張オーケストレーションskill
- `.claude/commands/auto-wiki-feedback.md` - フィードバック適用skill
- `.claude/commands/auto-wiki-request.md` - 新規記事リクエストskill
- `.claude/commands/auto-wiki-sync.md` - DB同期・再生成skill
- `.claude/commands/auto-wiki-theme.md` - テーマカスタマイズskill（カラー・フォント・ダークモード）
- `.claude/commands/auto-wiki-layout.md` - レイアウト・テンプレート変更skill

## JSON DB操作 CLI (`awiki`)

**JSONデータベースの操作はPython CLIツール経由で行う。** JSONファイルを直接Read/Write/Editしない。

```bash
# 記事操作
uv run awiki article list                    # 全記事一覧
uv run awiki article get {slug}              # 記事取得
uv run awiki article exists {slug}           # 存在チェック（終了コード0=存在）
uv run awiki article add --slug S --title T --filename F --summary S [--links-to L1,L2] [--origin O] [--source-id ID]
uv run awiki article update {slug} [--title T] [--summary S] [--expansion-status S] [--links-to L1,L2]
uv run awiki article set-links {slug} --links L1,L2  # links_to更新＋linked_from自動同期
uv run awiki article rebuild-linked-from     # 全linked_from再構築

# グラフ
uv run awiki graph rebuild                   # graph.json再生成

# ブレスト
uv run awiki brainstorm list                 # キュー一覧
uv run awiki brainstorm add --slug S --title T --source-id ID --rationale R --score 0.8
uv run awiki brainstorm add-batch --json '[...]'  # バッチ追加
uv run awiki brainstorm pop [--n N] [--min-score 0.5]  # 上位N件取得→history移動
uv run awiki brainstorm cleanup [--max-history 100]

# セッション
uv run awiki session get                     # セッション状態取得
uv run awiki session update --phase P [--setting key=value ...]
uv run awiki session frontier-add {slug}
uv run awiki session frontier-remove {slug}

# 一括同期
uv run awiki sync                            # 整合性チェック＋再構築＋クリーンアップ
```

全コマンドはJSON形式で結果を出力する。

## 運用ルール

1. 記事は必ず `templates/article.html` テンプレートベースで生成する
2. 記事作成・修正時は必ず `uv run awiki` コマンドでDB更新する（JSONファイル直接編集禁止）
3. リンク整合性を常に維持する（`article set-links` が `linked_from` を自動同期）
4. サブエージェントは `max_agents` 上限を超えない
5. `uv run awiki session update` でセッション状態を永続化する

## 現在の状態

- Wiki未初期化（記事なし）
- `/auto-wiki [トピック]` でルート記事を作成してください

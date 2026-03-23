# Auto-Wiki Project

自己増殖するwikiを生成するClaude Code Skillプロジェクト。

## プロジェクト構造

- `articles/` - 生成されたHTML記事
- `assets/css/wiki.css` - Wikipedia風テーマ
- `assets/js/graph.js` - D3.js力指向グラフ
- `assets/js/search.js` - クライアントサイド検索
- `templates/` - HTML テンプレート
- `db/` - JSONデータベース（articles.json, brainstorm.json, graph.json, session.json）
- `.claude/commands/auto-wiki.md` - オーケストレータ（メインエントリポイント）
- `.claude/commands/auto-wiki-create.md` - 記事作成skill
- `.claude/commands/auto-wiki-expand.md` - 拡張オーケストレーションskill
- `.claude/commands/auto-wiki-feedback.md` - フィードバック適用skill
- `.claude/commands/auto-wiki-request.md` - 新規記事リクエストskill
- `.claude/commands/auto-wiki-sync.md` - DB同期・再生成skill
- `.claude/commands/auto-wiki-theme.md` - テーマカスタマイズskill（カラー・フォント・ダークモード）
- `.claude/commands/auto-wiki-layout.md` - レイアウト・テンプレート変更skill

## 運用ルール

1. 記事は必ず `templates/article.html` テンプレートベースで生成する
2. 記事作成・修正時は必ず `db/articles.json`, `db/graph.json`, `index.html` を同期更新する
3. リンク整合性を常に維持する（`links_to` と `linked_from` の双方向同期）
4. サブエージェントは `max_agents` 上限を超えない
5. `db/session.json` でセッション状態を永続化する

## 現在の状態

- Wiki未初期化（記事なし）
- `/auto-wiki [トピック]` でルート記事を作成してください

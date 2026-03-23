# Auto-Wiki Project

自己増殖するwikiを生成するプロジェクト。

## プロジェクト構造

- `articles/` - 生成されたHTML記事
- `assets/css/wiki.css` - Wikipedia風テーマ
- `assets/js/graph.js` - D3.js力指向グラフ
- `assets/js/search.js` - クライアントサイド検索
- `templates/` - HTML テンプレート（article.html, index.html）
- `db/` - JSONデータベース（articles.json, brainstorm.json, graph.json, session.json）
- `.codex/skills/` - Codex CLI用スキル定義

## 運用ルール

1. 記事は必ず `templates/article.html` テンプレートベースで生成する
2. 記事作成・修正時は必ず `db/articles.json`, `db/graph.json`, `index.html` を同期更新する
3. リンク整合性を常に維持する（`links_to` と `linked_from` の双方向同期）
4. サブエージェントは `max_agents` 上限を超えない
5. `db/session.json` でセッション状態を永続化する

## スキル一覧

| スキル | 責務 |
|---|---|
| `auto-wiki` | オーケストレータ（引数解析・Phase判定・skill呼び出し） |
| `auto-wiki-create` | 単一記事の生成 |
| `auto-wiki-expand` | 拡張オーケストレーション（ブレスト・並列記事生成） |
| `auto-wiki-feedback` | 既存記事へのフィードバック適用 |
| `auto-wiki-request` | 新規記事リクエスト |
| `auto-wiki-sync` | DB同期・グラフ再構築・index再生成 |
| `auto-wiki-theme` | テーマカスタマイズ（カラー・フォント・ダークモード） |
| `auto-wiki-layout` | レイアウト・テンプレート構造変更 |

## 現在の状態

- Wiki未初期化（記事なし）
- `auto-wiki` スキルでルート記事を作成してください

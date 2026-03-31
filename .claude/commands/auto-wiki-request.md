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
description: "Auto-Wiki: Handle user requests for new articles with automatic cross-linking to existing articles"
---

# Auto-Wiki: 新規記事リクエスト (Multi-Wiki)

ユーザーが指定した新トピックの記事を特定wiki内に作成し、既存記事と相互リンクするskill。

## 入力

$ARGUMENTS:
```
--wiki WIKI_ID "新トピック名"
```

## 実行手順

### 1. コンテキスト把握

1. `uv run awiki article list --wiki {wiki-id}` で全既存記事を取得
2. `uv run awiki wiki get {wiki-id}` でwiki情報を取得
3. 新トピックからslugを生成
4. 重複チェック: `uv run awiki article exists --wiki {wiki-id} {slug}`

### 2. 関連記事分析

1. 新トピックと関連性が高い既存記事をリストアップ（最大5件）
2. 接続候補をユーザーに提示

### 3. 記事作成

1. `templates/article.html` テンプレートを読み込む
2. 記事本文を作成（SVGダイアグラム含む）
3. プレースホルダーを置換（`{{WIKI_TITLE}}` 含む）
4. `wikis/{wiki-id}/articles/{slug}.html` に書き出す

### 4. 既存記事への逆リンク追加

関連性の高い既存記事に対して:
1. `wikis/{wiki-id}/articles/{existing-slug}.html` を修正
2. `uv run awiki article set-links --wiki {wiki-id} {existing-slug} --links "..."` でリンク更新

### 5. DB更新

```bash
uv run awiki article add --wiki {wiki-id} --slug {slug} --title "{title}" --filename "wikis/{wiki-id}/articles/{slug}.html" --summary "{summary}" --links-to "{links}" --origin requested
uv run awiki brainstorm add-batch --wiki {wiki-id} --json '[...]'
uv run awiki graph rebuild --wiki {wiki-id}
```

wiki index.html を再生成（出力先: `wikis/{wiki-id}/index.html`）

### 6. 完了報告

- 新記事のタイトルとslug
- 相互リンクされた既存記事一覧
- 新たに追加された拡張候補

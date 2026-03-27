# Auto-Wiki

同一リポジトリ内で**複数の自己増殖wiki**を管理し、wiki間の**化学反応**を起こす Claude Code Skill。

## 特徴

- **マルチwiki**: 1リポジトリで複数の独立したwikiを運用
- **自己増殖**: 記事から派生トピックを自動でブレスト・生成
- **化学反応**: wiki間の概念的重なりを検出し、ブリッジ・合成記事を生成
- **統合ポータル**: 全wikiを俯瞰する統合グラフと横断検索
- **Wikipedia風HTML**: インラインSVGダイアグラム、D3.jsサイトグラフ
- **セッション永続化**: 中断しても次回セッションで続行可能
- **GitHub Pages対応**: pushするだけで公開

## セットアップ

### 前提条件

- [Claude Code](https://claude.ai/claude-code) がインストール済みであること
- Python 3.11+ / [uv](https://github.com/astral-sh/uv)

### 手順

1. リポジトリをクローン:
   ```bash
   git clone https://github.com/YOUR_USERNAME/autowiki.git
   cd autowiki
   ```

2. Claude Code を起動:
   ```bash
   claude
   ```

3. wikiを作成:
   ```
   /auto-wiki 人工知能 --wiki ai
   ```

## 使い方

### 新規wiki作成
```
/auto-wiki "トピック名" --wiki wiki-id
```
wikiを作成し、ルート記事から自動拡張を開始します。

### 拡張の続行
```
/auto-wiki --wiki wiki-id --resume
```
前回のセッションから記事の拡張を続行します。

### 記事へのフィードバック
```
/auto-wiki --wiki wiki-id --feedback "article-slug"
```

### 新規記事のリクエスト
```
/auto-wiki --wiki wiki-id --request "新しいトピック"
```

### wiki間の化学反応
```
/auto-wiki-react
/auto-wiki-react --wikis ai,philosophy
```
複数wiki間の概念的親和性をスキャンし、反応記事を生成します。

### ポータル再生成
```
/auto-wiki-portal
```

### オプション
- `--max-agents N`: 同時サブエージェント数（デフォルト: 3）

## 反応タイプ

| タイプ | 説明 | 例 |
|--------|------|---|
| **bridge** | 2つの概念を接続 | 量子測定 ↔ 意識のハードプロブレム |
| **synthesis** | 2分野を統合した新概念 | 自然選択 + 市場競争 → 進化経済学 |
| **debate** | 対立する見解を整理 | 自由意志 ⇔ 決定論 |
| **analogy** | 構造的類似性を論じる | トポロジー ≈ 音韻変化 |

## プロジェクト構造

```
autowiki/
├── wikis/
│   └── {wiki-id}/
│       ├── articles/           # 生成された記事HTML
│       ├── db/                 # wiki固有DB
│       │   ├── articles.json
│       │   ├── brainstorm.json
│       │   ├── graph.json
│       │   └── session.json
│       └── index.html          # wiki個別トップ
├── db/                         # グローバルDB
│   ├── registry.json           # wiki一覧
│   ├── reactions.json          # 反応レジストリ
│   └── cross-graph.json        # 統合グラフ
├── assets/
│   ├── css/wiki.css            # Wikipedia風テーマ
│   └── js/
│       ├── graph.js            # D3.js力指向グラフ
│       └── search.js           # 検索機能
├── templates/
│   ├── article.html            # 記事テンプレート
│   ├── wiki-index.html         # wiki個別トップ
│   └── portal.html             # 統合ポータル
├── tools/
│   ├── db.py                   # JSON DB操作
│   └── cli.py                  # CLIエントリポイント
├── index.html                  # 生成済みポータル
└── .claude/commands/           # Skill定義
```

## CLI (`awiki`)

```bash
# Wiki管理
uv run awiki wiki create --id ai --title "人工知能" --root-topic "AI" --color "#0645ad"
uv run awiki wiki list

# 記事操作（--wiki 必須）
uv run awiki article list --wiki ai
uv run awiki article add --wiki ai --slug S --title T --filename F --summary S
uv run awiki sync --wiki ai

# 反応
uv run awiki reaction list
uv run awiki portal rebuild
```

## GitHub Actions でスキル実行

Actions タブから手動でAuto-Wikiスキルを実行できます。

### 必要なトークン

ワークフローは以下の2つのトークンを使用します:

| トークン | 用途 | 設定方法 |
|----------|------|----------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude API 認証 | 手動でリポジトリシークレットに登録 |
| `GITHUB_TOKEN` | リポジトリ操作（PR作成・push等） | GitHub Actions が自動提供（設定不要） |

### OAuthトークンの取得と登録

Claude Max / Pro サブスクリプションに含まれるClaude CodeのOAuth認証を使います。追加のAPI課金は発生しません。

#### 1. OAuthトークンを生成

ローカルでClaude Codeを起動し、以下を実行:

```bash
claude setup-token
```

`sk-ant-oat01-...` 形式のトークンが出力されます。

#### 2. GitHubリポジトリに登録

1. リポジトリの Settings > Secrets and variables > Actions を開く
2. 「New repository secret」をクリック
3. Name: `CLAUDE_CODE_OAUTH_TOKEN`
4. Value: 上記で取得したトークンを入力して保存

> **注意**: `ANTHROPIC_API_KEY`（従量課金のAPIキー）とは別物です。環境に `ANTHROPIC_API_KEY` が設定されているとそちらが優先され、サブスク外の課金が発生します。

### ワークフローのパーミッション

ワークフロー（`.github/workflows/auto-wiki.yml`）には以下のパーミッションが必要です:

```yaml
permissions:
  contents: write       # ブランチ作成・コミット・push
  pull-requests: write  # PR作成
  id-token: write       # OIDC認証（claude-code-action が使用）
```

これらはワークフローファイルに設定済みです。リポジトリ側の Settings > Actions > General > Workflow permissions が「Read and write permissions」になっていることを確認してください。

### 実行方法

1. Actions タブ > 「Auto-Wiki Skill Runner」を選択
2. 「Run workflow」をクリック
3. スキルを選択、引数を入力して実行

| スキル | 用途 | 引数例 |
|--------|------|--------|
| `/auto-wiki` | wiki作成・拡張 | `人工知能 --wiki ai` |
| `/auto-wiki-expand` | 記事拡張 | `--wiki ai` |
| `/auto-wiki-sync` | DB同期 | `--wiki ai` |
| `/auto-wiki-react` | wiki間反応 | `--wikis ai,philosophy` |
| `/auto-wiki-portal` | ポータル再生成 | (なし) |
| `/auto-wiki-feedback` | 記事フィードバック | `--wiki ai "article-slug" 修正内容` |
| `/auto-wiki-request` | 新規記事リクエスト | `--wiki ai "新トピック"` |

## GitHub Pages でデプロイ

1. GitHubにリポジトリを作成してpush
2. Settings > Pages > Source で「GitHub Actions」を選択
3. `index.html` がトップページとして公開されます

## 技術スタック

| 項目 | 技術 |
|------|------|
| 記事 | 静的HTML + インラインSVG |
| サイトグラフ | D3.js 力指向グラフ |
| スタイル | Wikipedia風CSS (カスタム変数) |
| データベース | JSON ファイル (per-wiki) |
| CLI | Python 3.11+ / uv |
| デプロイ | GitHub Pages |
| AI | Claude Code Skill |

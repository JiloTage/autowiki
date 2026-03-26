---
name: auto-wiki
description: Orchestrate the Auto-Wiki workflow for creating, resuming, expanding, or updating a self-growing multi-wiki system. Use when the user wants to start a wiki from a root topic, resume, apply feedback, request articles, run expansion, or trigger cross-wiki reactions.
---

# Auto-Wiki Orchestrator (Multi-Wiki)

自己増殖するマルチwikiのメインオーケストレータ。引数を解析し、適切なサブスキルにディスパッチする。

## Usage

```
auto-wiki 人工知能                         # wikiを自動作成（IDはトピックから生成）
auto-wiki 人工知能 --wiki custom-id        # wiki IDを明示指定
auto-wiki --resume                         # wikiが1つなら自動選択
auto-wiki --feedback "slug"                # wikiが1つなら自動選択
auto-wiki --request "新トピック"            # wikiが1つなら自動選択
auto-wiki --expand                         # wikiが1つなら自動選択
auto-wiki --max-agents N                   # サブエージェント数上限（デフォルト: 3）
```

## 実行手順

### Step 1: 引数解析

引数を解析し、以下を判定する:

1. `--wiki` の解決（以下の優先順位）:
   - `--wiki ID` が明示指定されていればそのまま使用
   - 新規作成時（トピック指定あり）: トピックからIDを自動生成
     - 日本語: ローマ字変換 → kebab-case（例: "人工知能" → "jinkou-chinou"）
     - 英語: kebab-case（例: "Quantum Physics" → "quantum-physics"）
   - 既存操作時（--resume, --expand, --feedback, --request）:
     - wikiが1つだけ存在 → 自動選択
     - wikiが複数存在 → 一覧を表示してユーザーに選択を促す
     - wikiが0個 → エラー
2. wikiが未作成の場合は `uv run awiki wiki create` で作成

| 条件 | Phase | ディスパッチ先 |
|------|-------|---------------|
| トピック文字列がある（フラグなし） | Phase 1→2 | `auto-wiki-create` → `auto-wiki-expand` |
| `--resume` フラグ | Phase 5→2 | セッション再開 → `auto-wiki-expand` |
| `--feedback` フラグ | Phase 3 | `auto-wiki-feedback` |
| `--request` フラグ | Phase 4 | `auto-wiki-request` |
| `--expand` フラグ | Phase 2 | `auto-wiki-expand` |

### Step 2: 状態確認

1. `uv run awiki wiki get {wiki-id}` でwiki情報を取得（存在しなければ作成）
2. `uv run awiki session get --wiki {wiki-id}` で現在の状態を把握
3. `uv run awiki article list --wiki {wiki-id}` で既存記事数を確認
4. `--max-agents N` が指定されていれば抽出（デフォルト: 3）

### Step 3: Phase別ディスパッチ

全サブスキルに `--wiki {wiki-id}` を渡す。

#### Phase 1→2: 新規wiki作成

1. wikiが未登録なら作成:
   ```bash
   uv run awiki wiki create --id {wiki-id} --title "{タイトル}" --root-topic "{トピック}" --color "{色}"
   ```
2. `auto-wiki-create` スキルの手順に従いルート記事を作成（`origin: "root"`）
3. 作成完了後、`auto-wiki-sync` スキルの手順に従いDB同期
4. Phase 1完了を報告し、Phase 2へ進むか確認
5. 続行する場合、`auto-wiki-expand` スキルの手順に従い拡張

#### Phase 2: 拡張サイクル

1. `auto-wiki-expand` スキルの手順に従い拡張サイクル実行
2. 完了後、`auto-wiki-sync` スキルの手順に従いDB同期

#### Phase 3: フィードバック

1. `auto-wiki-feedback` スキルの手順に従いフィードバック適用
2. 完了後、`auto-wiki-sync` スキルの手順に従いDB同期

#### Phase 4: 新規記事リクエスト

1. `auto-wiki-request` スキルの手順に従い新記事作成
2. 完了後、`auto-wiki-sync` スキルの手順に従いDB同期

#### Phase 5→2: セッション再開

1. `uv run awiki session get --wiki {wiki-id}` でセッション状態を取得
2. `uv run awiki article list --wiki {wiki-id}` と `uv run awiki brainstorm list --wiki {wiki-id}` で現在のデータを取得
3. 現在の状態をサマリー表示
4. `auto-wiki-expand` スキルの手順に従い拡張

### Step 4: セッション状態更新

各Phase完了後:
1. セッション状態を更新:
   ```bash
   uv run awiki session update --wiki {wiki-id} --phase phase_N
   ```
2. 結果サマリーを表示

## 爆発防止メカニズム

- サイクルあたり記事数上限 = `max_agents`（デフォルト3）
- スコア足切り: `interestingness_score` 0.5未満は自動却下
- セッションあたり総記事数上限: `max_total_articles`（デフォルト50）
- 重複チェック: 同一slugの候補は却下
- 類似チェック: 既存記事と意味的に重複するタイトルの候補は却下

---
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
  - Skill
description: "Self-expanding wiki - orchestrator that coordinates article creation, expansion, feedback, and synchronization"
---

# Auto-Wiki Orchestrator

自己増殖するwikiのメインオーケストレータ。引数を解析し、適切なサブskillにディスパッチする。

## Usage

```
/auto-wiki [topic]                  # 新規wiki作成 → Phase 1 → Phase 2
/auto-wiki --resume                 # 前回セッションから続行 → Phase 2
/auto-wiki --feedback "記事slug"    # 記事へのフィードバック → Phase 3
/auto-wiki --request "新トピック"   # 新規記事リクエスト → Phase 4
/auto-wiki --expand                 # 手動で拡張サイクル実行 → Phase 2
/auto-wiki --max-agents N           # サブエージェント数上限（デフォルト: 3）
```

## 実行手順

ユーザー入力: $ARGUMENTS

### Step 1: 引数解析

`$ARGUMENTS` を解析し、以下のいずれかを判定する:

| 条件 | Phase | ディスパッチ先 |
|------|-------|---------------|
| トピック文字列がある（フラグなし） | Phase 1→2 | `/auto-wiki-create` → `/auto-wiki-expand` |
| `--resume` フラグ | Phase 5→2 | セッション再開 → `/auto-wiki-expand` |
| `--feedback` フラグ | Phase 3 | `/auto-wiki-feedback` |
| `--request` フラグ | Phase 4 | `/auto-wiki-request` |
| `--expand` フラグ | Phase 2 | `/auto-wiki-expand` |

### Step 2: 状態確認

1. `uv run awiki session get` で現在の状態を把握
2. `uv run awiki article list` で既存記事数を確認
3. `--max-agents N` が指定されていれば抽出（デフォルト: 3）

### Step 3: Phase別ディスパッチ

#### Phase 1→2: 新規wiki作成

1. `/auto-wiki-create` を `Skill` で呼び出す:
   - 引数: トピック文字列
   - `origin: "root"` を指定
2. 作成完了後、`/auto-wiki-sync` を `Skill` で呼び出してDB同期
3. Phase 1完了を報告し、Phase 2へ進むか確認
4. 続行する場合、`/auto-wiki-expand` を `Skill` で呼び出す

#### Phase 2: 拡張サイクル

1. `/auto-wiki-expand` を `Skill` で呼び出す:
   - 引数: `--max-agents N`
2. expand skillが内部でサブエージェント起動・結果収集を行う
3. 完了後、`/auto-wiki-sync` を `Skill` で呼び出してDB同期

#### Phase 3: フィードバック

1. `/auto-wiki-feedback` を `Skill` で呼び出す:
   - 引数: 記事slug + フィードバック内容
2. 完了後、`/auto-wiki-sync` を `Skill` で呼び出してDB同期

#### Phase 4: 新規記事リクエスト

1. `/auto-wiki-request` を `Skill` で呼び出す:
   - 引数: 新トピック
2. 完了後、`/auto-wiki-sync` を `Skill` で呼び出してDB同期

#### Phase 5→2: セッション再開

1. `uv run awiki session get` でセッション状態を取得
2. `uv run awiki article list` と `uv run awiki brainstorm list` で現在のデータを取得
3. 現在の状態をサマリー表示:
   - 総記事数
   - 拡張待ちの記事一覧（`expansion_status: "pending"`）
   - キューに残っている候補数とトップ5
   - 最後に実行したフェーズ
4. `/auto-wiki-expand` を `Skill` で呼び出す

### Step 4: セッション状態更新

各Phase完了後:
1. セッション状態を更新:
   ```bash
   uv run awiki session update --phase phase_N
   ```
2. 結果サマリーを表示

## 爆発防止メカニズム

- サイクルあたり記事数上限 = `max_agents`（デフォルト3）
- スコア足切り: `interestingness_score` 0.5未満は自動却下
- セッションあたり総記事数上限: `max_total_articles`（デフォルト50）
- 重複チェック: 同一slugの候補は却下
- 類似チェック: 既存記事と意味的に重複するタイトルの候補は却下

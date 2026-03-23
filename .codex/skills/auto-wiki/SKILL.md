---
name: auto-wiki
description: Orchestrate the Auto-Wiki workflow for creating, resuming, expanding, or updating a self-growing wiki. Use when the user wants to start a wiki from a root topic, resume from db/session.json, apply article feedback, request a new article, or run an expansion cycle.
---

# Auto-Wiki Orchestrator

自己増殖するwikiのメインオーケストレータ。引数を解析し、適切なサブスキルにディスパッチする。

## Usage

```
auto-wiki [topic]                  # 新規wiki作成 → Phase 1 → Phase 2
auto-wiki --resume                 # 前回セッションから続行 → Phase 2
auto-wiki --feedback "記事slug"    # 記事へのフィードバック → Phase 3
auto-wiki --request "新トピック"   # 新規記事リクエスト → Phase 4
auto-wiki --expand                 # 手動で拡張サイクル実行 → Phase 2
auto-wiki --max-agents N           # サブエージェント数上限（デフォルト: 3）
```

## 実行手順

### Step 1: 引数解析

引数を解析し、以下のいずれかを判定する:

| 条件 | Phase | ディスパッチ先 |
|------|-------|---------------|
| トピック文字列がある（フラグなし） | Phase 1→2 | `auto-wiki-create` → `auto-wiki-expand` |
| `--resume` フラグ | Phase 5→2 | セッション再開 → `auto-wiki-expand` |
| `--feedback` フラグ | Phase 3 | `auto-wiki-feedback` |
| `--request` フラグ | Phase 4 | `auto-wiki-request` |
| `--expand` フラグ | Phase 2 | `auto-wiki-expand` |

### Step 2: 状態確認

1. プロジェクトルートを特定（`AGENTS.md` がある階層）
2. `db/session.json` を読み込み、現在の状態を把握
3. `db/articles.json` を読み込み、既存記事数を確認
4. `--max-agents N` が指定されていれば抽出（デフォルト: 3）

### Step 3: Phase別ディスパッチ

#### Phase 1→2: 新規wiki作成

1. `auto-wiki-create` スキルの手順に従いルート記事を作成（`origin: "root"`）
2. 作成完了後、`auto-wiki-sync` スキルの手順に従いDB同期
3. Phase 1完了を報告し、Phase 2へ進むか確認
4. 続行する場合、`auto-wiki-expand` スキルの手順に従い拡張

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

1. `db/session.json` を読み込む
2. `db/articles.json`, `db/brainstorm.json` を読み込む
3. 現在の状態をサマリー表示:
   - 総記事数
   - 拡張待ちの記事一覧（`expansion_status: "pending"`）
   - キューに残っている候補数とトップ5
   - 最後に実行したフェーズ
4. `auto-wiki-expand` スキルの手順に従い拡張

### Step 4: セッション状態更新

各Phase完了後:
1. `db/session.json` を更新:
   ```json
   {
     "last_phase": "phase_N",
     "last_run": "ISO8601",
     "total_articles": N,
     "queue_size": N,
     "max_agents": N,
     "max_total_articles": 50
   }
   ```
2. 結果サマリーを表示

## 爆発防止メカニズム

- サイクルあたり記事数上限 = `max_agents`（デフォルト3）
- スコア足切り: `interestingness_score` 0.5未満は自動却下
- セッションあたり総記事数上限: `max_total_articles`（デフォルト50）
- 重複チェック: 同一slugの候補は却下
- 類似チェック: 既存記事と意味的に重複するタイトルの候補は却下

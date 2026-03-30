/**
 * Auto-Wiki Admin Panel
 * GitHub Actions workflow_dispatch経由でスキルを実行し、ステータスを監視する
 */
const AutoWikiAdmin = (() => {
  const OWNER = 'JiloTage';
  const REPO = 'autowiki';
  const WORKFLOW_FILE = 'auto-wiki.yml';
  const STORAGE_KEY = 'autowiki_gh_token';
  const POLL_INTERVAL = 8000; // 8秒
  const MAX_POLLS = 150; // 最大20分

  const SKILLS = [
    {
      id: 'auto-wiki',
      skill: '/auto-wiki',
      label: '新規Wiki作成',
      description: 'トピックから新しいwikiを作成し、ルート記事と初期拡張を行う',
      argsPlaceholder: 'トピック名（例: 量子コンピュータ）',
      argsRequired: true,
      wikiSelect: false,
      icon: '+',
    },
    {
      id: 'auto-wiki-expand',
      skill: '/auto-wiki-expand',
      label: '記事を拡張',
      description: '既存記事から関連トピックをブレストし、新しい記事を生成する',
      argsPlaceholder: '追加オプション（省略可）',
      argsRequired: false,
      wikiSelect: 'required',
      icon: '\u21C0', // ⇀
    },
    {
      id: 'auto-wiki-react',
      skill: '/auto-wiki-react',
      label: 'Wiki間反応',
      description: '複数wikiの記事間の親和性を検出し、橋渡し・統合記事を生成する',
      argsPlaceholder: '',
      argsRequired: false,
      wikiSelect: false,
      icon: '\u2194', // ↔
    },
    {
      id: 'auto-wiki-request',
      skill: '/auto-wiki-request',
      label: '記事リクエスト',
      description: '特定のトピックの記事を指定wikiに作成する',
      argsPlaceholder: '記事タイトル',
      argsRequired: true,
      wikiSelect: 'required',
      icon: '\u270E', // ✎
    },
    {
      id: 'auto-wiki-sync',
      skill: '/auto-wiki-sync',
      label: 'DB同期',
      description: 'データベースの整合性チェック、グラフ再構築、インデックス再生成',
      argsPlaceholder: '追加オプション（省略可）',
      argsRequired: false,
      wikiSelect: 'required',
      icon: '\u21BB', // ↻
    },
    {
      id: 'auto-wiki-feedback',
      skill: '/auto-wiki-feedback',
      label: 'フィードバック',
      description: '既存記事に修正・改善を適用する',
      argsPlaceholder: 'slug 修正内容',
      argsRequired: true,
      wikiSelect: 'required',
      icon: '\u2709', // ✉
    },
    {
      id: 'auto-wiki-portal',
      skill: '/auto-wiki-portal',
      label: 'ポータル再生成',
      description: '統合ポータル（このページ）を最新状態に再生成する',
      argsPlaceholder: '',
      argsRequired: false,
      wikiSelect: false,
      icon: '\u2302', // ⌂
    },
  ];

  let wikiList = []; // { id, title, color } from registry.json

  let pollingTimers = {};

  // --- Wiki Registry ---
  async function loadWikiList() {
    try {
      const resp = await fetch('db/registry.json');
      if (!resp.ok) return;
      const data = await resp.json();
      const wikis = data.wikis || {};
      wikiList = Object.entries(wikis).map(([id, info]) => ({
        id,
        title: info.title || id,
        color: info.color || '#4a7ebb',
      }));
    } catch {
      wikiList = [];
    }
  }

  function buildWikiSelectHTML(skillId, mode) {
    if (!mode) return '';
    const options = wikiList.map(w =>
      `<option value="${w.id}">${w.title} (${w.id})</option>`
    ).join('');
    return `
      <select class="admin-select admin-wiki-select" data-skill="${skillId}" required>
        <option value="">-- Wiki選択 --</option>
        ${options}
      </select>
    `;
  }

  // --- Storage ---
  function getToken() {
    return localStorage.getItem(STORAGE_KEY) || '';
  }

  function setToken(token) {
    if (token) {
      localStorage.setItem(STORAGE_KEY, token);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  // --- GitHub API ---
  async function ghFetch(path, options = {}) {
    const token = getToken();
    if (!token) throw new Error('GitHub tokenが設定されていません');

    const resp = await fetch(`https://api.github.com${path}`, {
      ...options,
      headers: {
        'Accept': 'application/vnd.github+json',
        'Authorization': `Bearer ${token}`,
        'X-GitHub-Api-Version': '2022-11-28',
        ...(options.headers || {}),
      },
    });

    if (!resp.ok) {
      const body = await resp.text();
      throw new Error(`GitHub API ${resp.status}: ${body}`);
    }

    if (resp.status === 204) return null;
    return resp.json();
  }

  async function triggerWorkflow(skill, args, maxTurns, model) {
    await ghFetch(`/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW_FILE}/dispatches`, {
      method: 'POST',
      body: JSON.stringify({
        ref: 'main',
        inputs: {
          skill: skill,
          args: args || '',
          model: model || 'claude-opus-4-6',
          max_turns: String(maxTurns || 50),
        },
      }),
    });
  }

  async function getRecentRuns(limit = 5) {
    const data = await ghFetch(
      `/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW_FILE}/runs?per_page=${limit}&branch=main`
    );
    return data.workflow_runs || [];
  }

  async function getRunStatus(runId) {
    return ghFetch(`/repos/${OWNER}/${REPO}/actions/runs/${runId}`);
  }

  // --- UI Rendering ---
  async function init(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    await loadWikiList();
    container.innerHTML = buildPanelHTML();
    bindEvents(container);
    refreshStatus();
  }

  function buildPanelHTML() {
    const token = getToken();
    const isConfigured = !!token;

    return `
      <div class="admin-panel" id="admin-panel">
        <div class="admin-header" id="admin-toggle">
          <span class="admin-header-icon">\u2699</span>
          <span>管理パネル</span>
          <span class="admin-toggle-arrow" id="admin-arrow">\u25BC</span>
        </div>
        <div class="admin-body" id="admin-body">
          <!-- Token設定 -->
          <div class="admin-section admin-token-section">
            <div class="admin-token-row">
              <input type="password" id="admin-token-input"
                placeholder="GitHub Personal Access Token (repo, workflow)"
                value="${isConfigured ? '••••••••••••••••' : ''}"
                class="admin-input" />
              <button id="admin-token-save" class="admin-btn admin-btn-small">
                ${isConfigured ? '更新' : '保存'}
              </button>
              ${isConfigured ? '<button id="admin-token-clear" class="admin-btn admin-btn-small admin-btn-danger">削除</button>' : ''}
            </div>
            <div class="admin-token-hint">
              scope: <code>repo</code>, <code>workflow</code> が必要 ·
              <a href="https://github.com/settings/tokens/new?scopes=repo,workflow&description=autowiki-admin" target="_blank" rel="noopener">トークン作成</a>
            </div>
          </div>

          ${isConfigured ? buildSkillsHTML() + buildStatusHTML() : '<div class="admin-section admin-locked">トークンを設定するとスキルを実行できます</div>'}
        </div>
      </div>
    `;
  }

  function buildSkillsHTML() {
    const cards = SKILLS.map(s => `
      <div class="admin-skill-card" data-skill-id="${s.id}">
        <div class="admin-skill-header">
          <span class="admin-skill-icon">${s.icon}</span>
          <span class="admin-skill-label">${s.label}</span>
        </div>
        <div class="admin-skill-desc">${s.description}</div>
        <div class="admin-skill-form">
          ${s.wikiSelect ? buildWikiSelectHTML(s.id, s.wikiSelect) : ''}
          ${s.argsPlaceholder ? `<input type="text" class="admin-input admin-skill-args" placeholder="${s.argsPlaceholder}" data-skill="${s.id}" />` : ''}
          <div class="admin-skill-actions">
            <select class="admin-select admin-model-select" data-skill="${s.id}">
              <option value="claude-opus-4-6">Opus</option>
              <option value="claude-sonnet-4-6">Sonnet</option>
            </select>
            <button class="admin-btn admin-btn-primary admin-run-btn" data-skill="${s.id}" data-skill-cmd="${s.skill}">
              実行
            </button>
          </div>
        </div>
      </div>
    `).join('');

    return `
      <div class="admin-section">
        <h3 class="admin-section-title">スキル実行</h3>
        <div class="admin-skills-grid">${cards}</div>
      </div>
    `;
  }

  function buildStatusHTML() {
    return `
      <div class="admin-section">
        <h3 class="admin-section-title">
          実行状況
          <button id="admin-refresh" class="admin-btn admin-btn-small">更新</button>
        </h3>
        <div id="admin-runs" class="admin-runs">
          <div class="admin-loading">読み込み中...</div>
        </div>
      </div>
    `;
  }

  function renderRuns(runs) {
    const el = document.getElementById('admin-runs');
    if (!el) return;

    if (!runs.length) {
      el.innerHTML = '<div class="admin-empty">実行履歴はありません</div>';
      return;
    }

    el.innerHTML = runs.map(run => {
      const status = formatStatus(run.status, run.conclusion);
      const skill = extractSkill(run);
      const time = formatTime(run.created_at);
      const duration = run.updated_at && run.status === 'completed'
        ? formatDuration(new Date(run.created_at), new Date(run.updated_at))
        : '';

      return `
        <div class="admin-run ${run.status === 'in_progress' ? 'admin-run-active' : ''}">
          <span class="admin-run-status ${status.cls}">${status.icon}</span>
          <span class="admin-run-skill">${skill}</span>
          <span class="admin-run-time">${time}${duration ? ' (' + duration + ')' : ''}</span>
          <a href="${run.html_url}" target="_blank" rel="noopener" class="admin-run-link">ログ</a>
        </div>
      `;
    }).join('');
  }

  function formatStatus(status, conclusion) {
    if (status === 'queued') return { icon: '\u23F3', cls: 'status-queued' }; // ⏳
    if (status === 'in_progress') return { icon: '\u25B6', cls: 'status-running' }; // ▶
    if (status === 'completed') {
      if (conclusion === 'success') return { icon: '\u2713', cls: 'status-success' }; // ✓
      if (conclusion === 'failure') return { icon: '\u2717', cls: 'status-failure' }; // ✗
      if (conclusion === 'cancelled') return { icon: '\u2014', cls: 'status-cancelled' }; // —
      return { icon: '?', cls: 'status-unknown' };
    }
    return { icon: '\u2026', cls: 'status-unknown' }; // …
  }

  function extractSkill(run) {
    // workflow_dispatch の display_title にスキル名が含まれることがある
    const title = run.display_title || run.name || '';
    const match = title.match(/\/auto-wiki[\w-]*/);
    return match ? match[0] : run.name || 'Auto-Wiki';
  }

  function formatTime(iso) {
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now - d;
    const diffMin = Math.floor(diffMs / 60000);

    if (diffMin < 1) return '今';
    if (diffMin < 60) return `${diffMin}分前`;
    const diffH = Math.floor(diffMin / 60);
    if (diffH < 24) return `${diffH}時間前`;
    return d.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' });
  }

  function formatDuration(start, end) {
    const sec = Math.floor((end - start) / 1000);
    if (sec < 60) return `${sec}秒`;
    const min = Math.floor(sec / 60);
    const remSec = sec % 60;
    return `${min}分${remSec}秒`;
  }

  // --- Events ---
  function bindEvents(container) {
    // Toggle panel
    const toggle = container.querySelector('#admin-toggle');
    const body = container.querySelector('#admin-body');
    const arrow = container.querySelector('#admin-arrow');
    if (toggle && body) {
      // Start collapsed
      body.style.display = 'none';
      toggle.addEventListener('click', () => {
        const open = body.style.display !== 'none';
        body.style.display = open ? 'none' : 'block';
        arrow.textContent = open ? '\u25BC' : '\u25B2';
      });
    }

    // Token save
    const saveBtn = container.querySelector('#admin-token-save');
    if (saveBtn) {
      saveBtn.addEventListener('click', () => {
        const input = container.querySelector('#admin-token-input');
        const val = input.value.trim();
        if (val && !val.startsWith('\u2022')) { // not bullet mask
          setToken(val);
          init('admin-container'); // re-render
        }
      });
    }

    // Token clear
    const clearBtn = container.querySelector('#admin-token-clear');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        setToken('');
        init('admin-container');
      });
    }

    // Run buttons
    container.querySelectorAll('.admin-run-btn').forEach(btn => {
      btn.addEventListener('click', () => handleRun(btn, container));
    });

    // Refresh
    const refreshBtn = container.querySelector('#admin-refresh');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', refreshStatus);
    }

    // Enter key in args inputs
    container.querySelectorAll('.admin-skill-args').forEach(input => {
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          const skillId = input.dataset.skill;
          const btn = container.querySelector(`.admin-run-btn[data-skill="${skillId}"]`);
          if (btn) handleRun(btn, container);
        }
      });
    });
  }

  async function handleRun(btn, container) {
    const skillId = btn.dataset.skill;
    const skillCmd = btn.dataset.skillCmd;
    const skillDef = SKILLS.find(s => s.id === skillId);
    const argsInput = container.querySelector(`.admin-skill-args[data-skill="${skillId}"]`);
    const wikiSelect = container.querySelector(`.admin-wiki-select[data-skill="${skillId}"]`);
    const argsText = argsInput ? argsInput.value.trim() : '';
    const selectedWiki = wikiSelect ? wikiSelect.value : '';

    if (skillDef.argsRequired && !argsText) {
      argsInput.classList.add('admin-input-error');
      argsInput.focus();
      setTimeout(() => argsInput.classList.remove('admin-input-error'), 2000);
      return;
    }

    if (skillDef.wikiSelect && !selectedWiki) {
      wikiSelect.classList.add('admin-input-error');
      wikiSelect.focus();
      setTimeout(() => wikiSelect.classList.remove('admin-input-error'), 2000);
      return;
    }

    // Build args: user text + --wiki flag from dropdown
    const wikiFlag = selectedWiki ? `--wiki ${selectedWiki}` : '';
    const args = [argsText, wikiFlag].filter(Boolean).join(' ');

    const modelSelect = container.querySelector(`.admin-model-select[data-skill="${skillId}"]`);
    const model = modelSelect ? modelSelect.value : 'claude-opus-4-6';

    // Confirm
    const label = skillDef.label;
    const argDisplay = args ? ` (${args})` : '';
    const modelDisplay = model.includes('opus') ? 'Opus' : 'Sonnet';
    if (!confirm(`「${label}${argDisplay}」を ${modelDisplay} で実行しますか？`)) return;

    btn.disabled = true;
    btn.textContent = '送信中...';

    try {
      await triggerWorkflow(skillCmd, args, 50, model);

      btn.textContent = '発火済';
      btn.classList.add('admin-btn-success');

      // Show notification
      showNotification(`${label} を発火しました。結果はGitHub Actionsで確認できます。`, 'success');

      // Start polling for new run
      setTimeout(() => {
        refreshStatus();
        startPolling();
      }, 3000);

      // Reset button after a bit
      setTimeout(() => {
        btn.disabled = false;
        btn.textContent = '実行';
        btn.classList.remove('admin-btn-success');
      }, 5000);
    } catch (err) {
      btn.disabled = false;
      btn.textContent = '実行';
      showNotification(`エラー: ${err.message}`, 'error');
    }
  }

  async function refreshStatus() {
    try {
      const runs = await getRecentRuns(8);
      renderRuns(runs);

      // If any run is in_progress or queued, keep polling
      const active = runs.some(r => r.status === 'in_progress' || r.status === 'queued');
      if (active) {
        startPolling();
      } else {
        stopPolling();
      }
    } catch (err) {
      const el = document.getElementById('admin-runs');
      if (el) {
        el.innerHTML = `<div class="admin-error">取得失敗: ${err.message}</div>`;
      }
    }
  }

  function startPolling() {
    if (pollingTimers.status) return; // already polling
    let polls = 0;
    pollingTimers.status = setInterval(async () => {
      polls++;
      if (polls > MAX_POLLS) {
        stopPolling();
        return;
      }
      await refreshStatus();
    }, POLL_INTERVAL);
  }

  function stopPolling() {
    if (pollingTimers.status) {
      clearInterval(pollingTimers.status);
      pollingTimers.status = null;
    }
  }

  function showNotification(message, type) {
    const existing = document.querySelector('.admin-notification');
    if (existing) existing.remove();

    const el = document.createElement('div');
    el.className = `admin-notification admin-notification-${type}`;
    el.textContent = message;
    document.body.appendChild(el);

    setTimeout(() => {
      el.classList.add('admin-notification-hide');
      setTimeout(() => el.remove(), 300);
    }, 4000);
  }

  return { init };
})();

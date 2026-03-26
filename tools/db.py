"""Auto-Wiki JSON database operations."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent.parent / "db"

# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load(name: str) -> dict:
    path = DB_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    return json.loads(path.read_text(encoding="utf-8"))


def _save(name: str, data: dict) -> None:
    path = DB_DIR / name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ===================================================================
# articles.json
# ===================================================================

def article_add(
    slug: str,
    title: str,
    filename: str,
    summary: str,
    links_to: list[str],
    origin: str = "root",
    source_id: str | None = None,
) -> dict:
    """Add a new article entry. Returns the created article object."""
    db = _load("articles.json")
    if slug in db["articles"]:
        raise ValueError(f"Article '{slug}' already exists")
    now = _now()
    article = {
        "id": slug,
        "title": title,
        "filename": filename,
        "created_at": now,
        "updated_at": now,
        "links_to": links_to,
        "linked_from": [],
        "summary": summary,
        "expansion_status": "pending",
        "origin": origin,
    }
    if source_id:
        article["source_id"] = source_id
    db["articles"][slug] = article
    db["total_count"] = len(db["articles"])
    # Update linked_from on targets
    for target in links_to:
        if target in db["articles"] and slug not in db["articles"][target]["linked_from"]:
            db["articles"][target]["linked_from"].append(slug)
    _save("articles.json", db)
    return article


def article_update(slug: str, **fields) -> dict:
    """Update fields on an existing article. Returns updated article."""
    db = _load("articles.json")
    if slug not in db["articles"]:
        raise ValueError(f"Article '{slug}' not found")
    art = db["articles"][slug]
    allowed = {
        "title", "summary", "links_to", "linked_from",
        "expansion_status", "updated_at", "filename",
    }
    for k, v in fields.items():
        if k not in allowed:
            raise ValueError(f"Cannot update field '{k}'")
        art[k] = v
    art["updated_at"] = _now()
    db["articles"][slug] = art
    _save("articles.json", db)
    return art


def article_get(slug: str) -> dict | None:
    """Get a single article by slug."""
    db = _load("articles.json")
    return db["articles"].get(slug)


def article_list() -> dict:
    """Return the full articles database."""
    return _load("articles.json")


def article_exists(slug: str) -> bool:
    db = _load("articles.json")
    return slug in db["articles"]


def article_set_links(slug: str, links_to: list[str]) -> dict:
    """Set links_to for an article and update all linked_from references."""
    db = _load("articles.json")
    if slug not in db["articles"]:
        raise ValueError(f"Article '{slug}' not found")
    art = db["articles"][slug]
    old_links = set(art["links_to"])
    new_links = set(links_to)

    # Remove this slug from old targets' linked_from
    for removed in old_links - new_links:
        if removed in db["articles"]:
            lf = db["articles"][removed]["linked_from"]
            if slug in lf:
                lf.remove(slug)

    # Add this slug to new targets' linked_from
    for added in new_links - old_links:
        if added in db["articles"]:
            lf = db["articles"][added]["linked_from"]
            if slug not in lf:
                lf.append(slug)

    art["links_to"] = links_to
    art["updated_at"] = _now()
    _save("articles.json", db)
    return art


def articles_rebuild_linked_from() -> int:
    """Rebuild all linked_from from links_to. Returns number of updates."""
    db = _load("articles.json")
    # Clear all linked_from
    for art in db["articles"].values():
        art["linked_from"] = []
    # Rebuild
    for slug, art in db["articles"].items():
        for target in art["links_to"]:
            if target in db["articles"]:
                db["articles"][target]["linked_from"].append(slug)
    db["total_count"] = len(db["articles"])
    _save("articles.json", db)
    return len(db["articles"])


# ===================================================================
# graph.json
# ===================================================================

def graph_rebuild() -> dict:
    """Regenerate graph.json from articles.json. Returns the graph."""
    articles_db = _load("articles.json")
    nodes = []
    links = []
    root_id = articles_db.get("root_id")
    for slug, art in articles_db["articles"].items():
        nodes.append({
            "id": slug,
            "title": art["title"],
            "url": art["filename"],
            "summary": art.get("summary", ""),
            "is_root": slug == root_id,
        })
        for target in art["links_to"]:
            if target in articles_db["articles"]:
                links.append({"source": slug, "target": target})
    graph = {"nodes": nodes, "links": links}
    _save("graph.json", graph)
    return graph


# ===================================================================
# brainstorm.json
# ===================================================================

def brainstorm_add(
    proposed_slug: str,
    proposed_title: str,
    source_id: str,
    rationale: str,
    score: float,
) -> dict | None:
    """Add a candidate to the queue. Returns the candidate or None if duplicate."""
    db = _load("brainstorm.json")
    articles_db = _load("articles.json")
    # Dedup: skip if article already exists or already queued
    if proposed_slug in articles_db["articles"]:
        return None
    for item in db["queue"]:
        if item["proposed_slug"] == proposed_slug:
            return None
    candidate = {
        "proposed_slug": proposed_slug,
        "proposed_title": proposed_title,
        "source_id": source_id,
        "rationale": rationale,
        "interestingness_score": score,
        "status": "queued",
    }
    db["queue"].append(candidate)
    # Keep sorted by score DESC
    db["queue"].sort(key=lambda x: x["interestingness_score"], reverse=True)
    _save("brainstorm.json", db)
    return candidate


def brainstorm_add_batch(candidates: list[dict]) -> list[dict]:
    """Add multiple candidates at once. Returns list of added candidates."""
    db = _load("brainstorm.json")
    articles_db = _load("articles.json")
    existing_slugs = set(articles_db["articles"].keys())
    queued_slugs = {item["proposed_slug"] for item in db["queue"]}
    added = []
    for c in candidates:
        slug = c["proposed_slug"]
        if slug in existing_slugs or slug in queued_slugs:
            continue
        candidate = {
            "proposed_slug": slug,
            "proposed_title": c["proposed_title"],
            "source_id": c["source_id"],
            "rationale": c["rationale"],
            "interestingness_score": c["interestingness_score"],
            "status": "queued",
        }
        db["queue"].append(candidate)
        queued_slugs.add(slug)
        added.append(candidate)
    db["queue"].sort(key=lambda x: x["interestingness_score"], reverse=True)
    _save("brainstorm.json", db)
    return added


def brainstorm_pop(n: int = 1, min_score: float = 0.5) -> list[dict]:
    """Pop top N candidates from queue (score >= min_score), move to history."""
    db = _load("brainstorm.json")
    eligible = [c for c in db["queue"] if c["interestingness_score"] >= min_score]
    picked = eligible[:n]
    picked_slugs = {c["proposed_slug"] for c in picked}
    db["queue"] = [c for c in db["queue"] if c["proposed_slug"] not in picked_slugs]
    for c in picked:
        c["status"] = "processing"
    db["history"].extend(picked)
    _save("brainstorm.json", db)
    return picked


def brainstorm_cleanup(max_history: int = 100) -> int:
    """Remove queued items that already exist as articles, trim history. Returns removed count."""
    db = _load("brainstorm.json")
    articles_db = _load("articles.json")
    existing = set(articles_db["articles"].keys())
    before = len(db["queue"])
    # Remove already-existing articles from queue
    db["queue"] = [c for c in db["queue"] if c["proposed_slug"] not in existing]
    # Deduplicate queue by slug
    seen = set()
    deduped = []
    for c in db["queue"]:
        if c["proposed_slug"] not in seen:
            seen.add(c["proposed_slug"])
            deduped.append(c)
    db["queue"] = deduped
    # Trim history
    if len(db["history"]) > max_history:
        db["history"] = db["history"][-max_history:]
    _save("brainstorm.json", db)
    return before - len(db["queue"])


def brainstorm_list() -> dict:
    """Return the full brainstorm database."""
    return _load("brainstorm.json")


# ===================================================================
# session.json
# ===================================================================

def session_get() -> dict:
    """Return session state."""
    return _load("session.json")


def session_update(last_phase: str | None = None, **settings_overrides) -> dict:
    """Update session state. Returns updated session."""
    db = _load("session.json")
    if last_phase is not None:
        db["last_phase"] = last_phase
    db["updated_at"] = _now()
    if db["created_at"] is None:
        db["created_at"] = db["updated_at"]
    for k, v in settings_overrides.items():
        if k in db["settings"]:
            db["settings"][k] = v
    _save("session.json", db)
    return db


def session_frontier_add(slug: str) -> dict:
    """Add a slug to expansion frontier."""
    db = _load("session.json")
    if slug not in db["expansion_frontier"]:
        db["expansion_frontier"].append(slug)
    db["updated_at"] = _now()
    _save("session.json", db)
    return db


def session_frontier_remove(slug: str) -> dict:
    """Remove a slug from expansion frontier."""
    db = _load("session.json")
    if slug in db["expansion_frontier"]:
        db["expansion_frontier"].remove(slug)
    db["updated_at"] = _now()
    _save("session.json", db)
    return db


# ===================================================================
# Composite: full sync
# ===================================================================

def sync_all() -> dict:
    """Run full integrity sync. Returns summary."""
    articles_db = _load("articles.json")
    articles_dir = DB_DIR.parent / "articles"

    # Check for orphan DB entries (no HTML file)
    orphans = []
    for slug, art in list(articles_db["articles"].items()):
        html_path = DB_DIR.parent / art["filename"]
        if not html_path.exists():
            orphans.append(slug)

    # Check for HTML files without DB entries
    untracked = []
    if articles_dir.exists():
        for html_file in articles_dir.glob("*.html"):
            slug = html_file.stem
            if slug not in articles_db["articles"]:
                untracked.append(slug)

    # Rebuild linked_from
    count = articles_rebuild_linked_from()

    # Rebuild graph
    graph = graph_rebuild()

    # Cleanup brainstorm
    removed = brainstorm_cleanup()

    # Update session
    session_update(last_phase="sync")

    return {
        "articles_count": count,
        "orphan_db_entries": orphans,
        "untracked_html_files": untracked,
        "graph_nodes": len(graph["nodes"]),
        "graph_links": len(graph["links"]),
        "brainstorm_cleaned": removed,
    }

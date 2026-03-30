"""Auto-Wiki JSON database operations — multi-wiki edition."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GLOBAL_DB_DIR = PROJECT_ROOT / "db"
WIKIS_DIR = PROJECT_ROOT / "wikis"

# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _wiki_db_dir(wiki_id: str) -> Path:
    return WIKIS_DIR / wiki_id / "db"


def _load_global(name: str) -> dict:
    path = GLOBAL_DB_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    return json.loads(path.read_text(encoding="utf-8"))


def _save_global(name: str, data: dict) -> None:
    path = GLOBAL_DB_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load(wiki_id: str, name: str) -> dict:
    path = _wiki_db_dir(wiki_id) / name
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    return json.loads(path.read_text(encoding="utf-8"))


def _save(wiki_id: str, name: str, data: dict) -> None:
    path = _wiki_db_dir(wiki_id) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ===================================================================
# registry.json — Global wiki registry
# ===================================================================

_REGISTRY_INIT = {"wikis": {}}

_WIKI_DB_INIT = {
    "articles.json": {"articles": {}, "root_id": None, "total_count": 0},
    "brainstorm.json": {"queue": [], "history": []},
    "graph.json": {"nodes": [], "links": []},
    "session.json": {
        "last_phase": None,
        "expansion_frontier": [],
        "settings": {
            "max_total_articles": 50,
            "score_threshold": 0.5,
            "language": "ja",
        },
        "created_at": None,
        "updated_at": None,
    },
}


def _ensure_registry() -> dict:
    path = GLOBAL_DB_DIR / "registry.json"
    if not path.exists():
        _save_global("registry.json", _REGISTRY_INIT)
    return _load_global("registry.json")


def wiki_create(wiki_id: str, title: str, root_topic: str, color: str = "#36c") -> dict:
    """Create a new wiki. Initialises directory structure and DB files."""
    reg = _ensure_registry()
    if wiki_id in reg["wikis"]:
        raise ValueError(f"Wiki '{wiki_id}' already exists")
    now = _now()
    wiki = {
        "id": wiki_id,
        "title": title,
        "root_topic": root_topic,
        "created_at": now,
        "article_count": 0,
        "color": color,
        "status": "active",
    }
    reg["wikis"][wiki_id] = wiki
    _save_global("registry.json", reg)

    # Create wiki directory structure
    wiki_dir = WIKIS_DIR / wiki_id
    (wiki_dir / "articles").mkdir(parents=True, exist_ok=True)
    (wiki_dir / "db").mkdir(parents=True, exist_ok=True)

    # Initialise DB files
    for name, init_data in _WIKI_DB_INIT.items():
        _save(wiki_id, name, init_data)

    return wiki


def wiki_list() -> dict:
    """Return the registry."""
    return _ensure_registry()


def wiki_get(wiki_id: str) -> dict | None:
    reg = _ensure_registry()
    return reg["wikis"].get(wiki_id)


def wiki_delete(wiki_id: str) -> dict:
    """Soft-delete a wiki (set status to archived)."""
    reg = _ensure_registry()
    if wiki_id not in reg["wikis"]:
        raise ValueError(f"Wiki '{wiki_id}' not found")
    reg["wikis"][wiki_id]["status"] = "archived"
    _save_global("registry.json", reg)
    return reg["wikis"][wiki_id]


def _update_registry_count(wiki_id: str, count: int) -> None:
    """Update article_count in registry."""
    reg = _ensure_registry()
    if wiki_id in reg["wikis"]:
        reg["wikis"][wiki_id]["article_count"] = count
        _save_global("registry.json", reg)


# ===================================================================
# articles.json — per-wiki
# ===================================================================

def article_add(
    wiki_id: str,
    slug: str,
    title: str,
    filename: str,
    summary: str,
    links_to: list[str],
    origin: str = "root",
    source_id: str | None = None,
) -> dict:
    """Add a new article entry. Returns the created article object."""
    db = _load(wiki_id, "articles.json")
    if slug in db["articles"]:
        raise ValueError(f"Article '{slug}' already exists in wiki '{wiki_id}'")
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
    # Update linked_from on local targets
    for target in links_to:
        # Only update local refs (no colon = same wiki)
        if ":" not in target and target in db["articles"] and slug not in db["articles"][target]["linked_from"]:
            db["articles"][target]["linked_from"].append(slug)
    _save(wiki_id, "articles.json", db)
    _update_registry_count(wiki_id, db["total_count"])
    return article


def article_update(wiki_id: str, slug: str, **fields) -> dict:
    """Update fields on an existing article. Returns updated article."""
    db = _load(wiki_id, "articles.json")
    if slug not in db["articles"]:
        raise ValueError(f"Article '{slug}' not found in wiki '{wiki_id}'")
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
    _save(wiki_id, "articles.json", db)
    return art


def article_get(wiki_id: str, slug: str) -> dict | None:
    db = _load(wiki_id, "articles.json")
    return db["articles"].get(slug)


def article_list(wiki_id: str) -> dict:
    return _load(wiki_id, "articles.json")


def article_exists(wiki_id: str, slug: str) -> bool:
    db = _load(wiki_id, "articles.json")
    return slug in db["articles"]


def article_set_links(wiki_id: str, slug: str, links_to: list[str]) -> dict:
    """Set links_to for an article and update all linked_from references."""
    db = _load(wiki_id, "articles.json")
    if slug not in db["articles"]:
        raise ValueError(f"Article '{slug}' not found in wiki '{wiki_id}'")
    art = db["articles"][slug]
    old_links = set(art["links_to"])
    new_links = set(links_to)

    # Only manage linked_from for local refs (no colon)
    for removed in old_links - new_links:
        if ":" not in removed and removed in db["articles"]:
            lf = db["articles"][removed]["linked_from"]
            if slug in lf:
                lf.remove(slug)

    for added in new_links - old_links:
        if ":" not in added and added in db["articles"]:
            lf = db["articles"][added]["linked_from"]
            if slug not in lf:
                lf.append(slug)

    art["links_to"] = links_to
    art["updated_at"] = _now()
    _save(wiki_id, "articles.json", db)
    return art


def articles_rebuild_linked_from(wiki_id: str) -> int:
    """Rebuild all linked_from from links_to. Returns number of updates."""
    db = _load(wiki_id, "articles.json")
    for art in db["articles"].values():
        art["linked_from"] = []
    for slug, art in db["articles"].items():
        for target in art["links_to"]:
            if ":" not in target and target in db["articles"]:
                db["articles"][target]["linked_from"].append(slug)
    db["total_count"] = len(db["articles"])
    _save(wiki_id, "articles.json", db)
    return len(db["articles"])


# ===================================================================
# graph.json — per-wiki
# ===================================================================

def graph_rebuild(wiki_id: str) -> dict:
    """Regenerate graph.json from articles.json. Returns the graph."""
    articles_db = _load(wiki_id, "articles.json")
    nodes = []
    links = []
    root_id = articles_db.get("root_id")
    for slug, art in articles_db["articles"].items():
        nodes.append({
            "id": slug,
            "title": art["title"],
            "url": f"articles/{slug}.html",
            "summary": art.get("summary", ""),
            "is_root": slug == root_id,
        })
        for target in art["links_to"]:
            # Local links only for per-wiki graph
            if ":" not in target and target in articles_db["articles"]:
                links.append({"source": slug, "target": target})
    graph = {"nodes": nodes, "links": links}
    _save(wiki_id, "graph.json", graph)
    return graph


# ===================================================================
# brainstorm.json — per-wiki
# ===================================================================

def brainstorm_add(
    wiki_id: str,
    proposed_slug: str,
    proposed_title: str,
    source_id: str,
    rationale: str,
    score: float,
) -> dict | None:
    db = _load(wiki_id, "brainstorm.json")
    articles_db = _load(wiki_id, "articles.json")
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
    db["queue"].sort(key=lambda x: x["interestingness_score"], reverse=True)
    _save(wiki_id, "brainstorm.json", db)
    return candidate


def brainstorm_add_batch(wiki_id: str, candidates: list[dict]) -> list[dict]:
    db = _load(wiki_id, "brainstorm.json")
    articles_db = _load(wiki_id, "articles.json")
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
    _save(wiki_id, "brainstorm.json", db)
    return added


def brainstorm_pop(wiki_id: str, n: int = 1, min_score: float = 0.5) -> list[dict]:
    db = _load(wiki_id, "brainstorm.json")
    eligible = [c for c in db["queue"] if c["interestingness_score"] >= min_score]
    picked = eligible[:n]
    picked_slugs = {c["proposed_slug"] for c in picked}
    db["queue"] = [c for c in db["queue"] if c["proposed_slug"] not in picked_slugs]
    for c in picked:
        c["status"] = "processing"
    db["history"].extend(picked)
    _save(wiki_id, "brainstorm.json", db)
    return picked


def brainstorm_cleanup(wiki_id: str, max_history: int = 100) -> int:
    db = _load(wiki_id, "brainstorm.json")
    articles_db = _load(wiki_id, "articles.json")
    existing = set(articles_db["articles"].keys())
    before = len(db["queue"])
    db["queue"] = [c for c in db["queue"] if c["proposed_slug"] not in existing]
    seen = set()
    deduped = []
    for c in db["queue"]:
        if c["proposed_slug"] not in seen:
            seen.add(c["proposed_slug"])
            deduped.append(c)
    db["queue"] = deduped
    if len(db["history"]) > max_history:
        db["history"] = db["history"][-max_history:]
    _save(wiki_id, "brainstorm.json", db)
    return before - len(db["queue"])


def brainstorm_list(wiki_id: str) -> dict:
    return _load(wiki_id, "brainstorm.json")


# ===================================================================
# session.json — per-wiki
# ===================================================================

def session_get(wiki_id: str) -> dict:
    return _load(wiki_id, "session.json")


def session_update(wiki_id: str, last_phase: str | None = None, **settings_overrides) -> dict:
    db = _load(wiki_id, "session.json")
    if last_phase is not None:
        db["last_phase"] = last_phase
    db["updated_at"] = _now()
    if db["created_at"] is None:
        db["created_at"] = db["updated_at"]
    for k, v in settings_overrides.items():
        if k in db["settings"]:
            db["settings"][k] = v
    _save(wiki_id, "session.json", db)
    return db


def session_frontier_add(wiki_id: str, slug: str) -> dict:
    db = _load(wiki_id, "session.json")
    if slug not in db["expansion_frontier"]:
        db["expansion_frontier"].append(slug)
    db["updated_at"] = _now()
    _save(wiki_id, "session.json", db)
    return db


def session_frontier_remove(wiki_id: str, slug: str) -> dict:
    db = _load(wiki_id, "session.json")
    if slug in db["expansion_frontier"]:
        db["expansion_frontier"].remove(slug)
    db["updated_at"] = _now()
    _save(wiki_id, "session.json", db)
    return db


# ===================================================================
# Reactions — global
# ===================================================================

_REACTIONS_INIT = {"reactions": [], "pending_affinities": []}


def _ensure_reactions() -> dict:
    path = GLOBAL_DB_DIR / "reactions.json"
    if not path.exists():
        _save_global("reactions.json", _REACTIONS_INIT)
    return _load_global("reactions.json")


def reaction_add_affinity(
    wiki_a: str, article_a: str,
    wiki_b: str, article_b: str,
    score: float,
    suggested_type: str,
    rationale: str,
) -> dict:
    """Add a pending affinity between two articles in different wikis."""
    db = _ensure_reactions()
    affinity = {
        "wiki_a": wiki_a,
        "article_a": article_a,
        "wiki_b": wiki_b,
        "article_b": article_b,
        "affinity_score": score,
        "suggested_type": suggested_type,
        "rationale": rationale,
    }
    db["pending_affinities"].append(affinity)
    db["pending_affinities"].sort(key=lambda x: x["affinity_score"], reverse=True)
    _save_global("reactions.json", db)
    return affinity


def reaction_create(
    reaction_type: str,
    reagent_a_wiki: str, reagent_a_slug: str,
    reagent_b_wiki: str, reagent_b_slug: str,
    product_wiki: str, product_slug: str, product_title: str,
    catalyst: str,
    score: float,
) -> dict:
    """Register a completed reaction."""
    db = _ensure_reactions()
    reaction_id = f"r-{uuid.uuid4().hex[:6]}"
    reaction = {
        "id": reaction_id,
        "type": reaction_type,
        "reagents": [
            {"wiki": reagent_a_wiki, "article": reagent_a_slug},
            {"wiki": reagent_b_wiki, "article": reagent_b_slug},
        ],
        "product": {
            "wiki": product_wiki,
            "slug": product_slug,
            "title": product_title,
        },
        "catalyst": catalyst,
        "affinity_score": score,
        "created_at": _now(),
    }
    db["reactions"].append(reaction)
    db["last_react_total_articles"] = _total_article_count()
    db["last_react_at"] = _now()

    # Remove matching pending affinity if exists
    db["pending_affinities"] = [
        a for a in db["pending_affinities"]
        if not (
            {a["wiki_a"], a["wiki_b"]} == {reagent_a_wiki, reagent_b_wiki}
            and {a["article_a"], a["article_b"]} == {reagent_a_slug, reagent_b_slug}
        )
    ]
    _save_global("reactions.json", db)
    return reaction


def reaction_mark_reacted() -> dict:
    """Record current total article count as the last react checkpoint."""
    db = _ensure_reactions()
    total = _total_article_count()
    db["last_react_total_articles"] = total
    db["last_react_at"] = _now()
    _save_global("reactions.json", db)
    return {"last_react_total_articles": total, "last_react_at": db["last_react_at"]}


def reaction_should_react(threshold: int = 5) -> dict:
    """Check if auto-react conditions are met.

    Conditions:
    - At least 2 active wikis
    - New articles since last react >= threshold
    """
    reg = _ensure_registry()
    active_wikis = [wid for wid, w in reg["wikis"].items() if w.get("status") == "active"]
    wiki_count = len(active_wikis)

    total = _total_article_count()
    db = _ensure_reactions()
    last_total = db.get("last_react_total_articles", 0)
    new_articles = total - last_total

    should = wiki_count >= 2 and new_articles >= threshold
    return {
        "should_react": should,
        "wiki_count": wiki_count,
        "total_articles": total,
        "last_react_total_articles": last_total,
        "new_articles_since_react": new_articles,
        "threshold": threshold,
    }


def _total_article_count() -> int:
    """Sum article counts across all active wikis."""
    reg = _ensure_registry()
    total = 0
    for wiki_id, wiki_info in reg["wikis"].items():
        if wiki_info.get("status") != "active":
            continue
        try:
            articles_db = _load(wiki_id, "articles.json")
            total += articles_db.get("total_count", 0)
        except FileNotFoundError:
            pass
    return total


def reaction_list() -> dict:
    return _ensure_reactions()


def reaction_get(reaction_id: str) -> dict | None:
    db = _ensure_reactions()
    for r in db["reactions"]:
        if r["id"] == reaction_id:
            return r
    return None


# ===================================================================
# Portal — cross-wiki graph
# ===================================================================

def portal_rebuild_graph() -> dict:
    """Build cross-graph.json from all active wikis."""
    reg = _ensure_registry()
    reactions_db = _ensure_reactions()
    nodes = []
    links = []

    for wiki_id, wiki_info in reg["wikis"].items():
        if wiki_info.get("status") != "active":
            continue
        try:
            articles_db = _load(wiki_id, "articles.json")
        except FileNotFoundError:
            continue
        root_id = articles_db.get("root_id")
        color = wiki_info.get("color", "#36c")

        for slug, art in articles_db["articles"].items():
            node_id = f"{wiki_id}:{slug}"
            nodes.append({
                "id": node_id,
                "wiki": wiki_id,
                "title": art["title"],
                "url": f"wikis/{wiki_id}/articles/{slug}.html",
                "color": color,
                "is_root": slug == root_id,
                "summary": art.get("summary", ""),
            })
            for target in art["links_to"]:
                if ":" in target:
                    # Cross-wiki link
                    links.append({
                        "source": node_id,
                        "target": target,
                        "type": "cross",
                    })
                elif target in articles_db["articles"]:
                    links.append({
                        "source": node_id,
                        "target": f"{wiki_id}:{target}",
                        "type": "internal",
                    })

    # Add reaction links
    for r in reactions_db["reactions"]:
        for reagent in r["reagents"]:
            product_id = f"{r['product']['wiki']}:{r['product']['slug']}"
            reagent_id = f"{reagent['wiki']}:{reagent['article']}"
            links.append({
                "source": reagent_id,
                "target": product_id,
                "type": "reaction",
                "reaction_id": r["id"],
            })

    graph = {"nodes": nodes, "links": links}
    _save_global("cross-graph.json", graph)
    return graph


# ===================================================================
# Composite: full sync (per-wiki)
# ===================================================================

def sync_all(wiki_id: str) -> dict:
    """Run full integrity sync for a wiki. Returns summary."""
    articles_db = _load(wiki_id, "articles.json")
    articles_dir = WIKIS_DIR / wiki_id / "articles"

    # Check for orphan DB entries (no HTML file)
    orphans = []
    for slug, art in list(articles_db["articles"].items()):
        html_path = PROJECT_ROOT / art["filename"]
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
    count = articles_rebuild_linked_from(wiki_id)

    # Rebuild graph
    graph = graph_rebuild(wiki_id)

    # Cleanup brainstorm
    removed = brainstorm_cleanup(wiki_id)

    # Update session
    session_update(wiki_id, last_phase="sync")

    # Update registry count
    _update_registry_count(wiki_id, count)

    return {
        "wiki_id": wiki_id,
        "articles_count": count,
        "orphan_db_entries": orphans,
        "untracked_html_files": untracked,
        "graph_nodes": len(graph["nodes"]),
        "graph_links": len(graph["links"]),
        "brainstorm_cleaned": removed,
    }

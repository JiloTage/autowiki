#!/usr/bin/env python3
"""Auto-Wiki JSON database CLI — multi-wiki edition.

Usage:
    awiki wiki create --id ID --title T --root-topic TOPIC [--color C]
    awiki wiki list
    awiki wiki get WIKI_ID
    awiki wiki delete WIKI_ID

    awiki article add --wiki W --slug S --title T --filename F --summary S [--links-to L1,L2] [--origin O] [--source-id ID]
    awiki article get --wiki W SLUG
    awiki article list --wiki W
    awiki article exists --wiki W SLUG
    awiki article update --wiki W SLUG [--title T] [--summary S] [--expansion-status S] [--links-to L1,L2]
    awiki article set-links --wiki W SLUG --links L1,L2
    awiki article rebuild-linked-from --wiki W

    awiki graph rebuild --wiki W

    awiki brainstorm add --wiki W --slug S --title T --source-id ID --rationale R --score 0.8
    awiki brainstorm add-batch --wiki W --json '[...]'
    awiki brainstorm pop --wiki W [--n N] [--min-score 0.5]
    awiki brainstorm cleanup --wiki W [--max-history 100]
    awiki brainstorm list --wiki W

    awiki session get --wiki W
    awiki session update --wiki W [--phase P] [--setting key=value ...]
    awiki session frontier-add --wiki W SLUG
    awiki session frontier-remove --wiki W SLUG

    awiki sync --wiki W

    awiki reaction add-affinity --wiki-a A --article-a SA --wiki-b B --article-b SB --score 0.8 --type TYPE --rationale R
    awiki reaction create --type TYPE --reagent-a A:slug --reagent-b B:slug --product-wiki W --product-slug S --product-title T --catalyst C --score 0.8
    awiki reaction list
    awiki reaction get ID

    awiki portal rebuild
"""

from __future__ import annotations

import argparse
import json
import sys

from tools import db


def _print_json(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _parse_list(s: str) -> list[str]:
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


def _resolve_wiki(args) -> str:
    """Resolve wiki ID: use --wiki if given, auto-select if only one exists, error otherwise."""
    if args.wiki:
        return args.wiki
    # Auto-select if exactly one active wiki exists
    reg = db.wiki_list()
    active = [w for w in reg.get("wikis", {}).values() if w.get("status") == "active"]
    if len(active) == 1:
        wiki_id = active[0]["id"]
        print(json.dumps({"auto_selected_wiki": wiki_id}), file=sys.stderr)
        return wiki_id
    if len(active) == 0:
        print(json.dumps({"error": "No wikis exist. Create one first: awiki wiki create --id ID --title T --root-topic TOPIC"}), file=sys.stderr)
    else:
        ids = [w["id"] for w in active]
        print(json.dumps({"error": f"Multiple wikis exist. Specify --wiki: {', '.join(ids)}"}), file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# wiki subcommands
# ---------------------------------------------------------------------------

def cmd_wiki_create(args):
    result = db.wiki_create(
        wiki_id=args.id,
        title=args.title,
        root_topic=args.root_topic,
        color=args.color or "#36c",
    )
    _print_json(result)


def cmd_wiki_list(args):
    _print_json(db.wiki_list())


def cmd_wiki_get(args):
    result = db.wiki_get(args.wiki_id)
    if result is None:
        print(f"Wiki '{args.wiki_id}' not found", file=sys.stderr)
        sys.exit(1)
    _print_json(result)


def cmd_wiki_delete(args):
    result = db.wiki_delete(args.wiki_id)
    _print_json(result)


# ---------------------------------------------------------------------------
# article subcommands
# ---------------------------------------------------------------------------

def cmd_article_add(args):
    wiki = _resolve_wiki(args)
    result = db.article_add(
        wiki_id=wiki,
        slug=args.slug,
        title=args.title,
        filename=args.filename,
        summary=args.summary,
        links_to=_parse_list(args.links_to or ""),
        origin=args.origin or "root",
        source_id=args.source_id,
    )
    _print_json(result)


def cmd_article_get(args):
    wiki = _resolve_wiki(args)
    result = db.article_get(wiki, args.slug)
    if result is None:
        print(f"Article '{args.slug}' not found in wiki '{wiki}'", file=sys.stderr)
        sys.exit(1)
    _print_json(result)


def cmd_article_list(args):
    wiki = _resolve_wiki(args)
    _print_json(db.article_list(wiki))


def cmd_article_exists(args):
    wiki = _resolve_wiki(args)
    exists = db.article_exists(wiki, args.slug)
    print(json.dumps({"exists": exists}))
    sys.exit(0 if exists else 1)


def cmd_article_update(args):
    wiki = _resolve_wiki(args)
    fields = {}
    if args.title:
        fields["title"] = args.title
    if args.summary:
        fields["summary"] = args.summary
    if args.expansion_status:
        fields["expansion_status"] = args.expansion_status
    if args.links_to is not None:
        fields["links_to"] = _parse_list(args.links_to)
    result = db.article_update(wiki, args.slug, **fields)
    _print_json(result)


def cmd_article_set_links(args):
    wiki = _resolve_wiki(args)
    result = db.article_set_links(wiki, args.slug, _parse_list(args.links))
    _print_json(result)


def cmd_article_rebuild_linked_from(args):
    wiki = _resolve_wiki(args)
    count = db.articles_rebuild_linked_from(wiki)
    print(json.dumps({"updated_articles": count}))


# ---------------------------------------------------------------------------
# graph subcommands
# ---------------------------------------------------------------------------

def cmd_graph_rebuild(args):
    wiki = _resolve_wiki(args)
    result = db.graph_rebuild(wiki)
    _print_json(result)


# ---------------------------------------------------------------------------
# brainstorm subcommands
# ---------------------------------------------------------------------------

def cmd_brainstorm_add(args):
    wiki = _resolve_wiki(args)
    result = db.brainstorm_add(
        wiki_id=wiki,
        proposed_slug=args.slug,
        proposed_title=args.title,
        source_id=args.source_id,
        rationale=args.rationale,
        score=args.score,
    )
    if result is None:
        print(json.dumps({"skipped": True, "reason": "duplicate"}))
    else:
        _print_json(result)


def cmd_brainstorm_add_batch(args):
    wiki = _resolve_wiki(args)
    candidates = json.loads(args.json)
    result = db.brainstorm_add_batch(wiki, candidates)
    _print_json(result)


def cmd_brainstorm_pop(args):
    wiki = _resolve_wiki(args)
    result = db.brainstorm_pop(wiki, n=args.n, min_score=args.min_score)
    _print_json(result)


def cmd_brainstorm_cleanup(args):
    wiki = _resolve_wiki(args)
    removed = db.brainstorm_cleanup(wiki, max_history=args.max_history)
    print(json.dumps({"removed": removed}))


def cmd_brainstorm_list(args):
    wiki = _resolve_wiki(args)
    _print_json(db.brainstorm_list(wiki))


# ---------------------------------------------------------------------------
# session subcommands
# ---------------------------------------------------------------------------

def cmd_session_get(args):
    wiki = _resolve_wiki(args)
    _print_json(db.session_get(wiki))


def cmd_session_update(args):
    wiki = _resolve_wiki(args)
    settings = {}
    if args.setting:
        for s in args.setting:
            k, v = s.split("=", 1)
            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    if v.lower() in ("true", "false"):
                        v = v.lower() == "true"
            settings[k] = v
    result = db.session_update(wiki, last_phase=args.phase, **settings)
    _print_json(result)


def cmd_session_frontier_add(args):
    wiki = _resolve_wiki(args)
    result = db.session_frontier_add(wiki, args.slug)
    _print_json(result)


def cmd_session_frontier_remove(args):
    wiki = _resolve_wiki(args)
    result = db.session_frontier_remove(wiki, args.slug)
    _print_json(result)


# ---------------------------------------------------------------------------
# sync
# ---------------------------------------------------------------------------

def cmd_sync(args):
    wiki = _resolve_wiki(args)
    result = db.sync_all(wiki)
    _print_json(result)


# ---------------------------------------------------------------------------
# reaction subcommands
# ---------------------------------------------------------------------------

def cmd_reaction_add_affinity(args):
    result = db.reaction_add_affinity(
        wiki_a=args.wiki_a,
        article_a=args.article_a,
        wiki_b=args.wiki_b,
        article_b=args.article_b,
        score=args.score,
        suggested_type=args.type,
        rationale=args.rationale,
    )
    _print_json(result)


def _parse_reagent(s: str) -> tuple[str, str]:
    """Parse 'wiki:slug' into (wiki, slug)."""
    parts = s.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Reagent must be wiki:slug format, got '{s}'")
    return parts[0], parts[1]


def cmd_reaction_create(args):
    wiki_a, slug_a = _parse_reagent(args.reagent_a)
    wiki_b, slug_b = _parse_reagent(args.reagent_b)
    result = db.reaction_create(
        reaction_type=args.type,
        reagent_a_wiki=wiki_a,
        reagent_a_slug=slug_a,
        reagent_b_wiki=wiki_b,
        reagent_b_slug=slug_b,
        product_wiki=args.product_wiki,
        product_slug=args.product_slug,
        product_title=args.product_title,
        catalyst=args.catalyst,
        score=args.score,
    )
    _print_json(result)


def cmd_reaction_should_react(args):
    threshold = args.threshold if args.threshold else 5
    _print_json(db.reaction_should_react(threshold))


def cmd_reaction_mark_reacted(args):
    _print_json(db.reaction_mark_reacted())


def cmd_reaction_list(args):
    _print_json(db.reaction_list())


def cmd_reaction_get(args):
    result = db.reaction_get(args.reaction_id)
    if result is None:
        print(f"Reaction '{args.reaction_id}' not found", file=sys.stderr)
        sys.exit(1)
    _print_json(result)


# ---------------------------------------------------------------------------
# portal
# ---------------------------------------------------------------------------

def cmd_portal_rebuild(args):
    result = db.portal_rebuild_graph()
    _print_json(result)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _add_wiki_flag(parser):
    """Add --wiki flag to a parser."""
    parser.add_argument("--wiki", default=None, help="Wiki ID")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="awiki", description="Auto-Wiki JSON DB CLI (multi-wiki)")
    sub = parser.add_subparsers(dest="command", required=True)

    # --- wiki ---
    wiki_cmd = sub.add_parser("wiki", help="Wiki management")
    wiki_sub = wiki_cmd.add_subparsers(dest="action", required=True)

    p = wiki_sub.add_parser("create", help="Create a new wiki")
    p.add_argument("--id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--root-topic", required=True)
    p.add_argument("--color", default="#36c")
    p.set_defaults(func=cmd_wiki_create)

    p = wiki_sub.add_parser("list", help="List all wikis")
    p.set_defaults(func=cmd_wiki_list)

    p = wiki_sub.add_parser("get", help="Get wiki info")
    p.add_argument("wiki_id")
    p.set_defaults(func=cmd_wiki_get)

    p = wiki_sub.add_parser("delete", help="Archive a wiki")
    p.add_argument("wiki_id")
    p.set_defaults(func=cmd_wiki_delete)

    # --- article ---
    art = sub.add_parser("article", help="Article operations")
    art_sub = art.add_subparsers(dest="action", required=True)

    p = art_sub.add_parser("add", help="Add a new article")
    _add_wiki_flag(p)
    p.add_argument("--slug", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--filename", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--links-to", default="")
    p.add_argument("--origin", default="root")
    p.add_argument("--source-id", default=None)
    p.set_defaults(func=cmd_article_add)

    p = art_sub.add_parser("get", help="Get article by slug")
    _add_wiki_flag(p)
    p.add_argument("slug")
    p.set_defaults(func=cmd_article_get)

    p = art_sub.add_parser("list", help="List all articles")
    _add_wiki_flag(p)
    p.set_defaults(func=cmd_article_list)

    p = art_sub.add_parser("exists", help="Check if article exists")
    _add_wiki_flag(p)
    p.add_argument("slug")
    p.set_defaults(func=cmd_article_exists)

    p = art_sub.add_parser("update", help="Update article fields")
    _add_wiki_flag(p)
    p.add_argument("slug")
    p.add_argument("--title", default=None)
    p.add_argument("--summary", default=None)
    p.add_argument("--expansion-status", default=None)
    p.add_argument("--links-to", default=None)
    p.set_defaults(func=cmd_article_update)

    p = art_sub.add_parser("set-links", help="Set links and sync linked_from")
    _add_wiki_flag(p)
    p.add_argument("slug")
    p.add_argument("--links", required=True)
    p.set_defaults(func=cmd_article_set_links)

    p = art_sub.add_parser("rebuild-linked-from", help="Rebuild all linked_from")
    _add_wiki_flag(p)
    p.set_defaults(func=cmd_article_rebuild_linked_from)

    # --- graph ---
    gr = sub.add_parser("graph", help="Graph operations")
    gr_sub = gr.add_subparsers(dest="action", required=True)

    p = gr_sub.add_parser("rebuild", help="Rebuild graph.json")
    _add_wiki_flag(p)
    p.set_defaults(func=cmd_graph_rebuild)

    # --- brainstorm ---
    bs = sub.add_parser("brainstorm", help="Brainstorm operations")
    bs_sub = bs.add_subparsers(dest="action", required=True)

    p = bs_sub.add_parser("add", help="Add a candidate")
    _add_wiki_flag(p)
    p.add_argument("--slug", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--rationale", required=True)
    p.add_argument("--score", type=float, required=True)
    p.set_defaults(func=cmd_brainstorm_add)

    p = bs_sub.add_parser("add-batch", help="Add candidates from JSON")
    _add_wiki_flag(p)
    p.add_argument("--json", required=True)
    p.set_defaults(func=cmd_brainstorm_add_batch)

    p = bs_sub.add_parser("pop", help="Pop top N candidates")
    _add_wiki_flag(p)
    p.add_argument("--n", type=int, default=1)
    p.add_argument("--min-score", type=float, default=0.5)
    p.set_defaults(func=cmd_brainstorm_pop)

    p = bs_sub.add_parser("cleanup", help="Cleanup brainstorm queue")
    _add_wiki_flag(p)
    p.add_argument("--max-history", type=int, default=100)
    p.set_defaults(func=cmd_brainstorm_cleanup)

    p = bs_sub.add_parser("list", help="List brainstorm queue")
    _add_wiki_flag(p)
    p.set_defaults(func=cmd_brainstorm_list)

    # --- session ---
    ss = sub.add_parser("session", help="Session operations")
    ss_sub = ss.add_subparsers(dest="action", required=True)

    p = ss_sub.add_parser("get", help="Get session state")
    _add_wiki_flag(p)
    p.set_defaults(func=cmd_session_get)

    p = ss_sub.add_parser("update", help="Update session state")
    _add_wiki_flag(p)
    p.add_argument("--phase", default=None)
    p.add_argument("--setting", action="append", help="key=value pairs")
    p.set_defaults(func=cmd_session_update)

    p = ss_sub.add_parser("frontier-add", help="Add to expansion frontier")
    _add_wiki_flag(p)
    p.add_argument("slug")
    p.set_defaults(func=cmd_session_frontier_add)

    p = ss_sub.add_parser("frontier-remove", help="Remove from expansion frontier")
    _add_wiki_flag(p)
    p.add_argument("slug")
    p.set_defaults(func=cmd_session_frontier_remove)

    # --- sync ---
    p = sub.add_parser("sync", help="Full integrity sync")
    _add_wiki_flag(p)
    p.set_defaults(func=cmd_sync)

    # --- reaction ---
    rx = sub.add_parser("reaction", help="Cross-wiki reaction operations")
    rx_sub = rx.add_subparsers(dest="action", required=True)

    p = rx_sub.add_parser("add-affinity", help="Add pending affinity")
    p.add_argument("--wiki-a", required=True)
    p.add_argument("--article-a", required=True)
    p.add_argument("--wiki-b", required=True)
    p.add_argument("--article-b", required=True)
    p.add_argument("--score", type=float, required=True)
    p.add_argument("--type", required=True)
    p.add_argument("--rationale", required=True)
    p.set_defaults(func=cmd_reaction_add_affinity)

    p = rx_sub.add_parser("create", help="Register a completed reaction")
    p.add_argument("--type", required=True)
    p.add_argument("--reagent-a", required=True, help="wiki:slug")
    p.add_argument("--reagent-b", required=True, help="wiki:slug")
    p.add_argument("--product-wiki", required=True)
    p.add_argument("--product-slug", required=True)
    p.add_argument("--product-title", required=True)
    p.add_argument("--catalyst", required=True)
    p.add_argument("--score", type=float, required=True)
    p.set_defaults(func=cmd_reaction_create)

    p = rx_sub.add_parser("should-react", help="Check if auto-react conditions are met")
    p.add_argument("--threshold", type=int, default=5, help="New articles threshold (default: 5)")
    p.set_defaults(func=cmd_reaction_should_react)

    p = rx_sub.add_parser("mark-reacted", help="Record current state as last react checkpoint")
    p.set_defaults(func=cmd_reaction_mark_reacted)

    p = rx_sub.add_parser("list", help="List all reactions")
    p.set_defaults(func=cmd_reaction_list)

    p = rx_sub.add_parser("get", help="Get a reaction by ID")
    p.add_argument("reaction_id")
    p.set_defaults(func=cmd_reaction_get)

    # --- portal ---
    p = sub.add_parser("portal", help="Portal operations")
    p_sub = p.add_subparsers(dest="action", required=True)

    p2 = p_sub.add_parser("rebuild", help="Rebuild cross-graph and portal")
    p2.set_defaults(func=cmd_portal_rebuild)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except (ValueError, FileNotFoundError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Auto-Wiki JSON database CLI.

Usage:
    awiki article add --slug S --title T --filename F --summary S [--links-to L1,L2] [--origin O] [--source-id ID]
    awiki article get SLUG
    awiki article list
    awiki article exists SLUG
    awiki article update SLUG --field value ...
    awiki article set-links SLUG --links L1,L2
    awiki article rebuild-linked-from
    awiki graph rebuild
    awiki brainstorm add --slug S --title T --source-id ID --rationale R --score 0.8
    awiki brainstorm add-batch --json '[...]'
    awiki brainstorm pop [--n N] [--min-score 0.5]
    awiki brainstorm cleanup [--max-history 100]
    awiki brainstorm list
    awiki session get
    awiki session update [--phase P] [--setting key=value ...]
    awiki session frontier-add SLUG
    awiki session frontier-remove SLUG
    awiki sync
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


# ---------------------------------------------------------------------------
# article subcommands
# ---------------------------------------------------------------------------

def cmd_article_add(args):
    result = db.article_add(
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
    result = db.article_get(args.slug)
    if result is None:
        print(f"Article '{args.slug}' not found", file=sys.stderr)
        sys.exit(1)
    _print_json(result)


def cmd_article_list(args):
    _print_json(db.article_list())


def cmd_article_exists(args):
    exists = db.article_exists(args.slug)
    print(json.dumps({"exists": exists}))
    sys.exit(0 if exists else 1)


def cmd_article_update(args):
    fields = {}
    if args.title:
        fields["title"] = args.title
    if args.summary:
        fields["summary"] = args.summary
    if args.expansion_status:
        fields["expansion_status"] = args.expansion_status
    if args.links_to is not None:
        fields["links_to"] = _parse_list(args.links_to)
    result = db.article_update(args.slug, **fields)
    _print_json(result)


def cmd_article_set_links(args):
    result = db.article_set_links(args.slug, _parse_list(args.links))
    _print_json(result)


def cmd_article_rebuild_linked_from(args):
    count = db.articles_rebuild_linked_from()
    print(json.dumps({"updated_articles": count}))


# ---------------------------------------------------------------------------
# graph subcommands
# ---------------------------------------------------------------------------

def cmd_graph_rebuild(args):
    result = db.graph_rebuild()
    _print_json(result)


# ---------------------------------------------------------------------------
# brainstorm subcommands
# ---------------------------------------------------------------------------

def cmd_brainstorm_add(args):
    result = db.brainstorm_add(
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
    candidates = json.loads(args.json)
    result = db.brainstorm_add_batch(candidates)
    _print_json(result)


def cmd_brainstorm_pop(args):
    result = db.brainstorm_pop(n=args.n, min_score=args.min_score)
    _print_json(result)


def cmd_brainstorm_cleanup(args):
    removed = db.brainstorm_cleanup(max_history=args.max_history)
    print(json.dumps({"removed": removed}))


def cmd_brainstorm_list(args):
    _print_json(db.brainstorm_list())


# ---------------------------------------------------------------------------
# session subcommands
# ---------------------------------------------------------------------------

def cmd_session_get(args):
    _print_json(db.session_get())


def cmd_session_update(args):
    settings = {}
    if args.setting:
        for s in args.setting:
            k, v = s.split("=", 1)
            # Try to parse as int/float/bool
            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    if v.lower() in ("true", "false"):
                        v = v.lower() == "true"
            settings[k] = v
    result = db.session_update(last_phase=args.phase, **settings)
    _print_json(result)


def cmd_session_frontier_add(args):
    result = db.session_frontier_add(args.slug)
    _print_json(result)


def cmd_session_frontier_remove(args):
    result = db.session_frontier_remove(args.slug)
    _print_json(result)


# ---------------------------------------------------------------------------
# sync
# ---------------------------------------------------------------------------

def cmd_sync(args):
    result = db.sync_all()
    _print_json(result)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="awiki", description="Auto-Wiki JSON DB CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # --- article ---
    art = sub.add_parser("article", help="Article operations")
    art_sub = art.add_subparsers(dest="action", required=True)

    p = art_sub.add_parser("add", help="Add a new article")
    p.add_argument("--slug", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--filename", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--links-to", default="")
    p.add_argument("--origin", default="root")
    p.add_argument("--source-id", default=None)
    p.set_defaults(func=cmd_article_add)

    p = art_sub.add_parser("get", help="Get article by slug")
    p.add_argument("slug")
    p.set_defaults(func=cmd_article_get)

    p = art_sub.add_parser("list", help="List all articles")
    p.set_defaults(func=cmd_article_list)

    p = art_sub.add_parser("exists", help="Check if article exists")
    p.add_argument("slug")
    p.set_defaults(func=cmd_article_exists)

    p = art_sub.add_parser("update", help="Update article fields")
    p.add_argument("slug")
    p.add_argument("--title", default=None)
    p.add_argument("--summary", default=None)
    p.add_argument("--expansion-status", default=None)
    p.add_argument("--links-to", default=None)
    p.set_defaults(func=cmd_article_update)

    p = art_sub.add_parser("set-links", help="Set links and sync linked_from")
    p.add_argument("slug")
    p.add_argument("--links", required=True)
    p.set_defaults(func=cmd_article_set_links)

    p = art_sub.add_parser("rebuild-linked-from", help="Rebuild all linked_from")
    p.set_defaults(func=cmd_article_rebuild_linked_from)

    # --- graph ---
    gr = sub.add_parser("graph", help="Graph operations")
    gr_sub = gr.add_subparsers(dest="action", required=True)

    p = gr_sub.add_parser("rebuild", help="Rebuild graph.json from articles.json")
    p.set_defaults(func=cmd_graph_rebuild)

    # --- brainstorm ---
    bs = sub.add_parser("brainstorm", help="Brainstorm operations")
    bs_sub = bs.add_subparsers(dest="action", required=True)

    p = bs_sub.add_parser("add", help="Add a candidate")
    p.add_argument("--slug", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--rationale", required=True)
    p.add_argument("--score", type=float, required=True)
    p.set_defaults(func=cmd_brainstorm_add)

    p = bs_sub.add_parser("add-batch", help="Add candidates from JSON")
    p.add_argument("--json", required=True)
    p.set_defaults(func=cmd_brainstorm_add_batch)

    p = bs_sub.add_parser("pop", help="Pop top N candidates")
    p.add_argument("--n", type=int, default=1)
    p.add_argument("--min-score", type=float, default=0.5)
    p.set_defaults(func=cmd_brainstorm_pop)

    p = bs_sub.add_parser("cleanup", help="Cleanup brainstorm queue")
    p.add_argument("--max-history", type=int, default=100)
    p.set_defaults(func=cmd_brainstorm_cleanup)

    p = bs_sub.add_parser("list", help="List brainstorm queue")
    p.set_defaults(func=cmd_brainstorm_list)

    # --- session ---
    ss = sub.add_parser("session", help="Session operations")
    ss_sub = ss.add_subparsers(dest="action", required=True)

    p = ss_sub.add_parser("get", help="Get session state")
    p.set_defaults(func=cmd_session_get)

    p = ss_sub.add_parser("update", help="Update session state")
    p.add_argument("--phase", default=None)
    p.add_argument("--setting", action="append", help="key=value pairs")
    p.set_defaults(func=cmd_session_update)

    p = ss_sub.add_parser("frontier-add", help="Add to expansion frontier")
    p.add_argument("slug")
    p.set_defaults(func=cmd_session_frontier_add)

    p = ss_sub.add_parser("frontier-remove", help="Remove from expansion frontier")
    p.add_argument("slug")
    p.set_defaults(func=cmd_session_frontier_remove)

    # --- sync ---
    p = sub.add_parser("sync", help="Full integrity sync")
    p.set_defaults(func=cmd_sync)

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

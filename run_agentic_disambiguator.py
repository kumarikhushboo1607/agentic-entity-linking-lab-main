from __future__ import annotations

import argparse
import json

import anyio

from wikidata_lab.agentic_disambiguator import (
    build_lexical_candidate_shortlist,
    detect_claude_cli_path,
    disambiguate_with_claude_code,
)
from wikidata_lab.wikidata import (
    DEFAULT_BOOTSTRAP_QUERY_PATH,
    fetch_knowledge_base_from_query,
    load_sparql_query,
)


async def _run(args: argparse.Namespace) -> None:
    query = load_sparql_query(args.query_path)
    _, knowledge_base = fetch_knowledge_base_from_query(query)

    candidates = build_lexical_candidate_shortlist(
        args.mention,
        knowledge_base,
        top_k=args.top_k,
    )
    if not candidates:
        raise SystemExit(f"No lexical candidates found for mention: {args.mention!r}")

    result = await disambiguate_with_claude_code(
        full_text=args.text,
        mention_text=args.mention,
        start=args.start,
        end=args.end if args.end is not None else args.start + len(args.mention),
        candidates=candidates,
        model=args.model,
        cli_path=detect_claude_cli_path(),
    )
    print(json.dumps(result.__dict__, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a local agentic disambiguation demo.")
    parser.add_argument("--mention", default="Martin", help="Mention text to disambiguate.")
    parser.add_argument(
        "--text",
        default="Martin said the government would bring the bill to the Dail next week.",
        help="Full text containing the mention.",
    )
    parser.add_argument("--start", type=int, default=0, help="Mention start offset in the text.")
    parser.add_argument("--end", type=int, default=None, help="Mention end offset in the text.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of lexical candidates to send to the agent.")
    parser.add_argument("--model", default="haiku", help="Claude Code model alias, for example haiku, sonnet, or opus.")
    parser.add_argument(
        "--query-path",
        default=str(DEFAULT_BOOTSTRAP_QUERY_PATH),
        help="Path to a .sparql query file.",
    )
    args = parser.parse_args()
    anyio.run(_run, args)


if __name__ == "__main__":
    main()

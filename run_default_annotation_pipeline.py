from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from wikidata_lab.wikidata import (
    DEFAULT_BOOTSTRAP_QUERY_PATH,
    annotate_text,
    build_surface_form_index,
    fetch_knowledge_base_from_query,
    load_sparql_query,
)


def read_input_text(path: str | None, use_stdin: bool) -> str:
    if use_stdin:
        return sys.stdin.read()
    if path is None:
        raise SystemExit("Provide --input-file PATH or use --stdin.")
    return Path(path).read_text(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the default Wikidata bootstrap pipeline on a text file or stdin.")
    parser.add_argument("--input-file", help="Path to a UTF-8 text file to annotate.")
    parser.add_argument("--stdin", action="store_true", help="Read input text from stdin.")
    parser.add_argument(
        "--query-path",
        default=str(DEFAULT_BOOTSTRAP_QUERY_PATH),
        help="Path to the .sparql bootstrap query file.",
    )
    args = parser.parse_args()

    input_text = read_input_text(args.input_file, args.stdin)
    query = load_sparql_query(args.query_path)
    _, knowledge_base = fetch_knowledge_base_from_query(query)
    surface_form_index = build_surface_form_index(knowledge_base)
    annotations = annotate_text(input_text, surface_form_index)
    print(json.dumps(annotations, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

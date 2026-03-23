from __future__ import annotations

import argparse
import json

from wikidata_lab.candidate_retrieval import SimpleVectorStoreTemplate
from wikidata_lab.sentence_transformer_embeddings import SentenceTransformerEmbeddingProvider
from wikidata_lab.wikidata import (
    DEFAULT_BOOTSTRAP_QUERY_PATH,
    fetch_knowledge_base_from_query,
    load_sparql_query,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run sentence-transformer candidate retrieval against the default Wikidata KB.")
    parser.add_argument("--mention", default="Simon Harris", help="Mention text to retrieve candidates for.")
    parser.add_argument("--top-k", type=int, default=5, help="How many candidates to print.")
    parser.add_argument(
        "--query-path",
        default=str(DEFAULT_BOOTSTRAP_QUERY_PATH),
        help="Path to a .sparql query file.",
    )
    args = parser.parse_args()

    query = load_sparql_query(args.query_path)
    _, knowledge_base = fetch_knowledge_base_from_query(query)

    provider = SentenceTransformerEmbeddingProvider()
    store = SimpleVectorStoreTemplate(provider)
    store.index_entities(knowledge_base)
    candidates = store.retrieve(args.mention, top_k=args.top_k)

    print(json.dumps([candidate.__dict__ for candidate in candidates], indent=2))


if __name__ == "__main__":
    main()

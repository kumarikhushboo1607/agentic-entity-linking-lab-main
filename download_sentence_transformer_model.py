from __future__ import annotations

import json

from wikidata_lab.sentence_transformer_embeddings import download_sentence_transformer_model


def main() -> None:
    result = download_sentence_transformer_model()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

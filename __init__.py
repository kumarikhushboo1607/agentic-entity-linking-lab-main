"""Educational helpers for a Wikidata-backed entity linking lab."""

from .agentic_disambiguator import (
    AgenticDisambiguationResult,
    build_lexical_candidate_shortlist,
    detect_claude_cli_path,
    disambiguate_with_claude_code,
    parse_agentic_json_response,
)
from .agentic_linking import (
    AgenticLinkerTemplate,
    extract_context_window,
)
from .candidate_retrieval import EntityCandidate, SimpleVectorStoreTemplate
from .sentence_transformer_embeddings import (
    DEFAULT_SENTENCE_TRANSFORMER_CACHE_DIR,
    DEFAULT_SENTENCE_TRANSFORMER_MODEL,
    SentenceTransformerEmbeddingProvider,
    download_sentence_transformer_model,
)
from .wikidata import (
    DEFAULT_BOOTSTRAP_QUERY_PATH,
    DEFAULT_WIKIDATA_ENDPOINT,
    QUERIES_DIR,
    annotate_text,
    build_knowledge_base,
    build_surface_form_index,
    execute_sparql_query,
    fetch_default_bootstrap_knowledge_base,
    fetch_knowledge_base_from_query,
    load_sparql_query,
    normalize_surface_form,
)

__all__ = [
    "AgenticDisambiguationResult",
    "AgenticLinkerTemplate",
    "DEFAULT_BOOTSTRAP_QUERY_PATH",
    "DEFAULT_SENTENCE_TRANSFORMER_CACHE_DIR",
    "DEFAULT_SENTENCE_TRANSFORMER_MODEL",
    "DEFAULT_WIKIDATA_ENDPOINT",
    "EntityCandidate",
    "QUERIES_DIR",
    "SentenceTransformerEmbeddingProvider",
    "SimpleVectorStoreTemplate",
    "annotate_text",
    "build_lexical_candidate_shortlist",
    "build_knowledge_base",
    "build_surface_form_index",
    "detect_claude_cli_path",
    "disambiguate_with_claude_code",
    "download_sentence_transformer_model",
    "execute_sparql_query",
    "extract_context_window",
    "fetch_default_bootstrap_knowledge_base",
    "fetch_knowledge_base_from_query",
    "load_sparql_query",
    "normalize_surface_form",
    "parse_agentic_json_response",
]

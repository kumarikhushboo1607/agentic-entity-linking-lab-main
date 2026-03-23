"""Simple, explicit Wikidata bootstrapping utilities for entity linking labs."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
DEFAULT_USER_AGENT = "agentic-entity-linking-lab/0.1 (educational notebook)"
PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
QUERIES_DIR = PROJECT_ROOT / "queries"
DEFAULT_BOOTSTRAP_QUERY_PATH = QUERIES_DIR / "current_living_irish_office_holders.sparql"


def load_sparql_query(query_path: str | Path = DEFAULT_BOOTSTRAP_QUERY_PATH) -> str:
    """Load SPARQL query text from a version-controlled .sparql file."""
    return Path(query_path).read_text(encoding="utf-8").strip()


def execute_sparql_query(
    query: str,
    endpoint: str = DEFAULT_WIKIDATA_ENDPOINT,
    *,
    user_agent: str = DEFAULT_USER_AGENT,
    timeout: int = 60,
) -> list[dict[str, str]]:
    """Run a SPARQL query and return a simple row-oriented result set."""
    url = endpoint + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/sparql-results+json",
            "User-Agent": user_agent,
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)

    rows: list[dict[str, str]] = []
    for binding in payload["results"]["bindings"]:
        row = {}
        for variable, value in binding.items():
            row[variable] = value.get("value", "")
        rows.append(row)
    return rows


def fetch_knowledge_base_from_query(
    query: str,
    *,
    endpoint: str = DEFAULT_WIKIDATA_ENDPOINT,
    timeout: int = 60,
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    """Execute a SPARQL query and convert the rows into the local KB format."""
    rows = execute_sparql_query(query, endpoint=endpoint, timeout=timeout)
    return rows, build_knowledge_base(rows)


def build_knowledge_base(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Collapse raw query rows into explicit entity records."""
    entities_by_uri: dict[str, dict[str, Any]] = {}

    for row in rows:
        uri = row["person"]
        label = row["personLabel"]
        office = row.get("officeLabel", "")

        entity = entities_by_uri.setdefault(
            uri,
            {
                "uri": uri,
                "label": label,
                "surface_forms": [label],
                "current_offices": [],
                "metadata": {
                    "wikidata_id": uri.rsplit("/", 1)[-1],
                },
            },
        )

        if office and office not in entity["current_offices"]:
            entity["current_offices"].append(office)

    return sorted(entities_by_uri.values(), key=lambda entity: entity["label"].lower())


def fetch_default_bootstrap_knowledge_base(
    *,
    endpoint: str = DEFAULT_WIKIDATA_ENDPOINT,
    query_path: str | Path = DEFAULT_BOOTSTRAP_QUERY_PATH,
    timeout: int = 60,
) -> tuple[str, list[dict[str, str]], list[dict[str, Any]]]:
    """Fetch the default educational KB bootstrap from a named .sparql file."""
    query = load_sparql_query(query_path)
    rows, knowledge_base = fetch_knowledge_base_from_query(
        query,
        endpoint=endpoint,
        timeout=timeout,
    )
    return query, rows, knowledge_base


def normalize_surface_form(text: str) -> str:
    """Normalize text for dictionary lookups."""
    collapsed = re.sub(r"\s+", " ", text.strip())
    return collapsed.casefold()


def build_surface_form_index(
    entities: list[dict[str, Any]],
    *,
    extra_surface_forms_by_uri: dict[str, list[str]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Build an explicit surface-form index from the KB entities."""
    index: dict[str, list[dict[str, Any]]] = {}
    extra_surface_forms_by_uri = extra_surface_forms_by_uri or {}

    for entity in entities:
        all_forms = list(entity.get("surface_forms", []))
        all_forms.extend(extra_surface_forms_by_uri.get(entity["uri"], []))

        deduped_forms = []
        seen = set()
        for form in all_forms:
            form = re.sub(r"\s+", " ", form.strip())
            if not form:
                continue
            normalized = normalize_surface_form(form)
            if normalized in seen:
                continue
            seen.add(normalized)
            deduped_forms.append(form)

        entity["surface_forms"] = deduped_forms

        for form in deduped_forms:
            normalized = normalize_surface_form(form)
            bucket = index.setdefault(normalized, [])
            if not any(existing["uri"] == entity["uri"] for existing in bucket):
                bucket.append(entity)

    return index


def _surface_form_pattern(surface_form: str) -> re.Pattern[str]:
    parts = [re.escape(part) for part in surface_form.split()]
    body = r"\s+".join(parts)
    return re.compile(rf"(?<!\w){body}(?!\w)", flags=re.IGNORECASE)


def annotate_text(
    text: str,
    surface_form_index: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Annotate spans via explicit string matching against the surface-form index."""
    candidates: list[dict[str, Any]] = []
    occupied_spans: list[tuple[int, int]] = []

    for normalized_surface_form, entities in sorted(
        surface_form_index.items(),
        key=lambda item: (-len(item[0]), item[0]),
    ):
        pattern = _surface_form_pattern(entities[0]["surface_forms"][0] if len(entities) == 1 else normalized_surface_form)
        literal_pattern = _surface_form_pattern(normalized_surface_form)
        patterns = [literal_pattern]

        literal_forms = []
        for entity in entities:
            for form in entity["surface_forms"]:
                if normalize_surface_form(form) == normalized_surface_form:
                    literal_forms.append(form)

        if literal_forms:
            patterns = [_surface_form_pattern(form) for form in sorted(set(literal_forms), key=len, reverse=True)]
        else:
            patterns = [pattern]

        for compiled in patterns:
            for match in compiled.finditer(text):
                start, end = match.span()
                if any(not (end <= left or start >= right) for left, right in occupied_spans):
                    continue

                unique_uri = entities[0]["uri"] if len(entities) == 1 else None
                candidates.append(
                    {
                        "start": start,
                        "end": end,
                        "text": match.group(0),
                        "normalized_surface_form": normalized_surface_form,
                        "uri": unique_uri,
                        "candidate_uris": [entity["uri"] for entity in entities],
                        "candidate_labels": [entity["label"] for entity in entities],
                    }
                )
                occupied_spans.append((start, end))

    return sorted(candidates, key=lambda item: (item["start"], item["end"]))

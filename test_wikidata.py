from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from wikidata_lab.agentic_disambiguator import (
    build_lexical_candidate_shortlist,
    parse_agentic_json_response,
)
from wikidata_lab.agentic_linking import AgenticLinkerTemplate
from wikidata_lab.candidate_retrieval import EntityCandidate, SimpleVectorStoreTemplate
from wikidata_lab.wikidata import (
    DEFAULT_BOOTSTRAP_QUERY_PATH,
    annotate_text,
    build_knowledge_base,
    build_surface_form_index,
    load_sparql_query,
    normalize_surface_form,
)


class StubEmbeddingProvider:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        lookup = {
            "mary lou mcdonald": [1.0, 0.0],
            "micheal martin": [0.0, 1.0],
            "mary lou": [0.9, 0.1],
        }
        return [lookup[text.casefold()] for text in texts]


class WikidataHelpersTest(unittest.TestCase):
    def test_default_query_file_includes_live_office_filters(self) -> None:
        self.assertTrue(DEFAULT_BOOTSTRAP_QUERY_PATH.exists())
        query = load_sparql_query(DEFAULT_BOOTSTRAP_QUERY_PATH)
        self.assertIn("FILTER NOT EXISTS { ?positionStatement pq:P582 ?endTime }", query)
        self.assertIn("FILTER EXISTS { ?office (wdt:P17|wdt:P1001) wd:Q27 }", query)
        self.assertIn("ORDER BY ?personLabel", query)

    def test_build_knowledge_base_groups_duplicate_people(self) -> None:
        rows = [
            {
                "person": "http://www.wikidata.org/entity/Q1",
                "personLabel": "Mary Lou McDonald",
                "officeLabel": "Teachta Dala",
            },
            {
                "person": "http://www.wikidata.org/entity/Q1",
                "personLabel": "Mary Lou McDonald",
                "officeLabel": "Leader of Sinn Fein",
            },
            {
                "person": "http://www.wikidata.org/entity/Q2",
                "personLabel": "Micheal Martin",
                "officeLabel": "Taoiseach",
            },
        ]
        kb = build_knowledge_base(rows)
        self.assertEqual(len(kb), 2)
        self.assertEqual(kb[0]["label"], "Mary Lou McDonald")
        self.assertEqual(
            kb[0]["current_offices"],
            ["Teachta Dala", "Leader of Sinn Fein"],
        )

    def test_surface_form_index_accepts_explicit_aliases(self) -> None:
        entities = [
            {
                "uri": "http://www.wikidata.org/entity/Q1",
                "label": "Mary Lou McDonald",
                "surface_forms": ["Mary Lou McDonald"],
                "current_offices": ["Teachta Dala"],
                "metadata": {},
            }
        ]
        index = build_surface_form_index(
            entities,
            extra_surface_forms_by_uri={
                "http://www.wikidata.org/entity/Q1": ["Mary Lou", " MARY LOU "],
            },
        )
        self.assertIn("mary lou mcdonald", index)
        self.assertIn("mary lou", index)
        self.assertEqual(len(index["mary lou"]), 1)

    def test_annotate_text_prefers_longer_matches(self) -> None:
        entities = [
            {
                "uri": "http://www.wikidata.org/entity/Q1",
                "label": "Mary Lou McDonald",
                "surface_forms": ["Mary Lou McDonald", "Mary Lou"],
                "current_offices": ["Teachta Dala"],
                "metadata": {},
            }
        ]
        index = build_surface_form_index(entities)
        annotations = annotate_text("Mary Lou McDonald spoke today.", index)
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0]["text"], "Mary Lou McDonald")
        self.assertEqual(annotations[0]["uri"], "http://www.wikidata.org/entity/Q1")

    def test_annotate_text_returns_candidate_list_for_ambiguity(self) -> None:
        entities = [
            {
                "uri": "http://www.wikidata.org/entity/Q1",
                "label": "John Smith A",
                "surface_forms": ["John Smith"],
                "current_offices": [],
                "metadata": {},
            },
            {
                "uri": "http://www.wikidata.org/entity/Q2",
                "label": "John Smith B",
                "surface_forms": ["John Smith"],
                "current_offices": [],
                "metadata": {},
            },
        ]
        index = build_surface_form_index(entities)
        annotations = annotate_text("John Smith voted yes.", index)
        self.assertEqual(len(annotations), 1)
        self.assertIsNone(annotations[0]["uri"])
        self.assertEqual(
            annotations[0]["candidate_uris"],
            ["http://www.wikidata.org/entity/Q1", "http://www.wikidata.org/entity/Q2"],
        )

    def test_normalize_surface_form(self) -> None:
        self.assertEqual(normalize_surface_form("  Mary   Lou "), "mary lou")


class ExtensionTemplatesTest(unittest.TestCase):
    def test_vector_store_template_retrieves_expected_candidate(self) -> None:
        store = SimpleVectorStoreTemplate(StubEmbeddingProvider())
        store.index_entities(
            [
                {
                    "uri": "http://www.wikidata.org/entity/Q1",
                    "label": "Mary Lou McDonald",
                    "current_offices": ["Teachta Dala"],
                    "metadata": {"wikidata_id": "Q1"},
                },
                {
                    "uri": "http://www.wikidata.org/entity/Q2",
                    "label": "Micheal Martin",
                    "current_offices": ["Taoiseach"],
                    "metadata": {"wikidata_id": "Q2"},
                },
            ]
        )
        candidates = store.retrieve("Mary Lou", top_k=1)
        self.assertEqual(candidates[0].uri, "http://www.wikidata.org/entity/Q1")

    def test_agentic_prompt_contains_context_and_candidates(self) -> None:
        agent = AgenticLinkerTemplate()
        prompt = agent.build_prompt(
            full_text="Mary Lou McDonald addressed the Dail.",
            mention_text="Mary Lou McDonald",
            start=0,
            end=17,
            candidates=[
                EntityCandidate(
                    uri="http://www.wikidata.org/entity/Q1",
                    label="Mary Lou McDonald",
                    score=0.99,
                    metadata={"current_offices": ["Teachta Dala"]},
                )
            ],
        )
        self.assertIn("Context:", prompt)
        self.assertIn("Mary Lou McDonald", prompt)
        self.assertIn("http://www.wikidata.org/entity/Q1", prompt)

    def test_lexical_candidate_shortlist_prefers_overlap(self) -> None:
        candidates = build_lexical_candidate_shortlist(
            "Martin",
            [
                {
                    "uri": "http://www.wikidata.org/entity/Q1",
                    "label": "Micheal Martin",
                    "current_offices": ["Taoiseach"],
                    "metadata": {"wikidata_id": "Q1"},
                },
                {
                    "uri": "http://www.wikidata.org/entity/Q2",
                    "label": "Simon Harris",
                    "current_offices": ["Tanaiste"],
                    "metadata": {"wikidata_id": "Q2"},
                },
            ],
            top_k=2,
        )
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].label, "Micheal Martin")

    def test_parse_agentic_json_response_accepts_fenced_json(self) -> None:
        parsed = parse_agentic_json_response(
            """```json
{"chosen_uri":"http://www.wikidata.org/entity/Q1","confidence":"high"}
```"""
        )
        self.assertEqual(parsed["chosen_uri"], "http://www.wikidata.org/entity/Q1")
        self.assertEqual(parsed["confidence"], "high")


if __name__ == "__main__":
    unittest.main()

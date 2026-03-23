from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from urllib.error import URLError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from wikidata_lab.wikidata import fetch_default_bootstrap_knowledge_base
from wikidata_lab.wikidata import annotate_text, build_surface_form_index


@unittest.skipUnless(
    os.environ.get("LIVE_WIKIDATA_TESTS") == "1",
    "Set LIVE_WIKIDATA_TESTS=1 to run live Wikidata integration tests.",
)
class LiveWikidataQueryTest(unittest.TestCase):
    def test_live_query_returns_rows(self) -> None:
        try:
            _, rows, kb = fetch_default_bootstrap_knowledge_base(timeout=60)
        except URLError as exc:
            self.skipTest(f"Live network unavailable: {exc}")

        self.assertGreaterEqual(len(rows), 5)
        self.assertGreaterEqual(len(kb), 5)

        for entity in kb[:5]:
            self.assertTrue(entity["uri"].startswith("http://www.wikidata.org/entity/Q"))
            self.assertTrue(entity["label"])
            self.assertGreaterEqual(len(entity["surface_forms"]), 1)

    def test_example_document_annotates_against_live_kb(self) -> None:
        try:
            _, _, kb = fetch_default_bootstrap_knowledge_base(timeout=60)
        except URLError as exc:
            self.skipTest(f"Live network unavailable: {exc}")

        example_path = PROJECT_ROOT / "data" / "example_current_irish_office_holders.txt"
        text = example_path.read_text(encoding="utf-8")
        surface_form_index = build_surface_form_index(kb)
        annotations = annotate_text(text, surface_form_index)

        self.assertGreaterEqual(len(annotations), 4)
        self.assertEqual(annotations[0]["text"], "Aengus Ó Snodaigh")


if __name__ == "__main__":
    unittest.main()

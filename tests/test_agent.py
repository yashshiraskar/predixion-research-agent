
import unittest

from agent import run_research
from schemas import validate_report


class TestResearchAgent(unittest.TestCase):

    def test_empty_question_fails_before_api_call(self):
        with self.assertRaises(ValueError):
            run_research("")

    def test_accepts_retrieved_source(self):
        evidence = [{
            "title": "Qdrant Vector Search",
            "url": "https://example.com/qdrant",
            "domain": "example.com",
            "content": (
                "Qdrant is a vector database that supports "
                "vector search and metadata filtering."
            ),
        }]

        data = {
            "short_answer": "Qdrant supports vector search.",
            "key_findings": [{
                "claim": "Qdrant supports vector search.",
                "source_urls": [
                    "https://example.com/qdrant"
                ],
            }],
            "sources_used": [],
            "limitations_or_assumptions": [],
            "suggested_next_steps": [],
        }

        report = validate_report(data, evidence)

        self.assertEqual(len(report["key_findings"]), 1)
        self.assertEqual(len(report["sources_used"]), 1)
        self.assertEqual(
            report["sources_used"][0]["url"],
            "https://example.com/qdrant",
        )

    def test_rejects_localhost_urls(self):
        evidence = [{
            "title": "Local page",
            "url": "http://localhost:8000/test",
            "content": "Qdrant supports vector search.",
        }]

        data = {
            "short_answer": "Test",
            "key_findings": [{
                "claim": "Qdrant supports vector search.",
                "source_urls": [
                    "http://localhost:8000/test"
                ],
            }],
            "sources_used": [],
        }

        report = validate_report(data, evidence)

        self.assertEqual(report["key_findings"], [])
        self.assertEqual(report["sources_used"], [])
        self.assertEqual(report["confidence"], "Low")

    def test_rejects_unretrieved_sources(self):
        evidence = [{
            "title": "Retrieved page",
            "url": "https://example.com/real",
            "content": "Qdrant supports vector search.",
        }]

        data = {
            "short_answer": "Test",
            "key_findings": [{
                "claim": "Qdrant supports vector search.",
                "source_urls": [
                    "https://fake-example.com/fake"
                ],
            }],
            "sources_used": [],
        }

        report = validate_report(data, evidence)

        self.assertEqual(report["key_findings"], [])
        self.assertEqual(report["sources_used"], [])

    def test_unlinked_finding_lowers_confidence(self):
        evidence = [{
            "title": "Database information",
            "url": "https://example.com/database",
            "content": "Qdrant supports vector search.",
        }]

        data = {
            "short_answer": "Database information",
            "key_findings": [{
                "claim": "Qdrant supports vector search.",
                "source_urls": [],
            }],
            "sources_used": [],
            "limitations_or_assumptions": [],
            "suggested_next_steps": [],
        }

        report = validate_report(data, evidence)

        self.assertEqual(report["confidence"], "Low")
        self.assertEqual(report["key_findings"], [])


if __name__ == "__main__":
    unittest.main()
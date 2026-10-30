
import unittest
from unittest.mock import patch

from schemas import validate_report


class EvidenceValidationTests(unittest.TestCase):

    def setUp(self):
        self.url1 = "https://docs.example.com/database"
        self.url2 = "https://guide.example.org/database"

        self.evidence = [
            {
                "title": "Database consistency documentation",
                "url": self.url1,
                "content": (
                    "The database provides strong consistency for reads "
                    "and writes. Transactions support consistent data "
                    "operations across multiple records."
                ),
                "official_source": True,
            },
            {
                "title": "Database transaction guide",
                "url": self.url2,
                "content": (
                    "Database transactions provide atomic operations. "
                    "Applications can use transactions to maintain "
                    "consistent records during concurrent updates."
                ),
                "official_source": False,
            },
        ]

        # Mock URL safety validation for placeholder example domains.
        # Real URL validation remains active in the application.
        self.url_validation_patcher = patch(
            "schemas._is_public_http_url",
            return_value=True,
        )
        self.url_validation_patcher.start()

    def tearDown(self):
        self.url_validation_patcher.stop()

    def make_report(self, claim, urls, confidence="High"):
        return {
            "short_answer": "Database consistency depends on its design.",
            "key_findings": [
                {"claim": claim, "source_urls": urls}
            ],
            "sources_used": [
                {"title": "Model supplied title", "url": url}
                for url in urls
            ],
            "confidence": confidence,
            "limitations_or_assumptions": [],
            "suggested_next_steps": [],
        }

    def test_rejects_unretrieved_url(self):
        report = validate_report(
            self.make_report(
                "Database provides strong consistency for reads.",
                ["https://fake.example/page"],
            ),
            self.evidence,
        )
        self.assertEqual(report["key_findings"], [])
        self.assertEqual(report["sources_used"], [])
        self.assertEqual(report["confidence"], "Low")

    def test_rejects_irrelevant_citation(self):
        report = validate_report(
            self.make_report(
                "The product supports advanced image recognition.",
                [self.url1],
            ),
            self.evidence,
        )
        self.assertEqual(report["key_findings"], [])
        self.assertEqual(report["confidence"], "Low")

    def test_keeps_relevant_citation(self):
        report = validate_report(
            self.make_report(
                "The database provides strong consistency for reads and writes.",
                [self.url1],
                "Medium",
            ),
            self.evidence,
        )
        self.assertEqual(len(report["key_findings"]), 1)
        self.assertEqual(
            report["key_findings"][0]["source_urls"],
            [self.url1],
        )

    def test_sources_only_include_cited_pages(self):
        report = validate_report(
            self.make_report(
                "The database provides strong consistency for reads and writes.",
                [self.url1],
            ),
            self.evidence,
        )
        self.assertEqual(
            [source["url"] for source in report["sources_used"]],
            [self.url1],
        )

    def test_unlinked_finding_lowers_confidence(self):
        report = validate_report(
            self.make_report(
                "The database supports strong consistency.",
                [],
            ),
            self.evidence,
        )
        self.assertEqual(report["confidence"], "Low")

    def test_invalid_evidence_is_ignored(self):
        report = validate_report(
            self.make_report(
                "The database provides strong consistency for reads and writes.",
                [self.url1],
            ),
            [{"url": "file:///etc/passwd", "content": "Some content"}],
        )
        self.assertEqual(report["key_findings"], [])
        self.assertEqual(report["confidence"], "Low")

    def test_malformed_findings_do_not_crash(self):
        report = validate_report(
            {
                "short_answer": "Test",
                "key_findings": "not a list",
                "sources_used": [],
                "confidence": "High",
                "limitations_or_assumptions": [],
                "suggested_next_steps": [],
            },
            self.evidence,
        )
        self.assertEqual(report["key_findings"], [])
        self.assertEqual(report["confidence"], "Low")


if __name__ == "__main__":
    unittest.main()
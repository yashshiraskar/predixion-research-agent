"""Small manual evaluation runner. Run with: python evaluator.py"""
from agent import run_research

TEST_QUERIES = [
    "Compare three open-source vector databases for a small RAG startup.",
    "Find three Indian HR technology B2B SaaS companies and summarize their positioning.",
    "What are the main tradeoffs of a multi-agent customer support system?",
    "Compare common approaches to adding memory to an AI support agent.",
    "Explain the benefits and limitations of using Python for data analysis.",
]

if __name__ == "__main__":
    for index, question in enumerate(TEST_QUERIES, 1):
        print(f"\n{'=' * 80}\nTEST {index}: {question}\n")
        try:
            result = run_research(question, max_sources=4)
            report = result["report"]
            print("Short answer:", report["short_answer"])
            print("Confidence:", report["confidence"])
            print("Sources:", len(report["sources_used"]))
            print("Findings:", len(report["key_findings"]))
            print("Limitations:", report["limitations_or_assumptions"])
        except Exception as exc:
            print("TEST ERROR:", type(exc).__name__, str(exc))

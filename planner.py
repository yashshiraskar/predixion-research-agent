
import json
from config import GROQ_MODEL


def create_plan(client, question: str) -> list[str]:
    """Generate a short research plan with a deterministic fallback."""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        'Return JSON only in the form {"plan":["step 1","step 2"]}. '
                        "Make 3-5 practical research steps. "
                        "Cover the different aspects of the question. "
                        "Do not answer the question yet."
                    ),
                },
                {"role": "user", "content": question},
            ],
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        plan = data.get("plan", [])

        if isinstance(plan, list) and plan:
            cleaned = [
                step.strip()[:300]
                for step in plan
                if isinstance(step, str) and step.strip()
            ]
            if cleaned:
                return cleaned[:5]

    except Exception:
        pass

    return [
        "Identify the main entities and criteria in the question.",
        "Research the key features and technical details.",
        "Investigate performance, costs, and practical considerations.",
        "Compare findings across reliable sources.",
        "Synthesize evidence and disclose gaps or uncertainty.",
    ]


def create_search_queries(client, question: str, plan: list[str]) -> list[str]:
    """
    Generate separate search queries covering the original question
    and each important research-plan aspect.
    """

    fallback_queries = _fallback_search_queries(question, plan)

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        'Return JSON only in this format: {"queries": ["query 1", "query 2"]}. '
                        "Generate 3-6 distinct, focused web search queries. "
                        "The queries together must cover every important aspect "
                        "of the research question and research plan. "
                        "Each query must investigate a different aspect. "
                        "Avoid repeating the same broad question. "
                        "Use concise search-engine-friendly phrases. "
                        "Do not answer the question."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Research question:\n{question}\n\n"
                        f"Research plan:\n{json.dumps(plan, ensure_ascii=False)}"
                    ),
                },
            ],
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        queries = data.get("queries", [])

        if isinstance(queries, list):
            cleaned = []
            for query in queries:
                if isinstance(query, str) and query.strip():
                    query = query.strip()[:300]
                    if query.lower() not in {
                        item.lower() for item in cleaned
                    }:
                        cleaned.append(query)

            if len(cleaned) >= 2:
                return cleaned[:6]

    except Exception:
        pass

    return fallback_queries


def _fallback_search_queries(question: str, plan: list[str]) -> list[str]:
    """Create deterministic queries if model-based query generation fails."""

    queries = [question.strip()[:300]]

    for step in plan:
        if not isinstance(step, str) or not step.strip():
            continue

        query = f"{question.strip()} {step.strip()}"
        query = query[:300]

        if query.lower() not in {item.lower() for item in queries}:
            queries.append(query)

        if len(queries) >= 5:
            break

    return queries
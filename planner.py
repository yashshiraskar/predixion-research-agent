import json

def create_plan(client, question: str) -> list[str]:
    """Ask the model for a short plan; fall back to a deterministic plan on failure."""
    try:
        response = client.chat.completions.create(
            model=__import__("config").GROQ_MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": 'Return JSON only in the form {"plan":["step 1","step 2"]}. Make 3-5 practical research steps. Do not answer the question yet.'
                },
                {"role": "user", "content": question},
            ],
        )
        data = json.loads(response.choices[0].message.content)
        plan = data.get("plan", [])
        if isinstance(plan, list) and plan:
            return [str(step)[:300] for step in plan[:5]]
    except Exception:
        pass
    return [
        "Identify the main entities and criteria in the question.",
        "Search the web for relevant sources.",
        "Read and filter available source pages.",
        "Synthesize evidence and disclose gaps or uncertainty.",
    ]

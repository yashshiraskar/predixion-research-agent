# Predixion AI Research Agent 🔎

**An evidence-grounded AI research assistant built using Python, Groq, DuckDuckGo, and Streamlit.**

## 1. Overview

Predixion AI Research Agent is an AI-powered application that answers complex research questions through structured planning, web search, webpage retrieval, evidence filtering, and LLM-based synthesis.

It generates structured research reports with source citations, confidence levels, limitations, and suggested next steps.

## 2. Key Features

- Research question understanding and planning.
- DuckDuckGo-powered web search.
- Automated webpage reading and content extraction.
- Evidence filtering and relevance scoring.
- Official-source classification.
- Groq-powered research synthesis.
- Citation URL validation.
- Unsupported finding detection.
- Confidence assessment and limitation reporting.
- Structured JSON report generation and download.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend development |
| Streamlit | User interface |
| Groq API | LLM integration |
| DuckDuckGo | Web search |
| Requests | Webpage retrieval |
| BeautifulSoup | HTML extraction |
| Git & GitHub | Version control |

## 4. Architecture

```text
User Research Question
         |
         v
    Streamlit UI
         |
         v
    Research Agent
         |
         v
       Planner
         |
         v
     Tool Selection
         |
         v
      Web Search
         |
         v
   Webpage Reading
         |
         v
  Evidence Filtering
         |
         v
    Groq Synthesis
         |
         v
  Report Validation
         |
         v
   Research Report
```

## 5. Project Structure

```text
predixion-research-agent/
│
├── app.py
├── agent.py
├── planner.py
├── tools.py
├── schemas.py
├── config.py
├── evaluator.py
├── tests/
├── outputs/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 6. Installation and Setup

**Clone the repository:**

```bash
git clone https://github.com/YOUR-USERNAME/predixion-research-agent.git
cd predixion-research-agent
```

**Create and activate a virtual environment:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Install dependencies:**

```bash
pip install -r requirements.txt
```

**Configure environment variables:**

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
```

Never commit your `.env` file or expose your API key.

## 7. Run the Application

```bash
python -m streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## 8. Run Tests

```bash
python -m unittest discover -s tests -v
```

The baseline test suite covers:

- Empty research questions.
- Retrieved URL validation.
- Localhost URL rejection.
- Unretrieved source rejection.
- Missing citation handling.

## 9. Reliability and Evidence Validation

The application incorporates:

- Public HTTP/HTTPS URL validation.
- Private and localhost destination rejection.
- Redirect validation and response-size limits.
- Untrusted webpage content handling.
- Citation URL validation.
- Basic citation relevance checks.
- Unsupported finding warnings.

Evidence filtering uses lightweight heuristics. These checks reduce unsupported claims but do not guarantee factual correctness.

## 10. Design Decisions and Tradeoffs

- **Single-agent architecture:** Keeps orchestration simple and maintainable.
- **Groq:** Provides LLM-powered research synthesis.
- **DuckDuckGo:** Enables web search without a separate search API key.
- **Streamlit:** Provides a lightweight interactive interface.
- **Custom validation:** Gives control over citations, evidence, and report structure.

## 11. Known Limitations

- Search coverage depends on external search results.
- Some webpages may block automated retrieval.
- Lexical relevance does not guarantee semantic support.
- Official-domain classification does not guarantee accuracy.
- Confidence scores are heuristic, not statistical probabilities.
- Production-scale monitoring and cost tracking require further development.

## 12. Future Improvements

- Semantic evidence verification.
- Improved source prioritization and diversity.
- Better research coverage tracking.
- Expanded automated evaluation.
- Logging, latency, and API cost monitoring.
- Improved Streamlit dashboard.
- Caching and asynchronous tool execution.

## 13. Evaluation Plan

The agent will be evaluated using five research scenarios:

1. PostgreSQL vs MongoDB comparison.
2. Open-source vector database comparison.
3. Indian B2B SaaS startup research.
4. Multi-agent vs single-agent architecture research.
5. Research with insufficient available evidence.

Evaluation will consider retrieval quality, citation validity, evidence coverage, unsupported claims, report completeness, and failure handling.

## 14. Final Deliverables

- GitHub source-code repository.
- Project documentation.
- 3–5 minute demonstration video.
- Evaluation report containing five test queries.
- Two or three sample research reports.

---

**Predixion AI Research Agent**

*Research smarter. Retrieve evidence. Generate traceable insights.*
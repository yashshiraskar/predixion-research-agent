# Predixion AI Research Agent 🔎

**An evidence-grounded AI research assistant built using Python, Groq, DuckDuckGo, and Streamlit.**

## 1. Overview

Predixion AI Research Agent is an AI-powered research application that answers complex research questions through structured planning, web search, webpage retrieval, evidence filtering, and LLM-powered synthesis.

Unlike a basic chatbot, the agent follows a research workflow to gather relevant information, evaluate retrieved evidence, validate citations, and generate structured research reports.

Each report includes key findings, source references, confidence assessments, limitations, and suggested next steps.

## 2. Key Features

- **Research Planning:** Breaks research questions into structured research tasks.
- **Web Search:** Retrieves relevant web results using DuckDuckGo.
- **Webpage Extraction:** Reads webpages and extracts useful content.
- **Evidence Filtering:** Uses relevance scoring and content-quality checks to filter retrieved information.
- **Source Classification:** Identifies sources belonging to configured official domains.
- **AI-Powered Synthesis:** Uses Groq to generate structured research findings.
- **Citation Validation:** Checks that cited URLs belong to retrieved sources.
- **Unsupported Finding Detection:** Flags findings that lack sufficient evidence.
- **Confidence Assessment:** Provides heuristic confidence assessments.
- **Structured Reports:** Generates research reports in JSON format.
- **Report Export:** Allows users to download generated research results.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend development |
| Streamlit | Interactive user interface |
| Groq API | LLM-powered synthesis |
| DuckDuckGo | Web search |
| Requests | HTTP requests and webpage retrieval |
| BeautifulSoup | HTML parsing and content extraction |
| Git & GitHub | Version control |

## 4. System Architecture

The agent follows a modular, single-agent architecture.

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
                       |
                       v
                   JSON Export
```

## 5. Project Structure

```text
predixion-research-agent/
│
├── app.py                  # Streamlit application
├── agent.py                # Main research agent
├── planner.py              # Research planning
├── tools.py                # Search, retrieval and evidence filtering
├── schemas.py              # Report validation and evidence checks
├── config.py               # Configuration and environment settings
├── evaluator.py            # Evaluation utilities
│
├── tests/
│   └── test_agent.py        # Automated tests
│
├── outputs/
│   └── sample_report.md     # Sample research report
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 6. Installation and Setup

### Prerequisites

- Python 3.10 or later
- Git
- A Groq API key

### Step 1: Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/predixion-research-agent.git
cd predixion-research-agent
```

### Step 2: Create a virtual environment

```powershell
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

For macOS/Linux:

```bash
source .venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

Replace the placeholder with your own Groq API key.

**Security:** Never commit `.env`, API keys, or other secrets to GitHub. The repository includes `.env.example` for configuration guidance.

## 7. Running the Application

Start the Streamlit application:

```bash
python -m streamlit run app.py
```

Open the following address in your browser:

```text
http://localhost:8501
```

Enter a research question to start the research workflow and generate a structured report.

## 8. Running Tests

Run the automated test suite:

```bash
python -m unittest discover -s tests -v
```

The baseline test suite covers:

- Empty research questions.
- Retrieved URL validation.
- Localhost URL rejection.
- Unretrieved source rejection.
- Unsupported findings and missing citation handling.

## 9. Reliability and Evidence Validation

The application incorporates several safeguards to improve research reliability:

- Public HTTP/HTTPS URL validation.
- Private IP and localhost destination rejection.
- Redirect validation.
- Request timeouts and response-size limits.
- Webpage content extraction and filtering.
- Relevance-based evidence scoring.
- Retrieved-source citation validation.
- Unsupported finding detection.
- Prompt-injection awareness for untrusted webpage content.

Evidence filtering and citation checks use lightweight heuristics. They help reduce unsupported claims but do not guarantee factual correctness or prove that a source semantically supports a finding.

## 10. Why an Agentic Approach?

A traditional LLM chatbot generates responses directly from a user prompt and its existing knowledge. However, research questions often require current information, multiple sources, and evidence-based conclusions.

I chose an agentic approach because the research process involves multiple dependent steps:

1. **Planning:** The agent breaks the research question into smaller research tasks.
2. **Query generation:** It generates focused search queries to improve topic coverage.
3. **Tool execution:** It invokes web search and webpage retrieval tools.
4. **Evidence processing:** Retrieved content is filtered based on relevance, quality, and source characteristics.
5. **Synthesis:** The LLM combines retrieved evidence into a structured report.
6. **Validation:** The final report is checked against the retrieved sources.

This architecture separates research execution from language generation, making the workflow more modular, traceable, and easier to evaluate.

The system uses a single-agent architecture rather than multiple specialized agents to reduce orchestration complexity and unnecessary API calls.

## 11. Tool Selection and Execution

The agent uses two primary external tools.

| Tool | Technology | Responsibility |
|---|---|---|
| web_search | DuckDuckGo (DDGS) | Finds potentially relevant webpages for research queries. |
| read_webpage | Requests + BeautifulSoup | Retrieves webpage content and extracts readable text. |

### Why these tools?

**DuckDuckGo Search**
- Provides web discovery without requiring a separate search API key.
- Supports multiple focused research queries.
- Helps identify potentially useful primary and secondary sources.

**Webpage Reader**
- Retrieves the actual content of discovered webpages.
- Removes common HTML elements that are not useful for research.
- Provides content for evidence filtering and report generation.

**Groq LLM**
- Generates research plans and focused search queries.
- Synthesizes retrieved evidence into structured JSON reports.
- Produces findings, confidence assessments, limitations, and suggested next steps.

The agent controls tool execution through Python orchestration rather than allowing unrestricted tool calls.

## 12. Handling Bad Tool Results and Failures

The application includes several mechanisms to handle unreliable tool responses.

### Search failures
- Search exceptions are recorded rather than immediately terminating the entire workflow.
- The agent continues with other available search queries.
- If no usable search results remain, the workflow returns a clear error.

### Webpage retrieval failures
- HTTP requests use connection and read timeouts.
- Redirect destinations are validated before following them.
- Response sizes are limited to prevent excessive downloads.
- Unsupported content types and unreadable pages are rejected.
- Failed page retrievals are recorded in the retrieval issues list.
- The agent attempts additional search candidates when selected pages cannot be read.

### Invalid or low-quality evidence
- Invalid and unsafe URLs are rejected.
- Duplicate pages are removed.
- Irrelevant content and low-information pages are filtered.
- Freelancer advertisements and service listings are rejected.

### LLM response failures
- The JSON parser handles Markdown-wrapped responses and malformed output where possible.
- The model request is retried once after a generation or parsing failure.
- Transient failures receive a short delay before retrying.
- If the response remains invalid, the workflow reports the error instead of silently accepting malformed output.

These mechanisms improve resilience, although they do not eliminate every possible tool or network failure.

## 13. Hallucination Reduction and Citation Validation

The agent uses an evidence-grounded generation approach to reduce unsupported statements.

Key safeguards include:

1. Retrieved webpage content is supplied to the LLM as research evidence.
2. Webpage instructions are treated as untrusted input, reducing prompt-injection risks.
3. The model is instructed not to invent facts, statistics, prices, dates, or sources.
4. Findings must include exact source URLs copied from retrieved evidence.
5. Search results that were not successfully retrieved cannot be cited.
6. The final report passes through a separate validation stage.
7. Unsupported findings and invalid citations are rejected or flagged.
8. Confidence is assessed cautiously, with limitations and evidence gaps disclosed.

**Important limitation:** Citation validation uses lightweight heuristics. A URL matching a retrieved page does not independently prove that the page semantically supports the claim. Therefore, the system reduces hallucination risk but cannot guarantee factual correctness.

## 14. Production Readiness and Future Improvements

The current application provides a functional research workflow, but additional capabilities would be needed before deploying it as a production service.

Potential improvements include:

- **Scalability:** Introduce asynchronous and concurrent retrieval with controlled rate limits.
- **Caching:** Cache search results and retrieved pages to reduce repeated requests, latency, and API costs.
- **Security:** Use managed secret storage, stronger URL and network controls, and isolated execution where appropriate.
- **Reliability:** Add exponential backoff, circuit breakers, and more comprehensive failure recovery.
- **Observability:** Introduce structured logs, request tracing, and application metrics.
- **Evaluation:** Expand automated tests with research-quality benchmarks and citation-support checks.
- **Deployment:** Package the application using Docker and deploy it with appropriate resource limits and health checks.
- **Data management:** Add persistent research history and configurable retention policies where required.

These are proposed improvements, not capabilities currently implemented in the application.

## 15. Production Monitoring Strategy

If deployed in production, the following metrics should be monitored:

| Monitoring Area | Metrics |
|---|---|
| Application performance | Request latency, total research duration, throughput |
| Search reliability | Search success rate, empty-result rate, search failures |
| Retrieval reliability | Page retrieval success rate, timeout rate, extraction failures |
| LLM performance | API latency, token usage, error rate, retry rate |
| Research quality | Citation validity, unsupported finding rate, source relevance |
| Cost efficiency | LLM API cost, average tokens per research request, cost per report |
| Security | Rejected unsafe URLs, suspicious retrieval patterns, prompt-injection detections |

Structured logs should include a request identifier, workflow stage, tool name, execution duration, success or failure status, and bounded error details.

API keys, credentials, and sensitive user information must never be included in logs.

Alerts should be configured for repeated API failures, increasing retrieval failures, abnormal latency, and unusual cost increases.

## 16. Key Architectural Tradeoffs

| Decision | Advantages | Limitations / Tradeoffs |
|---|---|---|
| Single-agent architecture | Simple orchestration and easier maintenance | Less specialized than a multi-agent system |
| DuckDuckGo search | No separate search API key required | Search coverage and ranking are not fully controllable |
| Groq API | Convenient LLM inference integration | External API dependency, rate limits, and usage costs |
| Streamlit | Fast development and interactive interface | Less flexible than a dedicated frontend/backend architecture |
| Heuristic evidence filtering | Lightweight and inexpensive | Cannot fully understand semantic relevance |
| Structured JSON reports | Easier validation and integration | Requires robust parsing and schema handling |
| Sequential research workflow | Predictable execution and easier debugging | Can increase total latency |
| Bounded webpage extraction | Controls response size and processing cost | May omit relevant information from long pages |

The project prioritizes simplicity, traceability, cost awareness, and maintainability over unrestricted autonomy or complex multi-agent orchestration.

## 17. Future Roadmap

Potential future enhancements include:

- Semantic relevance scoring using embedding models.
- Stronger claim-to-source entailment verification.
- Concurrent search and webpage retrieval.
- Persistent research history and report comparison.
- Additional search providers and source-quality controls.
- Automated evaluation using a larger benchmark of research questions.

These enhancements would improve research coverage, factual reliability, scalability, and production observability.
---

**Predixion AI Research Agent**

*Research smarter. Retrieve evidence. Generate traceable insights.*

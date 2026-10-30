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

## 10. Design Decisions and Tradeoffs

| Design Decision | Reasoning |
|---|---|
| Single-agent architecture | Keeps orchestration simple, modular, and maintainable. |
| Groq API | Provides LLM-powered research synthesis. |
| DuckDuckGo | Provides web search without requiring a separate search API key. |
| Streamlit | Enables rapid development of an interactive research interface. |
| Custom evidence validation | Provides greater control over citations and report quality. |
| Structured JSON output | Makes research results easier to validate, export, and integrate. |

---

**Predixion AI Research Agent**

*Research smarter. Retrieve evidence. Generate traceable insights.*

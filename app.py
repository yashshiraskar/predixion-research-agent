
import json
import streamlit as st
from agent import run_research

st.set_page_config(
    page_title="Predixion Research Agent",
    page_icon="🔎",
    layout="wide",
)

st.title("🔎 AI Research Agent")
st.caption(
    "A source-grounded research agent built with Python, Groq, "
    "web search, and webpage reading."
)

with st.sidebar:
    st.subheader("Configuration")
    st.write("Set `GROQ_API_KEY` in your `.env` file.")
    st.write(
        "Web search uses DuckDuckGo; no separate search API key is required."
    )
    st.info(
        "Web pages are untrusted input. The agent treats page text "
        "as evidence, not instructions."
    )
    st.caption("Use verified sources for important decisions.")

question = st.text_area(
    "What would you like to research?",
    placeholder=(
        "Compare three open-source vector databases for a startup "
        "building RAG products."
    ),
    height=110,
    max_chars=2000,
)

max_sources = st.slider(
    "Maximum search results to inspect",
    min_value=3,
    max_value=8,
    value=5,
)

if st.button(
    "Research",
    type="primary",
    disabled=not question.strip(),
):
    try:
        with st.spinner(
            "Planning, searching, reading sources, and synthesizing findings..."
        ):
            result = run_research(
                question.strip(),
                max_sources=max_sources,
            )

        report = result["report"]

        # Research plan
        st.subheader("Research plan")

        plan = result.get("plan", [])
        if plan:
            for i, task in enumerate(plan, 1):
                st.write(f"{i}. {task}")
        else:
            st.warning("No research plan was returned.")

        # Execution details
        st.subheader("Tools used")
        tools_used = result.get("tools_used", [])

        st.write(
            ", ".join(tools_used)
            if tools_used
            else "No tools completed successfully."
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Pages read",
            len(result.get("evidence", [])),
        )
        col2.metric(
            "Sources cited",
            len(report.get("sources_used", [])),
        )
        col3.metric(
            "Confidence",
            report.get("confidence", "Low"),
        )

        # Retrieval errors
        read_errors = result.get("read_errors", [])

        if read_errors:
            with st.expander(
                f"Retrieval issues ({len(read_errors)})"
            ):
                for error in read_errors:
                    st.warning(error)

        # Main report
        st.subheader("Research report")

        st.markdown("### Short answer")
        st.write(
            report.get(
                "short_answer",
                "Insufficient verified evidence to answer confidently.",
            )
        )

        # Findings with individual citations
        st.markdown("### Key findings and evidence")

        findings = report.get("key_findings", [])

        if not findings:
            st.warning("No findings were returned.")
        else:
            for i, finding in enumerate(findings, 1):
                if isinstance(finding, str):
                    st.markdown(f"**{i}.** {finding}")
                    st.warning(
                        "This finding has no validated source links."
                    )
                    continue

                claim = finding.get(
                    "claim",
                    finding.get("finding", ""),
                )

                st.markdown(f"**{i}.** {claim}")

                source_urls = finding.get("source_urls", [])

                if source_urls:
                    for url in source_urls:
                        matching_source = next(
                            (
                                source
                                for source in report.get(
                                    "sources_used", []
                                )
                                if source.get("url") == url
                            ),
                            None,
                        )

                        label = (
                            matching_source.get("title", url)
                            if matching_source
                            else url
                        )

                        st.markdown(
                            f"- Supporting source: [{label}]({url})"
                        )
                else:
                    st.warning(
                        "No supporting source URL was attached "
                        "to this finding."
                    )

        # Source list
        st.markdown("### Sources")

        sources = report.get("sources_used", [])

        if sources:
            for source in sources:
                title = source.get("title") or "Source"
                url = source.get("url", "")

                if not url:
                    continue

                if source.get("official_source", False):
                    source_type = "Official source"
                else:
                    source_type = "Secondary/other source"

                st.markdown(
                    f"- [{title}]({url}) — **{source_type}**"
                )
        else:
            st.warning(
                "No sources could be verified. Treat the findings "
                "as unverified."
            )

        # Confidence and limitations
        st.markdown("### Confidence")
        confidence = report.get("confidence", "Low")

        st.write(confidence)

        if confidence == "Low":
            st.warning(
                "The available evidence is limited or does not "
                "adequately support the findings."
            )

        st.markdown("### Assumptions and limitations")

        limitations = report.get(
            "limitations_or_assumptions", []
        )

        if limitations:
            for item in limitations:
                st.markdown(f"- {item}")
        else:
            st.write("No limitations were reported by the agent.")

        st.markdown("### Suggested next steps")

        next_steps = report.get("suggested_next_steps", [])

        if next_steps:
            for item in next_steps:
                st.markdown(f"- {item}")
        else:
            st.write("No next steps were suggested.")

        # Raw evidence
        with st.expander("Evidence collected"):
            evidence = result.get("evidence", [])

            if not evidence:
                st.write("No webpage evidence was collected.")

            for source in evidence:
                title = source.get("title", "Untitled")
                url = source.get("url", "")
                content = source.get("content", "")

                st.markdown(f"**{title}**")

                if url:
                    st.markdown(f"[Open source webpage]({url})")

                if source.get("official_source", False):
                    st.caption("Classified as an official source")

                st.write(content[:2200] or "No readable page text.")

                st.divider()

        # Structured report
        with st.expander("Raw structured report"):
            st.json(report)

        # Download complete result for evaluation
        st.download_button(
            label="Download research result (JSON)",
            data=json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            file_name="research_result.json",
            mime="application/json",
        )

    except ValueError as exc:
        st.warning(str(exc))

    except Exception as exc:
        st.error(
            f"Research could not be completed: "
            f"{type(exc).__name__}: {exc}"
        )

        st.caption(
            "Check your API key, model configuration, network "
            "connection, and terminal logs. Never share API keys "
            "in screenshots or GitHub."
        )

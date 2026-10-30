
"""Validate research reports and check citation relevance."""

import ipaddress
import re
import socket
from urllib.parse import urlparse


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being",
    "by", "can", "could", "did", "do", "does", "for", "from",
    "had", "has", "have", "how", "if", "in", "into", "is", "it",
    "its", "may", "might", "more", "most", "of", "on", "or",
    "our", "should", "than", "that", "the", "their", "them",
    "there", "these", "this", "those", "to", "under", "use",
    "used", "using", "was", "were", "what", "when", "which",
    "while", "with", "would", "you", "your", "both", "also",
    "such", "each", "other", "based", "compared", "different",
}


def _is_public_http_url(url):
    """Reject localhost, private IPs, and non-public URLs."""

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        hostname = parsed.hostname

        if not hostname:
            return False

        hostname = hostname.lower()

        if hostname == "localhost" or hostname.endswith(".localhost"):
            return False

        # Check literal IP addresses first.
        try:
            ip_addresses = [ipaddress.ip_address(hostname)]

        except ValueError:
            # Resolve domain names and check every returned IP.
            try:
                resolved = socket.getaddrinfo(
                    hostname,
                    None,
                    type=socket.SOCK_STREAM,
                )

                ip_addresses = [
                    ipaddress.ip_address(result[4][0])
                    for result in resolved
                ]

            except (socket.gaierror, OSError, ValueError):
                return False

        if not ip_addresses:
            return False

        return all(address.is_global for address in ip_addresses)

    except (ValueError, TypeError):
        return False


def _tokens(text):
    """Extract informative terms for a lightweight relevance check."""

    words = re.findall(
        r"[a-zA-Z0-9][a-zA-Z0-9+#.-]*",
        text.lower()
    )

    return {
        word for word in words
        if len(word) > 2 and word not in STOPWORDS
    }


def _source_supports_claim(claim, source):
    """
    Check basic lexical relevance to a retrieved source.

    This is a heuristic, not proof that the source supports the claim.
    """

    source_text = " ".join((
        str(source.get("title", "")),
        str(source.get("search_snippet", "")),
        str(source.get("content", "")),
    ))

    claim_terms = _tokens(claim)
    source_terms = _tokens(source_text)

    if not claim_terms or not source_terms:
        return False

    matched = claim_terms & source_terms
    minimum_matches = 1 if len(claim_terms) <= 3 else 2

    return (
        len(matched) >= minimum_matches
        and len(matched) / len(claim_terms) >= 0.15
    )


def validate_report(data: dict, evidence: list[dict]) -> dict:
    """Keep evidence-linked findings and flag unsupported claims."""

    if not isinstance(data, dict):
        raise ValueError("Model output was not a JSON object.")

    if not isinstance(evidence, list):
        evidence = []

    # Index successfully retrieved pages with valid public HTTP(S) URLs.
    evidence_by_url = {}

    for item in evidence:
        if not isinstance(item, dict):
            continue

        url = item.get("url")
        content = item.get("content", "")

        if not (
            isinstance(url, str)
            and url.strip()
            and isinstance(content, str)
            and content.strip()
        ):
            continue

        url = url.strip()

        if not _is_public_http_url(url):
            continue

        evidence_by_url[url] = item

    findings, unsupported = _normalize_findings(
        data.get("key_findings"),
        evidence_by_url,
    )

    report = {
        "short_answer": _string(
            data.get("short_answer"),
            "Insufficient verified evidence to answer confidently.",
        ),
        "key_findings": findings,
        "sources_used": [],
        "confidence": "Low",
        "limitations_or_assumptions": _string_list(
            data.get("limitations_or_assumptions")
        ),
        "suggested_next_steps": _string_list(
            data.get("suggested_next_steps")
        ),
    }

    # Build sources_used from validated finding citations.
    validated_source_urls = dict.fromkeys(
        url
        for finding in findings
        for url in finding["source_urls"]
        if url in evidence_by_url
    )

    for url in validated_source_urls:
        item = evidence_by_url[url]

        report["sources_used"].append({
            "title": _string(
                item.get("title"),
                "Source"
            )[:300],
            "url": url,
            "domain": item.get("domain") or _domain(url),
            "official_source": bool(
                item.get("official_source", False)
            ),
        })

    limitations = report["limitations_or_assumptions"]

    # Flag findings rejected during validation.
    for claim, reason in unsupported[:5]:
        limitations.append(
            f"UNSUPPORTED FINDING: {claim[:180]} — {reason}"
        )

    if len(unsupported) > 5:
        limitations.append(
            f"{len(unsupported) - 5} additional finding(s) were excluded "
            "during evidence validation."
        )

    cited_urls = {
        url
        for finding in findings
        for url in finding["source_urls"]
    }

    if not findings:
        limitations.append(
            "No findings passed citation and relevance validation."
        )

    if not report["sources_used"]:
        limitations.append(
            "No sources passed citation and evidence validation."
        )

    # Remove duplicate limitation messages.
    report["limitations_or_assumptions"] = list(
        dict.fromkeys(limitations)
    )

    # Recalculate confidence using citation coverage and disclosed gaps.
    usable_sources = cited_urls & set(evidence_by_url)

    has_critical_gap = not findings or not usable_sources
    has_unsupported = bool(unsupported)

    limitation_text = " ".join(
        report["limitations_or_assumptions"]
    ).lower()

    has_material_uncertainty = any(term in limitation_text for term in (
        "conflicting evidence",
        "could not verify",
        "may be outdated",
        "incomplete evidence",
        "unsupported finding",
        "insufficient evidence",
    ))

    if (
        has_critical_gap
        or has_unsupported
        or has_material_uncertainty
    ):
        report["confidence"] = "Low"

    elif (
        len(cited_urls) >= 2
        and not report["limitations_or_assumptions"]
    ):
        report["confidence"] = "High"

    else:
        report["confidence"] = "Medium"

    return report


def _normalize_findings(value, evidence_by_url):
    """Validate findings and explain why rejected claims were excluded."""

    if not isinstance(value, list):
        return [], [(
            "Model findings",
            "findings were not provided as a list; findings excluded",
        )]

    findings = []
    unsupported = []

    for item in value[:10]:

        if isinstance(item, str):
            claim = item.strip()
            raw_urls = []

        elif isinstance(item, dict):
            claim = str(
                item.get("claim", item.get("finding", ""))
            ).strip()

            raw_urls = item.get("source_urls", [])

        else:
            unsupported.append((
                "Unrecognized finding",
                "finding excluded because it had an invalid structure",
            ))
            continue

        if not claim:
            unsupported.append((
                "Empty claim",
                "finding excluded because it did not contain a claim",
            ))
            continue

        if not isinstance(raw_urls, list):
            unsupported.append((
                claim,
                "finding excluded because citation URLs were not "
                "provided as a list",
            ))
            continue

        # Accept only exact URLs matching retrieved evidence.
        valid_urls = list(dict.fromkeys(
            url for url in raw_urls
            if isinstance(url, str)
            and url.strip() in evidence_by_url
        ))

        if not valid_urls:
            unsupported.append((
                claim,
                "finding excluded because no citation matched a "
                "successfully retrieved public page",
            ))
            continue

        claim_terms = _tokens(claim)
        is_generic_claim = len(claim_terms) < 2

        if is_generic_claim:
            relevant_urls = valid_urls

        else:
            relevant_urls = [
                url for url in valid_urls
                if _source_supports_claim(
                    claim,
                    evidence_by_url[url],
                )
            ]

        if not relevant_urls:
            unsupported.append((
                claim,
                "finding excluded because cited pages did not pass "
                "the text relevance check",
            ))
            continue

        findings.append({
            "claim": claim[:1200],
            "source_urls": relevant_urls[:5],
        })

    if len(value) > 10:
        unsupported.append((
            "Additional findings",
            "additional findings were excluded because only the first "
            "10 findings were considered",
        ))

    return findings, unsupported


def _string(value, fallback):
    """Return a non-empty, bounded string."""

    if isinstance(value, str) and value.strip():
        return value.strip()[:4000]

    return fallback


def _string_list(value):
    """Normalize a list of strings."""

    if not isinstance(value, list):
        return []

    result = []

    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip()[:1000])

        if len(result) >= 10:
            break

    return result


def _domain(url):
    """Extract the hostname from a URL."""

    return (urlparse(url).hostname or "").lower()
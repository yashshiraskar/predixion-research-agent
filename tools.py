
"""Web search, webpage reading, and evidence filtering tools."""

from ipaddress import ip_address
from urllib.parse import (
    urlparse,
    urljoin,
    urlunparse,
    parse_qsl,
    urlencode,
)
import re
import socket

import requests
from bs4 import BeautifulSoup


USER_AGENT = "PredixionResearchAgent/0.4"

MAX_SEARCH_RESULTS = 8
MAX_PAGE_BYTES = 1_000_000
MIN_CONTENT_LENGTH = 200

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been",
    "by", "can", "could", "did", "do", "does", "for",
    "from", "had", "has", "have", "how", "if", "in",
    "into", "is", "it", "its", "may", "might", "more",
    "most", "of", "on", "or", "our", "should", "than",
    "that", "the", "their", "them", "there", "these",
    "this", "those", "to", "under", "use", "used",
    "using", "was", "were", "what", "when", "which",
    "while", "with", "would", "you", "your", "about",
    "also", "between", "compare", "comparison",
    "explain", "find", "research", "information",
}


# Official product and documentation domains.
# This is a heuristic classification, not a guarantee of reliability.
OFFICIAL_DOMAINS = {
    # General developer platforms and cloud providers
    "python.org",
    "docs.python.org",
    "firebase.google.com",
    "cloud.google.com",
    "mongodb.com",
    "postgresql.org",
    "neon.tech",
    "amazonaws.com",
    "aws.amazon.com",
    "docs.aws.amazon.com",
    "learn.microsoft.com",
    "groq.com",
    "openai.com",

    # Vector databases
    "qdrant.tech",
    "qdrant.io",
    "milvus.io",
    "weaviate.io",
    "pinecone.io",
    "trychroma.com",

    # RAG and data infrastructure
    "langchain.com",
    "llamaindex.ai",
    "redis.io",
    "elastic.co",
    "opensearch.org",
    "datastax.com",
    "cockroachlabs.com",
}


# GitHub is not universally official.
# Only repositories belonging to known project organizations
# receive the official repository classification.
OFFICIAL_GITHUB_ORGS = {
    "qdrant",
    "milvus-io",
    "weaviate",
    "pinecone-io",
    "chroma-core",
    "langchain-ai",
    "run-llama",
    "redis",
    "elastic",
    "opensearch-project",
    "postgres",
    "mongodb",
    "google",
}


TRACKING_PARAMETERS = {
    "fbclid",
    "gclid",
    "ref",
    "source",
}


def _domain(url):
    """Return a normalized hostname."""
    return (
        (urlparse(url).hostname or "")
        .lower()
        .removeprefix("www.")
    )


def _normalize_url(url):
    """Normalize URLs to help identify duplicate pages."""
    parsed = urlparse(url)

    clean_query = [
        (key, value)
        for key, value in parse_qsl(
            parsed.query,
            keep_blank_values=True,
        )
        if not key.lower().startswith("utm_")
        and key.lower() not in TRACKING_PARAMETERS
    ]

    return urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/") or "/",
        "",
        urlencode(clean_query),
        "",
    ))


def _is_official(url):
    """Classify known official documentation and project websites."""
    parsed = urlparse(url)
    host = _domain(url)

    if host == "github.com":
        parts = [
            part for part in parsed.path.split("/")
            if part
        ]

        return bool(
            parts
            and parts[0].lower() in OFFICIAL_GITHUB_ORGS
        )

    return any(
        host == domain.removeprefix("www.")
        or host.endswith("." + domain.removeprefix("www."))
        for domain in OFFICIAL_DOMAINS
    )


def _source_priority(url):
    """
    Return source authority tier.

    3 = Official documentation or vendor website
    2 = Recognized official project repository
    1 = Other sources
    """
    parsed = urlparse(url)
    host = _domain(url)

    if host == "github.com":
        parts = [
            part for part in parsed.path.split("/")
            if part
        ]

        if (
            parts
            and parts[0].lower() in OFFICIAL_GITHUB_ORGS
        ):
            return 2

        return 1

    if _is_official(url):
        return 3

    return 1


def _ranking_score(relevance, quality, url):
    """
    Combine relevance, authority, and metadata quality.

    Relevance remains the largest factor.
    Authority helps rank close matches.
    """
    authority = {
        1: 0.0,
        2: 0.75,
        3: 1.0,
    }[_source_priority(url)]

    return round(
        (0.70 * relevance)
        + (0.20 * authority)
        + (0.10 * quality),
        3,
    )


def _validate_public_http_url(url):
    """Reject non-HTTP URLs and non-public destinations."""
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError(
            "Only HTTP and HTTPS URLs are allowed."
        )

    if parsed.username or parsed.password:
        raise ValueError(
            "URLs containing credentials are not allowed."
        )

    host = parsed.hostname.lower()

    if host == "localhost" or host.endswith(
        (".localhost", ".local", ".internal")
    ):
        raise ValueError(
            "Local network URLs are not allowed."
        )

    try:
        addresses = {ip_address(host)}

    except ValueError:
        try:
            addresses = {
                ip_address(item[4][0])
                for item in socket.getaddrinfo(host, None)
            }

        except OSError as exc:
            raise ValueError(
                "Could not validate the URL host."
            ) from exc

    if not addresses or not all(
        address.is_global for address in addresses
    ):
        raise ValueError(
            "Private or non-public URLs are not allowed."
        )


def _tokens(text):
    """Extract informative terms from text."""
    words = re.findall(
        r"[a-zA-Z0-9][a-zA-Z0-9+#.-]*",
        str(text).lower(),
    )

    return {
        word for word in words
        if len(word) > 2 and word not in STOPWORDS
    }


def _relevance_score(query, text):
    """
    Estimate query relevance using informative term overlap.

    This is a heuristic, not semantic verification.
    """
    query_terms = _tokens(query)
    content_terms = _tokens(text)

    if not query_terms or not content_terms:
        return 0.0

    matched = query_terms & content_terms

    return round(
        len(matched) / len(query_terms),
        3,
    )


def _source_quality_score(title, snippet, official_source=False):
    """
    Estimate basic source quality from search metadata.

    Official status is a positive signal, not proof of accuracy.
    """
    score = 0.0

    if title and len(title.strip()) >= 8:
        score += 0.25

    if snippet and len(snippet.strip()) >= 80:
        score += 0.45

    elif snippet and len(snippet.strip()) >= 30:
        score += 0.25

    if official_source:
        score += 0.15

    return round(min(score, 1.0), 2)


def _content_quality(content):
    """Check whether a retrieved page contains useful text."""
    text = str(content or "").strip()
    words = _tokens(text)

    flags = []

    if len(text) < MIN_CONTENT_LENGTH:
        flags.append("Very little readable content")

    if len(words) < 20:
        flags.append("Low information density")

    if not text:
        flags.append("Empty page content")

    return {
        "content_length": len(text),
        "word_count": len(text.split()),
        "quality_flags": flags,
        "usable_content": (
            len(text) >= MIN_CONTENT_LENGTH
            and len(words) >= 20
        ),
    }


def filter_evidence(question, evidence, min_relevance=0.10):
    """
    Filter retrieved evidence by relevance and content quality.

    Returns accepted and rejected evidence separately.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError(
            "Research question cannot be empty."
        )

    if not isinstance(evidence, list):
        return [], []

    accepted = []
    rejected = []
    seen_urls = set()

    for item in evidence:

        if not isinstance(item, dict):
            rejected.append({
                "title": "Unknown source",
                "reason": "Invalid evidence structure",
            })
            continue

        url = item.get("url", "")
        title = str(item.get("title", "Untitled"))
        content = str(item.get("content", ""))
        snippet = str(
            item.get(
                "search_snippet",
                item.get("snippet", ""),
            )
        )

        if not isinstance(url, str) or not url.strip():
            rejected.append({
                "title": title,
                "reason": "Missing source URL",
            })
            continue

        try:
            _validate_public_http_url(url)

        except (ValueError, TypeError):
            rejected.append({
                "title": title,
                "url": url,
                "reason": "Invalid or unsafe URL",
            })
            continue

        normalized_url = _normalize_url(url)

        if normalized_url in seen_urls:
            rejected.append({
                "title": title,
                "url": url,
                "reason": "Duplicate URL",
            })
            continue

        seen_urls.add(normalized_url)

        # Reject freelancer listings even if they were supplied directly.
        if _looks_like_freelance_listing(
            title=title,
            snippet=snippet,
            content=content,
            url=url,
        ):
            rejected.append({
                "title": title,
                "url": url,
                "reason": "Freelancer advertisement or service listing",
            })
            continue

        if not content.strip():
            rejected.append({
                "title": title,
                "url": url,
                "reason": "No retrieved page content",
            })
            continue

        quality = _content_quality(content)

        if not quality["usable_content"]:
            rejected.append({
                "title": title,
                "url": url,
                "reason": "; ".join(
                    quality["quality_flags"]
                ),
            })
            continue

        relevance = _relevance_score(
            question,
            f"{title} {snippet} {content}",
        )

        if relevance < min_relevance:
            rejected.append({
                "title": title,
                "url": url,
                "relevance_score": relevance,
                "reason": (
                    "Page does not sufficiently match "
                    "the research question"
                ),
            })
            continue

        official = bool(
            item.get(
                "official_source",
                _is_official(url),
            )
        )

        source_quality = _source_quality_score(
            title,
            snippet or content[:500],
            official,
        )

        accepted_item = dict(item)

        accepted_item.update({
            "official_source": official,
            "source_priority": _source_priority(url),
            "relevance_score": relevance,
            "quality_score": source_quality,
            "ranking_score": _ranking_score(
                relevance,
                source_quality,
                url,
            ),
            "content_length": quality["content_length"],
            "word_count": quality["word_count"],
            "quality_flags": quality["quality_flags"],
            "filter_status": "accepted",
        })

        accepted.append(accepted_item)

    # Rank by combined relevance, authority, and quality.
    # Secondary sources remain available for useful comparisons.
    accepted.sort(
        key=lambda item: item["ranking_score"],
        reverse=True,
    )

    return accepted, rejected


def _looks_like_freelance_listing(
    title="",
    snippet="",
    content="",
    url="",
):
    """
    Detect marketplace gigs and service advertisements.

    Uses marketplace domains and characteristic listing phrases.
    """
    text = f"{title} {snippet} {content}".lower()
    host = _domain(url) if url else ""

    marketplace_domains = {
        "fiverr.com",
        "upwork.com",
        "freelancer.com",
        "peopleperhour.com",
        "guru.com",
        "workana.com",
        "truelancer.com",
        "contra.com",
        "khamsat.com",
        "mostaql.com",
    }

    if any(
        host == domain or host.endswith("." + domain)
        for domain in marketplace_domains
    ):
        return True

    strong_phrases = (
        "what you get with this offer",
        "what the freelancer needs to start the work",
        "what the freelancer needs to start work",
        "amount of days required to complete work",
        "contact the seller",
        "purchase this gig",
        "place an order for this service",
        "hire me for this project",
        "buy this service",
    )

    if any(phrase in text for phrase in strong_phrases):
        return True

    generic_signals = (
        "freelancer",
        "service offer",
        "delivery in",
        "starting at",
        "quantity",
        "show more details",
        "average time for the freelancer to first reply",
        "days required to complete",
    )

    return sum(
        phrase in text for phrase in generic_signals
    ) >= 3


def web_search(query, max_results=5):
    """Tool 1: Search the web using DuckDuckGo."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError(
            "Search query cannot be empty."
        )

    max_results = max(
        1,
        min(int(max_results), MAX_SEARCH_RESULTS),
    )

    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            raw_results = list(
                ddgs.text(
                    query.strip(),
                    max_results=max_results * 3,
                )
            )

    except Exception as exc:
        raise RuntimeError(
            f"Web search failed: {type(exc).__name__}. "
            "Check your network."
        ) from exc

    results = []
    seen_urls = set()

    for item in raw_results:

        url = item.get("href") or item.get("url")

        if not url:
            continue

        try:
            _validate_public_http_url(url)

        except (ValueError, TypeError):
            continue

        normalized_url = _normalize_url(url)

        if normalized_url in seen_urls:
            continue

        seen_urls.add(normalized_url)

        title = str(
            item.get("title", "Untitled")
        )[:300]

        snippet = str(
            item.get("body", "")
        )[:1000]

        # Reject freelancer listings before ranking search results.
        if _looks_like_freelance_listing(
            title=title,
            snippet=snippet,
            url=url,
        ):
            continue

        official = _is_official(url)

        relevance = _relevance_score(
            query,
            f"{title} {snippet}",
        )

        quality = _source_quality_score(
            title,
            snippet,
            official,
        )

        if relevance < 0.10:
            continue

        results.append({
            "title": title,
            "url": url,
            "snippet": snippet,
            "domain": _domain(url),
            "official_source": official,
            "source_priority": _source_priority(url),
            "relevance_score": relevance,
            "quality_score": quality,
            "ranking_score": _ranking_score(
                relevance,
                quality,
                url,
            ),
        })

    results.sort(
        key=lambda item: item["ranking_score"],
        reverse=True,
    )

    return results[:max_results]


def read_webpage(url):
    """Tool 2: Read text from a public webpage."""
    _validate_public_http_url(url)

    response = None

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=(5, 15),
            allow_redirects=False,
            stream=True,
        )

        redirects = 0

        # Validate every redirect destination.
        while (
            response.is_redirect
            or response.is_permanent_redirect
        ):
            if redirects >= 4:
                raise ValueError("Too many redirects.")

            location = response.headers.get("Location")

            if not location:
                raise ValueError(
                    "Redirect did not provide a destination."
                )

            target = urljoin(response.url, location)

            _validate_public_http_url(target)

            response.close()

            response = requests.get(
                target,
                headers={"User-Agent": USER_AGENT},
                timeout=(5, 15),
                allow_redirects=False,
                stream=True,
            )

            redirects += 1

        response.raise_for_status()

        content_type = response.headers.get(
            "content-type",
            "",
        ).lower()

        if not any(
            kind in content_type
            for kind in ("text/html", "text/plain")
        ):
            raise ValueError(
                f"Unsupported content type: "
                f"{content_type or 'unknown'}"
            )

        chunks = []
        total_size = 0

        for chunk in response.iter_content(
            chunk_size=8192
        ):
            if not chunk:
                continue

            remaining = MAX_PAGE_BYTES - total_size

            if remaining <= 0:
                break

            chunk = chunk[:remaining]
            chunks.append(chunk)
            total_size += len(chunk)

            if total_size >= MAX_PAGE_BYTES:
                break

        raw_html = b"".join(chunks)

        soup = BeautifulSoup(
            raw_html,
            "html.parser",
        )

        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "noscript",
            "svg",
            "form",
        ]):
            tag.decompose()

        title = (
            soup.title.get_text(" ", strip=True)
            if soup.title
            else response.url
        )

        content = " ".join(
            soup.get_text(" ", strip=True).split()
        )

        # Recheck the actual page because search snippets can be incomplete.
        if _looks_like_freelance_listing(
            title=title,
            content=content,
            url=response.url,
        ):
            raise ValueError(
                "Freelancer advertisement or service listing "
                "rejected as a research source."
            )

        quality = _content_quality(content)
        official = _is_official(response.url)

        return {
            "title": title[:300],
            "url": response.url,
            "content": content[:7000],
            "domain": _domain(response.url),
            "official_source": official,
            "source_priority": _source_priority(response.url),
            "content_length": quality["content_length"],
            "word_count": quality["word_count"],
            "quality_flags": quality["quality_flags"],
            "usable_content": quality["usable_content"],
        }

    finally:
        if response is not None:
            response.close()

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


USER_AGENT = "PredixionResearchAgent/0.3"

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


# Domains used for official-source classification.
# This is a classification aid, not a guarantee of reliability.
OFFICIAL_DOMAINS = {
    "python.org",
    "firebase.google.com",
    "cloud.google.com",
    "mongodb.com",
    "postgresql.org",
    "neon.tech",
    "amazonaws.com",
    "aws.amazon.com",
    "docs.aws.amazon.com",
    "learn.microsoft.com",
    "github.com",
    "groq.com",
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
    """Classify URLs belonging to explicitly listed official domains."""
    host = _domain(url)

    return any(
        host == domain.removeprefix("www.")
        or host.endswith("." + domain.removeprefix("www."))
        for domain in OFFICIAL_DOMAINS
    )


def _validate_public_http_url(url):
    """Reject non-HTTP URLs and non-public destinations."""
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Only HTTP and HTTPS URLs are allowed.")

    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not allowed.")

    host = parsed.hostname.lower()

    if host == "localhost" or host.endswith(
        (".localhost", ".local", ".internal")
    ):
        raise ValueError("Local network URLs are not allowed.")

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
        raise ValueError("Private or non-public URLs are not allowed.")


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

    This is a lightweight heuristic, not semantic verification.
    """
    query_terms = _tokens(query)
    content_terms = _tokens(text)

    if not query_terms or not content_terms:
        return 0.0

    matched = query_terms & content_terms

    return round(len(matched) / len(query_terms), 3)


def _source_quality_score(title, snippet, official_source=False):
    """
    Estimate basic source quality from available search metadata.

    Official status is a small positive signal, not proof of accuracy.
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
    """Check whether a retrieved page contains enough useful text."""
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
    Filter retrieved evidence by query relevance and content quality.

    Returns:
        accepted: Evidence suitable for further synthesis.
        rejected: Evidence with explicit rejection reasons.

    The scoring is heuristic and should not be interpreted as
    proof that a source supports a particular factual claim.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Research question cannot be empty.")

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
        snippet = str(item.get("search_snippet", item.get("snippet", "")))

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
                "reason": "; ".join(quality["quality_flags"]),
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
                "reason": "Page does not sufficiently match the research question",
            })
            continue

        official = bool(
            item.get("official_source", _is_official(url))
        )

        source_quality = _source_quality_score(
            title,
            snippet or content[:500],
            official,
        )

        accepted_item = dict(item)

        accepted_item.update({
            "official_source": official,
            "relevance_score": relevance,
            "quality_score": source_quality,
            "content_length": quality["content_length"],
            "word_count": quality["word_count"],
            "quality_flags": quality["quality_flags"],
            "filter_status": "accepted",
        })

        accepted.append(accepted_item)

    # Rank relevant evidence first, then use source quality as a
    # secondary signal. Do not automatically discard secondary sources.
    accepted.sort(
        key=lambda item: (
            item["relevance_score"],
            item["quality_score"],
        ),
        reverse=True,
    )

    return accepted, rejected


def web_search(query, max_results=5):
    """Tool 1: Search the web using DuckDuckGo."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query cannot be empty.")

    max_results = max(1, min(int(max_results), MAX_SEARCH_RESULTS))

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

        title = str(item.get("title", "Untitled"))[:300]
        snippet = str(item.get("body", ""))[:1000]
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

        # Very weak matches are excluded from the search output.
        if relevance < 0.10:
            continue

        results.append({
            "title": title,
            "url": url,
            "snippet": snippet,
            "domain": _domain(url),
            "official_source": official,
            "relevance_score": relevance,
            "quality_score": quality,
        })

    results.sort(
        key=lambda item: (
            item["relevance_score"],
            item["quality_score"],
        ),
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

        while response.is_redirect or response.is_permanent_redirect:
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
            "content-type", ""
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

        for chunk in response.iter_content(chunk_size=8192):
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

        # Parse downloaded bytes directly to avoid rereading
        # an already-consumed HTTP response stream.
        soup = BeautifulSoup(raw_html, "html.parser")

        for tag in soup([
            "script", "style", "nav", "footer",
            "header", "noscript", "svg", "form",
        ]):
            tag.decompose()

        title = (
            soup.title.get_text(" ", strip=True)
            if soup.title else response.url
        )

        content = " ".join(
            soup.get_text(" ", strip=True).split()
        )

        quality = _content_quality(content)
        official = _is_official(response.url)

        return {
            "title": title[:300],
            "url": response.url,
            "content": content[:7000],
            "domain": _domain(response.url),
            "official_source": official,
            "content_length": quality["content_length"],
            "word_count": quality["word_count"],
            "quality_flags": quality["quality_flags"],
            "usable_content": quality["usable_content"],
        }

    finally:
        if response is not None:
            response.close()
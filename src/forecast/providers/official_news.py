import ipaddress
import re
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from forecast.audit.hashing import redact, sha256
from forecast.domain.time_policy import utc
from forecast.ingestion.canonicalize import canonical_url
from forecast.providers.base import DataFetchResult

PRIORITY_DOMAINS = (
    "openai.com",
    "nasdaqprivatemarket.com",
    "nasdaq.com",
    "reuters.com",
    "bloomberg.com",
    "ft.com",
)


def public_article_url(url: str) -> str:
    """Accept public publishers beyond priority sources, but reject local/network targets."""
    normalized = canonical_url(url)
    parsed = urlsplit(normalized)
    host = parsed.hostname or ""
    if (
        parsed.port not in (None, 80, 443)
        or host in ("localhost",)
        or host.endswith((".localhost", ".local", ".internal"))
        or "." not in host
    ):
        raise ValueError("PUBLIC_ARTICLE_URL_REQUIRED")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return normalized
    raise ValueError("PUBLIC_ARTICLE_URL_REQUIRED")


def source_priority(host: str) -> str:
    return (
        "priority"
        if any(host == d or host.endswith("." + d) for d in PRIORITY_DOMAINS)
        else "other_publication"
    )


class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.published = None
        self.canonical = None
        self.paragraphs = []
        self.links = []
        self.in_p = False
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style", "nav"):
            self.skip += 1
        if tag == "p":
            self.in_p = True
            self.paragraphs.append("")
        if tag == "meta" and attrs.get("property", attrs.get("name")) in (
            "article:published_time",
            "datePublished",
            "date",
        ):
            self.published = attrs.get("content")
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href")
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav"):
            self.skip = max(0, self.skip - 1)
        if tag == "p":
            self.in_p = False

    def handle_data(self, data):
        if self.in_p and not self.skip and self.paragraphs:
            self.paragraphs[-1] += data


class PublicArticleRetriever:
    def __init__(self, client=None, respect_robots=True):
        self.client = client or httpx.Client(
            timeout=20, follow_redirects=False, headers={"User-Agent": "ValuationResearch/1.0"}
        )
        self.respect_robots = respect_robots

    def fetch(self, candidate):
        try:
            url = public_article_url(candidate["url"])
        except (KeyError, TypeError, ValueError):
            return DataFetchResult("Article", "METADATA_ONLY", reason="PUBLIC_ARTICLE_URL_REQUIRED")
        try:
            host = urlsplit(url).hostname or ""
            if self.respect_robots:
                robots_url = urljoin(url, "/robots.txt")
                robots_response = self.client.get(robots_url)
                if robots_response.status_code not in (200, 404):
                    return DataFetchResult("Article", "METADATA_ONLY", reason="ROBOTS_UNAVAILABLE")
                robots = RobotFileParser()
                robots.parse(
                    robots_response.text.splitlines() if robots_response.status_code == 200 else []
                )
                if not robots.can_fetch("ValuationResearch", url):
                    return DataFetchResult("Article", "METADATA_ONLY", reason="ROBOTS_DISALLOW")
            response = self.client.get(url)
            if response.status_code != 200:
                return DataFetchResult(
                    "Article",
                    "METADATA_ONLY",
                    http_status=response.status_code,
                    reason="ACCESS_RESTRICTED_OR_REDIRECT; no bypass attempted",
                )
            if len(response.content) > 2_000_000:
                return DataFetchResult("Article", "METADATA_ONLY", reason="DOCUMENT_SIZE_LIMIT")
            if "html" not in response.headers.get("content-type", "text/html").lower():
                return DataFetchResult("Article", "METADATA_ONLY", reason="NON_HTML_DOCUMENT")
            parser = ArticleParser()
            parser.feed(response.text)
            if parser.canonical:
                target = canonical_url(urljoin(url, parser.canonical))
                if urlsplit(target).hostname == host:
                    url = target
            if not parser.published:
                return DataFetchResult(
                    "Article", "TIME_NOT_VERIFIED", reason="PUBLICATION_TIME_MISSING"
                )
            published = utc(parser.published).isoformat()
            if utc(published) > datetime.now(UTC):
                return DataFetchResult(
                    "Article", "TIME_NOT_VERIFIED", reason="PUBLICATION_TIME_IN_FUTURE"
                )
            paragraphs = [
                re.sub(r"\s+", " ", p).strip() for p in parser.paragraphs if "openai" in p.lower()
            ]
            excerpt = " ".join(" ".join(paragraphs).split()[:200])
            if not excerpt:
                return DataFetchResult(
                    "Article", "METADATA_ONLY", reason="NO_ACCESSIBLE_RELEVANT_BODY"
                )
            return DataFetchResult(
                "Article",
                "OK",
                data={
                    "url": url,
                    "publisher": host,
                    "source_priority": source_priority(host),
                    "published_at": published,
                    "seen_at": datetime.now(UTC).isoformat(),
                    "title": redact(candidate.get("title", "")),
                    "excerpt": redact(excerpt),
                    "page_sha256": sha256(response.content),
                    "links": parser.links[:100],
                    "quote_location": "accessible OpenAI paragraph excerpt; first 200 words",
                },
                http_status=200,
            )
        except (httpx.HTTPError, ValueError, TypeError):
            return DataFetchResult(
                "Article", "TIME_NOT_VERIFIED", reason="FETCH_PARSE_OR_TIME_ERROR"
            )

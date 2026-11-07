import json
from copy import deepcopy

import httpx
import pytest

from forecast.agent.extractor import DeepSeekExtractor
from forecast.agent.verifier import verify_claim
from forecast.domain.schemas import Claim
from forecast.providers.npm import ManualNpmProvider
from forecast.providers.official_news import PublicArticleRetriever
from forecast.providers.tavily_search import TavilySearch


def client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_tavily_contract_and_missing_key():
    assert TavilySearch(api_key="").search("OpenAI").status == "SEARCH_FAILURE"

    def handler(request):
        assert request.headers["Authorization"] == "Bearer fake"
        assert json.loads(request.content)["include_raw_content"] is False
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "url": "https://openai.com/news/example",
                        "title": "OpenAI",
                        "content": "Discovery only",
                    }
                ]
            },
        )

    result = TavilySearch(client(handler), "fake").search("OpenAI", start_date="2026-11-01")
    assert result.status == "OK" and result.data["results"][0]["rank"] == 1


def test_rate_limit_retries_and_transport():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(429, json={"error": "rate limited"})

    assert (
        TavilySearch(client(handler), "fake", retry_wait=0).search("OpenAI").status
        == "SEARCH_FAILURE"
    )
    assert len(calls) == 3
    assert (
        TavilySearch(client(lambda r: httpx.Response(401)), "fake").search("x").http_status == 401
    )
    assert (
        TavilySearch(client(lambda r: httpx.Response(200, json={})), "fake").search("x").status
        == "SEARCH_FAILURE"
    )


def test_deepseek_valid_and_invalid_json(demo):
    source = demo["claims"][0]["source"]
    payload = {"claims": [demo["claims"][0]["claim_json"]]}

    def handler(request):
        body = json.loads(request.content)
        assert body["model"] == "deepseek-v4-pro"
        assert body["temperature"] == 0
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": json.dumps(payload)}}],
                "usage": {"total_tokens": 25},
            },
        )

    result = DeepSeekExtractor(client(handler), "fake").extract(source)
    assert result.status == "OK" and result.data["usage"]["total_tokens"] == 25
    assert DeepSeekExtractor(api_key="").extract(source).status == "LLM_FAILURE"
    calls = []

    def invalid(request):
        calls.append(request)
        return httpx.Response(200, json={"choices": [{"message": {"content": "not json"}}]})

    assert DeepSeekExtractor(client(invalid), "fake").extract(source).status == "REVIEW_REQUIRED"
    assert len(calls) == 3
    assert (
        DeepSeekExtractor(client(lambda r: httpx.Response(503)), "fake").extract(source).status
        == "LLM_FAILURE"
    )


def test_llm_hallucination_sources_numbers_scope_states(demo):
    row = demo["claims"][0]
    source = row["source"]
    claim = Claim.model_validate(row["claim_json"])
    assert verify_claim(claim, {source["source_id"]: source}) == (True, "VERIFIED")
    for change in (
        {"source_ids": ["invented"]},
        {"reported_valuation_trillion": "1.9"},
        {"supporting_quote": "invented number"},
        {"event_status": "closed"},
        {"published_at": "2026-11-01T00:00:00Z"},
        {"synthetic": False},
    ):
        altered = Claim.model_validate(row["claim_json"] | change)
        assert not verify_claim(altered, {source["source_id"]: source})[0]
    with pytest.raises(ValueError):
        Claim.model_validate(row["claim_json"] | {"delta_probability": 0.8})
    with pytest.raises(ValueError):
        Claim.model_validate(row["claim_json"] | {"supporting_quote": "word " * 26})
    fake_scope = deepcopy(row["claim_json"])
    fake_scope["supporting_quote"] = "OpenAI proposed raising $1.4 trillion."
    assert not verify_claim(
        Claim.model_validate(fake_scope),
        {source["source_id"]: source | {"raw_excerpt": fake_scope["supporting_quote"]}},
    )[0]


def test_public_article_metadata_not_search_snippet():
    html = (
        '<meta property="article:published_time" content="2026-11-01T12:00:00Z">'
        "<p>OpenAI proposed a financing at a valuation of $1.4 trillion.</p>"
    )
    retriever = PublicArticleRetriever(
        client(lambda r: httpx.Response(200, text=html, headers={"content-type": "text/html"})),
        respect_robots=False,
    )
    result = retriever.fetch({"url": "https://openai.com/news/example", "title": "OpenAI"})
    assert result.status == "OK" and result.data["published_at"].endswith("+00:00")
    assert retriever.fetch({"url": "http://127.0.0.1/private"}).status == "METADATA_ONLY"
    blocked = PublicArticleRetriever(client(lambda r: httpx.Response(403)), respect_robots=False)
    assert blocked.fetch({"url": "https://ft.com/a"}).status == "METADATA_ONLY"
    assert ManualNpmProvider().fetch_latest().status == "NPM_FETCH_BLOCKED"


def test_nonpriority_publication_is_read_before_source_review():
    requests = []
    html = (
        '<meta property="article:published_time" content="2026-11-01T12:00:00Z">'
        "<p>OpenAI proposed financing at a post-money valuation of $1.4 trillion.</p>"
    )

    def handler(request):
        requests.append(str(request.url))
        if str(request.url).endswith("/robots.txt"):
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    result = PublicArticleRetriever(client(handler)).fetch(
        {
            "url": "https://www.example-news.com/openai",
            "title": "OpenAI",
            "discovery_snippet": "This is not evidence.",
        }
    )
    assert result.status == "OK"
    assert result.data["source_priority"] == "other_publication"
    assert result.data["excerpt"].startswith("OpenAI proposed")
    assert "This is not evidence." not in result.data["excerpt"]
    assert len(requests) == 2
    denied = PublicArticleRetriever(
        client(lambda r: httpx.Response(200, text="User-agent: *\nDisallow: /"))
    )
    assert denied.fetch({"url": "https://example-news.com/openai"}).reason == "ROBOTS_DISALLOW"
    redirected = PublicArticleRetriever(client(lambda r: httpx.Response(302)), respect_robots=False)
    assert redirected.fetch({"url": "https://example-news.com/openai"}).status == "METADATA_ONLY"
    missing = PublicArticleRetriever(
        client(
            lambda r: httpx.Response(
                200, text="<p>OpenAI article</p>", headers={"content-type": "text/html"}
            )
        ),
        respect_robots=False,
    )
    assert (
        missing.fetch({"url": "https://example-news.com/undated"}).reason
        == "PUBLICATION_TIME_MISSING"
    )
    assert (
        PublicArticleRetriever(client(handler)).fetch({"url": "http://127.0.0.1/private"}).status
        != "OK"
    )


def test_financing_amount_never_becomes_valuation(demo):
    row = demo["claims"][0]
    quote = "OpenAI proposed raising $10 billion at a post-money valuation of $1.4 trillion."
    claim = Claim.model_validate(
        row["claim_json"] | {"supporting_quote": quote, "reported_valuation_trillion": ".010"}
    )
    assert not verify_claim(
        claim, {row["source"]["source_id"]: row["source"] | {"raw_excerpt": quote}}
    )[0]


def test_normal_trailing_slash_redirect_is_followed():
    calls = []

    def handler(request):
        calls.append(str(request.url))
        if request.url.path == "/news":
            return httpx.Response(301, headers={"location": "/news/"})
        return httpx.Response(
            200,
            text='<meta property="article:published_time" content="2026-11-01T12:00:00Z"><p>OpenAI reported revenue growth.</p>',
            headers={"content-type": "text/html"},
        )

    result = PublicArticleRetriever(client(handler), respect_robots=False).fetch(
        {"url": "https://example-news.com/news/"}
    )
    assert result.status == "OK"
    assert calls == ["https://example-news.com/news", "https://example-news.com/news/"]


def test_cross_site_redirect_is_not_followed():
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(302, headers={"location": "https://other-site.com/login"})

    result = PublicArticleRetriever(client(handler), respect_robots=False).fetch(
        {"url": "https://example-news.com/news"}
    )
    assert result.status == "METADATA_ONLY"
    assert len(calls) == 1

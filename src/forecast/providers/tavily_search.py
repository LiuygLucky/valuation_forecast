import os
from datetime import UTC, datetime

import httpx
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from forecast.audit.hashing import object_hash, redact
from forecast.providers.base import DataFetchResult


class RetryableSearchError(Exception):
    pass


class TavilySearch:
    def __init__(self, client=None, api_key=None, max_attempts=3, retry_wait=1):
        self.client = client or httpx.Client(timeout=25, follow_redirects=False)
        self.api_key = api_key if api_key is not None else os.getenv("TAVILY_API_KEY", "")
        self.max_attempts = max_attempts
        self.retry_wait = retry_wait

    def search(self, query, *, max_results=3, start_date=None, end_date=None):
        if not self.api_key:
            return DataFetchResult("Tavily", "SEARCH_FAILURE", reason="MISSING_TAVILY_API_KEY")
        payload = {
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_raw_content": False,
            "include_answer": False,
            "include_published_date": True,
            "topic": "news",
        }
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date
        status = None
        try:
            for attempt in Retrying(
                stop=stop_after_attempt(self.max_attempts),
                wait=wait_exponential(multiplier=self.retry_wait, max=8),
                retry=retry_if_exception_type((httpx.TransportError, RetryableSearchError)),
                reraise=True,
            ):
                with attempt:
                    response = self.client.post(
                        "https://api.tavily.com/search",
                        json=payload,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                    )
                    status = response.status_code
                    if status == 429 or status >= 500:
                        raise RetryableSearchError()
                    response.raise_for_status()
                    body = response.json()
                    if not isinstance(body.get("results"), list):
                        raise ValueError("missing results field")
                    results = [
                        {
                            "rank": i + 1,
                            "url": r["url"],
                            "title": redact(r.get("title", "")),
                            "published_at_claimed": r.get("published_date"),
                            "discovery_snippet": redact(r.get("content", "")[:1500]),
                        }
                        for i, r in enumerate(body["results"][:max_results])
                    ]
                    return DataFetchResult(
                        "Tavily",
                        "OK",
                        data={
                            "query": query,
                            "requested_at": datetime.now(UTC).isoformat(),
                            "results": results,
                            "response_sha256": object_hash(body),
                        },
                        http_status=status,
                    )
        except (httpx.HTTPError, RetryableSearchError, ValueError, KeyError, TypeError):
            return DataFetchResult(
                "Tavily",
                "SEARCH_FAILURE",
                http_status=status,
                reason="HTTP_OR_RESPONSE_ERROR; no inference about absent news",
            )
        return DataFetchResult("Tavily", "SEARCH_FAILURE", reason="RETRY_EXHAUSTED")

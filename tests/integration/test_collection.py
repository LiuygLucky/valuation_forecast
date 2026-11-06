from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from forecast.agent.orchestrator import collect_live
from forecast.application.demo import demo_inputs
from forecast.audit.hashing import object_hash
from forecast.db.models import ClaimRecord, ExtractionRecord
from forecast.providers.base import DataFetchResult


def test_full_mock_pipeline_cache_and_source_ids(engine):
    now = datetime.now(UTC)
    published = (now - timedelta(hours=1)).isoformat()
    quote = "OpenAI proposed a financing at a post-money valuation of $1.4 trillion."

    class Search:
        def search(self, query, **kwargs):
            return DataFetchResult(
                "Tavily",
                "OK",
                data={
                    "requested_at": now.isoformat(),
                    "response_sha256": object_hash(query),
                    "results": [
                        {
                            "url": "https://openai.com/news/test",
                            "title": "OpenAI test",
                            "rank": 1,
                            "discovery_snippet": "not evidence",
                        }
                    ],
                },
            )

    class Retriever:
        def fetch(self, candidate):
            return DataFetchResult(
                "Article",
                "OK",
                data={
                    "url": candidate["url"],
                    "publisher": "openai.com",
                    "seen_at": now.isoformat(),
                    "published_at": published,
                    "title": "OpenAI test",
                    "excerpt": quote,
                    "page_sha256": object_hash(quote),
                    "links": [],
                    "quote_location": "p1",
                },
            )

    class Extractor:
        calls = 0
        model = "mock-deepseek"

        def extract(self, source):
            self.calls += 1
            claim = demo_inputs(now)["claims"][0]["claim_json"]
            claim.update(
                source_ids=[source["source_id"]],
                published_at=published,
                supporting_quote=quote,
                synthetic=False,
            )
            return DataFetchResult(
                "DeepSeek",
                "OK",
                data={
                    "claims": [claim],
                    "model_id": self.model,
                    "prompt_version": "claims-v1",
                    "usage": {},
                    "response_sha256": object_hash(claim),
                },
            )

    extractor = Extractor()
    result = collect_live(engine, Search(), extractor, Retriever())
    assert result["new_verified_claims"] == 1
    result = collect_live(engine, Search(), extractor, Retriever())
    assert extractor.calls == 1 and result["new_verified_claims"] == 0
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(ClaimRecord)) == 1
        assert session.scalar(select(func.count()).select_from(ExtractionRecord)) == 1
        claim = session.scalar(select(ClaimRecord))
        assert claim.claim_json["event_cluster_id"] == "OpenAI:financing:2026"

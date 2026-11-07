from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from forecast.agent.extractor import QwenExtractor
from forecast.agent.verifier import verify_claim
from forecast.audit.hashing import object_hash, redact
from forecast.config import load_yaml
from forecast.db.models import (
    ClaimRecord,
    Event,
    ExtractionRecord,
    ProviderHealth,
    SearchRecord,
    Source,
    SourceVersion,
)
from forecast.db.queries import source_version_dict
from forecast.domain.schemas import Claim
from forecast.domain.time_policy import utc
from forecast.ingestion.canonicalize import canonical_url
from forecast.ingestion.npm_capture import ingest_capture
from forecast.ingestion.versioning import save_source
from forecast.providers.npm_browser import NpmBrowserProvider
from forecast.providers.official_news import PublicArticleRetriever, source_priority
from forecast.providers.tavily_search import TavilySearch


def record_health(session, result):
    previous = session.scalar(
        select(ProviderHealth)
        .where(ProviderHealth.provider == result.provider, ProviderHealth.status == "OK")
        .order_by(ProviderHealth.checked_at.desc())
    )
    now = datetime.now(UTC).isoformat()
    session.add(
        ProviderHealth(
            health_id=str(uuid4()),
            provider=result.provider,
            checked_at=now,
            last_success_at=now
            if result.status == "OK"
            else (previous.checked_at if previous else None),
            status=result.status,
            http_status=result.http_status,
            reason=result.reason,
            details_json={},
        )
    )


def collect_live(engine, search=None, extractor=None, retriever=None, npm=None):
    search = search or TavilySearch()
    extractor = extractor or QwenExtractor()
    retriever = retriever or PublicArticleRetriever()
    npm = npm or NpmBrowserProvider()
    config = load_yaml("search_queries.yaml")
    warnings, search_ids, candidates = [], [], []
    now = datetime.now(UTC)
    npm_result = npm.fetch_latest()
    npm_import = None
    with Session(engine) as session, session.begin():
        record_health(session, npm_result)
        if npm_result.status != "OK":
            warnings.append(npm_result.status)
        elif npm_result.data.get("capture_manifest"):
            npm_import = ingest_capture(session, Path(npm_result.data["capture_manifest"]))
        previous_searches = session.scalars(
            select(SearchRecord).order_by(SearchRecord.requested_at)
        ).all()
        last_by_query = {r.query: r.requested_at for r in previous_searches}
    request_limit = min(
        config["max_requests"], config["max_search_credits"] // config["max_attempts_per_request"]
    )
    for query in config["queries"][:request_limit]:
        last_seen = last_by_query.get(query)
        start = (
            now - timedelta(days=config["weekly_lookback_days"])
            if not last_seen or now.weekday() == 0 or (now - utc(last_seen)).days >= 7
            else utc(last_seen) - timedelta(days=config["overlap_days"])
        )
        result = search.search(
            query,
            max_results=config["max_results_per_topic"],
            start_date=start.date().isoformat(),
            end_date=now.date().isoformat(),
        )
        with Session(engine) as session, session.begin():
            record_health(session, result)
            if result.status != "OK":
                warnings.append(result.status + ":" + str(result.reason))
                break
            search_id = str(uuid4())
            session.add(
                SearchRecord(
                    search_id=search_id,
                    query=query,
                    requested_at=result.data["requested_at"],
                    response_sha256=result.data["response_sha256"],
                    results_json=result.data["results"],
                )
            )
            search_ids.append(search_id)
            candidates.extend(result.data["results"])
    # V1 source preference is a retrieval order, not a blanket credibility verdict.
    candidates.sort(
        key=lambda item: (
            0 if source_priority(urlsplit(item.get("url", "")).hostname or "") == "priority" else 1
        )
    )
    seen: set[str] = set()
    llm_count, added = 0, 0
    for candidate in candidates:
        if len(seen) >= config["max_documents"]:
            break
        try:
            url = canonical_url(candidate["url"])
        except ValueError:
            continue
        if url in seen:
            continue
        seen.add(url)
        article = retriever.fetch(candidate)
        with Session(engine) as session, session.begin():
            record_health(session, article)
            if article.status != "OK":
                save_source(
                    session,
                    url=url,
                    publisher="discovery_metadata",
                    source_type="discovery_only",
                    seen_at=datetime.now(UTC),
                    published_at=None,
                    content=redact(candidate.get("discovery_snippet", "")),
                    title=redact(candidate.get("title", "")),
                    access_status="METADATA_ONLY",
                    metadata={"exclusion_reason": article.reason},
                )
                warnings.append(article.status + ":" + str(article.reason))
                continue
            a = article.data
            # Link dependencies are resolved only against actual stored source IDs.
            linked = []
            for link in a["links"]:
                try:
                    normalized = canonical_url(link)
                except ValueError:
                    continue
                source_id = session.scalar(
                    select(Source.source_id).where(Source.canonical_url == normalized)
                )
                if source_id:
                    linked.append(source_id)
            # Hosting a public article does not by itself establish original reporting.
            host = a["publisher"]
            source_type = (
                "official_primary"
                if host == "openai.com" or host.endswith(".openai.com")
                else "unclassified_publication"
            )
            sid, vid = save_source(
                session,
                url=a["url"],
                publisher=a["publisher"],
                source_type=source_type,
                seen_at=a["seen_at"],
                published_at=a["published_at"],
                content=a["excerpt"],
                title=a["title"],
                content_digest=a["page_sha256"],
                metadata={
                    "page_sha256": a["page_sha256"],
                    "quote_location": a["quote_location"],
                    "cites_source_ids": linked,
                    "source_priority": a.get("source_priority", "other_publication"),
                    "source_tier_basis": "host and accessible article; original reporting not independently established",
                },
            )
            previous = session.scalar(
                select(ExtractionRecord).where(
                    ExtractionRecord.version_id == vid, ExtractionRecord.status == "OK"
                )
            )
            source = source_version_dict(session.get(Source, sid), session.get(SourceVersion, vid))
        if previous or not a["published_at"] or llm_count >= config["max_llm_documents"]:
            continue
        llm_count += 1
        extraction = extractor.extract(source)
        with Session(engine) as session, session.begin():
            record_health(session, extraction)
            session.add(
                ExtractionRecord(
                    extraction_id=str(uuid4()),
                    version_id=vid,
                    model_id=extraction.data.get(
                        "model_id", getattr(extractor, "model", "unknown")
                    ),
                    prompt_version=extraction.data.get("prompt_version", "claims-v1"),
                    response_sha256=extraction.data.get(
                        "response_sha256", object_hash(extraction.status)
                    ),
                    usage_json=extraction.data.get("usage", {}),
                    status=extraction.status,
                )
            )
            if extraction.status != "OK":
                warnings.append(extraction.status)
                continue
            for raw_claim in extraction.data["claims"]:
                claim = Claim.model_validate(raw_claim)
                valid, reason = verify_claim(claim, {sid: source})
                # Conservative V1 economic-family normalization prevents LLM-invented identities
                # from making dependent financing reports appear independent.
                family = (
                    "financing" if claim.claim_type.startswith("financing") else claim.claim_type
                )
                claim.event_cluster_id = f"OpenAI:{family}:2026"
                cid = (
                    "claim_"
                    + object_hash({"version": vid, "claim": claim.model_dump(mode="json")})[:24]
                )
                if session.get(ClaimRecord, cid):
                    continue
                event_id = "event_" + cid
                session.add(
                    Event(
                        event_id=event_id,
                        event_cluster_id=claim.event_cluster_id,
                        event_type=claim.claim_type,
                        event_at=claim.event_at.isoformat() if claim.event_at else None,
                        effective_at=claim.effective_at.isoformat() if claim.effective_at else None,
                        state_asof=claim.event_status,
                        state_recorded_at=claim.published_at.isoformat(),
                        entity=claim.entity,
                        valuation_basis=claim.valuation_basis,
                    )
                )
                session.flush()
                session.add(
                    ClaimRecord(
                        claim_id=cid,
                        event_id=event_id,
                        source_version_id=vid,
                        claim_key=claim.claim_type,
                        claim_value=str(claim.reported_valuation_trillion),
                        claim_unit="USD_trillion" if claim.reported_valuation_trillion else None,
                        scope={
                            "entity": claim.entity,
                            "basis": claim.valuation_basis,
                            "state": claim.event_status,
                        },
                        supporting_span=claim.supporting_quote,
                        extractor_model=extraction.data["model_id"],
                        extractor_version=extraction.data["prompt_version"],
                        verification_status="VERIFIED" if valid else reason,
                        claim_json=claim.model_dump(mode="json"),
                    )
                )
                added += int(valid)
    if not added:
        warnings.append(
            "NO_EVIDENCE: no new verified claims; existing eligible evidence may still apply"
        )
    return {
        "npm_import": npm_import,
        "npm_status": npm_result.status,
        "warnings": sorted(set(warnings)),
        "search_ids": search_ids,
        "llm_documents": llm_count,
        "documents": len(seen),
        "new_verified_claims": added,
    }

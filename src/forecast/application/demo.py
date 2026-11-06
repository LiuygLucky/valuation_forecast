from copy import deepcopy
from datetime import timedelta

from forecast.audit.hashing import object_hash
from forecast.domain.time_policy import utc


def demo_inputs(as_of):
    """Entirely fictional, relative-time fixtures. Never written into the real source ledger."""
    cutoff = utc(as_of)
    anchor_time = cutoff - timedelta(days=3)
    anchor = {
        "obs_id": "synthetic_anchor",
        "value": "1.20",
        "metric_name": "npm_valuation",
        "unit": "USD_trillion",
        "observed_at": anchor_time.isoformat(),
        "effective_date": anchor_time.date().isoformat(),
        "source_id": "synthetic_npm",
        "source_version_id": "synthetic_npm_v1",
        "quality_flag": "SYNTHETIC",
        "synthetic": True,
        "methodology": "Fictional illustrative anchor; not NPM history",
    }
    records = []
    for name, offset, event, kind in (
        ("accepted", -1, "fictional_round", "financing_valuation_target"),
        ("duplicate", -1, "fictional_round", "financing_valuation_target"),
        ("future", 1, "future_round", "financing_valuation_target"),
        ("absorbed", -5, "old_growth", "revenue"),
    ):
        published = (cutoff + timedelta(days=offset)).isoformat()
        quote = (
            "OpenAI proposed a financing at a post-money valuation of $1.4 trillion."
            if kind.startswith("financing")
            else "OpenAI reported growth in enterprise revenue."
        )
        source: dict = {
            "source_id": "synthetic_" + name,
            "version_id": "synthetic_" + name + "_v1",
            "canonical_url": "https://example.invalid/synthetic/" + name,
            "first_public_at": published,
            "published_at": published,
            "first_seen_at": published,
            "captured_at": published,
            "retrieved_at": published,
            "source_type": "syndicated" if name == "duplicate" else "official_primary",
            "publisher": "SYNTHETIC FIXTURE",
            "raw_excerpt": quote,
            "content_sha256": object_hash(quote),
            "synthetic": True,
            "title": "SYNTHETIC OpenAI example",
            "access_status": "ACCESSIBLE",
            "origin_group_id": event,
            "metadata_json": {},
            "parent_source_id": "synthetic_accepted" if name == "duplicate" else None,
        }
        claim = {
            "source_ids": [source["source_id"]],
            "entity": "OpenAI",
            "claim_type": kind,
            "event_cluster_id": event,
            "event_status": "proposed",
            "event_at": None,
            "effective_at": None,
            "published_at": published,
            "valuation_basis": "post_money",
            "reported_valuation_trillion": "1.4" if kind.startswith("financing") else None,
            "supporting_quote": quote,
            "quote_location": "synthetic paragraph 1",
            "supported": True,
            "causal_mechanisms": [
                "financing_valuation_anchor"
                if kind.startswith("financing")
                else "growth_fundamentals"
            ],
            "direction": "uncertain",
            "uncertainty_notes": ["SYNTHETIC; no actual event"],
            "scenario_tags": [],
            "drivers": [],
            "mechanism_path_ids": [],
            "alternative_explanations": [
                "Proposed transaction may never close; growth may raise costs."
            ],
            "hypothesis": "Illustrative uncalibrated mechanism",
            "synthetic": True,
        }
        records.append(
            {
                "claim_id": "synthetic_claim_" + name,
                "claim_json": claim,
                "verification_status": "VERIFIED",
                "source": source,
            }
        )
    return deepcopy(
        {
            "anchor": anchor,
            "observations": [anchor],
            "features": [],
            "claims": records,
            "sources": [r["source"] for r in records],
        }
    )

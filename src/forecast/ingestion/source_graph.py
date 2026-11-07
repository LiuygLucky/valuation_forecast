import networkx as nx

from forecast.agent.event_state import compare_claims, valid_transition
from forecast.audit.hashing import object_hash
from forecast.domain.time_policy import availability_reason, utc


def build_clusters(records: list[dict], as_of, *, archived=False):
    """Connected components combine origin chains AND economic event identity conservatively."""
    graph = nx.Graph()
    included, excluded = {}, []
    for row in records:
        cid = row["claim_id"]
        claim, source = row["claim_json"], row["source"]
        reason = availability_reason(source, as_of, archived)
        if utc(claim["published_at"]) > utc(as_of):
            reason = "EXCLUDED_FUTURE"
        if row["verification_status"] != "VERIFIED":
            reason = reason or "REVIEW_REQUIRED"
        if reason:
            excluded.append(
                {
                    "cluster_id": "excluded_" + cid,
                    "claim_ids": [cid],
                    "source_version_ids": [source["version_id"]],
                    "first_public_at": source.get("first_public_at"),
                    "exclusion_reason": reason,
                    "claim": claim,
                    "sources": [source],
                    "dedup_reason": reason,
                }
            )
            continue
        included[cid] = row
        graph.add_node(cid)
        family = "financing" if claim["claim_type"].startswith("financing") else claim["claim_type"]
        identities = ["event:" + claim["event_cluster_id"], "source:" + source["source_id"]]
        for key in ("origin_group_id", "parent_source_id"):
            if source.get(key):
                identities.append(
                    ("source:" if key == "parent_source_id" else "origin:") + source[key]
                )
        identities.extend(
            "source:" + s for s in source.get("metadata_json", {}).get("cites_source_ids", [])
        )
        for identity in identities:
            graph.add_edge(cid, family + ":" + identity)
    clusters = []
    for component in nx.connected_components(graph):
        rows = [included[cid] for cid in component if cid in included]
        rows.sort(key=lambda r: (utc(r["claim_json"]["published_at"]), r["claim_id"]))
        latest = rows[-1]
        reason = None
        # Within an event use latest available state once; same-state disagreements need review.
        events: dict[str, dict] = {}
        for row in rows:
            claim = row["claim_json"]
            old = events.get(claim["event_cluster_id"])
            if old and (
                (
                    claim["claim_type"].startswith("financing")
                    and not valid_transition(old["event_status"], claim["event_status"])
                )
                or compare_claims(old, claim) == "CONTRADICTS"
            ):
                reason = "REVIEW_REQUIRED"
            events[claim["event_cluster_id"]] = claim
        if latest["claim_json"]["event_status"] == "corrected":
            reason = "REVIEW_REQUIRED"
        # A later reprint must not make old information appear new to the overlap detector.
        same_fact = [
            r for r in rows if compare_claims(r["claim_json"], latest["claim_json"]) == "SUPPORTS"
        ]
        representative = min(
            same_fact, key=lambda r: (utc(r["claim_json"]["published_at"]), r["claim_id"])
        )
        clusters.append(
            {
                "cluster_id": "cluster_" + object_hash(sorted(r["claim_id"] for r in rows))[:24],
                "claim_ids": [r["claim_id"] for r in rows],
                "representative_claim_id": representative["claim_id"],
                "source_version_ids": sorted({r["source"]["version_id"] for r in rows}),
                "first_public_at": representative["claim_json"]["published_at"],
                "exclusion_reason": reason,
                "claim": representative["claim_json"],
                "sources": [r["source"] for r in rows],
                "duplicate_count": len(rows) - len(events),
                "dedup_reason": "same event/origin/citation; latest available state used once",
            }
        )
    return sorted(clusters + excluded, key=lambda c: c["cluster_id"])

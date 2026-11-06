ORDER = {"rumored": 0, "proposed": 1, "committed": 2, "closed": 3}


def valid_transition(before: str, after: str) -> bool:
    if before == after:
        return True
    if before == "closed":
        return after == "corrected"
    if before in ("cancelled", "expired", "corrected"):
        return False
    return after in ("cancelled", "expired") or (after in ORDER and ORDER[after] >= ORDER[before])


def compare_claims(a: dict, b: dict) -> str:
    fields = ("entity", "claim_type", "valuation_basis", "event_status", "effective_at", "event_at")
    if a["event_cluster_id"] != b["event_cluster_id"] or any(a.get(k) != b.get(k) for k in fields):
        return "NON_CONFLICT_DIFFERENT_SCOPE"
    return (
        "CONTRADICTS"
        if a.get("reported_valuation_trillion") != b.get("reported_valuation_trillion")
        else "SUPPORTS"
    )

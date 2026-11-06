import re
from decimal import Decimal

from forecast.domain.schemas import Claim
from forecast.domain.time_policy import utc


def verify_claim(claim: Claim, sources: dict[str, dict]) -> tuple[bool, str]:
    if not claim.supported or any(s not in sources for s in claim.source_ids):
        return False, "UNKNOWN_SOURCE_OR_UNSUPPORTED"
    if not claim.alternative_explanations:
        return False, "MISSING_ALTERNATIVE"
    for sid in claim.source_ids:
        source = sources[sid]
        quote = claim.supporting_quote
        if quote not in source["raw_excerpt"]:
            return False, "QUOTE_NOT_IN_SOURCE"
        if "openai" not in (source.get("title", "") + quote).lower():
            return False, "ENTITY_NOT_SUPPORTED"
        if source.get("access_status") != "ACCESSIBLE" or source.get("source_type") in (
            "commentary",
            "rumor",
            "discovery_only",
        ):
            return False, "SOURCE_NOT_PRIMARY_EVIDENCE"
        if not source.get("published_at") or utc(claim.published_at) != utc(source["published_at"]):
            return False, "PUBLICATION_TIME_MISMATCH"
        if claim.synthetic != bool(source.get("synthetic")):
            return False, "SYNTHETIC_MISMATCH"
        if claim.claim_type == "financing_completed" and claim.event_status != "closed":
            return False, "COMPLETION_STATE_MISMATCH"
        scope_patterns = {
            "pre_money": r"pre[- ]money",
            "post_money": r"post[- ]money",
            "secondary_implied": r"secondary|tender",
            "npm_valuation": r"NPM|Nasdaq Private Market",
        }
        if (
            claim.reported_valuation_trillion is not None
            and claim.valuation_basis in scope_patterns
        ):
            if not re.search(scope_patterns[claim.valuation_basis], quote, re.IGNORECASE):
                return False, "VALUATION_BASIS_NOT_SUPPORTED"
        if claim.reported_valuation_trillion is not None:
            # A value must occur WITH currency, scale and valuation context in its exact quote.
            if not re.search(r"valu(?:ation|ed)|worth", quote, re.I):
                return False, "VALUATION_SCOPE_NOT_SUPPORTED"
            values = []
            amount_pattern = r"(?:\$|USD\s*)([\d,.]+)\s*(trillion|billion|million|tn|bn)\b"
            valuation_pattern = (
                r"(?:valuation\s+(?:of\s+|at\s+)?|valued\s+at\s+|worth\s+)" + amount_pattern
            )
            for m in re.finditer(valuation_pattern, quote, re.I):
                scale = {
                    "trillion": "1",
                    "tn": "1",
                    "billion": ".001",
                    "bn": ".001",
                    "million": ".000001",
                }
                values.append(Decimal(m[1].replace(",", "")) * Decimal(scale[m[2].lower()]))
            if claim.reported_valuation_trillion not in values:
                return False, "VALUE_NOT_SUPPORTED"
        state_patterns = {
            "closed": r"closed|completed|finalized",
            "proposed": r"propos|talks|seeking|target",
            "committed": r"commit|signed",
            "cancelled": r"cancel|withdraw",
            "expired": r"expir",
        }
        if claim.claim_type.startswith("financing"):
            pattern = state_patterns.get(claim.event_status)
            if pattern and not re.search(pattern, quote, re.I):
                return False, "STATE_NOT_SUPPORTED"
            if claim.event_status == "closed" and re.search(
                r"not closed|not completed|may close|could close", quote, re.I
            ):
                return False, "NEGATED_CLOSURE"
    return True, "VERIFIED"

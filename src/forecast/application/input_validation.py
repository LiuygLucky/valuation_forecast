from pathlib import Path

from forecast.audit.hashing import object_hash, sha256, stable_json
from forecast.domain.time_policy import availability_reason, utc


def validate_frozen_inputs(inputs, as_of, mode):
    anchor = inputs.get("anchor")
    if not anchor:
        raise ValueError("NO_VALID_ANCHOR")
    if utc(anchor["observed_at"]) > utc(as_of):
        raise ValueError("ANCHOR_TIME_LEAKAGE")
    if mode == "DEMO":
        if not anchor.get("synthetic"):
            raise ValueError("DEMO_REQUIRES_SYNTHETIC_INPUTS")
        return
    sources = {s["version_id"]: s for s in inputs["sources"]}
    source = sources.get(anchor["source_version_id"])
    if not source or source.get("synthetic") or anchor.get("synthetic"):
        raise ValueError("ANCHOR_SOURCE_INVALID")
    archived = mode == "HISTORICAL_ARCHIVED"
    if availability_reason(source, as_of, archived):
        raise ValueError("ANCHOR_TIME_LEAKAGE")
    if mode != "PROVISIONAL" and anchor["quality_flag"] != "VERIFIED":
        raise ValueError("NO_VALID_ANCHOR")
    if anchor["metric_name"] != "npm_valuation" or anchor["unit"] != "USD_trillion":
        raise ValueError("ANCHOR_METRIC_MISMATCH")
    used = {anchor["source_version_id"]}
    for feature in inputs["features"]:
        if utc(feature["first_public_at"]) > utc(as_of) or utc(feature["first_seen_at"]) > utc(
            as_of
        ):
            raise ValueError("FEATURE_TIME_LEAKAGE")
        used.add(feature["source_version_id"])
    for claim in inputs["claims"]:
        candidate = claim["source"]
        if candidate["version_id"] not in sources or object_hash(candidate) != object_hash(
            sources[candidate["version_id"]]
        ):
            raise ValueError("CLAIM_SOURCE_MISMATCH")
        if not availability_reason(candidate, as_of, archived):
            used.add(candidate["version_id"])
    for version in used:
        source = sources[version]
        if source.get("synthetic") or availability_reason(source, as_of, archived):
            raise ValueError("INPUT_SOURCE_INVALID")
        if archived:
            if not source.get("archive_verified") or not source.get("archive_capture_at"):
                raise ValueError("ARCHIVE_PROOF_REQUIRED")
            path = Path(source.get("archive_uri") or "")
            expected = source.get("metadata_json", {}).get("artifact_sha256")
            if not path.is_file() or not expected or sha256(path.read_bytes()) != expected:
                raise ValueError("ARCHIVE_HASH_MISMATCH")


def freeze_task_contract(directory: Path, task: dict):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "frozen_task_config.json"
    serialized = stable_json(task)
    try:
        with path.open("x", encoding="utf-8") as f:
            f.write(serialized)
    except FileExistsError:
        if path.read_text(encoding="utf-8") != serialized:
            raise ValueError("FROZEN_TASK_CONFIG_CHANGED")

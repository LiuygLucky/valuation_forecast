import importlib.metadata
import platform
import subprocess

from forecast.audit.hashing import object_hash, sha256
from forecast.config import ROOT


def code_identity():
    files = sorted((ROOT / "src" / "forecast").rglob("*.py"))
    digest = object_hash({str(p.relative_to(ROOT)): sha256(p.read_bytes()) for p in files})
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        commit = "UNVERSIONED"
    return {"git_commit": commit, "source_sha256": digest}


def library_versions():
    return {"python": platform.python_version()} | {
        name: importlib.metadata.version(name)
        for name in ("numpy", "scipy", "pydantic", "sqlalchemy", "alembic", "httpx", "networkx")
    }


def input_manifest(inputs):
    return [
        {
            "kind": key,
            "id": row.get(
                "version_id", row.get("obs_id", row.get("claim_id", row.get("feature_id")))
            ),
            "sha256": object_hash(row),
        }
        for key in ("sources", "observations", "features", "claims")
        for row in inputs[key]
    ]

import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from forecast.audit.hashing import assert_no_secrets, object_hash, redact, sha256, stable_json
from forecast.audit.manifest import code_identity, input_manifest, library_versions
from forecast.audit.snapshot import read_snapshot, write_snapshot


def test_hashing_redaction_and_types(monkeypatch, tmp_path):
    assert object_hash({"b": 1, "a": 2}) == object_hash({"a": 2, "b": 1})
    assert sha256("abc") == sha256(b"abc")
    assert "1.45" in stable_json({"x": Decimal("1.45"), "now": datetime.now(UTC), "path": tmp_path})
    monkeypatch.setenv("TAVILY_API_KEY", "private-test-value")
    assert redact("private-test-value") == "[REDACTED]"
    with pytest.raises(ValueError):
        assert_no_secrets({"secret": "private-test-value"})
    with pytest.raises(TypeError):
        stable_json(object())
    assert "python" in library_versions()
    assert len(code_identity()["source_sha256"]) == 64


def test_snapshot_immutable_hash_and_atomic_cleanup(tmp_path):
    path, hashes = write_snapshot(
        tmp_path, "run", {"value.json": {"a": 1}, "report.md": "report"}, {}
    )
    manifest, docs = read_snapshot(path)
    assert docs["value.json"] == {"a": 1}
    assert "manifest.json" in hashes
    with pytest.raises(FileExistsError):
        write_snapshot(tmp_path, "run", {}, {})
    (path / "value.json").write_text("{}")
    with pytest.raises(ValueError, match="HASH_MISMATCH"):
        read_snapshot(path)
    with pytest.raises(ValueError):
        write_snapshot(tmp_path, "run2", {"../evil": "x"}, {})
    assert not list(tmp_path.glob(".pending_*"))
    manifest["artifact_sha256"] = {"../evil": "abc"}
    (path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="invalid manifest path"):
        read_snapshot(path)


def test_input_manifest(demo):
    manifest = input_manifest(demo)
    assert len(manifest) == len(demo["sources"]) + len(demo["observations"]) + len(demo["claims"])

import json
import os
import shutil
from pathlib import Path
from uuid import uuid4

from forecast.audit.hashing import assert_no_secrets, sha256, stable_json


def write_snapshot(root: Path, run_id: str, documents: dict, manifest: dict):
    root.mkdir(parents=True, exist_ok=True)
    target = root / run_id
    if target.exists():
        raise FileExistsError("immutable snapshot already exists")
    temporary = root / (".pending_" + str(uuid4()))
    temporary.mkdir()
    try:
        hashes = {}
        for name, content in documents.items():
            if Path(name).name != name:
                raise ValueError("flat artifact filenames required")
            assert_no_secrets(content)
            data = content if isinstance(content, str) else stable_json(content)
            path = temporary / name
            with path.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            hashes[name] = sha256(path.read_bytes())
        manifest = manifest | {"artifact_sha256": hashes}
        assert_no_secrets(manifest)
        (temporary / "manifest.json").write_text(stable_json(manifest), encoding="utf-8")
        os.rename(temporary, target)
        return target, hashes | {"manifest.json": sha256((target / "manifest.json").read_bytes())}
    except BaseException:
        # Only our newly created, resolved child directory is removed on failure.
        if temporary.exists() and temporary.resolve().parent == root.resolve():
            shutil.rmtree(temporary)
        raise


def read_snapshot(path: Path):
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    result = {}
    for name, expected in manifest["artifact_sha256"].items():
        if Path(name).name != name:
            raise ValueError("invalid manifest path")
        raw = (path / name).read_bytes()
        if sha256(raw) != expected:
            raise ValueError("SNAPSHOT_HASH_MISMATCH: " + name)
        result[name] = json.loads(raw) if name.endswith(".json") else raw.decode("utf-8")
    return manifest, result

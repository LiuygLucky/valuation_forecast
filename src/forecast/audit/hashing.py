import hashlib
import json
import os
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path


def _default(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (Decimal, Path)):
        return str(value)
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    raise TypeError(type(value).__name__)


def stable_json(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, default=_default)


def sha256(value: bytes | str) -> str:
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def object_hash(value) -> str:
    return sha256(stable_json(value))


def redact(text: str) -> str:
    for name in ("QWEN_API_KEY", "DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "TAVILY_API_KEY"):
        secret = os.getenv(name)
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return re.sub(r"\b(?:sk-|tvly-)[A-Za-z0-9._-]{12,}", "[REDACTED]", text)


def assert_no_secrets(value):
    text = stable_json(value)
    if redact(text) != text:
        raise ValueError("SECRET_IN_ARTIFACT")

import os

import httpx

from forecast.agent.prompts import PROMPT_VERSION, messages
from forecast.audit.hashing import object_hash
from forecast.domain.schemas import Extraction
from forecast.providers.base import DataFetchResult


class DeepSeekExtractor:
    def __init__(self, client=None, api_key=None, model=None):
        self.client = client or httpx.Client(timeout=60, follow_redirects=False)
        self.api_key = api_key if api_key is not None else os.getenv("DEEPSEEK_API_KEY", "")
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")

    def extract(self, source):
        if not self.api_key:
            return DataFetchResult("DeepSeek", "LLM_FAILURE", reason="MISSING_DEEPSEEK_API_KEY")
        payload = {
            "model": self.model,
            "messages": messages(source),
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "max_tokens": 2500,
            "thinking": {"type": "disabled"},
        }
        status = None
        # Initial attempt + two schema/JSON retries. Raw error bodies never leave this provider.
        for _ in range(3):
            try:
                response = self.client.post(
                    "https://api.deepseek.com/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                status = response.status_code
                response.raise_for_status()
                body = response.json()
                parsed = Extraction.model_validate_json(body["choices"][0]["message"]["content"])
                return DataFetchResult(
                    "DeepSeek",
                    "OK",
                    data={
                        "claims": [c.model_dump(mode="json") for c in parsed.claims],
                        "model_id": self.model,
                        "prompt_version": PROMPT_VERSION,
                        "usage": body.get("usage", {}),
                        "response_sha256": object_hash(body),
                    },
                    http_status=status,
                )
            except httpx.HTTPError:
                return DataFetchResult(
                    "DeepSeek", "LLM_FAILURE", http_status=status, reason="HTTP_OR_TRANSPORT_ERROR"
                )
            except (ValueError, KeyError, IndexError, TypeError):
                continue
        return DataFetchResult(
            "DeepSeek",
            "REVIEW_REQUIRED",
            http_status=status,
            reason="INVALID_STRUCTURED_RESPONSE_AFTER_3_ATTEMPTS",
        )

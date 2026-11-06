import os

import httpx

from forecast.agent.prompts import PROMPT_VERSION, messages
from forecast.audit.hashing import object_hash
from forecast.domain.schemas import Extraction
from forecast.providers.base import DataFetchResult


class JsonClaimExtractor:
    provider = "LLM"
    key_env = "LLM_API_KEY"
    model_env = "LLM_MODEL"
    default_model = ""
    base_url_env = "LLM_BASE_URL"
    default_base_url = ""

    def __init__(self, client=None, api_key=None, model=None, base_url=None):
        self.client = client or httpx.Client(timeout=60, follow_redirects=False)
        self.api_key = api_key if api_key is not None else os.getenv(self.key_env, "")
        self.model = model or os.getenv(self.model_env) or self.default_model
        self.base_url = (base_url or os.getenv(self.base_url_env) or self.default_base_url).rstrip(
            "/"
        )

    def model_options(self) -> dict:
        return {}

    def extract(self, source):
        if not self.api_key:
            return DataFetchResult(self.provider, "LLM_FAILURE", reason="MISSING_" + self.key_env)
        payload = {
            "model": self.model,
            "messages": messages(source),
            "temperature": 0,
            "response_format": {"type": "json_object"},
            **self.model_options(),
        }
        status = None
        # Initial attempt + two schema/JSON retries. Raw error bodies never leave this provider.
        for _ in range(3):
            try:
                response = self.client.post(
                    self.base_url + "/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                status = response.status_code
                response.raise_for_status()
                body = response.json()
                parsed = Extraction.model_validate_json(body["choices"][0]["message"]["content"])
                return DataFetchResult(
                    self.provider,
                    "OK",
                    data={
                        "claims": [c.model_dump(mode="json") for c in parsed.claims],
                        "model_id": self.model,
                        "base_url": self.base_url,
                        "prompt_version": PROMPT_VERSION,
                        "usage": body.get("usage", {}),
                        "response_sha256": object_hash(body),
                    },
                    http_status=status,
                )
            except httpx.HTTPError:
                return DataFetchResult(
                    self.provider,
                    "LLM_FAILURE",
                    http_status=status,
                    reason="HTTP_OR_TRANSPORT_ERROR",
                )
            except (ValueError, KeyError, IndexError, TypeError):
                continue
        return DataFetchResult(
            self.provider,
            "REVIEW_REQUIRED",
            http_status=status,
            reason="INVALID_STRUCTURED_RESPONSE_AFTER_3_ATTEMPTS",
        )


class DeepSeekExtractor(JsonClaimExtractor):
    """Retained for explicitly selected legacy integrations; never an automatic fallback."""

    provider = "DeepSeek"
    key_env = "DEEPSEEK_API_KEY"
    model_env = "DEEPSEEK_MODEL"
    default_model = "deepseek-v4-pro"
    base_url_env = "DEEPSEEK_BASE_URL"
    default_base_url = "https://api.deepseek.com"

    def model_options(self) -> dict:
        return {"max_tokens": 2500, "thinking": {"type": "disabled"}}


class QwenExtractor(JsonClaimExtractor):
    provider = "QwenCloud"
    key_env = "QWEN_API_KEY"
    model_env = "QWEN_MODEL"
    default_model = "qwen3.8-max"
    base_url_env = "QWEN_BASE_URL"
    default_base_url = "https://maas.qianwenaiapi.com/compatible-mode/v1"

    def __init__(self, client=None, api_key=None, model=None, base_url=None):
        if api_key is None:
            api_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY", "")
        super().__init__(client, api_key, model, base_url)

    def model_options(self) -> dict:
        return {"max_completion_tokens": 2500, "enable_thinking": False}

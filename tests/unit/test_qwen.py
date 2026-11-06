import json

import httpx
import pytest

from forecast.agent.extractor import QwenExtractor
from forecast.audit.hashing import assert_no_secrets, redact


def test_qwen_request_and_schema(demo, monkeypatch):
    monkeypatch.delenv("QWEN_MODEL", raising=False)
    monkeypatch.delenv("QWEN_BASE_URL", raising=False)

    def respond(request):
        assert (
            str(request.url) == "https://maas.qianwenaiapi.com/compatible-mode/v1/chat/completions"
        )
        assert request.headers["Authorization"] == "Bearer fake"
        payload = json.loads(request.content)
        assert payload["model"] == "qwen3.8-max"
        assert payload["enable_thinking"] is False
        assert payload["max_completion_tokens"] == 2500
        assert "thinking" not in payload and "max_tokens" not in payload
        assert payload["response_format"] == {"type": "json_object"}
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({"claims": [demo["claims"][0]["claim_json"]]})
                        }
                    }
                ],
                "usage": {"total_tokens": 30},
            },
        )

    result = QwenExtractor(httpx.Client(transport=httpx.MockTransport(respond)), "fake").extract(
        demo["claims"][0]["source"]
    )
    assert result.provider == "QwenCloud" and result.status == "OK"
    assert result.data["model_id"] == "qwen3.8-max" and len(result.data["claims"]) == 1


def test_qwen_env_no_legacy_key_fallback(monkeypatch):
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "legacy-not-for-qwen")
    assert QwenExtractor().extract({}).reason == "MISSING_QWEN_API_KEY"
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-dashscope")
    assert QwenExtractor().api_key == "test-dashscope"
    monkeypatch.setenv("QWEN_API_KEY", "test-qwen")
    monkeypatch.setenv("QWEN_MODEL", "qwen3.8-max")
    monkeypatch.setenv("QWEN_BASE_URL", "https://gateway.example/v1/")
    instance = QwenExtractor()
    assert instance.api_key == "test-qwen" and instance.base_url == "https://gateway.example/v1"
    assert redact("test-qwen test-dashscope") == "[REDACTED] [REDACTED]"
    with pytest.raises(ValueError):
        assert_no_secrets({"value": "test-qwen"})


def test_qwen_schema_retries_and_http_failures(demo):
    calls = []

    def malformed(request):
        calls.append(request)
        return httpx.Response(200, json={"choices": [{"message": {"content": "invalid"}}]})

    result = QwenExtractor(httpx.Client(transport=httpx.MockTransport(malformed)), "fake").extract(
        demo["claims"][0]["source"]
    )
    assert result.status == "REVIEW_REQUIRED" and len(calls) == 3
    result = QwenExtractor(
        httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(503))), "fake"
    ).extract(demo["claims"][0]["source"])
    assert result.status == "LLM_FAILURE" and result.http_status == 503

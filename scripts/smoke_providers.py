"""Bounded opt-in credential smoke test; outputs only sanitized status and usage."""

import json
from datetime import UTC, datetime

from dotenv import load_dotenv

from forecast.agent.extractor import DeepSeekExtractor
from forecast.application.demo import demo_inputs
from forecast.audit.hashing import assert_no_secrets
from forecast.config import ROOT
from forecast.providers.tavily_search import TavilySearch


def main():
    load_dotenv(ROOT / ".env", override=False)
    search = TavilySearch(max_attempts=1).search("site:openai.com/news OpenAI", max_results=1)
    source = demo_inputs("2026-11-07T00:00:00Z")["claims"][0]["source"]
    llm = DeepSeekExtractor().extract(source)
    results = {
        "checked_at": datetime.now(UTC).isoformat(),
        "synthetic_llm_input": True,
        "providers": [
            {
                "provider": r.provider,
                "status": r.status,
                "http_status": r.http_status,
                "reason": r.reason,
                "usage": r.data.get("usage"),
                "response_sha256": r.data.get("response_sha256"),
            }
            for r in (search, llm)
        ],
    }
    assert_no_secrets(results)
    (ROOT / "docs" / "api_smoke.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

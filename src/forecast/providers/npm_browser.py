"""Read the public rendered page, never a hidden endpoint or an authenticated session."""

import json
import os
import re
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from forecast.audit.hashing import sha256, stable_json
from forecast.config import data_dir, load_config
from forecast.domain.time_policy import ET, utc
from forecast.providers.base import DataFetchResult


def parse_npm_text(text: str, captured_at: str) -> dict:
    if "Private Company Pricing by Nasdaq Private Market" not in text or not re.search(
        r"\bOpenAI\b", text
    ):
        raise ValueError("NPM_PAGE_IDENTITY_MISMATCH")
    values = re.findall(r"(?:^|\n)\s*Valuation\s*\n\s*\$([\d,.]+)\s*([TBM])\b", text)
    dates = re.findall(r"As of\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", text)
    if len(values) != 1 or len(set(dates)) != 1:
        raise ValueError("NPM_FIELDS_MISSING_OR_AMBIGUOUS")
    day = datetime.strptime(dates[0], "%b %d, %Y").date()
    captured = utc(captured_at)
    if day > captured.astimezone(ET).date():
        raise ValueError("NPM_FUTURE_EFFECTIVE_DATE")
    value = (
        Decimal(values[0][0].replace(",", ""))
        * {"T": Decimal(1), "B": Decimal(".001"), "M": Decimal(".000001")}[values[0][1]]
    )
    if not value.is_finite() or value <= 0:
        raise ValueError("NPM_INVALID_VALUE")
    return {
        "company": "OpenAI",
        "metric_type": "npm_valuation",
        "valuation_trillion": str(value),
        "effective_date": day.isoformat(),
        "effective_timestamp_precision": "date",
        "captured_at": captured.isoformat(),
        "synthetic": False,
    }


def render_public_page(url: str) -> dict:
    from playwright.sync_api import sync_playwright

    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(data_dir() / "browser-cache"))
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 1100}, locale="en-US")
            response = page.goto(url, wait_until="domcontentloaded", timeout=45000)
            if response is None or response.status != 200 or page.url.split("?")[0] != url:
                raise ValueError("NPM_ACCESS_RESTRICTED_OR_REDIRECTED")
            page.get_by_role("heading", name="OpenAI", exact=True).wait_for(timeout=30000)
            page.get_by_text(re.compile(r"As of\s+[A-Za-z]+\s+\d+,\s+\d{4}")).wait_for(
                timeout=30000
            )
            text = page.locator("body").inner_text()
            captured_at = datetime.now(UTC).isoformat()
            parsed = parse_npm_text(text, captured_at)
            screenshot = page.screenshot(full_page=True)
            html = page.content()
            # If the visible quote changed while taking evidence, reject the inconsistent bundle.
            if parse_npm_text(page.locator("body").inner_text(), captured_at) != parsed:
                raise ValueError("NPM_CHANGED_DURING_CAPTURE")
            return {
                "text": text,
                "html": html,
                "screenshot": screenshot,
                "url": page.url,
                "captured_at": captured_at,
                "http_status": response.status,
            }
        finally:
            browser.close()


class NpmBrowserProvider:
    def __init__(self, root: Path | None = None, renderer=None):
        self.root = root or data_dir() / "raw" / "npm"
        self.renderer = renderer or render_public_page

    def fetch_latest(self) -> DataFetchResult:
        target = None
        try:
            url = load_config().metric_url
            capture = self.renderer(url)
            browser_export = capture.get("capture_transport") == "codex_browser"
            if capture["url"].split("?")[0] != url or (
                capture["http_status"] != 200
                and not (browser_export and capture["http_status"] is None)
            ):
                raise ValueError("NPM_ACCESS_RESTRICTED_OR_REDIRECTED")
            parsed = parse_npm_text(capture["text"], capture["captured_at"])
            screenshot_name = (
                "page.png" if capture["screenshot"].startswith(b"\x89PNG\r\n\x1a\n") else "page.jpg"
            )
            if screenshot_name == "page.jpg" and not capture["screenshot"].startswith(
                b"\xff\xd8\xff"
            ):
                raise ValueError("NPM_SCREENSHOT_INVALID")
            self.root.mkdir(parents=True, exist_ok=True)
            capture_id = str(uuid4())
            temporary = self.root / (".pending_" + capture_id)
            temporary.mkdir()
            artifacts = {
                "page.txt": capture["text"].encode("utf-8"),
                "page.html": capture["html"].encode("utf-8"),
                screenshot_name: capture["screenshot"],
            }
            for name, payload in artifacts.items():
                (temporary / name).write_bytes(payload)
            manifest = parsed | {
                "capture_id": capture_id,
                "url": url,
                "http_status": capture["http_status"],
                "capture_transport": capture.get("capture_transport", "playwright"),
                "capture_method": "public_browser",
                "verification": "exact DOM metric/date; screenshot retained",
                "public_time_basis": "publicly visible at capture; original publication timestamp unknown",
                "artifacts": {k: sha256(v) for k, v in artifacts.items()},
            }
            (temporary / "capture.json").write_bytes(stable_json(manifest).encode("utf-8"))
            target = self.root / capture_id
            os.rename(temporary, target)
            return DataFetchResult(
                "NPM",
                "OK",
                {"capture_manifest": str(target / "capture.json")},
                http_status=capture["http_status"],
            )
        except Exception as error:
            reason = (
                str(error)
                if isinstance(error, ValueError) and str(error).startswith("NPM_")
                else type(error).__name__
            )
            return DataFetchResult("NPM", "NPM_FETCH_BLOCKED", reason=reason)


def exported_browser_renderer(directory: Path):
    """Explicit import of a browser export; never claims to be a new network fetch."""

    def render(url):
        metadata = json.loads((directory / "transfer.json").read_text(encoding="utf-8"))
        if metadata.get("capture_transport") != "codex_browser":
            raise ValueError("NPM_CAPTURE_TRANSPORT_INVALID")
        return metadata | {
            "text": (directory / "page.txt").read_text(encoding="utf-8"),
            "html": (directory / "page.html").read_text(encoding="utf-8"),
            "screenshot": (directory / "page.png").read_bytes(),
        }

    return render


def read_capture(path: Path) -> tuple[dict, str]:
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("url") != load_config().metric_url or record.get("synthetic") is not False:
        raise ValueError("NPM_CAPTURE_IDENTITY_INVALID")
    if set(record["artifacts"]) not in (
        {"page.txt", "page.html", "page.png"},
        {"page.txt", "page.html", "page.jpg"},
    ):
        raise ValueError("NPM_CAPTURE_ARTIFACTS_MISSING")
    for name, expected in record["artifacts"].items():
        if sha256((path.parent / name).read_bytes()) != expected:
            raise ValueError("NPM_CAPTURE_HASH_MISMATCH")
    text = (path.parent / "page.txt").read_text(encoding="utf-8")
    parsed = parse_npm_text(text, record["captured_at"])
    if any(record[k] != v for k, v in parsed.items()):
        raise ValueError("NPM_CAPTURE_FIELD_MISMATCH")
    return record, text

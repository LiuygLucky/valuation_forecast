import pytest

from forecast.application.demo import demo_inputs
from forecast.db.session import engine_for, init_db


@pytest.fixture(autouse=True)
def no_external_npm_browser(monkeypatch):
    monkeypatch.setattr(
        "forecast.providers.npm_browser.render_public_page",
        lambda url: (_ for _ in ()).throw(RuntimeError("OFFLINE_TEST")),
    )


@pytest.fixture
def engine(tmp_path):
    instance = init_db(engine_for(tmp_path / "test.sqlite3"))
    yield instance
    instance.dispose()


@pytest.fixture
def demo():
    return demo_inputs("2026-11-07T17:00:00+00:00")

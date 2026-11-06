from streamlit.testing.v1 import AppTest

from forecast.config import ROOT


def test_dashboard_load_and_demo_button(tmp_path, monkeypatch):
    monkeypatch.setenv("FORECAST_DATA_DIR", str(tmp_path / "dashboard"))
    app = AppTest.from_file(ROOT / "dashboard/app.py", default_timeout=30).run()
    assert not app.exception
    app.button[0].click().run(timeout=30)
    assert not app.exception
    assert any("完成" in item.value for item in app.success)

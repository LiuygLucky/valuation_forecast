from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from alembic import command
from forecast.config import ROOT, data_dir


def engine_for(path: Path | None = None):
    path = path or data_dir() / "forecast.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine("sqlite:///" + path.as_posix(), connect_args={"timeout": 30})

    @event.listens_for(engine, "connect")
    def pragmas(connection, _):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

    return engine


def init_db(engine=None):
    engine = engine or engine_for()
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")
    return engine


def session_for(engine=None) -> Session:
    return Session(engine or engine_for())

"""Initial append-only ledger, versioned schema baseline."""

import re
from pathlib import Path

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    schema = Path(__file__).with_name("schema_0001.sql").read_text(encoding="utf-8")
    for statement in schema.split(";"):
        if statement.strip():
            op.execute(statement)
    for table in re.findall(r"CREATE TABLE (\w+)", schema):
        for operation in ("UPDATE", "DELETE"):
            condition = "WHEN OLD.status != 'RUNNING'" if table == "prediction_runs" else ""
            op.execute(
                f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{operation.lower()} "
                f"BEFORE {operation} ON {table} {condition} BEGIN "
                "SELECT RAISE(ABORT, 'immutable audit record'); END"
            )


def downgrade():
    raise RuntimeError("Audit ledger downgrade is deliberately unsupported; restore a backup.")

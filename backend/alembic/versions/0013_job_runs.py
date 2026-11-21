"""Job runs: when each scheduled job last ran and last succeeded, for /metrics and the operator.

One row per job (`findings.detect`, `overlaps.detect`, `intake.process`, `alerts.deliver`, `audit.verify`,
`backup`, ...). The worker writes its jobs' rows; the backup service writes `backup` as the database
superuser (it already connects as such). Counts and times only. Read by system, admin, oversight and auditor.

Revision ID: 0013
"""
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

UPGRADE = """
CREATE TABLE sethu.job_runs (
    name         text PRIMARY KEY CHECK (name ~ '^[a-z][a-z0-9_.-]{1,60}$'),
    last_run_at  timestamptz NOT NULL,
    last_ok_at   timestamptz,
    last_ok      boolean NOT NULL,
    runs         bigint NOT NULL DEFAULT 1,
    failures     bigint NOT NULL DEFAULT 0
);
ALTER TABLE sethu.job_runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY job_runs_read ON sethu.job_runs FOR SELECT USING (sethu.ctx_sees_all());
CREATE POLICY job_runs_insert ON sethu.job_runs FOR INSERT WITH CHECK (sethu.ctx_role() IN ('admin','system'));
CREATE POLICY job_runs_update ON sethu.job_runs FOR UPDATE
    USING (sethu.ctx_role() IN ('admin','system')) WITH CHECK (sethu.ctx_role() IN ('admin','system'));
GRANT SELECT, INSERT, UPDATE ON sethu.job_runs TO sethu_app;
GRANT SELECT ON sethu.job_runs TO sethu_auditor;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute("DROP TABLE sethu.job_runs")

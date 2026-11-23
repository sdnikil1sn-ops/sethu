"""AI provenance and settings (docs/AI-PIPELINE.md).

sethu.ai_runs: one row per call of the AI router: task, subject, provider, model and version, the path taken
(primary, fallback, last resort; none when it went to a person), confidence, latency, status and why earlier
providers fell through. Identifiers and numbers only: never the payload or the output. Append-only: no UPDATE or
DELETE policy and no such grant. Read by the roles that see every bureau, and by anyone who may read the complaint a
run is about; written by the system principal (the ai-worker) and admin.

sethu.app_settings: small runtime settings as JSON values, starting with each AI task's minimum confidence
(`ai.<task>.min_confidence`). Read by every signed-in role; written by admin and system.

Revision ID: 0014
"""
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

UPGRADE = """
CREATE TABLE sethu.ai_runs (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    task           text NOT NULL CHECK (task ~ '^[a-z][a-z0-9_.-]{1,60}$'),
    subject_type   text CHECK (subject_type ~ '^[a-z][a-z_]{1,40}$'),
    subject_id     text CHECK (length(subject_id) <= 100),
    provider       text CHECK (length(provider) <= 100),
    model_name     text CHECK (length(model_name) <= 200),
    model_version  text CHECK (length(model_version) <= 100),
    path           text CHECK (path IN ('primary', 'fallback', 'last_resort')),
    confidence     numeric(6,5) CHECK (confidence BETWEEN 0 AND 1),
    latency_ms     integer NOT NULL CHECK (latency_ms >= 0),
    status         text NOT NULL CHECK (status IN ('ok', 'human_review')),
    error          text CHECK (length(error) <= 1000),
    created_at     timestamptz NOT NULL DEFAULT now(),
    CHECK ((status = 'ok') = (path IS NOT NULL AND provider IS NOT NULL))
);
CREATE INDEX ai_runs_created ON sethu.ai_runs (created_at);
CREATE INDEX ai_runs_subject ON sethu.ai_runs (subject_type, subject_id);
ALTER TABLE sethu.ai_runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY ai_runs_read ON sethu.ai_runs FOR SELECT USING (
    sethu.ctx_sees_all()
    OR (subject_type = 'complaint'
        AND EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id::text = ai_runs.subject_id)));
CREATE POLICY ai_runs_insert ON sethu.ai_runs FOR INSERT WITH CHECK (sethu.ctx_role() IN ('system', 'admin'));
GRANT SELECT, INSERT ON sethu.ai_runs TO sethu_app;
GRANT SELECT ON sethu.ai_runs TO sethu_auditor;

CREATE TABLE sethu.app_settings (
    key         text PRIMARY KEY CHECK (key ~ '^[a-z][a-z0-9_.-]{1,100}$'),
    value       jsonb NOT NULL,
    updated_at  timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE sethu.app_settings ENABLE ROW LEVEL SECURITY;
CREATE POLICY app_settings_read ON sethu.app_settings FOR SELECT USING (sethu.ctx_role() IS NOT NULL);
CREATE POLICY app_settings_insert ON sethu.app_settings FOR INSERT WITH CHECK (sethu.ctx_role() IN ('admin', 'system'));
CREATE POLICY app_settings_update ON sethu.app_settings FOR UPDATE
    USING (sethu.ctx_role() IN ('admin', 'system')) WITH CHECK (sethu.ctx_role() IN ('admin', 'system'));
GRANT SELECT, INSERT, UPDATE ON sethu.app_settings TO sethu_app;
GRANT SELECT ON sethu.app_settings TO sethu_auditor;
INSERT INTO sethu.app_settings (key, value) VALUES ('ai.stub.echo.min_confidence', '0.5');
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute("DROP TABLE sethu.app_settings; DROP TABLE sethu.ai_runs")

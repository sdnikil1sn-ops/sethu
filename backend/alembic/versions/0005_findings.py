"""Findings: what the deadlock and bottleneck detectors found.

1. A finding is a transfer loop or stalled transfer on one case, or a bottleneck on a
   bureau's or institution's queue. `key` names the finding, so a detector run that
   sees it again adds nothing (no duplicates). `evidence` holds identifiers and the
   numbers used, never complaint text.
2. Bureau staff read findings that involve their bureau; oversight, admin and auditor
   read all. Only the detector (system, or an admin) writes them.
3. A bureau head of an involved bureau, or oversight, may dismiss or reopen a finding;
   a guard trigger lets them change only the status columns. The detector resolves
   findings that no longer hold.

Revision ID: 0005
"""
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

INVOLVES_CALLER = "sethu.ctx_bureau() = ANY(bureau_ids)"
MAY_DECIDE = f"(sethu.ctx_role() = 'oversight' OR (sethu.ctx_role() = 'bureau_head' AND {INVOLVES_CALLER}))"

UPGRADE = f"""
CREATE TABLE sethu.findings (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    kind            text NOT NULL CHECK (kind IN ('transfer_loop','stalled_transfer','bottleneck')),
    key             text NOT NULL UNIQUE,
    complaint_id    uuid REFERENCES sethu.complaints(id),
    institution_id  uuid REFERENCES sethu.institutions(id),
    bureau_ids      uuid[] NOT NULL,
    evidence        jsonb NOT NULL DEFAULT '{{}}'::jsonb,
    alert_id        uuid REFERENCES sethu.alerts(id),
    status          text NOT NULL DEFAULT 'open' CHECK (status IN ('open','resolved','dismissed')),
    first_seen      timestamptz NOT NULL DEFAULT now(),
    decided_by      uuid REFERENCES sethu.app_users(id),
    decided_at      timestamptz,
    CHECK (cardinality(bureau_ids) > 0)
);
CREATE INDEX findings_status ON sethu.findings (status, kind, first_seen);
CREATE INDEX findings_bureaus ON sethu.findings USING gin (bureau_ids);

ALTER TABLE sethu.findings ENABLE ROW LEVEL SECURITY;

CREATE POLICY findings_read ON sethu.findings FOR SELECT
    USING (sethu.ctx_sees_all() OR {INVOLVES_CALLER});
CREATE POLICY findings_insert ON sethu.findings FOR INSERT
    WITH CHECK (sethu.ctx_role() IN ('admin','system'));
CREATE POLICY findings_detector ON sethu.findings FOR UPDATE
    USING (sethu.ctx_role() IN ('admin','system'))
    WITH CHECK (sethu.ctx_role() IN ('admin','system'));
CREATE POLICY findings_decide ON sethu.findings FOR UPDATE
    USING ({MAY_DECIDE})
    WITH CHECK (status IN ('open','dismissed') AND {MAY_DECIDE});

CREATE FUNCTION sethu.findings_only_status_changes() RETURNS trigger
LANGUAGE plpgsql
SET search_path = sethu, pg_catalog
AS $$
BEGIN
    IF sethu.ctx_role() IN ('admin', 'system') THEN
        RETURN NEW;
    END IF;
    IF (NEW.id, NEW.kind, NEW.key, NEW.complaint_id, NEW.institution_id, NEW.bureau_ids, NEW.evidence,
        NEW.alert_id, NEW.first_seen)
       IS DISTINCT FROM
       (OLD.id, OLD.kind, OLD.key, OLD.complaint_id, OLD.institution_id, OLD.bureau_ids, OLD.evidence,
        OLD.alert_id, OLD.first_seen) THEN
        RAISE EXCEPTION 'only the status of a finding can be changed'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    RETURN NEW;
END
$$;

CREATE TRIGGER findings_only_status_changes BEFORE UPDATE ON sethu.findings
    FOR EACH ROW EXECUTE FUNCTION sethu.findings_only_status_changes();

GRANT SELECT, INSERT, UPDATE ON sethu.findings TO sethu_app;
GRANT SELECT ON sethu.findings TO sethu_auditor;
"""  # noqa: S608 - constants only


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    raise RuntimeError("0005 is not reversible: findings are referenced by the audit log.")

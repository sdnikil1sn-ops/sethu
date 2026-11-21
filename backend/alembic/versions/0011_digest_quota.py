"""Escalation digests and an intake API quota.

1. alerts.bureau_id: an alert addressed to a bureau rather than a link or a case. Deadline escalations are
   sent as one digest per bureau per detector run (case references and counts, never text). The read,
   insert, approve and retry rules now also admit the staff (heads, for deciding) of that bureau. The guard
   trigger is the one from 0008 with bureau_id added to the columns nobody but admin and system may change.
2. intake_sources.rate_per_minute: an optional per-source quota for the intake API; empty means the
   default (SETHU_INTAKE_RATE_PER_MINUTE). Counted from intake_nonces, which records every accepted request.

Revision ID: 0011
"""
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

CONCERNS_CALLER = """(EXISTS (SELECT 1 FROM sethu.overlap_links l WHERE l.id = overlap_link_id)
                      OR EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id = complaint_id)
                      OR bureau_id = sethu.ctx_bureau())"""
IS_BUREAU_STAFF = "sethu.ctx_role() IN ('officer','bureau_head')"
MAY_APPROVE = f"(sethu.ctx_role() = 'oversight' OR (sethu.ctx_role() = 'bureau_head' AND {CONCERNS_CALLER}))"

UPGRADE = f"""
ALTER TABLE sethu.alerts ADD COLUMN bureau_id uuid REFERENCES sethu.bureaus(id);
ALTER TABLE sethu.intake_sources ADD COLUMN rate_per_minute integer CHECK (rate_per_minute BETWEEN 1 AND 10000);
CREATE INDEX intake_nonces_recent ON sethu.intake_nonces (source_id, seen_at);

DROP POLICY alerts_read ON sethu.alerts;
CREATE POLICY alerts_read ON sethu.alerts FOR SELECT
    USING (sethu.ctx_sees_all() OR {CONCERNS_CALLER});
DROP POLICY alerts_insert ON sethu.alerts;
CREATE POLICY alerts_insert ON sethu.alerts FOR INSERT
    WITH CHECK (sethu.ctx_role() IN ('admin','system') OR ({IS_BUREAU_STAFF} AND {CONCERNS_CALLER}));
DROP POLICY alerts_approve ON sethu.alerts;
CREATE POLICY alerts_approve ON sethu.alerts FOR UPDATE
    USING (status = 'pending_approval' AND {MAY_APPROVE})
    WITH CHECK (status IN ('approved', 'rejected') AND {MAY_APPROVE});
DROP POLICY alerts_retry ON sethu.alerts;
CREATE POLICY alerts_retry ON sethu.alerts FOR UPDATE
    USING (status = 'failed' AND sethu.ctx_role() = 'bureau_head' AND {CONCERNS_CALLER})
    WITH CHECK (status = 'approved' AND sethu.ctx_role() = 'bureau_head' AND {CONCERNS_CALLER});

CREATE OR REPLACE FUNCTION sethu.alerts_only_decision_changes() RETURNS trigger
LANGUAGE plpgsql
SET search_path = sethu, pg_catalog
AS $$
BEGIN
    IF sethu.ctx_role() IN ('admin', 'system') THEN
        RETURN NEW;
    END IF;
    IF OLD.status = 'failed' AND NEW.status = 'approved' THEN
        -- A retry: attempts start again, nothing else of the alert may change.
        IF NEW.attempts <> 0 OR NEW.last_error IS NOT NULL OR NEW.next_attempt_at IS NOT NULL
           OR (NEW.id, NEW.kind, NEW.overlap_link_id, NEW.complaint_id, NEW.bureau_id, NEW.recipients, NEW.subject,
               NEW.body, NEW.sent_at, NEW.created_at, NEW.missing_recipients)
              IS DISTINCT FROM
              (OLD.id, OLD.kind, OLD.overlap_link_id, OLD.complaint_id, OLD.bureau_id, OLD.recipients, OLD.subject,
               OLD.body, OLD.sent_at, OLD.created_at, OLD.missing_recipients) THEN
            RAISE EXCEPTION 'a retry only puts the alert back in the queue'
                USING ERRCODE = 'insufficient_privilege';
        END IF;
        RETURN NEW;
    END IF;
    IF (NEW.id, NEW.kind, NEW.overlap_link_id, NEW.complaint_id, NEW.bureau_id, NEW.recipients, NEW.subject,
        NEW.body, NEW.sent_at, NEW.attempts, NEW.last_error, NEW.created_at, NEW.missing_recipients,
        NEW.next_attempt_at)
       IS DISTINCT FROM
       (OLD.id, OLD.kind, OLD.overlap_link_id, OLD.complaint_id, OLD.bureau_id, OLD.recipients, OLD.subject,
        OLD.body, OLD.sent_at, OLD.attempts, OLD.last_error, OLD.created_at, OLD.missing_recipients,
        OLD.next_attempt_at) THEN
        RAISE EXCEPTION 'only the decision on an alert can be changed'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    RETURN NEW;
END
$$;
"""  # noqa: S608 - constants only


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    raise RuntimeError("0011 is not reversible: digest alerts are referenced by findings and the audit log.")

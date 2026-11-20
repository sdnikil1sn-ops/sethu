"""Alert delivery: backoff, a final failure, and a person's retry.

1. `alerts.next_attempt_at`: after a failed send the worker waits (exponential backoff) before
   trying again; after the maximum number of attempts the alert becomes `failed` with the reason.
2. A bureau head of a bureau the alert concerns may put a `failed` alert back to `approved` (Retry).
   Admin already may (alerts_deliver). Oversight may not.
3. The guard trigger still lets non-admins change only the decision, with one exception: the retry
   itself (failed -> approved) may also reset attempts, last_error and next_attempt_at. Every other
   column is still compared, so a retry cannot rewrite recipients, subject or body.

Revision ID: 0008
"""
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

CONCERNS_CALLER = """(EXISTS (SELECT 1 FROM sethu.overlap_links l WHERE l.id = overlap_link_id)
                      OR EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id = complaint_id))"""

UPGRADE = f"""
ALTER TABLE sethu.alerts ADD COLUMN next_attempt_at timestamptz;
CREATE INDEX alerts_due ON sethu.alerts (next_attempt_at) WHERE status = 'approved';

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
           OR (NEW.id, NEW.kind, NEW.overlap_link_id, NEW.complaint_id, NEW.recipients, NEW.subject, NEW.body,
               NEW.sent_at, NEW.created_at, NEW.missing_recipients)
              IS DISTINCT FROM
              (OLD.id, OLD.kind, OLD.overlap_link_id, OLD.complaint_id, OLD.recipients, OLD.subject, OLD.body,
               OLD.sent_at, OLD.created_at, OLD.missing_recipients) THEN
            RAISE EXCEPTION 'a retry only puts the alert back in the queue'
                USING ERRCODE = 'insufficient_privilege';
        END IF;
        RETURN NEW;
    END IF;
    IF (NEW.id, NEW.kind, NEW.overlap_link_id, NEW.complaint_id, NEW.recipients, NEW.subject, NEW.body,
        NEW.sent_at, NEW.attempts, NEW.last_error, NEW.created_at, NEW.missing_recipients, NEW.next_attempt_at)
       IS DISTINCT FROM
       (OLD.id, OLD.kind, OLD.overlap_link_id, OLD.complaint_id, OLD.recipients, OLD.subject, OLD.body,
        OLD.sent_at, OLD.attempts, OLD.last_error, OLD.created_at, OLD.missing_recipients, OLD.next_attempt_at) THEN
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
    raise RuntimeError("0008 is not reversible: it adds an access policy and changes the alert guard.")

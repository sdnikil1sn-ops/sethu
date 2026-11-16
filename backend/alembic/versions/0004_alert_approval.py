"""Alert approval: bureau heads and oversight decide alerts held in pending_approval.

1. A bureau head of a bureau the alert concerns, or oversight, may move an alert
   from pending_approval to approved or rejected.
2. Outside admin and system (the worker), an update may change only the decision
   columns. Without this, whoever may approve an alert could also rewrite its
   recipients or body, since Row-Level Security cannot compare old and new values.

Revision ID: 0004
"""
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

# Same rule as alerts_read in 0003: the caller can read the alert's link or its case.
CONCERNS_CALLER = """(EXISTS (SELECT 1 FROM sethu.overlap_links l WHERE l.id = overlap_link_id)
                      OR EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id = complaint_id))"""
MAY_APPROVE = f"(sethu.ctx_role() = 'oversight' OR (sethu.ctx_role() = 'bureau_head' AND {CONCERNS_CALLER}))"

UPGRADE = f"""
CREATE POLICY alerts_approve ON sethu.alerts FOR UPDATE
    USING (status = 'pending_approval' AND {MAY_APPROVE})
    WITH CHECK (status IN ('approved', 'rejected') AND {MAY_APPROVE});

CREATE FUNCTION sethu.alerts_only_decision_changes() RETURNS trigger
LANGUAGE plpgsql
SET search_path = sethu, pg_catalog
AS $$
BEGIN
    IF sethu.ctx_role() IN ('admin', 'system') THEN
        RETURN NEW;
    END IF;
    IF (NEW.id, NEW.kind, NEW.overlap_link_id, NEW.complaint_id, NEW.recipients, NEW.subject, NEW.body,
        NEW.sent_at, NEW.attempts, NEW.last_error, NEW.created_at)
       IS DISTINCT FROM
       (OLD.id, OLD.kind, OLD.overlap_link_id, OLD.complaint_id, OLD.recipients, OLD.subject, OLD.body,
        OLD.sent_at, OLD.attempts, OLD.last_error, OLD.created_at) THEN
        RAISE EXCEPTION 'only the decision on an alert can be changed'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    RETURN NEW;
END
$$;

CREATE TRIGGER alerts_only_decision_changes BEFORE UPDATE ON sethu.alerts
    FOR EACH ROW EXECUTE FUNCTION sethu.alerts_only_decision_changes();
"""  # noqa: S608 - constants only


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    raise RuntimeError("0004 is not reversible: it adds an access policy and a guard trigger.")

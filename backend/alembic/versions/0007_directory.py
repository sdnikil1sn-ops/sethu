"""Directory: bureaus managed by admins, people kept in step with their tokens, unreachable alerts named.

1. `bureaus.active` (a bureau is deactivated, never deleted: cases and history point at it).
   Row-Level Security: any signed-in role reads bureaus; only `admin` and `system` create or change them.
2. `app_users`: Row-Level Security. Any signed-in role reads people (names and roles are shown on
   screens). A person may create or update only their own row (`subject` = the token's subject), and
   only with the role and bureau their verified token carries, so nobody can raise their own role in
   SETHU. `admin` and `system` may write any row.
3. `alerts.missing_recipients`: the codes of bureaus that had no bureau head with an e-mail address
   when the alert was written, shown on the Alerts screen instead of being dropped silently. Covered
   by the guard trigger like the alert's other content.

No SECURITY DEFINER: the policies read the request context through the existing sethu.ctx_* functions.

Revision ID: 0007
"""
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

UPGRADE = """
CREATE FUNCTION sethu.ctx_subject() RETURNS text
LANGUAGE sql STABLE AS $$ SELECT nullif(current_setting('app.user_id', true), '') $$;

ALTER TABLE sethu.bureaus ADD COLUMN active boolean NOT NULL DEFAULT true;
ALTER TABLE sethu.bureaus ADD COLUMN updated_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE sethu.bureaus ENABLE ROW LEVEL SECURITY;
CREATE POLICY bureaus_read ON sethu.bureaus FOR SELECT USING (sethu.ctx_role() IS NOT NULL);
CREATE POLICY bureaus_insert ON sethu.bureaus FOR INSERT WITH CHECK (sethu.ctx_role() IN ('admin','system'));
CREATE POLICY bureaus_update ON sethu.bureaus FOR UPDATE
    USING (sethu.ctx_role() IN ('admin','system')) WITH CHECK (sethu.ctx_role() IN ('admin','system'));

ALTER TABLE sethu.app_users ADD COLUMN updated_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE sethu.app_users ENABLE ROW LEVEL SECURITY;
CREATE POLICY app_users_read ON sethu.app_users FOR SELECT USING (sethu.ctx_role() IS NOT NULL);
CREATE POLICY app_users_insert ON sethu.app_users FOR INSERT WITH CHECK (
    sethu.ctx_role() IN ('admin','system')
    OR (subject = sethu.ctx_subject() AND role = sethu.ctx_role()
        AND bureau_id IS NOT DISTINCT FROM sethu.ctx_bureau()));
CREATE POLICY app_users_update ON sethu.app_users FOR UPDATE
    USING (sethu.ctx_role() IN ('admin','system') OR subject = sethu.ctx_subject())
    WITH CHECK (
    sethu.ctx_role() IN ('admin','system')
    OR (subject = sethu.ctx_subject() AND role = sethu.ctx_role()
        AND bureau_id IS NOT DISTINCT FROM sethu.ctx_bureau()));

ALTER TABLE sethu.alerts ADD COLUMN missing_recipients text[] NOT NULL DEFAULT '{}';

-- Same guard as 0004, now also covering missing_recipients.
CREATE OR REPLACE FUNCTION sethu.alerts_only_decision_changes() RETURNS trigger
LANGUAGE plpgsql
SET search_path = sethu, pg_catalog
AS $$
BEGIN
    IF sethu.ctx_role() IN ('admin', 'system') THEN
        RETURN NEW;
    END IF;
    IF (NEW.id, NEW.kind, NEW.overlap_link_id, NEW.complaint_id, NEW.recipients, NEW.subject, NEW.body,
        NEW.sent_at, NEW.attempts, NEW.last_error, NEW.created_at, NEW.missing_recipients)
       IS DISTINCT FROM
       (OLD.id, OLD.kind, OLD.overlap_link_id, OLD.complaint_id, OLD.recipients, OLD.subject, OLD.body,
        OLD.sent_at, OLD.attempts, OLD.last_error, OLD.created_at, OLD.missing_recipients) THEN
        RAISE EXCEPTION 'only the decision on an alert can be changed'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    RETURN NEW;
END
$$;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    raise RuntimeError("0007 is not reversible: it adds access policies and audited columns.")

"""Case tracking: transfers between bureaus, assignee on history, tighter policies.

1. complaints.transferred_from_bureau_id: the bureau that handed a case over and is
   still waiting for an acknowledgement. Row-Level Security cannot let a bureau give
   a row away unless the new row names that bureau as the sender, and the sender
   keeps read access until the receiver acknowledges.
2. case_actions.assignee_id: who a case was assigned to (was free text in the note).
3. case_actions INSERT: only the bureau holding the case (or admin/system). Before
   this, anyone who could read a complaint could add history, auditors included.
4. Audit ledger: the database takes actor and role from the request context when
   there is one, so application code cannot record an entry under another name.

Revision ID: 0002
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

IS_BUREAU_STAFF = "sethu.ctx_role() IN ('officer','bureau_head')"

UPGRADE = f"""
ALTER TABLE sethu.complaints ADD COLUMN transferred_from_bureau_id uuid REFERENCES sethu.bureaus(id);
ALTER TABLE sethu.case_actions ADD COLUMN assignee_id uuid REFERENCES sethu.app_users(id);

DROP POLICY complaints_read ON sethu.complaints;
CREATE POLICY complaints_read ON sethu.complaints FOR SELECT
    USING (sethu.ctx_sees_all()
           OR bureau_id = sethu.ctx_bureau()
           OR transferred_from_bureau_id = sethu.ctx_bureau());

-- Only the holder may change a case. It may hand the case to another bureau only by
-- naming itself as the sender; the receiver clears that when it acknowledges.
DROP POLICY complaints_update ON sethu.complaints;
CREATE POLICY complaints_update ON sethu.complaints FOR UPDATE
    USING (sethu.ctx_role() IN ('admin','system')
           OR ({IS_BUREAU_STAFF} AND bureau_id = sethu.ctx_bureau()))
    WITH CHECK (sethu.ctx_role() IN ('admin','system')
                OR ({IS_BUREAU_STAFF} AND (bureau_id = sethu.ctx_bureau()
                                           OR transferred_from_bureau_id = sethu.ctx_bureau())));

DROP POLICY case_actions_insert ON sethu.case_actions;
CREATE POLICY case_actions_insert ON sethu.case_actions FOR INSERT
    WITH CHECK (sethu.ctx_role() IN ('admin','system')
                OR ({IS_BUREAU_STAFF} AND EXISTS (
                        SELECT 1 FROM sethu.complaints c
                         WHERE c.id = complaint_id AND c.bureau_id = sethu.ctx_bureau())));

-- Same function as in 0001 plus the two actor lines. The hash still covers actor and role.
CREATE OR REPLACE FUNCTION sethu.audit_log_before_insert() RETURNS trigger
LANGUAGE plpgsql
SET search_path = sethu, pg_catalog
AS $$
DECLARE
    last_seq  bigint;
    last_hash text;
BEGIN
    PERFORM pg_advisory_xact_lock(hashtext('sethu.audit_log'));
    SELECT seq, hash INTO last_seq, last_hash
      FROM sethu.audit_log ORDER BY seq DESC LIMIT 1;
    NEW.seq        := COALESCE(last_seq, 0) + 1;
    NEW.ts         := clock_timestamp();
    NEW.actor      := COALESCE(nullif(current_setting('app.user_id', true), ''), NEW.actor);
    NEW.actor_role := COALESCE(sethu.ctx_role(), NEW.actor_role);
    NEW.prev_hash  := COALESCE(last_hash, repeat('0', 64));
    NEW.payload    := COALESCE(NEW.payload, '{{}}'::jsonb);
    NEW.hash       := sethu.audit_hash(NEW.prev_hash, NEW.seq, NEW.ts, NEW.actor,
                          NEW.actor_role, NEW.action, NEW.entity_type, NEW.entity_id, NEW.payload);
    RETURN NEW;
END
$$;
"""  # noqa: S608 - constants only


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    raise RuntimeError("0002 is not reversible: it tightens access policies and the audit trigger.")

"""Case workflow: assignee, deadlines by category, close reasons, reopening, private notes, escalation.

1. complaints.assignee_id: who works the case now (the latest assignment). Back-filled from the history so
   the seeded assignments carry over; derived data, so not audited again (each assignment already is).
2. category_deadlines: days to close a case, per category, set by an admin. A category without a row uses
   the default (SETHU_SLA_DAYS). Read by every signed-in role; written by admin only.
3. case_actions.reason: why a case was closed, from a fixed list. 'reopened' is a new action; its reason is
   the note, which is required.
4. Notes (action 'note') are read only by the officers and heads of the bureau holding the case, and by the
   worker (the deadlock detector counts any action as someone picking the case up). The other history rows
   keep their old rule: whoever can read the case.
5. findings.kind gains 'deadline_escalation': an open case past its deadline, for the holding bureau's head.

Revision ID: 0010
"""
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

CLOSE_REASONS = ("resolved", "no_action_needed", "duplicate", "withdrawn", "outside_jurisdiction")
REASONS_SQL = ", ".join(f"'{r}'" for r in CLOSE_REASONS)

UPGRADE = f"""
ALTER TABLE sethu.complaints ADD COLUMN assignee_id uuid REFERENCES sethu.app_users(id);
CREATE INDEX complaints_assignee_open ON sethu.complaints (assignee_id) WHERE status <> 'closed';
UPDATE sethu.complaints c SET assignee_id = a.assignee_id
  FROM (SELECT DISTINCT ON (complaint_id) complaint_id, assignee_id FROM sethu.case_actions
         WHERE action = 'assigned' AND assignee_id IS NOT NULL ORDER BY complaint_id, created_at DESC) a
 WHERE a.complaint_id = c.id AND c.status <> 'transferred';

CREATE TABLE sethu.category_deadlines (
    category    text PRIMARY KEY CHECK (length(category) BETWEEN 1 AND 100),
    days        smallint NOT NULL CHECK (days BETWEEN 1 AND 365),
    updated_by  uuid REFERENCES sethu.app_users(id),
    updated_at  timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE sethu.category_deadlines ENABLE ROW LEVEL SECURITY;
CREATE POLICY category_deadlines_read ON sethu.category_deadlines FOR SELECT USING (sethu.ctx_role() IS NOT NULL);
CREATE POLICY category_deadlines_insert ON sethu.category_deadlines FOR INSERT
    WITH CHECK (sethu.ctx_role() IN ('admin','system'));
CREATE POLICY category_deadlines_update ON sethu.category_deadlines FOR UPDATE
    USING (sethu.ctx_role() IN ('admin','system')) WITH CHECK (sethu.ctx_role() IN ('admin','system'));
GRANT SELECT, INSERT, UPDATE ON sethu.category_deadlines TO sethu_app;
GRANT SELECT ON sethu.category_deadlines TO sethu_auditor;

ALTER TABLE sethu.case_actions ADD COLUMN reason text;
ALTER TABLE sethu.case_actions DROP CONSTRAINT case_actions_action_check;
ALTER TABLE sethu.case_actions ADD CONSTRAINT case_actions_action_check CHECK (action IN
    ('filed','assigned','transferred','acknowledged','replied','status_changed','closed','reopened','note'));
ALTER TABLE sethu.case_actions ADD CONSTRAINT case_actions_reason_check
    CHECK (reason IS NULL OR (action = 'closed' AND reason IN ({REASONS_SQL})));

DROP POLICY case_actions_read ON sethu.case_actions;
CREATE POLICY case_actions_read ON sethu.case_actions FOR SELECT
    USING ((action <> 'note' AND (sethu.ctx_sees_all()
                                  OR EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id = complaint_id)))
           OR (action = 'note' AND (sethu.ctx_role() = 'system'
                                    OR (sethu.ctx_role() IN ('officer','bureau_head') AND EXISTS (
                                            SELECT 1 FROM sethu.complaints c
                                             WHERE c.id = complaint_id AND c.bureau_id = sethu.ctx_bureau())))));

ALTER TABLE sethu.findings DROP CONSTRAINT findings_kind_check;
ALTER TABLE sethu.findings ADD CONSTRAINT findings_kind_check
    CHECK (kind IN ('transfer_loop','stalled_transfer','bottleneck','category_spike','deadline_escalation'));
"""  # noqa: S608 - constants only


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    raise RuntimeError("0010 is not reversible: closing reasons and escalations are referenced by the audit log.")

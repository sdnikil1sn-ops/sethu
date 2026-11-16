"""Row-Level Security for overlap links and the alert outbox.

A bureau is a party to a link when it holds one of the two cases. Parties (and
the oversight, admin and auditor roles) can read a link; only an officer or head
of a party can decide it; only the detector (system, or an admin starting it by
hand) creates one. An alert is readable by the parties of its link, or by whoever
can read the case it is about; only the worker changes it after it is written.

Revision ID: 0003
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

IS_BUREAU_STAFF = "sethu.ctx_role() IN ('officer','bureau_head')"
# complaint_summaries shows every bureau's cases without text, so this works for both parties.
IS_PARTY = """EXISTS (SELECT 1 FROM sethu.complaint_summaries s
                       WHERE s.id IN (complaint_a, complaint_b) AND s.bureau_id = sethu.ctx_bureau())"""
# Both subqueries are themselves filtered by Row-Level Security.
ALERT_CONCERNS_CALLER = """(EXISTS (SELECT 1 FROM sethu.overlap_links l WHERE l.id = overlap_link_id)
                            OR EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id = complaint_id))"""

UPGRADE = f"""
ALTER TABLE sethu.overlap_links ENABLE ROW LEVEL SECURITY;

CREATE POLICY overlap_links_read ON sethu.overlap_links FOR SELECT
    USING (sethu.ctx_sees_all() OR {IS_PARTY});
CREATE POLICY overlap_links_insert ON sethu.overlap_links FOR INSERT
    WITH CHECK (sethu.ctx_role() IN ('admin','system'));
CREATE POLICY overlap_links_decide ON sethu.overlap_links FOR UPDATE
    USING ({IS_BUREAU_STAFF} AND {IS_PARTY})
    WITH CHECK ({IS_BUREAU_STAFF} AND {IS_PARTY});

ALTER TABLE sethu.alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY alerts_read ON sethu.alerts FOR SELECT
    USING (sethu.ctx_sees_all() OR {ALERT_CONCERNS_CALLER});
CREATE POLICY alerts_insert ON sethu.alerts FOR INSERT
    WITH CHECK (sethu.ctx_role() IN ('admin','system') OR ({IS_BUREAU_STAFF} AND {ALERT_CONCERNS_CALLER}));
CREATE POLICY alerts_deliver ON sethu.alerts FOR UPDATE
    USING (sethu.ctx_role() IN ('admin','system'))
    WITH CHECK (sethu.ctx_role() IN ('admin','system'));
"""  # noqa: S608 - constants only


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    raise RuntimeError("0003 is not reversible: it adds access policies.")

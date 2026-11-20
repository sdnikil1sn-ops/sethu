"""Early warning: a finding may be a regional category spike.

A `category_spike` finding is one state and category whose complaint count in the last
30 days passes a minimum and exceeds its own baseline (the previous 90 days, scaled to
30) by a set ratio. It goes through the same table, key, policies and guard trigger as
the other findings: no new columns, no change to who can read or write.

Revision ID: 0006
"""
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE sethu.findings DROP CONSTRAINT findings_kind_check;
        ALTER TABLE sethu.findings ADD CONSTRAINT findings_kind_check
            CHECK (kind IN ('transfer_loop','stalled_transfer','bottleneck','category_spike'));
    """)


def downgrade() -> None:
    raise RuntimeError("0006 is not reversible: category_spike findings are referenced by the audit log.")

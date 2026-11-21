"""Semantic overlap signal: complaint embeddings (pgvector) and the signals behind each suggestion.

1. complaint_embeddings: one vector per complaint and model, computed by the worker from the complaint text.
   It is derived from the text, so it is protected like the text: a row is readable exactly when its complaint
   is (the policy reads sethu.complaints, whose own policy then applies), and only the worker (system) or an
   admin writes. No API returns it and no log carries it.
2. overlap_links.signals: the values behind a suggestion, e.g. {"trigram": 0.42, "semantic": 0.88,
   "fired": ["trigram", "semantic"], "model": "BAAI/bge-small-en-v1.5"}, shown with the suggestion.

Revision ID: 0012
"""
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

UPGRADE = """
CREATE TABLE sethu.complaint_embeddings (
    complaint_id  uuid NOT NULL REFERENCES sethu.complaints(id),
    model         text NOT NULL,
    embedding     vector(384) NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (complaint_id, model)
);
ALTER TABLE sethu.complaint_embeddings ENABLE ROW LEVEL SECURITY;
CREATE POLICY complaint_embeddings_read ON sethu.complaint_embeddings FOR SELECT
    USING (EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id = complaint_id));
CREATE POLICY complaint_embeddings_write ON sethu.complaint_embeddings FOR INSERT
    WITH CHECK (sethu.ctx_role() IN ('admin','system'));
CREATE POLICY complaint_embeddings_replace ON sethu.complaint_embeddings FOR UPDATE
    USING (sethu.ctx_role() IN ('admin','system')) WITH CHECK (sethu.ctx_role() IN ('admin','system'));
GRANT SELECT, INSERT, UPDATE ON sethu.complaint_embeddings TO sethu_app;

ALTER TABLE sethu.overlap_links ADD COLUMN signals jsonb NOT NULL DEFAULT '{}'::jsonb;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    raise RuntimeError("0012 is not reversible: suggestions keep the signals they were made with.")

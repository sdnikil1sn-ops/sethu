"""AI Phase A3: multilingual matching, semantic institution resolution, classification, officer feedback
(docs/AI-PIPELINE.md, "A3").

1. complaint_embeddings: every vector is labelled with embedding_model and embedding_version; the key includes both,
   so a complaint can hold vectors of several models side by side and a comparison joins on both (vectors of
   different models are never compared). The bge-small vectors made before A3 keep their model name and get the
   version "fastembed-0.9.1"; nothing reads them any more, and the re-embed job adds E5 vectors beside them.
2. institution_embeddings: one vector per registry name and alias (any script), per model and version, made by the
   ai-worker and refreshed when the registry changes. Read and written by the worker (system) and admin only.
3. match_evaluations: the last verdict on each pair the overlap rules allow (matched or not, method, score,
   confidence, the ai_runs row), keyed by what produced it (`match_key`), so a pair is judged again only when that
   changes (a new model version, a new vector, a changed category). Visible like overlap links; system writes.
4. ai_suggestions: the AI's suggested category and institution for a complaint, with its candidates, path (model,
   fallback, officer), confidence and the officer's decision. Visible where the complaint's text is; the worker
   writes; the holding bureau's officers and heads (and admin) decide.
5. ai_feedback: every officer decision on a category, institution or overlap suggestion (who, when, suggested, old,
   new). Append-only: no UPDATE or DELETE policy and no such grant. Audited by the service in the same transaction.
6. classifier_versions: trained category classifiers. The weights are a JSON document of a fixed shape
   (format "sethu-logreg-json-1") with its SHA-256; never a pickle. At most one is active; older ones stay for
   rollback. Read by admin, oversight, auditor and the worker; written by admin and system.
7. review_items may now also be about a category or an institution.
8. Thresholds and margins as settings (sethu.app_settings), with the defaults measured in docs/AI-PIPELINE.md.

Revision ID: 0016
"""
from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None

VISIBLE = "EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id = complaint_id)"
HOLDER = ("EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id = complaint_id AND c.bureau_id = sethu.ctx_bureau())"
          " AND sethu.ctx_role() IN ('officer', 'bureau_head')")
PARTY = ("EXISTS (SELECT 1 FROM sethu.complaint_summaries s WHERE s.id IN (complaint_a, complaint_b)"
         " AND s.bureau_id = sethu.ctx_bureau())")
WORKER = "sethu.ctx_role() IN ('admin', 'system')"

UPGRADE = f"""
ALTER TABLE sethu.complaint_embeddings RENAME COLUMN model TO embedding_model;
ALTER TABLE sethu.complaint_embeddings ADD COLUMN embedding_version text NOT NULL DEFAULT 'fastembed-0.9.1';
ALTER TABLE sethu.complaint_embeddings ALTER COLUMN embedding_version DROP DEFAULT;
ALTER TABLE sethu.complaint_embeddings DROP CONSTRAINT complaint_embeddings_pkey;
ALTER TABLE sethu.complaint_embeddings ADD PRIMARY KEY (complaint_id, embedding_model, embedding_version);
ALTER TABLE sethu.complaint_embeddings ADD CHECK (length(embedding_model) <= 200 AND length(embedding_version) <= 100);
CREATE INDEX complaint_embeddings_version ON sethu.complaint_embeddings (embedding_model, embedding_version);

CREATE TABLE sethu.institution_embeddings (
    institution_id     uuid NOT NULL REFERENCES sethu.institutions(id),
    label              text NOT NULL CHECK (length(label) BETWEEN 1 AND 300),
    embedding_model    text NOT NULL CHECK (length(embedding_model) <= 200),
    embedding_version  text NOT NULL CHECK (length(embedding_version) <= 100),
    embedding          vector(384) NOT NULL,
    created_at         timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (institution_id, label, embedding_model, embedding_version)
);
ALTER TABLE sethu.institution_embeddings ENABLE ROW LEVEL SECURITY;
CREATE POLICY institution_embeddings_read ON sethu.institution_embeddings FOR SELECT USING ({WORKER});
CREATE POLICY institution_embeddings_insert ON sethu.institution_embeddings FOR INSERT WITH CHECK ({WORKER});
CREATE POLICY institution_embeddings_delete ON sethu.institution_embeddings FOR DELETE USING ({WORKER});
GRANT SELECT, INSERT, DELETE ON sethu.institution_embeddings TO sethu_app;

CREATE TABLE sethu.match_evaluations (
    complaint_a   uuid NOT NULL REFERENCES sethu.complaints(id),
    complaint_b   uuid NOT NULL REFERENCES sethu.complaints(id),
    match_key     text NOT NULL CHECK (length(match_key) <= 300),
    matched       boolean NOT NULL,
    method        text NOT NULL CHECK (method IN ('e5', 'text', 'officer')),
    score         numeric(6,5),
    confidence    numeric(6,5) CHECK (confidence BETWEEN 0 AND 1),
    ai_run_id     uuid REFERENCES sethu.ai_runs(id),
    evaluated_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (complaint_a, complaint_b),
    CHECK (complaint_a < complaint_b)
);
ALTER TABLE sethu.match_evaluations ENABLE ROW LEVEL SECURITY;
CREATE POLICY match_evaluations_read ON sethu.match_evaluations FOR SELECT USING (sethu.ctx_sees_all() OR {PARTY});
CREATE POLICY match_evaluations_insert ON sethu.match_evaluations FOR INSERT WITH CHECK ({WORKER});
CREATE POLICY match_evaluations_update ON sethu.match_evaluations FOR UPDATE USING ({WORKER}) WITH CHECK ({WORKER});
GRANT SELECT, INSERT, UPDATE ON sethu.match_evaluations TO sethu_app;
GRANT SELECT ON sethu.match_evaluations TO sethu_auditor;

CREATE TABLE sethu.ai_suggestions (
    complaint_id   uuid NOT NULL REFERENCES sethu.complaints(id),
    kind           text NOT NULL CHECK (kind IN ('category', 'institution')),
    suggested      text CHECK (length(suggested) <= 200),
    candidates     jsonb NOT NULL DEFAULT '[]',
    path           text NOT NULL CHECK (path IN ('model', 'fallback', 'officer')),
    provider       text CHECK (length(provider) <= 100),
    confidence     numeric(6,5) CHECK (confidence BETWEEN 0 AND 1),
    model_version  text CHECK (length(model_version) <= 100),
    attempt_key    text NOT NULL CHECK (length(attempt_key) <= 300),
    ai_run_id      uuid REFERENCES sethu.ai_runs(id),
    status         text NOT NULL DEFAULT 'suggested'
                   CHECK (status IN ('suggested', 'auto_linked', 'accepted', 'changed', 'rejected')),
    created_at     timestamptz NOT NULL DEFAULT now(),
    decided_by     uuid REFERENCES sethu.app_users(id),
    decided_at     timestamptz,
    PRIMARY KEY (complaint_id, kind)
);
ALTER TABLE sethu.ai_suggestions ENABLE ROW LEVEL SECURITY;
CREATE POLICY ai_suggestions_read ON sethu.ai_suggestions FOR SELECT USING ({VISIBLE});
CREATE POLICY ai_suggestions_insert ON sethu.ai_suggestions FOR INSERT WITH CHECK ({WORKER});
CREATE POLICY ai_suggestions_update ON sethu.ai_suggestions FOR UPDATE
    USING ({WORKER} OR ({HOLDER})) WITH CHECK ({WORKER} OR ({HOLDER}));
GRANT SELECT, INSERT, UPDATE ON sethu.ai_suggestions TO sethu_app;
GRANT SELECT ON sethu.ai_suggestions TO sethu_auditor;

CREATE TABLE sethu.ai_feedback (
    id               bigserial PRIMARY KEY,
    kind             text NOT NULL CHECK (kind IN ('category', 'institution', 'overlap')),
    complaint_id     uuid NOT NULL REFERENCES sethu.complaints(id),
    overlap_link_id  uuid REFERENCES sethu.overlap_links(id),
    decision         text NOT NULL CHECK (decision IN ('accepted', 'rejected', 'changed')),
    suggested        text CHECK (length(suggested) <= 200),
    suggested_path   text CHECK (suggested_path IN ('model', 'fallback', 'officer')),
    old_value        text CHECK (length(old_value) <= 200),
    new_value        text CHECK (length(new_value) <= 200),
    decided_by       uuid REFERENCES sethu.app_users(id),
    decided_at       timestamptz NOT NULL DEFAULT now(),
    CHECK ((kind = 'overlap') = (overlap_link_id IS NOT NULL))
);
CREATE INDEX ai_feedback_kind ON sethu.ai_feedback (kind, decided_at);
ALTER TABLE sethu.ai_feedback ENABLE ROW LEVEL SECURITY;
CREATE POLICY ai_feedback_read ON sethu.ai_feedback FOR SELECT USING (
    sethu.ctx_sees_all() OR {VISIBLE}
    OR EXISTS (SELECT 1 FROM sethu.overlap_links l WHERE l.id = overlap_link_id));
CREATE POLICY ai_feedback_insert ON sethu.ai_feedback FOR INSERT WITH CHECK (
    {WORKER} OR (sethu.ctx_role() IN ('officer', 'bureau_head')
                 AND ({VISIBLE} OR EXISTS (SELECT 1 FROM sethu.overlap_links l WHERE l.id = overlap_link_id))));
GRANT SELECT, INSERT ON sethu.ai_feedback TO sethu_app;            -- append-only: no UPDATE, no DELETE
GRANT USAGE ON SEQUENCE sethu.ai_feedback_id_seq TO sethu_app;
GRANT SELECT ON sethu.ai_feedback TO sethu_auditor;

CREATE TABLE sethu.classifier_versions (
    version            integer PRIMARY KEY CHECK (version >= 1),
    task               text NOT NULL CHECK (task = 'classify.category'),
    format             text NOT NULL CHECK (format = 'sethu-logreg-json-1'),
    artifact           jsonb NOT NULL,
    sha256             text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{{64}}$'),
    embedding_model    text NOT NULL CHECK (length(embedding_model) <= 200),
    embedding_version  text NOT NULL CHECK (length(embedding_version) <= 100),
    metrics            jsonb NOT NULL,
    status             text NOT NULL CHECK (status IN ('active', 'inactive', 'rejected')),
    created_by         uuid REFERENCES sethu.app_users(id),
    created_at         timestamptz NOT NULL DEFAULT now(),
    activated_at       timestamptz
);
CREATE UNIQUE INDEX classifier_versions_one_active ON sethu.classifier_versions ((true)) WHERE status = 'active';
ALTER TABLE sethu.classifier_versions ENABLE ROW LEVEL SECURITY;
CREATE POLICY classifier_versions_read ON sethu.classifier_versions FOR SELECT
    USING (sethu.ctx_role() IN ('admin', 'system', 'oversight', 'auditor'));
CREATE POLICY classifier_versions_insert ON sethu.classifier_versions FOR INSERT WITH CHECK ({WORKER});
CREATE POLICY classifier_versions_update ON sethu.classifier_versions FOR UPDATE USING ({WORKER}) WITH CHECK ({WORKER});
GRANT SELECT, INSERT, UPDATE (status, activated_at) ON sethu.classifier_versions TO sethu_app;
GRANT SELECT ON sethu.classifier_versions TO sethu_auditor;

ALTER TABLE sethu.review_items DROP CONSTRAINT review_items_kind_check;
ALTER TABLE sethu.review_items ADD CONSTRAINT review_items_kind_check
    CHECK (kind IN ('language', 'ocr', 'translation', 'category', 'institution'));

INSERT INTO sethu.app_settings (key, value) VALUES
    ('ai.match.complaints.min_confidence', '0.5'),
    ('ai.match.complaints.e5_threshold', '0.88'),
    ('ai.match.complaints.trigram_threshold', '0.30'),
    ('ai.match.complaints.confidence_span', '0.06'),
    ('ai.match.complaints.agreement_bonus', '0.15'),
    ('ai.match.complaints.disagreement_penalty', '0.25'),
    ('ai.institution.resolve.min_confidence', '0.5'),
    ('ai.institution.resolve.e5_threshold', '0.93'),
    ('ai.institution.resolve.e5_margin', '0.03'),
    ('ai.institution.resolve.fuzzy_threshold', '95'),
    ('ai.institution.resolve.fuzzy_margin', '5'),
    ('ai.classify.category.min_confidence', '0.6'),
    ('ai.embed.text.timeout_seconds', '120'),
    ('ai.embed.reembed_batch', '64')
ON CONFLICT (key) DO NOTHING;
"""  # noqa: S608 - fixed SQL built from the constants above


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute("""
        DELETE FROM sethu.app_settings WHERE key LIKE 'ai.match.%' OR key LIKE 'ai.institution.%'
            OR key LIKE 'ai.classify.%' OR key LIKE 'ai.embed.%';
        ALTER TABLE sethu.review_items DROP CONSTRAINT review_items_kind_check;
        ALTER TABLE sethu.review_items ADD CONSTRAINT review_items_kind_check
            CHECK (kind IN ('language', 'ocr', 'translation'));
        DROP TABLE sethu.classifier_versions; DROP TABLE sethu.ai_feedback; DROP TABLE sethu.ai_suggestions;
        DROP TABLE sethu.match_evaluations; DROP TABLE sethu.institution_embeddings;
        DELETE FROM sethu.complaint_embeddings WHERE embedding_version <> 'fastembed-0.9.1';
        ALTER TABLE sethu.complaint_embeddings DROP CONSTRAINT complaint_embeddings_pkey;
        DROP INDEX sethu.complaint_embeddings_version;
        ALTER TABLE sethu.complaint_embeddings DROP COLUMN embedding_version;
        ALTER TABLE sethu.complaint_embeddings RENAME COLUMN embedding_model TO model;
        ALTER TABLE sethu.complaint_embeddings ADD PRIMARY KEY (complaint_id, model);""")

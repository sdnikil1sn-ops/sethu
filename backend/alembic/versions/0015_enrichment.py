"""AI Phase A2: enrichment, attachments, glossary, human review (docs/AI-PIPELINE.md).

sethu.complaint_enrichment: what the AI pipeline found about a complaint (detected language and confidence, an
English translation and how it was made, glossary tags, text read from attachments). The original complaint text
stays in sethu.complaints.body and is never changed. Readable exactly where the complaint's text is (the complaint
row must be visible); a pending row is written with the complaint; only the worker (system) updates it.

sethu.complaint_attachments: scans and PDFs, stored encrypted (AES-256-GCM, the complainant keyring, the attachment's
id as associated data). Size and type limited by CHECKs. Readable only where the complaint's text is; added by the
officers and heads of the bureau holding the case (and system); the worker updates only its OCR status. No delete.

sethu.glossary_terms: term normalisation (not translation): a term in a language or spelling, its English tag.
Versioned and append-only: an upload adds a whole new version; the newest is used. Read by every role; written by
admin and system.

sethu.review_items: work for a person when the AI is unsure or fails (language, OCR, translation). Visible where the
complaint's summary is to oversight and admin, and to the holding bureau; created by the worker; resolved by the
holding bureau's officers and heads, or admin.

Revision ID: 0015
"""
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

VISIBLE = "EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id = complaint_id)"
HOLDER = ("EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id = complaint_id AND c.bureau_id = sethu.ctx_bureau())"
          " AND sethu.ctx_role() IN ('officer', 'bureau_head')")

UPGRADE = f"""
CREATE TABLE sethu.complaint_enrichment (
    complaint_id         uuid PRIMARY KEY REFERENCES sethu.complaints(id),
    status               text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'done', 'review')),
    language             text CHECK (language ~ '^[a-z]{{2,3}}$' OR language = 'unknown'),
    language_confidence  numeric(6,5) CHECK (language_confidence BETWEEN 0 AND 1),
    language_candidates  text[] NOT NULL DEFAULT '{{}}',
    translated_text      text CHECK (length(translated_text) <= 20000),
    translation_path     text CHECK (translation_path IN ('not_needed', 'model', 'glossary', 'untranslated')),
    tags                 jsonb NOT NULL DEFAULT '[]',
    glossary_version     integer,
    glossary_coverage    numeric(6,5) CHECK (glossary_coverage BETWEEN 0 AND 1),
    ocr_text             text CHECK (length(ocr_text) <= 100000),
    ocr_path             text CHECK (ocr_path IN ('embedded', 'primary', 'fallback', 'manual')),
    attempts             integer NOT NULL DEFAULT 0,
    updated_at           timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX complaint_enrichment_pending ON sethu.complaint_enrichment (updated_at) WHERE status = 'pending';
ALTER TABLE sethu.complaint_enrichment ENABLE ROW LEVEL SECURITY;
CREATE POLICY complaint_enrichment_read ON sethu.complaint_enrichment FOR SELECT USING ({VISIBLE});
CREATE POLICY complaint_enrichment_insert ON sethu.complaint_enrichment FOR INSERT
    WITH CHECK (sethu.ctx_role() IN ('admin', 'system') OR {VISIBLE});
CREATE POLICY complaint_enrichment_update ON sethu.complaint_enrichment FOR UPDATE
    USING (sethu.ctx_role() = 'system') WITH CHECK (sethu.ctx_role() = 'system');
GRANT SELECT, INSERT, UPDATE ON sethu.complaint_enrichment TO sethu_app;
GRANT SELECT ON sethu.complaint_enrichment TO sethu_auditor;

CREATE TABLE sethu.complaint_attachments (
    id            uuid PRIMARY KEY,
    complaint_id  uuid NOT NULL REFERENCES sethu.complaints(id),
    filename      text NOT NULL CHECK (filename ~ '^[A-Za-z0-9._ -]{{1,120}}$'),
    content_type  text NOT NULL CHECK (content_type IN ('application/pdf', 'image/png', 'image/jpeg')),
    size_bytes    integer NOT NULL CHECK (size_bytes BETWEEN 1 AND 10000000),
    sha256        text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{{64}}$'),
    data_enc      bytea NOT NULL,
    uploaded_by   uuid REFERENCES sethu.app_users(id),
    ocr_status    text NOT NULL DEFAULT 'pending' CHECK (ocr_status IN ('pending', 'done', 'review', 'skipped')),
    created_at    timestamptz NOT NULL DEFAULT now(),
    UNIQUE (complaint_id, sha256)
);
CREATE INDEX complaint_attachments_pending ON sethu.complaint_attachments (created_at) WHERE ocr_status = 'pending';
ALTER TABLE sethu.complaint_attachments ENABLE ROW LEVEL SECURITY;
CREATE POLICY complaint_attachments_read ON sethu.complaint_attachments FOR SELECT USING ({VISIBLE});
CREATE POLICY complaint_attachments_insert ON sethu.complaint_attachments FOR INSERT
    WITH CHECK (sethu.ctx_role() = 'system' OR ({HOLDER}));
CREATE POLICY complaint_attachments_update ON sethu.complaint_attachments FOR UPDATE
    USING (sethu.ctx_role() = 'system') WITH CHECK (sethu.ctx_role() = 'system');
GRANT SELECT, INSERT, UPDATE (ocr_status, data_enc) ON sethu.complaint_attachments TO sethu_app;  -- data_enc: rekey
GRANT SELECT (id, complaint_id, filename, content_type, size_bytes, sha256, uploaded_by, ocr_status, created_at)
    ON sethu.complaint_attachments TO sethu_auditor;

CREATE TABLE sethu.glossary_terms (
    id            bigserial PRIMARY KEY,
    version       integer NOT NULL CHECK (version >= 1),
    language      text NOT NULL CHECK (language ~ '^[a-z]{{2,3}}(-latn)?$'),
    term          text NOT NULL CHECK (length(term) BETWEEN 1 AND 200),
    english       text NOT NULL CHECK (english ~ '^[a-z0-9][a-z0-9 /&-]{{0,79}}$'),
    type          text NOT NULL CHECK (type IN ('category', 'document', 'fee', 'approval', 'institution',
                                                'person', 'place', 'action', 'general')),
    notes         text CHECK (length(notes) <= 300),
    needs_review  boolean NOT NULL DEFAULT false,
    created_at    timestamptz NOT NULL DEFAULT now(),
    UNIQUE (version, language, term)
);
ALTER TABLE sethu.glossary_terms ENABLE ROW LEVEL SECURITY;
CREATE POLICY glossary_terms_read ON sethu.glossary_terms FOR SELECT USING (sethu.ctx_role() IS NOT NULL);
CREATE POLICY glossary_terms_insert ON sethu.glossary_terms FOR INSERT
    WITH CHECK (sethu.ctx_role() IN ('admin', 'system'));
GRANT SELECT, INSERT ON sethu.glossary_terms TO sethu_app;
GRANT USAGE ON SEQUENCE sethu.glossary_terms_id_seq TO sethu_app;
GRANT SELECT ON sethu.glossary_terms TO sethu_auditor;

CREATE TABLE sethu.review_items (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    kind           text NOT NULL CHECK (kind IN ('language', 'ocr', 'translation')),
    complaint_id   uuid NOT NULL REFERENCES sethu.complaints(id),
    attachment_id  uuid REFERENCES sethu.complaint_attachments(id),
    ai_run_id      uuid REFERENCES sethu.ai_runs(id),
    reason         text NOT NULL CHECK (length(reason) <= 500),
    status         text NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'resolved', 'dismissed')),
    created_at     timestamptz NOT NULL DEFAULT now(),
    resolved_by    uuid REFERENCES sethu.app_users(id),
    resolved_at    timestamptz
);
CREATE INDEX review_items_open ON sethu.review_items (created_at) WHERE status = 'open';
ALTER TABLE sethu.review_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY review_items_read ON sethu.review_items FOR SELECT USING (sethu.ctx_sees_all() OR {VISIBLE});
CREATE POLICY review_items_insert ON sethu.review_items FOR INSERT WITH CHECK (sethu.ctx_role() = 'system');
CREATE POLICY review_items_update ON sethu.review_items FOR UPDATE
    USING (sethu.ctx_role() IN ('admin', 'system') OR ({HOLDER}))
    WITH CHECK (sethu.ctx_role() IN ('admin', 'system') OR ({HOLDER}));
GRANT SELECT, INSERT, UPDATE (status, resolved_by, resolved_at) ON sethu.review_items TO sethu_app;
GRANT SELECT ON sethu.review_items TO sethu_auditor;

INSERT INTO sethu.app_settings (key, value) VALUES
    ('ai.language.detect.min_confidence', '0.5'),
    ('ai.ocr.read.min_confidence', '0.6'),
    ('ai.translate.to_en.min_confidence', '0.5'),
    ('ai.ocr.max_pages', '10'),
    ('ai.ocr.max_image_pixels', '25000000'),
    ('ai.ocr.read.timeout_seconds', '300'),
    ('ai.translate.to_en.timeout_seconds', '180'),
    ('ai.glossary.tag.min_confidence', '0');
"""  # noqa: S608 - fixed SQL built from the constants above


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute("""DROP TABLE sethu.review_items; DROP TABLE sethu.glossary_terms;
                  DROP TABLE sethu.complaint_attachments; DROP TABLE sethu.complaint_enrichment;
                  DELETE FROM sethu.app_settings WHERE key LIKE 'ai.language.%' OR key LIKE 'ai.ocr.%'
                     OR key LIKE 'ai.translate.%'""")

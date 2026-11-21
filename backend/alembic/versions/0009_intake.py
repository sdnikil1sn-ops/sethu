"""Complaint intake: sources, a durable queue, and replay protection for the intake API.

1. intake_sources: where complaints come from (a portal API, an officer's upload or manual entry, a spool
   folder), the bureau each feeds, a priority and an optional fallback source. A portal's API key is
   stored only as its SHA-256 hash. Health counters (last success, consecutive failures) are kept by the
   worker. Only an admin creates or changes a source (and the dev seed, as system); the worker updates its health
   columns.
2. intake_items: every incoming complaint is written here first, whatever the channel, so nothing is lost
   if processing fails. The complaint (text and complainant details) is held encrypted with the complainant
   keyring; the row itself carries identifiers, the fingerprint and the processing state only. The worker
   creates the complaint, retries with backoff on failure, and after the maximum moves the item to `dead`.
   Bureau staff read their own bureau's items and may mark a near duplicate as reviewed (a guard trigger
   lets them change only the review columns).
3. intake_nonces: each (source, nonce) pair an intake API request has used; a replay is refused.
4. The `intake` role is the API gateway: it reads sources (to check a key), records nonces, and reads and
   adds api-channel items (identifiers and fingerprints; the complaint itself is encrypted) for an active api
   source of the same bureau, so it can refuse a resubmission. It reads no complaints.
5. complaint_ref_seq numbers complaints that arrive through intake (IN-000001, ...).

Revision ID: 0009
"""
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

STAFF_OF_ROW = "(sethu.ctx_role() IN ('officer','bureau_head') AND bureau_id = sethu.ctx_bureau())"

UPGRADE = f"""
CREATE TABLE sethu.intake_sources (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name               text NOT NULL UNIQUE CHECK (name ~ '^[a-z0-9][a-z0-9-]{{1,40}}$'),
    channel            text NOT NULL CHECK (channel IN ('api','upload','manual','spool')),
    priority           smallint NOT NULL DEFAULT 1 CHECK (priority BETWEEN 1 AND 9),
    fallback_source_id uuid REFERENCES sethu.intake_sources(id),
    bureau_id          uuid NOT NULL REFERENCES sethu.bureaus(id),
    active             boolean NOT NULL DEFAULT true,
    marked_down        boolean NOT NULL DEFAULT false,
    key_sha256         text UNIQUE,
    last_success_at    timestamptz,
    last_failure_at    timestamptz,
    failures           integer NOT NULL DEFAULT 0,
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now(),
    CHECK (fallback_source_id IS DISTINCT FROM id),
    CHECK (key_sha256 IS NULL OR channel = 'api')
);

CREATE TABLE sethu.intake_items (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id          uuid NOT NULL REFERENCES sethu.intake_sources(id),
    bureau_id          uuid NOT NULL REFERENCES sethu.bureaus(id),
    channel            text NOT NULL CHECK (channel IN ('api','upload','manual','spool')),
    path               text NOT NULL CHECK (path IN ('primary','fallback')),
    fingerprint        text NOT NULL,
    external_ref       text,
    payload_enc        bytea NOT NULL,
    status             text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','done','duplicate','dead')),
    attempts           integer NOT NULL DEFAULT 0,
    next_attempt_at    timestamptz NOT NULL DEFAULT now(),
    last_error         text,
    complaint_id       uuid REFERENCES sethu.complaints(id),
    duplicate_of       uuid REFERENCES sethu.complaints(id),
    near_duplicate_of  uuid REFERENCES sethu.complaints(id),
    review_state       text CHECK (review_state IN ('pending','reviewed')),
    reviewed_by        uuid REFERENCES sethu.app_users(id),
    reviewed_at        timestamptz,
    received_by        uuid REFERENCES sethu.app_users(id),
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX intake_items_due ON sethu.intake_items (next_attempt_at) WHERE status = 'pending';
CREATE INDEX intake_items_source ON sethu.intake_items (source_id, status);
CREATE INDEX intake_items_fingerprint ON sethu.intake_items (fingerprint);
CREATE UNIQUE INDEX intake_items_external_ref ON sethu.intake_items (source_id, external_ref)
    WHERE external_ref IS NOT NULL AND status IN ('pending','done');

CREATE TABLE sethu.intake_nonces (
    source_id  uuid NOT NULL REFERENCES sethu.intake_sources(id),
    nonce      text NOT NULL,
    seen_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (source_id, nonce)
);

CREATE SEQUENCE sethu.complaint_ref_seq;

ALTER TABLE sethu.intake_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE sethu.intake_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE sethu.intake_nonces ENABLE ROW LEVEL SECURITY;

CREATE POLICY intake_sources_read ON sethu.intake_sources FOR SELECT
    USING (sethu.ctx_sees_all() OR sethu.ctx_role() = 'intake' OR {STAFF_OF_ROW});
CREATE POLICY intake_sources_insert ON sethu.intake_sources FOR INSERT
    WITH CHECK (sethu.ctx_role() IN ('admin','system'));   -- system: the dev seed
CREATE POLICY intake_sources_update ON sethu.intake_sources FOR UPDATE
    USING (sethu.ctx_role() IN ('admin','system'))
    WITH CHECK (sethu.ctx_role() IN ('admin','system'));

CREATE POLICY intake_items_read ON sethu.intake_items FOR SELECT
    USING (sethu.ctx_sees_all() OR {STAFF_OF_ROW}
           OR (sethu.ctx_role() = 'intake' AND channel = 'api'));   -- to refuse a resubmission
CREATE POLICY intake_items_insert ON sethu.intake_items FOR INSERT
    WITH CHECK (sethu.ctx_role() IN ('admin','system')
                OR ({STAFF_OF_ROW} AND channel IN ('upload','manual'))
                OR (sethu.ctx_role() = 'intake' AND channel = 'api' AND EXISTS (
                        SELECT 1 FROM sethu.intake_sources s
                         WHERE s.id = source_id AND s.bureau_id = intake_items.bureau_id
                           AND s.channel = 'api' AND s.active)));
CREATE POLICY intake_items_process ON sethu.intake_items FOR UPDATE
    USING (sethu.ctx_role() IN ('admin','system'))
    WITH CHECK (sethu.ctx_role() IN ('admin','system'));
CREATE POLICY intake_items_review ON sethu.intake_items FOR UPDATE
    USING ({STAFF_OF_ROW} AND review_state = 'pending')
    WITH CHECK ({STAFF_OF_ROW} AND review_state = 'reviewed');

CREATE FUNCTION sethu.intake_items_review_only() RETURNS trigger
LANGUAGE plpgsql
SET search_path = sethu, pg_catalog
AS $$
BEGIN
    IF sethu.ctx_role() IN ('admin', 'system') THEN
        RETURN NEW;
    END IF;
    IF (NEW.id, NEW.source_id, NEW.bureau_id, NEW.channel, NEW.path, NEW.fingerprint, NEW.external_ref,
        NEW.payload_enc, NEW.status, NEW.attempts, NEW.next_attempt_at, NEW.last_error, NEW.complaint_id,
        NEW.duplicate_of, NEW.near_duplicate_of, NEW.received_by, NEW.created_at)
       IS DISTINCT FROM
       (OLD.id, OLD.source_id, OLD.bureau_id, OLD.channel, OLD.path, OLD.fingerprint, OLD.external_ref,
        OLD.payload_enc, OLD.status, OLD.attempts, OLD.next_attempt_at, OLD.last_error, OLD.complaint_id,
        OLD.duplicate_of, OLD.near_duplicate_of, OLD.received_by, OLD.created_at) THEN
        RAISE EXCEPTION 'only the review of an intake item can be changed'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    RETURN NEW;
END
$$;
CREATE TRIGGER intake_items_review_only BEFORE UPDATE ON sethu.intake_items
    FOR EACH ROW EXECUTE FUNCTION sethu.intake_items_review_only();

CREATE POLICY intake_nonces_use ON sethu.intake_nonces FOR ALL
    USING (sethu.ctx_role() IN ('intake','system'))
    WITH CHECK (sethu.ctx_role() IN ('intake','system'));

GRANT SELECT, INSERT, UPDATE ON sethu.intake_sources, sethu.intake_items TO sethu_app;
GRANT SELECT, INSERT, DELETE ON sethu.intake_nonces TO sethu_app;
GRANT USAGE ON SEQUENCE sethu.complaint_ref_seq TO sethu_app;
GRANT SELECT ON sethu.intake_sources, sethu.intake_items TO sethu_auditor;
"""  # noqa: S608 - constants only


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    raise RuntimeError("0009 is not reversible: intake items are referenced by the audit log.")

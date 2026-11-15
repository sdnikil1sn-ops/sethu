"""Core schema: reference data, complaints, overlaps, alert outbox, audit ledger, RLS.

Runs as the schema owner (sethu_owner). The runtime role (sethu_app) gets only
the grants listed at the bottom and is subject to Row-Level Security.

Revision ID: 0001
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

TABLES = """
CREATE TABLE sethu.bureaus (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code        text NOT NULL UNIQUE,
    name        text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sethu.app_users (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    subject       text NOT NULL UNIQUE,            -- OIDC "sub" from Keycloak
    display_name  text NOT NULL,
    email         text,
    role          text NOT NULL CHECK (role IN
                  ('officer','bureau_head','oversight','admin','auditor')),
    bureau_id     uuid REFERENCES sethu.bureaus(id),
    active        boolean NOT NULL DEFAULT true,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sethu.institutions (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    permanent_id  text UNIQUE,
    name          text NOT NULL,
    state         text,
    district      text,
    pin           text,
    created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX institutions_name_trgm ON sethu.institutions USING gin (name gin_trgm_ops);
CREATE INDEX institutions_state_pin ON sethu.institutions (state, pin);

CREATE TABLE sethu.institution_aliases (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id  uuid NOT NULL REFERENCES sethu.institutions(id) ON DELETE CASCADE,
    alias           text NOT NULL,
    source          text NOT NULL DEFAULT 'manual',
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (institution_id, alias)
);
CREATE INDEX institution_aliases_trgm ON sethu.institution_aliases USING gin (alias gin_trgm_ops);

CREATE TABLE sethu.complaints (
    id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    ref                   text NOT NULL UNIQUE,
    source                text NOT NULL,
    bureau_id             uuid NOT NULL REFERENCES sethu.bureaus(id),
    institution_id        uuid REFERENCES sethu.institutions(id),
    institution_name_raw  text NOT NULL,
    resolution_state      text NOT NULL DEFAULT 'unresolved'
                          CHECK (resolution_state IN ('unresolved','auto','officer')),
    category              text,
    status                text NOT NULL DEFAULT 'open'
                          CHECK (status IN ('open','in_progress','transferred','replied','closed')),
    language              text NOT NULL DEFAULT 'en',
    body                  text NOT NULL,
    body_sha256           text NOT NULL,
    complainant_enc       bytea,                   -- encrypted by the application
    filed_at              timestamptz NOT NULL,
    due_at                timestamptz,
    closed_at             timestamptz,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX complaints_institution ON sethu.complaints (institution_id);
CREATE INDEX complaints_bureau_status ON sethu.complaints (bureau_id, status);
CREATE INDEX complaints_due_open ON sethu.complaints (due_at) WHERE status <> 'closed';
CREATE INDEX complaints_body_hash ON sethu.complaints (body_sha256);
CREATE INDEX complaints_body_trgm ON sethu.complaints USING gin (body gin_trgm_ops);

CREATE TABLE sethu.case_actions (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id     uuid NOT NULL REFERENCES sethu.complaints(id),
    action           text NOT NULL CHECK (action IN
                     ('filed','assigned','transferred','acknowledged','replied','status_changed','closed','note')),
    from_bureau_id   uuid REFERENCES sethu.bureaus(id),
    to_bureau_id     uuid REFERENCES sethu.bureaus(id),
    actor_id         uuid REFERENCES sethu.app_users(id),
    note             text,
    acknowledged_at  timestamptz,
    created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX case_actions_complaint ON sethu.case_actions (complaint_id, created_at);
CREATE INDEX case_actions_transfers ON sethu.case_actions (to_bureau_id, created_at)
    WHERE action = 'transferred';

CREATE TABLE sethu.overlap_links (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_a  uuid NOT NULL REFERENCES sethu.complaints(id),
    complaint_b  uuid NOT NULL REFERENCES sethu.complaints(id),
    tier         smallint NOT NULL CHECK (tier BETWEEN 1 AND 3),
    score        numeric(5,4),
    reasons      jsonb NOT NULL DEFAULT '[]'::jsonb,
    status       text NOT NULL DEFAULT 'proposed'
                 CHECK (status IN ('proposed','approved','rejected')),
    decided_by   uuid REFERENCES sethu.app_users(id),
    decided_at   timestamptz,
    created_at   timestamptz NOT NULL DEFAULT now(),
    CHECK (complaint_a < complaint_b),
    UNIQUE (complaint_a, complaint_b, tier)
);
CREATE INDEX overlap_links_status ON sethu.overlap_links (status, created_at);

-- Alert outbox: rows are written in the same transaction as the decision that
-- caused them; a worker delivers them. Nothing is sent before approval.
CREATE TABLE sethu.alerts (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    kind             text NOT NULL CHECK (kind IN ('overlap','bottleneck','early_warning','sla')),
    overlap_link_id  uuid REFERENCES sethu.overlap_links(id),
    complaint_id     uuid REFERENCES sethu.complaints(id),
    status           text NOT NULL DEFAULT 'pending_approval'
                     CHECK (status IN ('pending_approval','approved','sent','rejected','failed')),
    recipients       jsonb NOT NULL DEFAULT '[]'::jsonb,
    subject          text NOT NULL,
    body             text NOT NULL,
    approved_by      uuid REFERENCES sethu.app_users(id),
    approved_at      timestamptz,
    sent_at          timestamptz,
    attempts         integer NOT NULL DEFAULT 0,
    last_error       text,
    created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX alerts_outbox ON sethu.alerts (status, created_at);
"""

AUDIT = """
CREATE TABLE sethu.audit_log (
    seq          bigint PRIMARY KEY,
    ts           timestamptz NOT NULL,
    actor        text NOT NULL,
    actor_role   text,
    action       text NOT NULL,
    entity_type  text,
    entity_id    text,
    payload      jsonb NOT NULL DEFAULT '{}'::jsonb,
    prev_hash    text NOT NULL,
    hash         text NOT NULL UNIQUE
);

-- One canonical encoding, used by both the insert trigger and the verifier.
CREATE FUNCTION sethu.audit_hash(
    p_prev text, p_seq bigint, p_ts timestamptz, p_actor text, p_actor_role text,
    p_action text, p_entity_type text, p_entity_id text, p_payload jsonb
) RETURNS text
LANGUAGE sql STABLE
AS $$
    SELECT encode(sha256(convert_to(
        jsonb_build_array(
            p_prev, p_seq,
            to_char(p_ts AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
            p_actor, p_actor_role, p_action, p_entity_type, p_entity_id, p_payload
        )::text, 'UTF8')), 'hex')
$$;

-- The database, not the application, assigns seq, ts, prev_hash and hash.
CREATE FUNCTION sethu.audit_log_before_insert() RETURNS trigger
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
    NEW.seq       := COALESCE(last_seq, 0) + 1;
    NEW.ts        := clock_timestamp();
    NEW.prev_hash := COALESCE(last_hash, repeat('0', 64));
    NEW.payload   := COALESCE(NEW.payload, '{}'::jsonb);
    NEW.hash      := sethu.audit_hash(NEW.prev_hash, NEW.seq, NEW.ts, NEW.actor,
                         NEW.actor_role, NEW.action, NEW.entity_type, NEW.entity_id, NEW.payload);
    RETURN NEW;
END
$$;

CREATE FUNCTION sethu.audit_log_immutable() RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append-only (% not allowed)', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END
$$;

CREATE TRIGGER audit_log_chain BEFORE INSERT ON sethu.audit_log
    FOR EACH ROW EXECUTE FUNCTION sethu.audit_log_before_insert();
CREATE TRIGGER audit_log_no_change BEFORE UPDATE OR DELETE ON sethu.audit_log
    FOR EACH ROW EXECUTE FUNCTION sethu.audit_log_immutable();
CREATE TRIGGER audit_log_no_truncate BEFORE TRUNCATE ON sethu.audit_log
    FOR EACH STATEMENT EXECUTE FUNCTION sethu.audit_log_immutable();

-- Walks the whole chain. broken_seq is the first row that fails, or NULL.
CREATE FUNCTION sethu.audit_verify()
RETURNS TABLE (ok boolean, checked bigint, broken_seq bigint, reason text)
LANGUAGE plpgsql STABLE
SET search_path = sethu, pg_catalog
AS $$
DECLARE
    r         sethu.audit_log%ROWTYPE;
    expected  bigint := 1;
    prev      text := repeat('0', 64);
    n         bigint := 0;
BEGIN
    FOR r IN SELECT * FROM sethu.audit_log ORDER BY seq LOOP
        IF r.seq <> expected THEN
            RETURN QUERY SELECT false, n, r.seq, format('gap: expected seq %s', expected);
            RETURN;
        END IF;
        IF r.prev_hash <> prev THEN
            RETURN QUERY SELECT false, n, r.seq, 'prev_hash does not match previous row';
            RETURN;
        END IF;
        IF r.hash <> sethu.audit_hash(r.prev_hash, r.seq, r.ts, r.actor, r.actor_role,
                                      r.action, r.entity_type, r.entity_id, r.payload) THEN
            RETURN QUERY SELECT false, n, r.seq, 'row content does not match its hash';
            RETURN;
        END IF;
        prev := r.hash;
        expected := expected + 1;
        n := n + 1;
    END LOOP;
    RETURN QUERY SELECT true, n, NULL::bigint, NULL::text;
END
$$;
"""

RLS = """
-- Request context, set per transaction by the API (SET LOCAL via set_config).
-- Unset context yields NULL, so every policy fails closed.
CREATE FUNCTION sethu.ctx_role() RETURNS text
LANGUAGE sql STABLE AS $$ SELECT nullif(current_setting('app.role', true), '') $$;

CREATE FUNCTION sethu.ctx_bureau() RETURNS uuid
LANGUAGE sql STABLE AS $$ SELECT nullif(current_setting('app.bureau_id', true), '')::uuid $$;

CREATE FUNCTION sethu.ctx_sees_all() RETURNS boolean
LANGUAGE sql STABLE AS $$
    SELECT coalesce(sethu.ctx_role() IN ('oversight','admin','auditor','system'), false)
$$;

ALTER TABLE sethu.complaints ENABLE ROW LEVEL SECURITY;

CREATE POLICY complaints_read ON sethu.complaints FOR SELECT
    USING (sethu.ctx_sees_all() OR bureau_id = sethu.ctx_bureau());
CREATE POLICY complaints_insert ON sethu.complaints FOR INSERT
    WITH CHECK (sethu.ctx_role() IN ('admin','system')
                OR (sethu.ctx_role() IN ('officer','bureau_head') AND bureau_id = sethu.ctx_bureau()));
CREATE POLICY complaints_update ON sethu.complaints FOR UPDATE
    USING (sethu.ctx_role() IN ('admin','system')
           OR (sethu.ctx_role() IN ('officer','bureau_head') AND bureau_id = sethu.ctx_bureau()))
    WITH CHECK (sethu.ctx_role() IN ('admin','system')
                OR (sethu.ctx_role() IN ('officer','bureau_head') AND bureau_id = sethu.ctx_bureau()));

ALTER TABLE sethu.case_actions ENABLE ROW LEVEL SECURITY;

CREATE POLICY case_actions_read ON sethu.case_actions FOR SELECT
    USING (sethu.ctx_sees_all()
           OR EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id = complaint_id));
CREATE POLICY case_actions_insert ON sethu.case_actions FOR INSERT
    WITH CHECK (sethu.ctx_role() IN ('admin','system')
                OR EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id = complaint_id));

-- Cross-bureau visibility without the sensitive columns. The view is owned by
-- the schema owner, so it is not filtered by the policies above; it exposes no
-- complaint text and no complainant data, and still requires a request context.
CREATE VIEW sethu.complaint_summaries AS
    SELECT id, ref, bureau_id, institution_id, category, status,
           filed_at, due_at, closed_at
      FROM sethu.complaints
     WHERE sethu.ctx_role() IS NOT NULL;
"""

GRANTS = """
GRANT USAGE ON SCHEMA sethu TO sethu_app, sethu_auditor;

GRANT SELECT, INSERT, UPDATE ON
    sethu.bureaus, sethu.app_users, sethu.institutions, sethu.institution_aliases,
    sethu.complaints, sethu.overlap_links, sethu.alerts
    TO sethu_app;
GRANT SELECT, INSERT ON sethu.case_actions TO sethu_app;       -- history is never edited
GRANT SELECT ON sethu.complaint_summaries TO sethu_app;
GRANT SELECT, INSERT ON sethu.audit_log TO sethu_app;          -- append and read only
GRANT EXECUTE ON FUNCTION sethu.audit_verify() TO sethu_app, sethu_auditor;

GRANT SELECT ON sethu.audit_log, sethu.complaint_summaries, sethu.bureaus,
    sethu.institutions, sethu.overlap_links, sethu.alerts TO sethu_auditor;
"""


def upgrade() -> None:
    for block in (TABLES, AUDIT, RLS, GRANTS):
        op.execute(block)


def downgrade() -> None:
    raise RuntimeError(
        "0001 is not reversible: dropping the audit ledger is never an automated step."
    )

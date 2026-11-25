"""AI Phase A4: relationship graph, workflow bottlenecks, national early warning (docs/AI-PIPELINE.md, "A4").

1. graph_edges: one row per relationship, each derived from exactly one complaint, and visible exactly as its
   source is. `about` (complaint -> institution), `held_by` (complaint -> bureau) and `handled_by`
   (institution -> bureau, through that complaint) come from the summary (visible to every signed-in role, like
   sethu.complaint_summaries). `transfer` (bureau -> bureau) is visible where its case_actions row is. `overlap`
   (complaint -> complaint) is visible where its overlap_links row is. Rows hold ids, numbers, method and model
   version; never complaint text. Written by the worker (system) and admin only.
2. graph_runs and graph_communities: each graph build (method, sizes, time, memory, modularity) and the Louvain
   community of each institution and bureau, by version. Communities are kept for institutions and bureaus only
   (never complaints), so they reveal nothing a bureau cannot already see in the summary.
3. warning_signals: "Emerging signal: requires verification". A stable id across runs, the method and parameters,
   an explanation (states, time window, score, member ids), a lifecycle (new, acknowledged, dismissed with a
   reason, actioned). Visible to the roles that see everything and to the bureaus whose cases are in it; decided
   by oversight and those bureaus' heads; only the status columns may be changed by a person.
4. ai_feedback also records signal decisions (kind "signal", with a reason).
5. Settings for every A4 parameter.

Revision ID: 0017
"""
from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None

WORKER = "sethu.ctx_role() IN ('admin', 'system')"
INVOLVED = "sethu.ctx_bureau() = ANY(bureau_ids)"
MAY_DECIDE = f"(sethu.ctx_role() = 'oversight' OR (sethu.ctx_role() = 'bureau_head' AND {INVOLVED}))"

UPGRADE = f"""
CREATE TABLE sethu.graph_edges (
    id               bigserial PRIMARY KEY,
    edge_key         text NOT NULL UNIQUE CHECK (length(edge_key) <= 200),
    edge_type        text NOT NULL CHECK (edge_type IN ('about', 'held_by', 'handled_by', 'transfer', 'overlap')),
    source_type      text NOT NULL CHECK (source_type IN ('complaint', 'institution', 'bureau')),
    source_id        uuid NOT NULL,
    target_type      text NOT NULL CHECK (target_type IN ('complaint', 'institution', 'bureau')),
    target_id        uuid NOT NULL,
    complaint_id     uuid NOT NULL REFERENCES sethu.complaints(id),
    case_action_id   uuid REFERENCES sethu.case_actions(id),
    overlap_link_id  uuid REFERENCES sethu.overlap_links(id),
    weight           numeric NOT NULL DEFAULT 1,
    confidence       numeric(6,5) CHECK (confidence BETWEEN 0 AND 1),
    method           text NOT NULL CHECK (length(method) <= 60),
    model            text CHECK (length(model) <= 200),
    model_version    text CHECK (length(model_version) <= 100),
    evidence         jsonb NOT NULL DEFAULT '{{}}',
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now(),
    CHECK ((edge_type = 'transfer') = (case_action_id IS NOT NULL)),
    CHECK ((edge_type = 'overlap') = (overlap_link_id IS NOT NULL))
);
CREATE INDEX graph_edges_source ON sethu.graph_edges (source_type, source_id);
CREATE INDEX graph_edges_target ON sethu.graph_edges (target_type, target_id);
CREATE INDEX graph_edges_complaint ON sethu.graph_edges (complaint_id);
ALTER TABLE sethu.graph_edges ENABLE ROW LEVEL SECURITY;
CREATE POLICY graph_edges_read ON sethu.graph_edges FOR SELECT USING (
    -- The roles that see everything read every source, so they skip the per-row checks (same rows, much faster).
    sethu.ctx_sees_all() OR CASE edge_type
      WHEN 'transfer' THEN EXISTS (SELECT 1 FROM sethu.case_actions a WHERE a.id = case_action_id)
      WHEN 'overlap' THEN EXISTS (SELECT 1 FROM sethu.overlap_links l WHERE l.id = overlap_link_id)
      ELSE EXISTS (SELECT 1 FROM sethu.complaint_summaries s WHERE s.id = complaint_id)
    END);
CREATE POLICY graph_edges_insert ON sethu.graph_edges FOR INSERT WITH CHECK ({WORKER});
CREATE POLICY graph_edges_update ON sethu.graph_edges FOR UPDATE USING ({WORKER}) WITH CHECK ({WORKER});
CREATE POLICY graph_edges_delete ON sethu.graph_edges FOR DELETE USING ({WORKER});
GRANT SELECT, INSERT, UPDATE, DELETE ON sethu.graph_edges TO sethu_app;
GRANT USAGE ON SEQUENCE sethu.graph_edges_id_seq TO sethu_app;
GRANT SELECT ON sethu.graph_edges TO sethu_auditor;

CREATE TABLE sethu.graph_runs (
    version       serial PRIMARY KEY,
    method        text NOT NULL CHECK (method IN ('louvain', 'cte', 'direct')),
    path          text CHECK (path IN ('primary', 'fallback', 'last_resort')),
    nodes         integer NOT NULL DEFAULT 0,
    edges         integer NOT NULL DEFAULT 0,
    communities   integer,
    modularity    numeric(8,5),
    capped        boolean NOT NULL DEFAULT false,
    params        jsonb NOT NULL DEFAULT '{{}}',
    duration_ms   integer,
    peak_mb       numeric(10,1),
    ai_run_id     uuid REFERENCES sethu.ai_runs(id),
    created_at    timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE sethu.graph_runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY graph_runs_read ON sethu.graph_runs FOR SELECT USING (sethu.ctx_role() IS NOT NULL);
CREATE POLICY graph_runs_insert ON sethu.graph_runs FOR INSERT WITH CHECK ({WORKER});
GRANT SELECT, INSERT ON sethu.graph_runs TO sethu_app;
GRANT USAGE ON SEQUENCE sethu.graph_runs_version_seq TO sethu_app;
GRANT SELECT ON sethu.graph_runs TO sethu_auditor;

CREATE TABLE sethu.graph_communities (
    version    integer NOT NULL REFERENCES sethu.graph_runs(version),
    node_type  text NOT NULL CHECK (node_type IN ('institution', 'bureau')),
    node_id    uuid NOT NULL,
    community  integer NOT NULL,
    PRIMARY KEY (version, node_type, node_id)
);
ALTER TABLE sethu.graph_communities ENABLE ROW LEVEL SECURITY;
CREATE POLICY graph_communities_read ON sethu.graph_communities FOR SELECT USING (sethu.ctx_role() IS NOT NULL);
CREATE POLICY graph_communities_insert ON sethu.graph_communities FOR INSERT WITH CHECK ({WORKER});
GRANT SELECT, INSERT ON sethu.graph_communities TO sethu_app;
GRANT SELECT ON sethu.graph_communities TO sethu_auditor;

CREATE TABLE sethu.warning_signals (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    category_group  text NOT NULL CHECK (length(category_group) <= 100),
    categories      text[] NOT NULL,
    states          text[] NOT NULL CHECK (cardinality(states) > 0),
    window_start    date NOT NULL,
    window_end      date NOT NULL,
    method          text NOT NULL CHECK (method IN ('dbscan', 'zscore', 'ratio')),
    path            text NOT NULL CHECK (path IN ('primary', 'fallback', 'last_resort')),
    score           numeric(10,3),
    members         integer NOT NULL CHECK (members > 0),
    complaint_ids   uuid[] NOT NULL,
    bureau_ids      uuid[] NOT NULL CHECK (cardinality(bureau_ids) > 0),
    explanation     jsonb NOT NULL,
    parameters      jsonb NOT NULL,
    status          text NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'acknowledged', 'dismissed', 'actioned')),
    status_reason   text CHECK (length(status_reason) <= 500),
    decided_by      uuid REFERENCES sethu.app_users(id),
    decided_at      timestamptz,
    alert_ids       uuid[] NOT NULL DEFAULT '{{}}',
    ai_run_id       uuid REFERENCES sethu.ai_runs(id),
    first_seen      timestamptz NOT NULL DEFAULT now(),
    last_seen       timestamptz NOT NULL DEFAULT now(),
    CHECK (window_start <= window_end),
    CHECK (status <> 'dismissed' OR status_reason IS NOT NULL)
);
CREATE INDEX warning_signals_group ON sethu.warning_signals (category_group, window_end);
CREATE INDEX warning_signals_bureaus ON sethu.warning_signals USING gin (bureau_ids);
ALTER TABLE sethu.warning_signals ENABLE ROW LEVEL SECURITY;
CREATE POLICY warning_signals_read ON sethu.warning_signals FOR SELECT USING (sethu.ctx_sees_all() OR {INVOLVED});
CREATE POLICY warning_signals_insert ON sethu.warning_signals FOR INSERT WITH CHECK ({WORKER});
CREATE POLICY warning_signals_detector ON sethu.warning_signals FOR UPDATE USING ({WORKER}) WITH CHECK ({WORKER});
CREATE POLICY warning_signals_decide ON sethu.warning_signals FOR UPDATE USING ({MAY_DECIDE})
    WITH CHECK (status IN ('acknowledged', 'dismissed', 'actioned') AND {MAY_DECIDE});
GRANT SELECT, INSERT, UPDATE ON sethu.warning_signals TO sethu_app;
GRANT SELECT ON sethu.warning_signals TO sethu_auditor;

CREATE FUNCTION sethu.warning_signals_only_status_changes() RETURNS trigger
LANGUAGE plpgsql
SET search_path = sethu, pg_catalog
AS $$
BEGIN
    IF sethu.ctx_role() IN ('admin', 'system') THEN
        RETURN NEW;
    END IF;
    IF (NEW.id, NEW.category_group, NEW.categories, NEW.states, NEW.window_start, NEW.window_end, NEW.method,
        NEW.path, NEW.score, NEW.members, NEW.complaint_ids, NEW.bureau_ids, NEW.explanation, NEW.parameters,
        NEW.alert_ids, NEW.ai_run_id, NEW.first_seen, NEW.last_seen)
       IS DISTINCT FROM
       (OLD.id, OLD.category_group, OLD.categories, OLD.states, OLD.window_start, OLD.window_end, OLD.method,
        OLD.path, OLD.score, OLD.members, OLD.complaint_ids, OLD.bureau_ids, OLD.explanation, OLD.parameters,
        OLD.alert_ids, OLD.ai_run_id, OLD.first_seen, OLD.last_seen) THEN
        RAISE EXCEPTION 'only the status of a signal can be changed';
    END IF;
    RETURN NEW;
END
$$;
CREATE TRIGGER warning_signals_only_status_changes BEFORE UPDATE ON sethu.warning_signals
    FOR EACH ROW EXECUTE FUNCTION sethu.warning_signals_only_status_changes();

ALTER TABLE sethu.ai_feedback ADD COLUMN signal_id uuid REFERENCES sethu.warning_signals(id);
ALTER TABLE sethu.ai_feedback ADD COLUMN reason text CHECK (length(reason) <= 500);
ALTER TABLE sethu.ai_feedback ALTER COLUMN complaint_id DROP NOT NULL;
ALTER TABLE sethu.ai_feedback DROP CONSTRAINT ai_feedback_kind_check;
ALTER TABLE sethu.ai_feedback ADD CONSTRAINT ai_feedback_kind_check
    CHECK (kind IN ('category', 'institution', 'overlap', 'signal'));
ALTER TABLE sethu.ai_feedback DROP CONSTRAINT ai_feedback_decision_check;
ALTER TABLE sethu.ai_feedback ADD CONSTRAINT ai_feedback_decision_check
    CHECK (decision IN ('accepted', 'rejected', 'changed', 'acknowledged', 'dismissed', 'actioned'));
ALTER TABLE sethu.ai_feedback ADD CHECK ((kind = 'signal') = (signal_id IS NOT NULL));
ALTER TABLE sethu.ai_feedback ADD CHECK (kind = 'signal' OR complaint_id IS NOT NULL);
DROP POLICY ai_feedback_read ON sethu.ai_feedback;
CREATE POLICY ai_feedback_read ON sethu.ai_feedback FOR SELECT USING (
    sethu.ctx_sees_all()
    OR EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id = complaint_id)
    OR EXISTS (SELECT 1 FROM sethu.overlap_links l WHERE l.id = overlap_link_id)
    OR EXISTS (SELECT 1 FROM sethu.warning_signals w WHERE w.id = signal_id));
DROP POLICY ai_feedback_insert ON sethu.ai_feedback;
CREATE POLICY ai_feedback_insert ON sethu.ai_feedback FOR INSERT WITH CHECK (
    {WORKER}
    OR (sethu.ctx_role() IN ('officer', 'bureau_head') AND kind <> 'signal'
        AND (EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id = complaint_id)
             OR EXISTS (SELECT 1 FROM sethu.overlap_links l WHERE l.id = overlap_link_id)))
    OR (sethu.ctx_role() IN ('oversight', 'bureau_head') AND kind = 'signal'
        AND EXISTS (SELECT 1 FROM sethu.warning_signals w WHERE w.id = signal_id)));

INSERT INTO sethu.app_settings (key, value) VALUES
    ('ai.graph.build.min_confidence', '0.5'),
    ('ai.graph.build.timeout_seconds', '600'),
    ('ai.bottleneck.detect.timeout_seconds', '300'),
    ('ai.warning.detect.timeout_seconds', '300'),
    ('ai.graph.node_cap', '60000'),
    ('ai.graph.louvain_seed', '26264'),
    ('ai.graph.louvain_resolution', '1.0'),
    ('ai.graph.max_hops', '3'),
    ('ai.graph.min_edge_confidence', '0'),
    ('ai.bottleneck.detect.min_confidence', '0.5'),
    ('ai.bottleneck.min_dwell_days', '10'),
    ('ai.bottleneck.min_breach_rate', '0.6'),
    ('ai.bottleneck.min_betweenness', '0.1'),
    ('ai.bottleneck.min_cases', '3'),
    ('ai.bottleneck.loop_min_cases', '2'),
    ('ai.warning.detect.min_confidence', '0.5'),
    ('ai.warning.recent_days', '30'),
    ('ai.warning.baseline_days', '90'),
    ('ai.warning.km_per_unit', '500'),
    ('ai.warning.days_per_unit', '10'),
    ('ai.warning.eps', '1.0'),
    ('ai.warning.min_samples', '6'),
    ('ai.warning.min_members', '8'),
    ('ai.warning.max_points', '30000'),
    ('ai.warning.max_baseline_share', '0.5'),
    ('ai.warning.z_threshold', '3.0'),
    ('ai.warning.z_min_count', '5'),
    ('ai.warning.z_sd_floor', '1.0'),
    ('ai.warning.ratio_min_count', '5'),
    ('ai.warning.ratio_threshold', '3.0'),
    ('ai.warning.category_groups', '{{}}')
ON CONFLICT (key) DO NOTHING;
"""  # noqa: S608 - fixed SQL built from the constants above


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute("""
        DELETE FROM sethu.app_settings WHERE key LIKE 'ai.graph.%' OR key LIKE 'ai.bottleneck.%'
            OR key LIKE 'ai.warning.%';
        DELETE FROM sethu.ai_feedback WHERE kind = 'signal';
        DROP POLICY ai_feedback_insert ON sethu.ai_feedback;
        DROP POLICY ai_feedback_read ON sethu.ai_feedback;
        ALTER TABLE sethu.ai_feedback DROP COLUMN signal_id;
        ALTER TABLE sethu.ai_feedback DROP COLUMN reason;
        ALTER TABLE sethu.ai_feedback DROP CONSTRAINT ai_feedback_kind_check;
        ALTER TABLE sethu.ai_feedback ADD CONSTRAINT ai_feedback_kind_check
            CHECK (kind IN ('category', 'institution', 'overlap'));
        ALTER TABLE sethu.ai_feedback DROP CONSTRAINT ai_feedback_decision_check;
        ALTER TABLE sethu.ai_feedback ADD CONSTRAINT ai_feedback_decision_check
            CHECK (decision IN ('accepted', 'rejected', 'changed'));
        ALTER TABLE sethu.ai_feedback ALTER COLUMN complaint_id SET NOT NULL;
        CREATE POLICY ai_feedback_read ON sethu.ai_feedback FOR SELECT USING (
            sethu.ctx_sees_all() OR EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id = complaint_id)
            OR EXISTS (SELECT 1 FROM sethu.overlap_links l WHERE l.id = overlap_link_id));
        CREATE POLICY ai_feedback_insert ON sethu.ai_feedback FOR INSERT WITH CHECK (
            sethu.ctx_role() IN ('admin', 'system') OR (sethu.ctx_role() IN ('officer', 'bureau_head')
                AND (EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id = complaint_id)
                     OR EXISTS (SELECT 1 FROM sethu.overlap_links l WHERE l.id = overlap_link_id))));
        DROP TABLE sethu.warning_signals;
        DROP FUNCTION sethu.warning_signals_only_status_changes();
        DROP TABLE sethu.graph_communities; DROP TABLE sethu.graph_runs; DROP TABLE sethu.graph_edges;""")

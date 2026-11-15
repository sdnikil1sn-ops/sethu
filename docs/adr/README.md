# Architecture Decision Records

One short record per decision that would be expensive to reverse. Add a new numbered section when a decision changes; do not rewrite history.

## 0001. Modular monolith, not microservices
**Decision.** One FastAPI application with feature modules, plus Celery workers, on one PostgreSQL database.
**Why.** A small team must build, demo and operate this. Cross-feature transactions (decision + outbox + audit) need one database. Module boundaries keep a later split possible.
**Cost.** One deployable; a bad module can affect others. Mitigated by module rules and tests.

## 0002. Enforce access in the database with Row-Level Security
**Decision.** The API passes role and bureau into each transaction; PostgreSQL policies decide row visibility. The runtime role cannot bypass them.
**Why.** Complaint text is the most sensitive asset. An application-only filter fails open when one query forgets it; RLS fails closed.
**Cost.** Policies must be written and tested for each sensitive table; raw connections see nothing without context.

## 0003. Hash-chained audit log inside PostgreSQL, not a blockchain
**Decision.** An append-only table whose rows are chained by SHA-256, with sequence, time and hash assigned by a trigger.
**Why.** There is one trusted operator (AICTE), so distributed consensus adds cost and no assurance. A hash chain gives tamper evidence, and writing it in the same transaction as the change guarantees no action goes unrecorded.
**Cost.** A database superuser could rebuild the whole chain. Mitigation: export the head hash to write-once storage nightly (planned).

## 0004. Transactional outbox for alerts
**Decision.** Alerts are rows in `sethu.alerts`, written in the same transaction as the decision; a worker delivers approved rows.
**Why.** Email must never be sent for a decision that rolled back, and never lost for one that committed. It also gives human approval a natural place.
**Cost.** At-least-once delivery: a crash can cause one duplicate email. Acceptable for coordination alerts.

## 0005. Local models only, each with a deterministic fallback
**Decision.** Translation, classification and embeddings run on local open-licence models (IndicTrans2, multilingual-e5) inside the app network. Every step has a rule-based or lexical fallback, and the pipeline must pass tests with models off.
**Why.** "Data never leaves AICTE" rules out hosted AI. Fallbacks keep the PS features working on a laptop without a GPU, which is the demo machine.
**Cost.** Lower accuracy than hosted models; more engineering per step.

## 0006. Object storage deferred
**Decision.** No object store in the first build. Complaints are text; attachments are out of the must-ship scope.
**Why.** The earlier plan named MinIO, whose community edition's maintenance and container distribution should be re-checked before adopting it. Choosing later costs nothing now.
**Options when needed.** An S3-compatible store on the data network (check MinIO's current status, or Garage / SeaweedFS), with ClamAV scanning before write and metadata in PostgreSQL.

## 0007. Keycloak for identity
**Decision.** Self-hosted Keycloak issues OIDC tokens; the web app uses authorisation code flow with PKCE; the API validates tokens offline against the internal JWKS endpoint.
**Why.** MFA, password policy, brute-force protection and a path to AICTE single sign-on without writing authentication code.
**Cost.** A heavy container and a realm to manage. For the demo, seed users through the realm file or admin console.

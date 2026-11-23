# API

## Who calls what

| Caller | How it authenticates | Reachable at |
|---|---|---|
| The SETHU web app | A Keycloak access token (`Authorization: Bearer ...`, 5 minutes) | `https://<host>/api/v1/...` |
| A portal sending complaints (intake API) | The source's API key, a timestamp and a one-time nonce | `https://<host>/api/v1/intake/submissions` |
| Operators and developers (OpenAPI) | None; internal network only | `http://backend:8000/docs` and `/openapi.json` |

**OpenAPI is internal only.** The interactive description is served on the backend's own port, outside `/api/`, which
is all the public edge forwards to the backend. Through the edge, `/api/docs` and `/api/openapi.json` answer 404, and
`/docs` or `/openapi.json` reach only the web app's own page, never the backend (`backend/tests/test_security.py::test_a02_001_*`;
live check 2026-11-21). To read it: `docker compose exec backend python -c "import
urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/openapi.json').read().decode())"`, or a tunnel to
the host.

The rest of this page is for portal developers: the intake API.

## Intake API: send one complaint

`POST /api/v1/intake/submissions`, JSON body, over HTTPS only.

### Headers

| Header | Value |
|---|---|
| `Content-Type` | `application/json` |
| `X-Sethu-Key` | The source's API key (`sethu_...`), issued once by an AICTE administrator on Intake > Sources. SETHU keeps only its SHA-256 hash; a lost key is replaced, not recovered |
| `X-Sethu-Timestamp` | Now, as Unix seconds (UTC). Must be within 300 seconds of the server's clock |
| `X-Sethu-Nonce` | A fresh random string, 16 to 128 ASCII characters, never reused by this source (for example 24 random bytes in base64url) |

### Body

| Field | Required | Rules |
|---|---|---|
| `institution_name` | yes | 3 to 300 characters; any spelling (SETHU matches it to an institution or queues it for a person) |
| `category` | yes | 3 to 100 characters, for example `Fee refund`, `Faculty shortage`, `Ragging` |
| `body` | yes | The complaint, 20 to 10,000 characters |
| `language` | no | `en` (default) or `hi` |
| `filed_at` | no | ISO 8601 date-time; default: when SETHU received it |
| `external_ref` | no | The portal's own reference, up to 100 of `A-Z a-z 0-9 . _ : / -`; a second submission with the same reference from the same source is refused |
| `complainant` | no | `{"name": 2 to 200 characters, "email": optional, "phone": optional}`; stored encrypted, shown only to the bureau that holds the case |

Unknown fields are refused. Whitespace runs are folded to one space.

### Example

```powershell
$key = "<the source's API key>"
$nonce = [Convert]::ToBase64String((1..24 | ForEach-Object { Get-Random -Maximum 256 }) -as [byte[]]).Replace('+','-').Replace('/','_').TrimEnd('=')
$body = @{
  institution_name = "Greenfield Inst. of Tech., Pune"
  category         = "Fee refund"
  body             = "The caution deposit has not been refunded four months after withdrawal."
  external_ref     = "PORTAL-2026-000123"
  complainant      = @{ name = "Test Person"; email = "test.person@sethu.test" }
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "https://<host>/api/v1/intake/submissions" -ContentType "application/json" `
  -Headers @{ "X-Sethu-Key" = $key; "X-Sethu-Timestamp" = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds(); "X-Sethu-Nonce" = $nonce } `
  -Body $body
```

The same with curl:

```sh
curl -sS https://<host>/api/v1/intake/submissions \
  -H "Content-Type: application/json" -H "X-Sethu-Key: $KEY" \
  -H "X-Sethu-Timestamp: $(date +%s)" -H "X-Sethu-Nonce: $(openssl rand -base64 24 | tr '+/' '-_' | tr -d '=')" \
  --data '{"institution_name": "Greenfield Inst. of Tech., Pune", "category": "Fee refund",
           "body": "The caution deposit has not been refunded four months after withdrawal.",
           "external_ref": "PORTAL-2026-000123"}'
```

### Answer

`202 Accepted`:

```json
{"id": "6f1c2b9e-0a4d-4c55-9a8e-2f0d1c3b4a5e", "status": "queued", "path": "primary"}
```

The complaint is **queued**, not yet a case: the worker files it within seconds (institution matching, duplicate
checks), retrying with growing waits if a step fails; nothing accepted is dropped. `path` is `fallback` when this source
is standing in for another that is marked down. Keep `id` to quote to AICTE; the case reference appears on the Intake
screen.

### Errors

Errors are JSON `{"detail": "<reason>"}`. Reasons name fields and rules, never the values sent.

| Status | When | What to do |
|---|---|---|
| 401 | Unknown key, a timestamp that is not Unix seconds or is more than 300 s off, a nonce of the wrong length | Fix the request; check the server clock (NTP) |
| 409 | `this nonce was already used: replayed request refused`; `duplicate of C-...` (the same complaint is already a case); `already received from this source` (same `external_ref` or the same complaint still queued); the source is inactive or is not an API source | Do not resend the same request; for a duplicate, nothing more is needed |
| 413 | Body larger than the edge allows (10 MB) | Send one complaint per request |
| 422 | A field breaks a rule (the reason names the field and the rule) | Fix the field; do not retry unchanged |
| 429 | More than the source's quota in a minute (default 60; `Retry-After: 60`), or more than 20 requests a second from one address at the edge | Wait and retry with a **new** nonce and timestamp |
| 5xx | SETHU or its database is unavailable | Retry later with a new nonce; if the first attempt actually succeeded, the retry is answered 409 "already received" (when you send `external_ref`), so always send one |

### Signing and transport

Requests are **not signed** (there is no HMAC of the body). A request is trusted because:

- it carries the source's secret key, over TLS 1.3 to the AICTE host;
- its timestamp and one-time nonce stop a captured request from being replayed;
- each source has its own per-minute quota, and its key can be replaced at any time (Intake > Sources > Replace API key).

Body integrity therefore rests on TLS. A portal that needs proof of origin per message, beyond the key, would need a
signed-request scheme added to SETHU; none is built.

### Other channels

The same rules apply to an uploaded CSV or XLSX file (Intake screen, officers and bureau heads; one row per complaint,
header `institution_name,category,body` plus the optional `language,filed_at,external_ref,complainant_name,complainant_email,complainant_phone`; sample: `docs/samples/intake-sample.csv`), the
manual form, and the spool folder (a portal drops files into its source's subfolder of `SETHU_INTAKE_SPOOL_DIR`; links
and files over the size limit are refused unread).

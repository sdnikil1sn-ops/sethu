# SETHU

AICTE cross-bureau complaint monitoring. Smart India Hackathon 2026, SIH26264, team PIVOTT.

## Quick start (Windows, PowerShell)

Needs Docker Desktop and Python 3.12+.

```powershell
python scripts/init_env.py
docker compose --profile dev up --build -d
```

Then open http://localhost:8080 . Details and troubleshooting: `docs/RUNBOOK.md`.

## What is here

- A hardened platform skeleton: network zones with no outbound route, least-privilege database roles, Row-Level Security, a hash-chained audit log, token validation, health checks.
- Design docs in `docs/`: scope, PS checklist, demo story, architecture, data model, security, decisions, runbook.
- No product features yet. Build them in the order given in `docs/05-NEXT-CLAUDE-CODE-PROMPT.md`.

Mock data only. Nothing leaves the machine.

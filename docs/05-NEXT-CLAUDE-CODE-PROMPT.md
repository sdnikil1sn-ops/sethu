# 05. Next Claude Code Prompts

The platform skeleton already exists (see `docs/ARCHITECTURE.md` section 11 for what is verified). Run these in order, one per session. Open Claude Code in `E:\App\Project\SETHU` from a normal terminal (not PowerShell ISE).

## Prompt 1: bring the stack up

Read `CLAUDE.md` and `docs/RUNBOOK.md`. Run section 1 of the runbook. The full `docker compose up` has never been run: fix whatever fails (Keycloak realm import, Nginx proxy, Redis, line endings) with the smallest change, without weakening any rule in `CLAUDE.md`. Then run the backend tests as described in the runbook. Report what you changed and update `docs/ARCHITECTURE.md` section 11.

## Prompt 2: mock data

Read `docs/04-MOCK-DATA-SPEC.md`. Build a deterministic generator in `seed/` (fixed random seed) that produces the CSV files and a loader that inserts them through `session_for(SYSTEM)`, writing `case_actions` and audit entries. Add a test that the expected detections listed in the spec are present in the data.

## Prompt 3: first feature (institutions and resolution)

Read `docs/02-PS-COVERAGE-CHECKLIST.md` section 1 and `docs/ARCHITECTURE.md` sections 5 and 8. Build `backend/app/modules/institutions/` (api, service, repo, schemas): list, profile, alias search with `pg_trgm`, and the resolution cascade steps 1 to 3 with the officer queue for unresolved names. Add the React screens under `web/src/features/institutions/`. Tests must cover the three Greenfield spellings from the demo story.

## After that, in this order

Complaints and case tracking; overlap detection Tier 1 then Tier 2 with approval; alert outbox and email; dashboard; search; reports; then the flagship features. One feature per session, each ending with its checklist line ticked.

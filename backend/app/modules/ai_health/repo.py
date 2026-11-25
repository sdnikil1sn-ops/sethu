"""SQL for the AI health screen: counts of router calls by task, path and status (no subjects, no text)."""
from sqlalchemy import text
from sqlalchemy.orm import Session


def counts_last_day(session: Session) -> list[dict]:
    return [dict(r) for r in session.execute(text("""
        SELECT task, coalesce(path, 'human_review') AS path, count(*) AS runs
          FROM sethu.ai_runs WHERE created_at > now() - interval '24 hours'
         GROUP BY task, coalesce(path, 'human_review')""")).mappings()]


def last_runs(session: Session) -> dict[str, dict]:
    """Each task's latest run: when, which path and provider (A4: shows the active method)."""
    return {r["task"]: dict(r) for r in session.execute(text("""
        SELECT DISTINCT ON (task) task, created_at AS at, coalesce(path, 'human_review') AS path, provider, status
          FROM sethu.ai_runs ORDER BY task, created_at DESC""")).mappings()}

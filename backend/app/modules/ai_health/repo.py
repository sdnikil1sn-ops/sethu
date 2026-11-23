"""SQL for the AI health screen: counts of router calls by task, path and status (no subjects, no text)."""
from sqlalchemy import text
from sqlalchemy.orm import Session


def counts_last_day(session: Session) -> list[dict]:
    return [dict(r) for r in session.execute(text("""
        SELECT task, coalesce(path, 'human_review') AS path, count(*) AS runs
          FROM sethu.ai_runs WHERE created_at > now() - interval '24 hours'
         GROUP BY task, coalesce(path, 'human_review')""")).mappings()]

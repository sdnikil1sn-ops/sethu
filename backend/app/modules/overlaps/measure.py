"""Measure the semantic signal on the current data: which rule-allowed pairs trigram alone suggests, which the
combined rule suggests, and the values. Prints references, values and counts only; never text.

    docker compose exec worker python -m app.modules.overlaps.measure [semantic threshold]
"""
import sys

from app.core.config import get_settings
from app.db.session import SYSTEM, session_for
from app.modules.overlaps import repo, service


def main(threshold: float | None = None) -> None:
    s = get_settings()
    threshold = threshold if threshold is not None else s.semantic_threshold
    with session_for(SYSTEM) as session:
        embedded = service.embed_pending(session, limit=100_000)
    with session_for(SYSTEM) as session:
        pairs = repo.candidates(session, service.WINDOW_DAYS, s.embedding_model)
        ref = repo.refs(session, [c for p in pairs for c in (p["complaint_a"], p["complaint_b"])])
    print(f"model {s.embedding_model}; newly embedded {embedded}; rule-allowed pairs {len(pairs)};"
          f" trigram threshold {service.SIMILARITY_THRESHOLD}, semantic threshold {threshold}")
    trigram_only = {(p["complaint_a"], p["complaint_b"]) for p in pairs if p["trigram"] >= service.SIMILARITY_THRESHOLD}
    combined = trigram_only | {(p["complaint_a"], p["complaint_b"]) for p in pairs
                               if p["semantic"] is not None and p["semantic"] >= threshold}
    print(f"suggested: trigram only {len(trigram_only)}, combined {len(combined)},"
          f" added by the semantic signal {len(combined - trigram_only)}")
    for p in sorted(pairs, key=lambda p: -(p["semantic"] or 0)):
        key = (p["complaint_a"], p["complaint_b"])
        tag = "both" if key in trigram_only and key in combined and p["semantic"] and p["semantic"] >= threshold \
            else "trigram" if key in trigram_only else "semantic" if key in combined else "-"
        print(f"  {ref[p['complaint_a']]:>9} {ref[p['complaint_b']]:>9}  trigram {p['trigram']:.2f}"
              f"  semantic {'n/a ' if p['semantic'] is None else format(p['semantic'], '.2f')}  suggested by: {tag}")


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else None)

"""Write the category classifier's bootstrap set (backend/app/ai/data/category_bootstrap.jsonl) from the seed data.

    python scripts/make_category_bootstrap.py

Two sources, both synthetic: every seeded complaint (seed/complaints.csv: its text and category) and short examples
made from the glossary's category terms (seed/glossary.csv), in each term's own language, mapped to a category by
the classifier rules' tags (app/ai/classify.py). The file ships with the image so the ai-worker can train a first
classifier with no complaint data; officers' accepted corrections are added at each retrain.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.ai.classify import RULES  # noqa: E402

OUT = ROOT / "backend/app/ai/data/category_bootstrap.jsonl"


def main() -> None:
    rows = [{"text": c["body"], "category": c["category"], "source": "seed"}
            for c in csv.DictReader((ROOT / "seed/complaints.csv").open(encoding="utf-8"))]
    by_tag = {tag: category for category, rule in RULES.items() for tag in rule["tags"]}
    for term in csv.DictReader((ROOT / "seed/glossary.csv").open(encoding="utf-8")):
        category = by_tag.get(term["english"])
        if term["type"] == "category" and category:
            rows.append({"text": term["term"], "category": category, "source": "glossary"})
    seen, unique = set(), []
    for r in rows:
        if r["text"] not in seen:
            seen.add(r["text"])
            unique.append(r)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in unique), encoding="utf-8", newline="\n")
    seed = sum(r["source"] == "seed" for r in unique)
    print(f"{OUT.relative_to(ROOT)}: {len(unique)} examples ({seed} seed, {len(unique) - seed} glossary)")


if __name__ == "__main__":
    main()

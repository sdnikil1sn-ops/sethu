"""Glossary normalisation: find known terms in a complaint and give their English tags. This is term
normalisation, not translation: it says which known terms a text contains, never what the text says.

Text and terms are normalised the same way: Unicode NFC, case folded, zero-width joiners removed, punctuation made
spaces, runs of spaces made one. Matching is longest term first; a term must start at a word start. In Latin script
it must also end at a word end ("fee" never matches "feedback"); in Indic scripts it may be followed by a suffix,
because case endings attach to the word ("விண்ணப்பத்தை" contains "விண்ணப்ப"). Output: the English tags in the order
found, without repeats, and the coverage: the share of the text's letters inside a matched term.
"""
import unicodedata
from dataclasses import dataclass

ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿"))


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFC", text).casefold().translate(ZERO_WIDTH)
    out = []
    for ch in text:
        cat = unicodedata.category(ch)
        out.append(ch if cat[0] in "LMN" else " ")     # letters, combining marks (matras, viramas), digits
    return " ".join("".join(out).split())


def _latin(ch: str) -> bool:
    return ch.isascii() or "LATIN" in unicodedata.name(ch, "")


@dataclass(frozen=True)
class Match:
    term: str
    english: str
    start: int


class Glossary:
    def __init__(self, terms: list[tuple[str, str]], version: int = 0):
        """terms: (term, english) pairs in any language; normalised here, longest first."""
        self.version = version
        by_term: dict[str, str] = {}
        for term, english in terms:
            key = normalise(term)
            if key:
                by_term.setdefault(key, english)
        self._by_first: dict[str, list[tuple[str, str]]] = {}
        for key, english in sorted(by_term.items(), key=lambda kv: -len(kv[0])):
            self._by_first.setdefault(key[0], []).append((key, english))

    def matches(self, text: str) -> tuple[list[Match], str]:
        norm = normalise(text)
        found, i = [], 0
        while i < len(norm):
            if i > 0 and norm[i - 1] != " ":      # only at a word start
                i += 1
                continue
            for key, english in self._by_first.get(norm[i], ()):
                end = i + len(key)
                if norm.startswith(key, i) and (end == len(norm) or norm[end] == " " or not _latin(key[-1])):
                    found.append(Match(key, english, i))
                    i = end
                    break
            else:
                i += 1
        return found, norm

    def tag(self, text: str) -> dict:
        found, norm = self.matches(text)
        letters = sum(1 for ch in norm if ch != " ")
        covered = sum(sum(1 for ch in m.term if ch != " ") for m in found)
        tags = list(dict.fromkeys(m.english for m in found))
        return {"tags": tags, "coverage": round(covered / letters, 5) if letters else 0.0,
                "matches": [(m.term, m.english) for m in found], "glossary_version": self.version}

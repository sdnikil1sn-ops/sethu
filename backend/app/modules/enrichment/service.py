"""Enrichment of complaints by the AI layer (docs/AI-PIPELINE.md), attachments, and human review.

A complaint is usable the moment it is filed: `mark_pending` only writes a pending row with it (an outbox). The
ai-worker picks pending complaints up in batches (`enrich_pending`, every 10 seconds on the `ai` queue) and runs
each step through the AI router, so provenance, circuit breakers and confidence thresholds apply:

    detect language -> read attachments (OCR) -> translate to English -> glossary tags

The steps run stage by stage over the whole batch (all languages, then all attachments, then all translations), so
each model is loaded once per batch and never two at a time (app/ai/memory.py keeps one). A step that is unsure or
fails creates a review item for a person. The original complaint text is never changed: everything lands in
sethu.complaint_enrichment.
"""
import hashlib
import json
import re
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.ai import ocr, router
from app.audit import service as audit
from app.core.auth import Principal
from app.core.config import get_settings
from app.core.crypto import load_keyring
from app.db.session import SYSTEM, session_for
from app.modules.enrichment import repo
from app.modules.glossary import service as glossary
from app.modules.users import service as users

MAX_ATTACHMENT_BYTES = 10_000_000
MAX_ATTEMPTS = 3
TYPES = {"application/pdf": (b"%PDF-", ".pdf"), "image/png": (b"\x89PNG\r\n\x1a\n", ".png"),
         "image/jpeg": (b"\xff\xd8\xff", ".jpg")}
SAFE_NAME = re.compile(r"[^A-Za-z0-9._ -]")
TRANSLATION_PATH = {"indictrans2": "model", "glossary": "glossary"}


class EnrichmentError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def _keyring():
    path = get_settings().complainant_keys_file
    if not path:
        raise EnrichmentError(500, "SETHU_COMPLAINANT_KEYS_FILE is not set")
    return load_keyring(path)


# --- Called by other modules ---------------------------------------------------------------------------

def mark_pending(session: Session, complaint_id: UUID) -> None:
    """With a new complaint, in its transaction: enrichment is due."""
    repo.insert_pending(session, complaint_id)


def for_case(session: Session, complaint_id: UUID) -> dict:
    """What the case page shows: enrichment (if any) and the attachments' metadata (never their bytes)."""
    return {"enrichment": repo.enrichment(session, complaint_id),
            "attachments": repo.attachments(session, complaint_id)}


# --- Attachments ---------------------------------------------------------------------------------------

def add_attachment(session: Session, principal: Principal, complaint_id: UUID, data: bytes, filename: str) -> dict:
    """A scan or PDF for a case, by an officer or head of the bureau holding it (the database checks that).
    The type is decided by the file's first bytes, not its name; stored encrypted; audited without content."""
    if not data or len(data) > MAX_ATTACHMENT_BYTES:
        raise EnrichmentError(413, f"an attachment must be 1 to {MAX_ATTACHMENT_BYTES} bytes")
    content_type = next((t for t, (magic, _) in TYPES.items() if data.startswith(magic)), None)
    if content_type is None:
        raise EnrichmentError(415, "only PDF, PNG and JPEG files are accepted")
    stem = SAFE_NAME.sub("_", filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]).strip(" ._")[:100] or "attachment"
    stem = stem.rsplit(".", 1)[0] + TYPES[content_type][1]       # the extension follows the real type
    sha = hashlib.sha256(data).hexdigest()
    if not repo.can_read_case(session, complaint_id):    # Row-Level Security: only where its text is readable
        raise EnrichmentError(404, "case not found")
    if repo.same_file(session, complaint_id, sha):
        raise EnrichmentError(409, "this file is already attached to the case")
    attachment_id = uuid4()
    repo.insert_attachment(session, id=attachment_id, complaint_id=complaint_id, filename=stem,
                           content_type=content_type, size_bytes=len(data), sha256=sha,
                           data_enc=_keyring().encrypt_bytes(data, str(attachment_id)),
                           uploaded_by=users.sync(session, principal))
    repo.insert_pending(session, complaint_id)             # a complaint filed before A2 gets its row now
    audit.record(session, principal, "attachment.added", entity_type="complaint_attachments",
                 entity_id=str(attachment_id), payload={"complaint_id": str(complaint_id), "type": content_type,
                                                        "size": len(data), "sha256": sha})
    return {"id": attachment_id, "filename": stem, "content_type": content_type, "size_bytes": len(data),
            "sha256": sha}


def open_attachment(session: Session, principal: Principal, complaint_id: UUID, attachment_id: UUID) -> dict:
    """The file, for someone who may read the case's text; every opening is in the audit log."""
    found = repo.attachment(session, attachment_id)
    if found is None or found["complaint_id"] != complaint_id:   # Row-Level Security hides other bureaus' files
        raise EnrichmentError(404, "attachment not found")
    data = _keyring().decrypt_bytes(found.pop("data_enc"), str(attachment_id))
    if hashlib.sha256(data).hexdigest() != found["sha256"]:
        raise EnrichmentError(500, "the stored file does not match its checksum")
    audit.record(session, principal, "attachment.viewed", entity_type="complaint_attachments",
                 entity_id=str(attachment_id), payload={"complaint_id": str(complaint_id)})
    return found | {"data": data}


def rekey_attachments(session: Session, principal: Principal, batch: int = 50) -> dict:
    """With complainant key rotation (worker task sethu.complainant.rotate_keys): re-seal one batch of attachments
    with the active key, so the old key can be removed without losing them. Audited with counts and key ids."""
    ring = _keyring()
    rows = repo.not_on_key(session, ring.active, batch)
    for r in rows:
        aad = str(r["id"])
        repo.set_data(session, r["id"], ring.encrypt_bytes(ring.decrypt_bytes(r["data_enc"], aad), aad))
    if rows:
        audit.record(session, principal, "attachment.rekeyed", entity_type="complaint_attachments",
                     payload={"rows": len(rows), "to_key": ring.active})
    return {"rekeyed": len(rows), "left": len(repo.not_on_key(session, ring.active, 1))}


# --- Human review --------------------------------------------------------------------------------------

def review_items(session: Session, status: str | None) -> list[dict]:
    return repo.review_items(session, status, 200)


def resolve(session: Session, principal: Principal, item_id: UUID, status: str) -> dict:
    done = repo.resolve(session, item_id, status, users.sync(session, principal))
    if done is None:   # hidden by Row-Level Security, not open, or not the caller's bureau's case
        raise EnrichmentError(404, "open review item not found")
    audit.record(session, principal, f"review.{status}", entity_type="review_items", entity_id=str(item_id),
                 payload={"kind": done["kind"], "complaint_id": str(done["complaint_id"])})
    return done | {"status": status}


# --- The pipeline (ai-worker, as the system principal) -------------------------------------------------

def enrich_pending(limit: int = 10, engine=None) -> dict:
    with session_for(SYSTEM, engine) as s:
        batch = repo.claim(s, limit)
    if not batch:
        return {"complaints": 0}
    state = {b["complaint_id"]: {"review": False, "language": b["language"], "ocr_text": b["ocr_text"] or ""}
             for b in batch}
    for b in batch:
        if b["attempts"] > MAX_ATTEMPTS:
            with session_for(SYSTEM, engine) as s:
                repo.add_review(s, "language", b["complaint_id"], f"enrichment failed {MAX_ATTEMPTS} times")
                repo.save(s, b["complaint_id"], status="review")
            state.pop(b["complaint_id"])
    for cid, st in state.items():      # stage 1: language (one small model for the whole batch)
        _language(cid, st, engine)
    for cid, st in state.items():      # stage 2: attachments (the OCR model)
        _attachments(cid, st, engine)
    for cid, st in state.items():      # stage 3: translation (the translation model), then glossary tags
        _translate_and_tag(cid, st, engine)
    return {"complaints": len(state), "review": sum(st["review"] for st in state.values())}


def _language(cid: UUID, st: dict, engine) -> None:
    with session_for(SYSTEM, engine) as s:
        st["body"] = repo.body(s, cid)
        r = router.run(s, SYSTEM, "language.detect", {"text": st["body"]}, subject_type="complaint",
                       subject_id=str(cid))
        if r["status"] == "ok":
            st["language"] = r["output"]["language"]
            repo.save(s, cid, language=st["language"], language_confidence=r["confidence"],
                      language_candidates=r["output"].get("candidates") or [])
        else:
            st["language"], st["review"] = "unknown", True
            repo.save(s, cid, language="unknown", language_confidence=None, language_candidates=[])
            repo.add_review(s, "language", cid, "language not recognised with enough confidence", r["run_id"])


def _attachments(cid: UUID, st: dict, engine) -> None:
    with session_for(SYSTEM, engine) as s:
        pending = repo.pending_attachments(s, cid)
        max_pages = int(router.setting(s, "ai.ocr.max_pages", 10))
        max_pixels = int(router.setting(s, "ai.ocr.max_image_pixels", 25_000_000))
    for a in pending:
        with session_for(SYSTEM, engine) as s:
            data = _keyring().decrypt_bytes(a["data_enc"], str(a["id"]))
            try:
                pages = ocr.pages(data, a["content_type"], max_pages, max_pixels)
            except Exception as e:  # noqa: BLE001 - over a limit or unreadable: a person reads it
                repo.set_attachment_status(s, a["id"], "review")
                repo.add_review(s, "ocr", cid, f"attachment not read automatically ({type(e).__name__}: "
                                f"{str(e)[:200] if isinstance(e, ocr.PageLimit) else 'unreadable'})",
                                attachment_id=a["id"])
                st["review"] = True
                continue
            texts, path = [pages.embedded_text] if pages.embedded_text else [], "embedded"
            if pages.images:
                r = router.run(s, SYSTEM, "ocr.read", {"images": pages.images, "language": st["language"]},
                               subject_type="attachment", subject_id=str(a["id"]))
                if r["status"] == "ok":
                    texts.append(r["output"]["text"])
                    path = r["path"]
                else:
                    path = "manual"
                    repo.add_review(s, "ocr", cid, "needs manual entry: the text could not be read with enough "
                                    "confidence", r["run_id"], a["id"])
                    st["review"] = True
            st["ocr_text"] = "\n".join(t for t in (st["ocr_text"], *texts) if t)[:100_000]
            repo.set_attachment_status(s, a["id"], "review" if path == "manual" else "done")
            repo.save(s, cid, ocr_text=st["ocr_text"] or None, ocr_path=path)


def _translate_and_tag(cid: UUID, st: dict, engine) -> None:
    with session_for(SYSTEM, engine) as s:
        words = glossary.current(s)
        text = "\n".join(t for t in (st["body"], st["ocr_text"]) if t)[:20_000]
        fields: dict = {}
        english = None
        if st["language"] == "en":
            fields = {"translation_path": "not_needed", "translated_text": None}
        else:
            r = router.run(s, SYSTEM, "translate.to_en", {"text": text, "language": st["language"],
                                                         "glossary": words},
                           subject_type="complaint", subject_id=str(cid))
            if r["status"] == "ok":
                english = r["output"].get("text")
                fields = {"translation_path": TRANSLATION_PATH.get(r["provider"], "model"), "translated_text": english}
            else:
                fields = {"translation_path": "untranslated", "translated_text": None}
                repo.add_review(s, "translation", cid, "untranslated: shown in the original language only",
                                r["run_id"])
                st["review"] = True
        tags = router.run(s, SYSTEM, "glossary.tag", {"text": "\n".join(t for t in (text, english) if t),
                                                      "glossary": words},
                          subject_type="complaint", subject_id=str(cid))
        if tags["status"] == "ok":
            fields |= {"tags": json.dumps(tags["output"]["tags"]), "glossary_version": words.version,
                       "glossary_coverage": tags["output"]["coverage"]}
        repo.save(s, cid, status="review" if st["review"] else "done", **fields)

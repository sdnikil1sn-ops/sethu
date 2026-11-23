"""Authenticated encryption of complainant details (complaints.complainant_enc).

AES-256-GCM. A stored value is: b"S1" | key-id length (1 byte) | key id | 12-byte nonce | ciphertext+tag.
The key id travels with every value, so keys can be rotated: add a key to the keyring, make it active,
re-encrypt (complaints.service.rotate_complainant_keys), then drop the old key.

The associated data is the complaint's id: a value copied onto another complaint does not decrypt.

The keyring is a JSON file mounted as a read-only secret (never an environment value, never in the
image): {"active": "<key id>", "keys": {"<key id>": "<base64 of 32 random bytes>", ...}}.
Create or extend it with scripts/complainant_key.py. Nothing here logs a value or a key.
"""
import base64
import binascii
import json
import os
from functools import lru_cache
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"S1"
NONCE_BYTES = 12


class KeyringError(ValueError):
    """The keyring is missing, unreadable or incomplete. The message never contains a key."""


class Keyring:
    def __init__(self, active: str, keys: dict[str, bytes]):
        if active not in keys:
            raise KeyringError("the active key id is not in the keyring")
        for key_id, key in keys.items():
            if not key_id or len(key_id.encode()) > 255 or len(key) != 32:
                raise KeyringError(f"key {key_id!r} must have an id of 1-255 bytes and be 32 bytes long")
        self.active, self.keys = active, keys

    def encrypt(self, details: dict, aad: str) -> bytes:
        return self.encrypt_bytes(json.dumps(details).encode(), aad)

    def decrypt(self, value: bytes, aad: str) -> dict:
        return json.loads(self.decrypt_bytes(value, aad))

    def encrypt_bytes(self, data: bytes, aad: str) -> bytes:
        """The same sealed format for any bytes (attachments: the attachment's id is the associated data)."""
        key_id = self.active.encode()
        nonce = os.urandom(NONCE_BYTES)
        sealed = AESGCM(self.keys[self.active]).encrypt(nonce, data, aad.encode())
        return MAGIC + bytes([len(key_id)]) + key_id + nonce + sealed

    def decrypt_bytes(self, value: bytes, aad: str) -> bytes:
        key_id, nonce, sealed = _split(value)
        if key_id not in self.keys:
            raise KeyringError(f"no key {key_id!r} in the keyring: was it removed before re-encryption?")
        return AESGCM(self.keys[key_id]).decrypt(nonce, sealed, aad.encode())


def _split(value: bytes) -> tuple[str, bytes, bytes]:
    value = bytes(value)
    if value[:2] != MAGIC:
        raise KeyringError("not an encrypted complainant value")
    n = value[2]
    return value[3:3 + n].decode(), value[3 + n:3 + n + NONCE_BYTES], value[3 + n + NONCE_BYTES:]


def key_id_of(value: bytes) -> str:
    return _split(value)[0]


def parse_keyring(text: str) -> Keyring:
    try:
        data = json.loads(text)
        keys = {k: base64.b64decode(v, validate=True) for k, v in data["keys"].items()}
        return Keyring(str(data["active"]), keys)
    except (ValueError, KeyError, TypeError, binascii.Error) as e:
        if isinstance(e, KeyringError):
            raise
        raise KeyringError(f"the keyring is not valid ({type(e).__name__})") from None


@lru_cache
def load_keyring(path: str) -> Keyring:
    file = Path(path)
    if not file.is_file():
        raise KeyringError(f"the keyring file {path} does not exist")
    return parse_keyring(file.read_text(encoding="utf-8"))

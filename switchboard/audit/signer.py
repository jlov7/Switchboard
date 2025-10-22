from __future__ import annotations

import base64
import hashlib
import hmac
import os
from dataclasses import dataclass
from typing import Any

import cbor2

DEFAULT_ALGORITHM = "HS256"


class AuditSigningError(Exception):
    pass


@dataclass
class AuditSignature:
    algorithm: str
    signature: str


class AuditSigner:
    def __init__(self, secret: str | None = None, algorithm: str = DEFAULT_ALGORITHM) -> None:
        self.secret = (secret or os.getenv("AUDIT_SIGNING_KEY") or "switchboard-dev-key").encode()
        self.algorithm = algorithm

    def sign(self, payload: dict[str, Any]) -> AuditSignature:
        try:
            encoded = cbor2.dumps(payload)
        except ValueError as exc:
            raise AuditSigningError(f"Unable to encode payload for signing: {exc}") from exc
        digest = hmac.new(self.secret, encoded, hashlib.sha256).digest()
        signature = base64.urlsafe_b64encode(digest).decode()
        return AuditSignature(algorithm=self.algorithm, signature=signature)

    def verify(self, payload: dict[str, Any], signature: AuditSignature) -> bool:
        expected = self.sign(payload)
        return hmac.compare_digest(expected.signature, signature.signature)

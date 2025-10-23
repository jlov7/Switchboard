from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from switchboard.audit.rekor_client import RekorClient, RekorError
from switchboard.audit.signer import AuditSignature, AuditSigner
from switchboard.core.models import AuditRecord


@dataclass
class AuditVerificationResult:
    signature_valid: bool
    rekor_included: bool | None = None
    failure_reason: str | None = None

    @property
    def verified(self) -> bool:
        if self.failure_reason is not None:
            return False
        if not self.signature_valid:
            return False
        if self.rekor_included is False:
            return False
        return True


class AuditService:
    def __init__(
        self,
        signer: AuditSigner | None = None,
        output_path: Path | None = None,
        rekor_client: RekorClient | None = None,
    ) -> None:
        self.signer = signer or AuditSigner()
        self.output_path = output_path or Path("data/audit-log.jsonl")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.rekor_client = rekor_client or RekorClient()

    async def record(self, audit_record: AuditRecord) -> AuditRecord:
        canonical = self._canonical_payload(audit_record)
        signature = self.signer.sign(canonical)
        audit_record.signature = signature.signature
        audit_record.signature_algorithm = signature.algorithm
        verify_url = await self._persist(canonical, signature)
        audit_record.verification_url = verify_url
        return audit_record

    def _canonical_payload(self, record: AuditRecord) -> dict[str, Any]:
        payload: dict[str, Any] = record.model_dump()
        payload["signature"] = None
        payload["signature_algorithm"] = None
        payload["verification_url"] = None
        return payload

    async def _persist(self, payload: dict[str, Any], signature: AuditSignature) -> str:
        entry: dict[str, Any] = {
            "signature": signature.signature,
            "algorithm": signature.algorithm,
            "record": payload,
        }
        try:
            verify_url = await self.rekor_client.log_entry(entry)
        except Exception:
            # Best effort logging; do not block the critical path
            verify_url = "offline"
        entry["verification_reference"] = verify_url
        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, default=str) + "\n")
        return verify_url

    async def verify(
        self,
        payload: AuditRecord,
        verify_rekor: bool = True,
    ) -> AuditVerificationResult:
        if not payload.signature or not payload.signature_algorithm:
            return AuditVerificationResult(
                signature_valid=False,
                rekor_included=None,
                failure_reason="Audit record is missing signature metadata",
            )

        signature = AuditSignature(
            algorithm=payload.signature_algorithm,
            signature=payload.signature,
        )
        canonical = self._canonical_payload(payload)
        signature_valid = self.signer.verify(canonical, signature)
        rekor_included: bool | None = None
        failure_reason: str | None = None

        if signature_valid and verify_rekor:
            reference = payload.verification_url
            if reference and reference not in {"offline", ""}:
                try:
                    rekor_included = await self.rekor_client.verify_entry(reference)
                    if rekor_included is False:
                        failure_reason = "Rekor inclusion could not be confirmed"
                except RekorError as exc:
                    rekor_included = False
                    failure_reason = f"Rekor verification failed: {exc}"
            else:
                rekor_included = None
        elif not signature_valid:
            failure_reason = "Signature verification failed"

        return AuditVerificationResult(
            signature_valid=signature_valid,
            rekor_included=rekor_included,
            failure_reason=failure_reason,
        )

#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="data/audit-log.jsonl"

if [[ ! -f "$LOG_FILE" ]]; then
  echo "No audit log found at $LOG_FILE"
  exit 1
fi

echo "Verifying last audit entry..."
python - <<'PYTHON'
import json
from pathlib import Path

from switchboard.audit.signer import AuditSigner, AuditSignature
from switchboard.core.models import AuditRecord

log_path = Path("data/audit-log.jsonl")
line = list(log_path.read_text(encoding="utf-8").strip().splitlines())[-1]
payload = json.loads(line)
record = AuditRecord.model_validate(payload["record"])
signature = AuditSignature(
    algorithm=payload["algorithm"],
    signature=payload["signature"],
)
signer = AuditSigner()
is_valid = signer.verify(record.model_dump(), signature)
print("Valid signature:" if is_valid else "Invalid signature!", is_valid)
PYTHON

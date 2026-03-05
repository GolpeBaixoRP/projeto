import json
import os
import time
from typing import Any, Dict, Optional


class ForensicAuditTrail:
    """Auditoria forense append-only para trilha de decisão/execução."""

    def __init__(self, root_dir: str = "logs"):
        self.root_dir = root_dir
        os.makedirs(self.root_dir, exist_ok=True)
        self.path = os.path.join(self.root_dir, "forensic_audit.jsonl")

    def record(self, event: str, payload: Dict[str, Any], *, error_code: Optional[str] = None, stage: Optional[str] = None, severity: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        row = {
            "ts": time.time(),
            "event": event,
            "payload": payload,
            "error_code": error_code,
            "stage": stage,
            "severity": severity,
            "details": details,
        }
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception as exc:
            fallback = {
                "ts": time.time(),
                "event": "AUDIT_FALLBACK",
                "payload": {"original_event": event, "error": str(exc)},
                "error_code": "MS-AUD-001",
            }
            try:
                with open(os.path.join(self.root_dir, "forensic_audit_fallback.jsonl"), "a", encoding="utf-8") as f:
                    f.write(json.dumps(fallback, ensure_ascii=False) + "\n")
            except Exception:
                pass

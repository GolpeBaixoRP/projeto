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

    @staticmethod
    def _tail(value: Optional[str], max_len: int = 500) -> Optional[str]:
        if value is None:
            return None
        text = str(value)
        return text[-max_len:]

    def record(
        self,
        event: str,
        payload: Dict[str, Any],
        *,
        error_code: Optional[str] = None,
        stage: Optional[str] = None,
        severity: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        operation_id: Optional[str] = None,
        substep: Optional[str] = None,
        disk_number: Optional[int] = None,
        drive_letter: Optional[str] = None,
        expected: Optional[Any] = None,
        found: Optional[Any] = None,
        duration_ms: Optional[int] = None,
        stdout_tail: Optional[str] = None,
        stderr_tail: Optional[str] = None,
    ) -> None:
        now = time.time()
        row = {
            "ts": now,
            "timestamp": now,
            "event": event,
            "payload": payload or {},
            "error_code": error_code,
            "stage": stage,
            "severity": severity,
            "details": details,
            "operation_id": operation_id,
            "substep": substep,
            "disk_number": disk_number,
            "drive_letter": drive_letter,
            "expected": expected,
            "found": found,
            "duration_ms": duration_ms,
            "stdout_tail": self._tail(stdout_tail),
            "stderr_tail": self._tail(stderr_tail),
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

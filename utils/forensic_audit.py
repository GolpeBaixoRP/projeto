import json
import os
import time
from typing import Any, Dict


class ForensicAuditTrail:
    """Auditoria forense append-only para trilha de decisão/execução."""

    def __init__(self, root_dir: str = "logs"):
        self.root_dir = root_dir
        os.makedirs(self.root_dir, exist_ok=True)
        self.path = os.path.join(self.root_dir, "forensic_audit.jsonl")

    def record(self, event: str, payload: Dict[str, Any]) -> None:
        row = {
            "ts": time.time(),
            "event": event,
            "payload": payload,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class PipelineError(Exception):
    code: str
    stage: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    substep: Optional[str] = None
    severity_level: Optional[int] = None
    severity_label: Optional[str] = None
    retryable: Optional[bool] = None
    expected: Optional[Any] = None
    found: Optional[Any] = None
    disk_number: Optional[int] = None
    drive_letter: Optional[str] = None
    operation_id: Optional[str] = None
    cause_hint: Optional[str] = None
    timestamp: Optional[str] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def __str__(self) -> str:
        return f"[{self.code}] {self.stage}: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "stage": self.stage,
            "message": self.message,
            "details": self.details,
            "substep": self.substep,
            "severity_level": self.severity_level,
            "severity_label": self.severity_label,
            "retryable": self.retryable,
            "expected": self.expected,
            "found": self.found,
            "disk_number": self.disk_number,
            "drive_letter": self.drive_letter,
            "operation_id": self.operation_id,
            "cause_hint": self.cause_hint,
            "timestamp": self.timestamp,
        }

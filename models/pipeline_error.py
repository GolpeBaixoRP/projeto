from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class PipelineError(Exception):
    code: str
    stage: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.code}] {self.stage}: {self.message}"

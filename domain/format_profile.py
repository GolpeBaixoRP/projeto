from dataclasses import dataclass


@dataclass(frozen=True)
class FormatProfile:
    id: str
    filesystem: str
    partition_style: str
    worker_ps1: str

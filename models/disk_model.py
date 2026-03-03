from dataclasses import dataclass
from typing import List, Optional

@dataclass
class DiskModel:
    number: int
    friendly_name: str
    partition_style: str
    bus_type: str
    is_boot: bool
    is_system: bool
    is_offline: bool
    operational_status: str
    partitions: Optional[List[dict]] = None
    volumes: Optional[List[dict]] = None
    status: Optional[str] = None
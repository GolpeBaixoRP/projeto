from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DiskModel:
    number: int
    friendly_name: str
    serial_number: str
    partition_style: str
    bus_type: str
    is_boot: bool
    is_system: bool
    is_offline: bool
    operational_status: str
    size: Optional[int] = None
    unique_id: Optional[str] = None
    location_path: Optional[str] = None
    is_removable: Optional[bool] = None
    is_readonly: Optional[bool] = None
    partitions: Optional[List[dict]] = None
    volumes: Optional[List[dict]] = None
    status: Optional[str] = None

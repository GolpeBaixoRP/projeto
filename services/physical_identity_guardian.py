import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class PhysicalIdentity:
    disk_number: int
    serial_number: str
    partition_style: str
    device_status: str
    unique_id: str
    location_path: str
    size_bytes: int
    bus_type: str
    is_removable: bool


class GuardianObserver:
    def __init__(self):
        self.started_at = time.time()
        self.active = True

    def observe(self, snapshot: Dict[str, Any], operation_id: Optional[str] = None) -> Dict[str, Any]:
        return {
            "operation_id": operation_id,
            "ts": time.time(),
            "kind": "OBSERVATION",
            "summary": {
                "has_snapshot": bool(snapshot),
                "disk_number": snapshot.get("Disk", {}).get("Number") if snapshot else None,
            },
        }

    def detect_identity_violation(self, before: Optional[PhysicalIdentity], after: Optional[PhysicalIdentity], operation_id: Optional[str] = None) -> Dict[str, Any]:
        violations = []
        if before and after:
            if before.is_removable:
                score = 0
                if before.unique_id and after.unique_id and before.unique_id == after.unique_id:
                    score += 2
                if before.serial_number and after.serial_number and before.serial_number == after.serial_number:
                    score += 2
                if before.location_path and after.location_path and before.location_path == after.location_path:
                    score += 1
                if before.disk_number != after.disk_number and score < 2:
                    violations.append("IDENTITY_DRIFT_DISK_NUMBER")
                if score == 0:
                    violations.append("IDENTITY_DRIFT_REMOVABLE_NO_MATCH")
            else:
                if before.disk_number != after.disk_number:
                    violations.append("IDENTITY_DRIFT_DISK_NUMBER")
                if before.serial_number != after.serial_number:
                    violations.append("IDENTITY_DRIFT_SERIAL")

            if abs((before.size_bytes or 0) - (after.size_bytes or 0)) > 32 * 1024 * 1024:
                violations.append("IDENTITY_DRIFT_SIZE")

            if before.partition_style != after.partition_style:
                violations.append("STRUCTURAL_DRIFT_PARTITION_STYLE")
            if before.device_status != after.device_status:
                violations.append("HEALTH_DRIFT_DEVICE_STATUS")

        return {"operation_id": operation_id, "ts": time.time(), "kind": "IDENTITY_CHECK", "violations": violations, "healthy": len(violations) == 0}

    def report(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return {"guardian": "passive", "event": event}

    def shutdown(self, operation_id: Optional[str] = None) -> Dict[str, Any]:
        self.active = False
        return {"operation_id": operation_id, "ts": time.time(), "kind": "SHUTDOWN", "uptime_s": round(time.time() - self.started_at, 6)}


class PhysicalIdentityFactory:
    @staticmethod
    def from_disk_model(disk: Any) -> PhysicalIdentity:
        return PhysicalIdentity(
            disk_number=int(getattr(disk, "number")),
            serial_number=str(getattr(disk, "serial_number", "") or "").strip(),
            partition_style=str(getattr(disk, "partition_style", "UNKNOWN") or "UNKNOWN"),
            device_status=str(getattr(disk, "operational_status", "UNKNOWN") or "UNKNOWN"),
            unique_id=str(getattr(disk, "unique_id", "") or "").strip(),
            location_path=str(getattr(disk, "location_path", "") or "").strip(),
            size_bytes=int(getattr(disk, "size", 0) or 0),
            bus_type=str(getattr(disk, "bus_type", "") or "").strip(),
            is_removable=bool(getattr(disk, "is_removable", False)),
        )

    @staticmethod
    def from_snapshot_entry(entry: Dict[str, Any]) -> PhysicalIdentity:
        disk = entry.get("Disk", {})
        return PhysicalIdentity(
            disk_number=int(disk.get("Number")),
            serial_number=str(disk.get("SerialNumber") or "").strip(),
            partition_style=str(disk.get("PartitionStyle") or "UNKNOWN"),
            device_status=str(disk.get("OperationalStatus") or "UNKNOWN"),
            unique_id=str(disk.get("UniqueId") or "").strip(),
            location_path=str(disk.get("LocationPath") or "").strip(),
            size_bytes=int(disk.get("Size") or 0),
            bus_type=str(disk.get("BusType") or "").strip(),
            is_removable=bool(disk.get("IsRemovable") or False),
        )

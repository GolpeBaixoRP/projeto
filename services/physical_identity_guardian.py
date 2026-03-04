import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class PhysicalIdentity:
    disk_number: int
    serial_number: str
    partition_style: str
    device_status: str


class GuardianObserver:
    """Guardian observacional passivo e efêmero.

    Regras:
    - Não executa mutação.
    - Não decide pipeline.
    - Não corrige erro.
    - Apenas observa, valida sinais e reporta eventos.
    """

    def __init__(self):
        self.started_at = time.time()
        self.active = True

    def observe(self, snapshot: Dict[str, Any], operation_id: Optional[str] = None) -> Dict[str, Any]:
        event = {
            "operation_id": operation_id,
            "ts": time.time(),
            "kind": "OBSERVATION",
            "summary": {
                "has_snapshot": bool(snapshot),
                "disk_number": snapshot.get("Disk", {}).get("Number") if snapshot else None,
            },
        }
        return event

    def detect_identity_violation(
        self,
        before: Optional[PhysicalIdentity],
        after: Optional[PhysicalIdentity],
        operation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        violations = []

        if before and after:
            if before.disk_number != after.disk_number:
                violations.append("IDENTITY_DRIFT_DISK_NUMBER")
            if before.serial_number != after.serial_number:
                violations.append("IDENTITY_DRIFT_SERIAL")
            if before.partition_style != after.partition_style:
                violations.append("STRUCTURAL_DRIFT_PARTITION_STYLE")
            if before.device_status != after.device_status:
                violations.append("HEALTH_DRIFT_DEVICE_STATUS")

        return {
            "operation_id": operation_id,
            "ts": time.time(),
            "kind": "IDENTITY_CHECK",
            "violations": violations,
            "healthy": len(violations) == 0,
        }

    def report(self, event: Dict[str, Any]) -> Dict[str, Any]:
        # Guardian não persiste decisão nem aciona ações.
        # Apenas devolve payload observacional para camada superior auditar.
        return {
            "guardian": "passive",
            "event": event,
        }

    def shutdown(self, operation_id: Optional[str] = None) -> Dict[str, Any]:
        self.active = False
        return {
            "operation_id": operation_id,
            "ts": time.time(),
            "kind": "SHUTDOWN",
            "uptime_s": round(time.time() - self.started_at, 6),
        }


class PhysicalIdentityFactory:
    """Helpers puros para extrair identidade física de snapshots/modelos."""

    @staticmethod
    def from_disk_model(disk: Any) -> PhysicalIdentity:
        return PhysicalIdentity(
            disk_number=int(getattr(disk, "number")),
            serial_number=str(getattr(disk, "serial_number", "UNKNOWN") or "UNKNOWN").strip(),
            partition_style=str(getattr(disk, "partition_style", "UNKNOWN") or "UNKNOWN"),
            device_status=str(getattr(disk, "operational_status", "UNKNOWN") or "UNKNOWN"),
        )

    @staticmethod
    def from_snapshot_entry(entry: Dict[str, Any]) -> PhysicalIdentity:
        disk = entry.get("Disk", {})
        return PhysicalIdentity(
            disk_number=int(disk.get("Number")),
            serial_number=str(disk.get("SerialNumber") or "UNKNOWN").strip(),
            partition_style=str(disk.get("PartitionStyle") or "UNKNOWN"),
            device_status=str(disk.get("OperationalStatus") or "UNKNOWN"),
        )

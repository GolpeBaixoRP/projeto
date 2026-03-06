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
    """
    Observador de identidade física/lógica do dispositivo durante a operação.
    Interface esperada pelo OperationController:
      - observe(...)
      - detect_identity_violation(...)
      - report(...)
      - shutdown(...)
    """

    def __init__(self):
        self.started_at = time.time()
        self.active = True

    def observe(self, snapshot: Dict[str, Any], operation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Apenas registra um evento de observação.
        """
        return {
            "operation_id": operation_id,
            "ts": time.time(),
            "kind": "OBSERVATION",
            "summary": snapshot,
        }

    def report(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook padrão para permitir que o Controller injete eventos no audit.
        """
        return {"guardian": "passive", "event": event}

    def shutdown(self, operation_id: Optional[str] = None) -> Dict[str, Any]:
        self.active = False
        return {
            "operation_id": operation_id,
            "ts": time.time(),
            "kind": "SHUTDOWN",
            "uptime_s": round(time.time() - self.started_at, 6),
        }

    def detect_identity_violation(
        self,
        before: PhysicalIdentity,
        after: PhysicalIdentity,
        stage: str = "postcheck",
        operation_id: Optional[str] = None,
        **_extra: Any,
    ) -> Dict[str, Any]:
        """
        Decide se houve troca de dispositivo (violação crítica) ou apenas drift tolerável.

        IMPORTANTE:
        - PartitionStyle NÃO é identidade física. Ele muda de propósito (GPT -> MBR).
          Isso deve ser verificado no estágio VERIFY, não aqui.
        - Em USB-like, DiskNumber/LocationPath podem mudar e não devem ser fatal se houver match forte.
        """

        violations = []
        warnings = []

        # USB-like = removable ou bus USB (inclui bridges SATA->USB que reenumeram)
        usb_like = (
            bool(before.is_removable)
            or bool(after.is_removable)
            or (before.bus_type or "").upper() == "USB"
            or (after.bus_type or "").upper() == "USB"
        )

        # Funções utilitárias
        def _eq(a: str, b: str) -> bool:
            return bool(a) and bool(b) and a == b

        # Score de match
        score = 0
        if _eq(before.unique_id, after.unique_id):
            score += 4
        if _eq(before.serial_number, after.serial_number):
            score += 4

        # Size é bom como apoio (não suficiente sozinho)
        if before.size_bytes and after.size_bytes and before.size_bytes == after.size_bytes:
            score += 1

        # LocationPath é VOLÁTIL em USB: usar só como apoio (peso baixo)
        if _eq(before.location_path, after.location_path):
            score += 1

        # Drift informativo (não fatal em USB-like se match forte)
        if before.disk_number != after.disk_number:
            if usb_like:
                warnings.append("DRIFT_DISK_NUMBER_USB_LIKE")
            else:
                violations.append("DRIFT_DISK_NUMBER_NON_USB")

        if before.location_path != after.location_path:
            if usb_like:
                warnings.append("DRIFT_LOCATION_PATH_USB_LIKE")
            else:
                warnings.append("DRIFT_LOCATION_PATH_NON_USB")

        # PartitionStyle: NUNCA como violação aqui
        if before.partition_style != after.partition_style:
            warnings.append("STRUCTURAL_DRIFT_PARTITION_STYLE_EXPECTED")

        # Regras de decisão
        if usb_like:
            # Se UniqueId OU Serial bateu (score >=4), aceitável.
            # Se não bateu forte, pelo menos score >=2 (size + algum outro) para seguir, mas com warning.
            if score >= 4:
                ok = True
            elif score >= 2:
                ok = True
                warnings.append("WEAK_MATCH_USB_LIKE")
            else:
                ok = False
                violations.append("IDENTITY_MISMATCH_USB_LIKE")
        else:
            # Não-USB: precisa ser bem mais rígido.
            ok = score >= 5
            if not ok:
                violations.append("IDENTITY_MISMATCH_NON_USB")

        return {
            "operation_id": operation_id,
            "ok": ok,
            "stage": stage,
            "usb_like": usb_like,
            "score": score,
            "warnings": warnings,
            "violations": violations,
            "before": before.__dict__,
            "after": after.__dict__,
        }


class PhysicalIdentityFactory:
    """
    Cria uma identidade estável a partir do DiskModel do projeto.
    """

    @staticmethod
    def from_disk(disk: Any) -> PhysicalIdentity:
        # Alguns campos podem ser None no snapshot. Normalizar para string vazia/int 0 onde necessário.
        def s(x: Any) -> str:
            return "" if x is None else str(x)

        def i(x: Any) -> int:
            try:
                return int(x)
            except Exception:
                return 0

        return PhysicalIdentity(
            disk_number=i(getattr(disk, "number", getattr(disk, "disk_number", 0))),
            serial_number=s(getattr(disk, "serial_number", "")),
            partition_style=s(getattr(disk, "partition_style", "")),
            device_status=s(getattr(disk, "status", getattr(disk, "device_status", ""))),
            unique_id=s(getattr(disk, "unique_id", "")),
            location_path=s(getattr(disk, "location_path", "")),
            size_bytes=i(getattr(disk, "size", getattr(disk, "size_bytes", 0))),
            bus_type=s(getattr(disk, "bus_type", "")),
            is_removable=bool(getattr(disk, "is_removable", False)),
        )

    @staticmethod
    def from_disk_model(disk: Any) -> PhysicalIdentity:
        return PhysicalIdentityFactory.from_disk(disk)
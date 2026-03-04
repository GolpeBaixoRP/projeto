from core.disk_manager import DiskManager
from services.real_format_service import RealFormatterService
from services.physical_identity_guardian import GuardianObserver, PhysicalIdentityFactory
from utils.forensic_audit import ForensicAuditTrail
from utils.logger import setup_logger

logger = setup_logger()


class OperationController:

    def __init__(self):
        self.disk_manager = DiskManager()
        self.formatter = RealFormatterService()
        self.audit = ForensicAuditTrail()
        self.snapshot = []
        self.locked = False
        self.selected_disk = None
        self.selected_identity = None

    def initialize(self):
        self.snapshot = self.disk_manager.refresh()
        self.audit.record("SNAPSHOT_REFRESH", {"disk_count": len(self.snapshot)})
        logger.info("Snapshot atualizado.")
        return self.snapshot

    def _policy_validate_selection(self, disk):
        if disk.number == 0:
            raise ValueError("Disk 0 bloqueado por política de segurança")
        if getattr(disk, "is_boot", False):
            raise ValueError("Disco de boot bloqueado por política de segurança")
        if getattr(disk, "is_system", False):
            raise ValueError("Disco de sistema bloqueado por política de segurança")
        if getattr(disk, "is_offline", False):
            raise ValueError("Disco offline bloqueado por política de segurança")
        if getattr(disk, "partition_style", None) == "GPT":
            raise ValueError("PartitionStyle GPT bloqueado para pipeline legado")
        if disk.status == "BLOCKED":
            raise ValueError("Disco bloqueado")

    def select_disk(self, disk_number: int):
        if self.locked:
            raise RuntimeError("Sistema bloqueado.")

        guardian = GuardianObserver()
        operation_id = f"select-{disk_number}"

        try:
            for disk in self.snapshot:
                if disk.number != disk_number:
                    continue

                # Decisão é do controller/política, não do guardian.
                self._policy_validate_selection(disk)

                self.selected_disk = disk
                self.selected_identity = PhysicalIdentityFactory.from_disk_model(disk)
                self.locked = True

                observed = guardian.observe(
                    {
                        "Disk": {
                            "Number": disk.number,
                            "SerialNumber": getattr(disk, "serial_number", "UNKNOWN"),
                            "PartitionStyle": getattr(disk, "partition_style", "UNKNOWN"),
                            "OperationalStatus": getattr(disk, "operational_status", "UNKNOWN"),
                        }
                    },
                    operation_id=operation_id,
                )
                self.audit.record("GUARDIAN_OBSERVE", guardian.report(observed))
                self.audit.record(
                    "SELECTION_LOCKED",
                    {
                        "disk": disk_number,
                        "serial": self.selected_identity.serial_number,
                    },
                )
                logger.info(f"Disco {disk_number} selecionado.")
                return disk

            raise ValueError("Disco não encontrado.")

        except Exception as e:
            self.audit.record("SELECTION_BLOCKED", {"disk": disk_number, "reason": str(e)})
            raise
        finally:
            self.audit.record("GUARDIAN_SHUTDOWN", guardian.report(guardian.shutdown(operation_id=operation_id)))

    def execute_full_format(self, filesystem):
        guardian = GuardianObserver()
        operation_id = f"format-{getattr(self.selected_disk, 'number', 'none')}"

        try:
            if not self.selected_disk or not self.selected_identity:
                raise RuntimeError("Nenhum disco selecionado.")

            self.audit.record(
                "PIPELINE_EXECUTE_START",
                {"disk": self.selected_disk.number, "filesystem": filesystem},
            )

            before_event = guardian.observe(
                {
                    "Disk": {
                        "Number": self.selected_disk.number,
                        "SerialNumber": self.selected_identity.serial_number,
                        "PartitionStyle": self.selected_identity.partition_style,
                        "OperationalStatus": self.selected_identity.device_status,
                    }
                },
                operation_id=operation_id,
            )
            self.audit.record("GUARDIAN_OBSERVE", guardian.report(before_event))

            result = self.formatter.format_disk(self.selected_disk, filesystem)
            self.snapshot = self.disk_manager.refresh()

            refreshed_disk = None
            for disk in self.snapshot:
                if disk.number == self.selected_disk.number:
                    refreshed_disk = disk
                    break

            if refreshed_disk is None:
                raise RuntimeError("Falha crítica: disco selecionado ausente no snapshot pós-operação")

            refreshed_identity = PhysicalIdentityFactory.from_disk_model(refreshed_disk)
            identity_check = guardian.detect_identity_violation(
                before=self.selected_identity,
                after=refreshed_identity,
                operation_id=operation_id,
            )
            self.audit.record("GUARDIAN_IDENTITY_CHECK", guardian.report(identity_check))

            # Decisão operacional permanece no controller.
            if identity_check.get("violations"):
                raise RuntimeError(f"Falha de identidade física: {identity_check['violations']}")

            self.audit.record(
                "PIPELINE_VERIFY_OK",
                {"disk": refreshed_identity.disk_number, "identity": "IDENTITY_STABLE"},
            )

            self.selected_disk = None
            self.selected_identity = None
            self.locked = False
            self.audit.record("PIPELINE_COMMIT_RELEASE", {"result_status": result.get("Status")})
            return result

        except Exception as e:
            self.locked = False
            self.audit.record("PIPELINE_FAILURE", {"error": str(e)})
            logger.error(f"Format error: {e}")
            raise
        finally:
            self.audit.record("GUARDIAN_SHUTDOWN", guardian.report(guardian.shutdown(operation_id=operation_id)))

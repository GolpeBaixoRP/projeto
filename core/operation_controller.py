import time

from core.disk_manager import DiskManager
from models.pipeline_error import PipelineError
from services.physical_identity_guardian import GuardianObserver, PhysicalIdentityFactory
from services.real_format_service import RealFormatterService
from utils.forensic_audit import ForensicAuditTrail
from utils.logger import setup_logger
from utils.progress_reporter import ProgressReporter

logger = setup_logger()


class OperationController:

    def __init__(self):
        self.disk_manager = DiskManager()
        self.formatter = RealFormatterService()
        self.audit = ForensicAuditTrail()
        self.progress = ProgressReporter()
        self.snapshot = []
        self.locked = False
        self.selected_disk = None
        self.selected_identity = None

    def initialize(self):
        self.progress.set(10, "SNAPSHOT refresh + identidade")
        self.snapshot = self.disk_manager.refresh()
        self.audit.record("SNAPSHOT_REFRESH", {"disk_count": len(self.snapshot)})
        logger.info("Snapshot atualizado.")
        return self.snapshot

    def _policy_validate_selection(self, disk):
        if disk.number == 0 or getattr(disk, "is_boot", False) or getattr(disk, "is_system", False) or getattr(disk, "is_offline", False) or disk.status == "BLOCKED":
            raise PipelineError("MS-SEL-002", "selection", "Disco bloqueado por política", {"disk": disk.number})

    def select_disk(self, disk_number: int):
        if self.locked:
            raise RuntimeError("Sistema bloqueado.")
        guardian = GuardianObserver()
        operation_id = f"select-{disk_number}"
        try:
            for disk in self.snapshot:
                if disk.number != disk_number:
                    continue
                self._policy_validate_selection(disk)
                self.selected_disk = disk
                self.selected_identity = PhysicalIdentityFactory.from_disk_model(disk)
                self.locked = True
                observed = guardian.observe({"Disk": {"Number": disk.number, "SerialNumber": getattr(disk, "serial_number", "UNKNOWN"), "PartitionStyle": getattr(disk, "partition_style", "UNKNOWN"), "OperationalStatus": getattr(disk, "operational_status", "UNKNOWN")}}, operation_id=operation_id)
                self.audit.record("GUARDIAN_OBSERVE", guardian.report(observed))
                self.audit.record("SELECTION_LOCKED", {"disk": disk_number, "serial": self.selected_identity.serial_number})
                return disk
            raise ValueError("Disco não encontrado.")
        finally:
            self.audit.record("GUARDIAN_SHUTDOWN", guardian.report(guardian.shutdown(operation_id=operation_id)))

    def _verify_post_conditions(self, refreshed_disk, filesystem, ipc_data, operation_id):
        disk_number = getattr(refreshed_disk, "number", None)
        if str(getattr(refreshed_disk, "partition_style", "")).upper() != "MBR":
            found = getattr(refreshed_disk, "partition_style", None)
            raise PipelineError(
                "MS-VFY-001",
                "verify",
                "PartitionStyle divergente do esperado",
                {"expected": "MBR", "found": found},
                substep="partition_style",
                expected="MBR",
                found=found,
                disk_number=disk_number,
                operation_id=operation_id,
            )

        parts = getattr(refreshed_disk, "partitions", []) or []
        vols = getattr(refreshed_disk, "volumes", []) or []
        if len(parts) != 1:
            raise PipelineError(
                "MS-VFY-005",
                "verify",
                "Quantidade de partições inesperada",
                {"expected": 1, "found": len(parts)},
                substep="partition_count",
                expected=1,
                found=len(parts),
                disk_number=disk_number,
                operation_id=operation_id,
            )
        if not vols:
            raise PipelineError(
                "MS-VFY-002",
                "verify",
                "Volume ausente após execução do worker",
                {"expected": "volume presente", "found": "sem volumes"},
                substep="volume_presence",
                expected="volume presente",
                found="sem volumes",
                disk_number=disk_number,
                operation_id=operation_id,
            )

        drive_letter = str((ipc_data or {}).get("DriveLetter") or (vols[0].get("DriveLetter") if vols else "") or "").strip().upper()
        if not drive_letter:
            raise PipelineError(
                "MS-VOL-001",
                "verify",
                "Letra de unidade ausente após operação",
                {"expected": "drive letter", "found": "vazio"},
                substep="drive_letter",
                expected="drive letter",
                found="vazio",
                disk_number=disk_number,
                operation_id=operation_id,
            )

        fs_expected = (filesystem or "").upper()
        fs_found = str((ipc_data or {}).get("FileSystem") or (vols[0].get("FileSystem") if vols else "")).upper()
        if fs_found != fs_expected:
            raise PipelineError(
                "MS-VFY-003",
                "verify",
                "Filesystem divergente",
                {"expected": fs_expected, "found": fs_found},
                substep="filesystem",
                expected=fs_expected,
                found=fs_found,
                disk_number=disk_number,
                drive_letter=drive_letter,
                operation_id=operation_id,
            )

        if fs_expected == "FAT32":
            block_size = (ipc_data or {}).get("BlockSize")
            if int(block_size or 0) != 32768:
                raise PipelineError(
                    "MS-VFY-004",
                    "verify",
                    "BlockSize FAT32 divergente da política",
                    {"expected": 32768, "found": block_size},
                    substep="block_size",
                    expected=32768,
                    found=block_size,
                    disk_number=disk_number,
                    drive_letter=drive_letter,
                    operation_id=operation_id,
                )

        worker_success = bool((ipc_data or {}).get("Success", False))
        if not worker_success:
            raise PipelineError(
                "MS-VFY-006",
                "verify",
                "Sucesso reportado incompatível com evidência final",
                {"expected": True, "found": worker_success},
                substep="success_contract",
                expected=True,
                found=worker_success,
                disk_number=disk_number,
                drive_letter=drive_letter,
                operation_id=operation_id,
            )

    def _commit_barrier(self, disk_number, filesystem, operation_id):
        time.sleep(0.3)
        barrier_snapshot = self.disk_manager.refresh()

        stable_disk = next((d for d in barrier_snapshot if d.number == disk_number), None)
        if stable_disk is None and self.selected_identity is not None:
            for d in barrier_snapshot:
                if getattr(d, "serial_number", "") == self.selected_identity.serial_number or getattr(d, "unique_id", "") == self.selected_identity.unique_id:
                    stable_disk = d
                    break

        if stable_disk is None:
            raise PipelineError(
                "MS-VFY-006",
                "verify",
                "Commit barrier falhou: disco não encontrado após verify",
                {"expected": "disco estável", "found": "ausente"},
                substep="commit_barrier",
                expected="disco estável",
                found="ausente",
                disk_number=disk_number,
                operation_id=operation_id,
            )

        parts = getattr(stable_disk, "partitions", []) or []
        vols = getattr(stable_disk, "volumes", []) or []
        stable_fs = str((vols[0].get("FileSystem") if vols else "") or "").upper()
        stable_letter = str((vols[0].get("DriveLetter") if vols else "") or "").strip()

        if str(getattr(stable_disk, "partition_style", "")).upper() != "MBR" or not parts or not vols or not stable_letter or stable_fs != (filesystem or "").upper():
            raise PipelineError(
                "MS-VFY-006",
                "verify",
                "Commit barrier falhou: estado final instável após verify",
                {
                    "expected": {"partition_style": "MBR", "volume": True, "drive_letter": True, "filesystem": (filesystem or "").upper()},
                    "found": {
                        "partition_style": getattr(stable_disk, "partition_style", None),
                        "partition_count": len(parts),
                        "volume_count": len(vols),
                        "drive_letter": stable_letter or None,
                        "filesystem": stable_fs,
                    },
                },
                substep="commit_barrier",
                expected="estado estável pós-verify",
                found="estado divergente",
                disk_number=disk_number,
                drive_letter=stable_letter or None,
                operation_id=operation_id,
            )

        self.snapshot = barrier_snapshot

    def execute_full_format(self, filesystem):
        guardian = GuardianObserver()
        operation_id = f"format-{getattr(self.selected_disk, 'number', 'none')}"
        self.progress.set(0, "INIT / lock")
        try:
            if not self.selected_disk or not self.selected_identity:
                raise RuntimeError("Nenhum disco selecionado.")
            self.audit.record("PIPELINE_EXECUTE_START", {"disk": self.selected_disk.number, "filesystem": filesystem})
            self.audit.record("operation_start", {"disk": self.selected_disk.number, "filesystem": filesystem}, operation_id=operation_id, stage="pipeline")

            self.progress.set(10, "SNAPSHOT refresh + identidade")
            latest_snapshot = self.disk_manager.refresh()
            current_disk = next((d for d in latest_snapshot if d.number == self.selected_disk.number), None)
            if current_disk is None:
                raise PipelineError("MS-USB-003", "precheck", "Disco ausente antes da formatação", {})

            self.progress.set(25, "PRECHECK guardian")
            current_identity = PhysicalIdentityFactory.from_disk_model(current_disk)
            precheck = guardian.detect_identity_violation(before=self.selected_identity, after=current_identity, operation_id=f"{operation_id}-precheck")
            self.audit.record("GUARDIAN_PRECHECK", guardian.report(precheck))
            if precheck.get("violations"):
                raise PipelineError("MS-GRD-001", "precheck", "Falha de identidade pré-formatação", {"violations": precheck["violations"]})

            self.progress.set(35, "IPC start")
            result = self.formatter.format_disk(self.selected_disk, filesystem)
            self.progress.set(70, "IPC end")

            self.progress.set(85, "Snapshot refresh pós")
            self.snapshot = self.disk_manager.refresh()
            refreshed_disk = next((d for d in self.snapshot if d.number == self.selected_disk.number), None)
            if refreshed_disk is None:
                # reenumeração: tentar por identidade
                for d in self.snapshot:
                    if getattr(d, "serial_number", "") == self.selected_identity.serial_number or getattr(d, "unique_id", "") == self.selected_identity.unique_id:
                        refreshed_disk = d
                        break
            if refreshed_disk is None:
                raise PipelineError("MS-USB-003", "postcheck", "Dispositivo removível não foi re-adquirido", {})

            refreshed_identity = PhysicalIdentityFactory.from_disk_model(refreshed_disk)
            identity_check = guardian.detect_identity_violation(before=self.selected_identity, after=refreshed_identity, operation_id=operation_id)
            self.audit.record("GUARDIAN_IDENTITY_CHECK", guardian.report(identity_check))
            if identity_check.get("violations"):
                raise PipelineError("MS-GRD-001", "postcheck", "Falha de identidade física", {"violations": identity_check["violations"]})

            self.progress.set(95, "Verify evidência")
            self._verify_post_conditions(refreshed_disk, filesystem, result.get("data") or {}, operation_id)
            self.audit.record("operation_verify_success", {"disk": refreshed_disk.number, "filesystem": filesystem}, operation_id=operation_id, stage="verify")
            self._commit_barrier(refreshed_disk.number, filesystem, operation_id)
            self.audit.record("commit_barrier_passed", {"disk": refreshed_disk.number, "filesystem": filesystem}, operation_id=operation_id, stage="verify")

            self.selected_disk = None
            self.selected_identity = None
            self.locked = False
            self.progress.set(100, "Commit/release")
            self.audit.record("operation_commit", {"disk": result.get("disk"), "result_status": result.get("status")}, operation_id=operation_id, stage="commit")
            self.audit.record("PIPELINE_COMMIT_RELEASE", {"result_status": result.get("status")})
            return result
        except PipelineError as e:
            self.locked = False
            self.audit.record("PIPELINE_FAILURE", {"error": str(e), "details": e.details}, error_code=e.code, stage=e.stage, severity="ERROR")
            logger.error(f"Format error: {e}")
            raise
        except Exception as e:
            self.locked = False
            self.audit.record("PIPELINE_FAILURE", {"error": str(e)}, error_code="MS-RUN-003", stage="pipeline", severity="ERROR")
            logger.error(f"Format error: {e}")
            raise
        finally:
            self.audit.record("GUARDIAN_SHUTDOWN", guardian.report(guardian.shutdown(operation_id=operation_id)))

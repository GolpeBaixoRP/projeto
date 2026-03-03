from core.disk_manager import DiskManager
from services.real_format_service import RealFormatterService
from utils.logger import setup_logger

logger = setup_logger()


class OperationController:

    def __init__(self):
        self.disk_manager = DiskManager()
        self.formatter = RealFormatterService()
        self.snapshot = []
        self.locked = False
        self.selected_disk = None

    # ============================
    # Initialization
    # ============================

    def initialize(self):
        self.snapshot = self.disk_manager.refresh()
        logger.info("Snapshot atualizado.")
        return self.snapshot

    # ============================
    # Disk Selection
    # ============================

    def select_disk(self, disk_number: int):

        if self.locked:
            raise RuntimeError("Sistema bloqueado.")

        for disk in self.snapshot:

            if disk.number == disk_number:

                if disk.number == 0:
                    raise ValueError("Disk 0 nunca pode ser formatado.")

                if getattr(disk, "is_boot", False):
                    raise ValueError("Disco de boot não pode ser formatado.")

                if getattr(disk, "is_system", False):
                    raise ValueError("Disco do sistema não pode ser formatado.")

                if disk.status == "BLOCKED":
                    raise ValueError("Disco bloqueado.")

                self.selected_disk = disk
                self.locked = True

                logger.info(f"Disco {disk_number} selecionado.")

                return disk

        raise ValueError("Disco não encontrado.")

    # ============================
    # Format Execution
    # ============================

    def execute_full_format(self, filesystem):

        try:

            if not self.selected_disk:
                raise RuntimeError("Nenhum disco selecionado.")

            result = self.formatter.format_disk(
                self.selected_disk,
                filesystem
            )

            # Refresh snapshot after format
            self.snapshot = self.disk_manager.refresh()

            # Unlock system after success
            self.locked = False

            return result

        except Exception as e:

            # Recovery-safe unlock
            self.locked = False

            logger.error(f"Format error: {e}")

            raise
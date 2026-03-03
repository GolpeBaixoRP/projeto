import json
import os
import time
from utils.logger import setup_logger
from core.disk_manager import DiskManager
from core.operation_controller import OperationController

logger = setup_logger()

CHECKPOINT_FILE = "operation_checkpoint.json"


class SystemOrchestrator:

    def __init__(self):
        self.disk_manager = DiskManager()
        self.controller = OperationController()

    def save_checkpoint(self, state):
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def load_checkpoint(self):
        if not os.path.exists(CHECKPOINT_FILE):
            return None

        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def execute_pipeline(self, disk, filesystem):

        try:
            logger.info("Pipeline iniciado")

            checkpoint = {
                "disk": disk.number,
                "filesystem": filesystem,
                "stage": "START"
            }

            self.save_checkpoint(checkpoint)

            # 1️⃣ Preparar e formatar disco
            result = self.controller.format_disk(disk, filesystem)

            checkpoint["stage"] = "FORMAT_DONE"
            self.save_checkpoint(checkpoint)

            # 2️⃣ Validar resultado
            if not result:
                raise RuntimeError("Formatter retornou falha")

            checkpoint["stage"] = "VALIDATION_DONE"
            self.save_checkpoint(checkpoint)

            logger.info("Pipeline finalizado com sucesso")

            # Remove checkpoint ao final
            if os.path.exists(CHECKPOINT_FILE):
                os.remove(CHECKPOINT_FILE)

            return True

        except Exception as e:

            logger.error(f"Pipeline falhou: {e}")

            self.recovery_procedure()

            return False

    def recovery_procedure(self):

        logger.warning("Recovery procedure ativado")

        checkpoint = self.load_checkpoint()

        if checkpoint:
            logger.info(f"Recuperando estado: {checkpoint}")

        # Aqui você pode adicionar lógica de recovery real
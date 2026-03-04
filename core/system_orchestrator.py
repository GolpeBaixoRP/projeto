import json
import os
from utils.logger import setup_logger
from core.disk_manager import DiskManager
from core.operation_controller import OperationController
from utils.forensic_audit import ForensicAuditTrail

logger = setup_logger()

CHECKPOINT_FILE = "operation_checkpoint.json"


class SystemOrchestrator:

    def __init__(self):
        self.disk_manager = DiskManager()
        self.controller = OperationController()
        self.audit = ForensicAuditTrail()

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
                "stage": "VALIDATE",
            }
            self.save_checkpoint(checkpoint)
            self.audit.record("PIPELINE_STAGE", checkpoint)

            self.controller.select_disk(disk.number)

            checkpoint["stage"] = "LOCK"
            self.save_checkpoint(checkpoint)
            self.audit.record("PIPELINE_STAGE", checkpoint)

            result = self.controller.execute_full_format(filesystem)

            checkpoint["stage"] = "VERIFY"
            self.save_checkpoint(checkpoint)
            self.audit.record("PIPELINE_STAGE", checkpoint)

            if not result or result.get("Status") != "COMPLETED":
                raise RuntimeError("Formatter retornou falha")

            checkpoint["stage"] = "COMMIT"
            self.save_checkpoint(checkpoint)
            self.audit.record("PIPELINE_STAGE", checkpoint)

            checkpoint["stage"] = "RELEASE"
            self.save_checkpoint(checkpoint)
            self.audit.record("PIPELINE_STAGE", checkpoint)

            logger.info("Pipeline finalizado com sucesso")
            if os.path.exists(CHECKPOINT_FILE):
                os.remove(CHECKPOINT_FILE)
            return True

        except Exception as e:
            logger.error(f"Pipeline falhou: {e}")
            self.audit.record("PIPELINE_FAILURE", {"disk": getattr(disk, 'number', None), "error": str(e)})
            self.recovery_procedure()
            return False

    def recovery_procedure(self):
        logger.warning("Recovery procedure ativado")
        checkpoint = self.load_checkpoint()

        if checkpoint:
            logger.info(f"Recuperando estado: {checkpoint}")
            self.audit.record("PIPELINE_RECOVERY", checkpoint)

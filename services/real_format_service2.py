import json
from pathlib import Path
from utils.powershell_runner import run_powershell


class RealFormatService:

    def __init__(self):

        project_root = Path(__file__).resolve().parent.parent
        self.worker = project_root / "assets" / "xfat_process.ps1"
        self.stage = "format"

    def execute(self, disk_number: int):

        try:

            command = (
                f'powershell -NoProfile -ExecutionPolicy Bypass '
                f'-File "{self.worker}" '
                f'-DiskNumber {disk_number}'
            )

            output = run_powershell(
                command,
                elevated=True,
                timeout=120
            )

            data = json.loads(output)

            return {
                "disk": disk_number,
                "stage": self.stage,
                "status": "success",
                "data": data,
                "error": None
            }

        except Exception as e:

            return {
                "disk": disk_number,
                "stage": self.stage,
                "status": "error",
                "data": None,
                "error": str(e)
            }
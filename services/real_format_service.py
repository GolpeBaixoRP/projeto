import json
import subprocess
from pathlib import Path

from config.profiles import FILESYSTEM_TO_PROFILE
from domain.format_profile import FormatProfile


class RealFormatterService:
    stage = "format"
    required_ipc_keys = {
        "Success",
        "DriveLetter",
        "FileSystem",
        "PartitionStyle",
        "ExecutionTimeMs",
        "RebuildPerformed",
        "ErrorCode",
        "ErrorMessage",
    }

    def __init__(self):
        self._assets_dir = Path(__file__).resolve().parents[1] / "assets"

    def _resolve_profile(self, filesystem: str) -> FormatProfile:
        normalized = (filesystem or "").strip().upper()
        if normalized not in FILESYSTEM_TO_PROFILE:
            raise ValueError("Filesystem inválido. Use FAT32 ou EXFAT.")
        return FILESYSTEM_TO_PROFILE[normalized]

    def _resolve_worker_path(self, profile: FormatProfile) -> Path:
        worker_path = (self._assets_dir / profile.worker_ps1).resolve()
        if not worker_path.exists():
            raise FileNotFoundError(f"Worker PowerShell não encontrado: {worker_path}")
        return worker_path

    def _parse_ipc(self, output: str) -> dict:
        data = json.loads(output)
        missing = sorted(self.required_ipc_keys.difference(data.keys()))
        if missing:
            raise ValueError(f"IPC JSON inválido: chaves ausentes {missing}")
        return data

    def _error_payload(self, message: str, *, exit_code=None, stderr: str = "") -> dict:
        return {
            "message": message,
            "exit_code": exit_code,
            "stderr": (stderr or "").strip(),
        }

    def format_disk(self, disk, filesystem):
        base_response = {
            "disk": getattr(disk, "number", None),
            "stage": self.stage,
            "status": "error",
            "data": None,
            "error": None,
        }

        try:
            profile = self._resolve_profile(filesystem)
            worker_path = self._resolve_worker_path(profile)

            command = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(worker_path),
                "-DiskNumber",
                str(disk.number),
            ]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=240,
            )

            stdout = (result.stdout or "").strip()
            stderr = (result.stderr or "").strip()

            if result.returncode != 0:
                base_response["error"] = self._error_payload(
                    "PowerShell execution failed",
                    exit_code=result.returncode,
                    stderr=stderr,
                )
                return base_response

            ipc_data = self._parse_ipc(stdout) if stdout else None
            return {
                "disk": disk.number,
                "stage": self.stage,
                "status": "success",
                "data": ipc_data,
                "error": None,
            }
        except subprocess.TimeoutExpired as exc:
            base_response["error"] = self._error_payload(
                "PowerShell IPC timeout",
                exit_code=None,
                stderr=getattr(exc, "stderr", "") or "",
            )
            return base_response
        except Exception as exc:
            base_response["error"] = self._error_payload(str(exc), exit_code=None, stderr="")
            return base_response

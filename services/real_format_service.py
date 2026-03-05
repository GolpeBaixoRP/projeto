import json
from pathlib import Path

from config.profiles import FILESYSTEM_TO_PROFILE
from domain.format_profile import FormatProfile
from utils.powershell_runner import run_powershell


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

    def format_disk(self, disk, filesystem):
        profile = self._resolve_profile(filesystem)
        worker_path = self._resolve_worker_path(profile)

        try:
            raw_output = run_powershell(
                script_path=str(worker_path),
                args=["-DiskNumber", str(disk.number)],
                timeout=240,
            )
            ipc_data = self._parse_ipc(raw_output)
            return {
                "disk": disk.number,
                "stage": self.stage,
                "status": "success",
                "data": ipc_data,
                "error": None,
                "profile": profile.id,
            }
        except Exception as exc:
            return {
                "disk": getattr(disk, "number", None),
                "stage": self.stage,
                "status": "error",
                "data": None,
                "error": str(exc),
                "profile": profile.id,
            }

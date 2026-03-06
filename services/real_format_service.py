import json
import re
from pathlib import Path

from config.profiles import FILESYSTEM_TO_PROFILE
from domain.format_profile import FormatProfile
from models.pipeline_error import PipelineError
from utils.forensic_audit import ForensicAuditTrail
from utils.powershell_runner import run_powershell_capture


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
        self.audit = ForensicAuditTrail()

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

    def _extract_json(self, output: str) -> str:
        text = (output or "").strip()
        if not text:
            raise PipelineError("MS-IPC-001", self.stage, "Worker retornou stdout vazio", {"stdout_tail": ""})
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not m:
            raise PipelineError("MS-IPC-002", self.stage, "JSON não encontrado no stdout do worker", {"stdout_tail": text[-500:]})
        return m.group(0)

    def _parse_ipc(self, output: str) -> dict:
        json_payload = self._extract_json(output)
        try:
            data = json.loads(json_payload)
        except Exception as exc:
            raise PipelineError("MS-IPC-003", self.stage, "JSON inválido retornado pelo worker", {"stdout_tail": (output or "")[-500:]}) from exc

        if not isinstance(data, dict):
            raise PipelineError("MS-IPC-006", self.stage, "Schema IPC inesperado", {"found_type": type(data).__name__})

        missing = sorted(self.required_ipc_keys.difference(data.keys()))
        if missing:
            raise PipelineError("MS-IPC-004", self.stage, "Campos obrigatórios ausentes no IPC", {"missing": missing})
        return data

    def format_disk(self, disk, filesystem):
        profile = self._resolve_profile(filesystem)
        worker_path = self._resolve_worker_path(profile)
        args = [
            "-DiskNumber", str(disk.number),
            "-UniqueId", str(getattr(disk, "unique_id", "") or ""),
            "-SerialNumber", str(getattr(disk, "serial_number", "") or ""),
            "-SizeBytes", str(getattr(disk, "size", "") or ""),
            "-FriendlyName", str(getattr(disk, "friendly_name", "") or ""),
            "-BusType", str(getattr(disk, "bus_type", "") or ""),
            "-LocationPath", str(getattr(disk, "location_path", "") or ""),
        ]
        operation_id = f"fmt-ipc-{int(disk.number)}"
        self.audit.record("IPC_START", {"script": str(worker_path), "args": args, "disk": int(disk.number), "operation_id": operation_id})
        result = run_powershell_capture(script_path=str(worker_path), args=args, timeout=240, operation_id=operation_id)
        self.audit.record("IPC_END", {
            "script": str(worker_path),
            "exit_code": result.exit_code,
            "duration_ms": result.duration_ms,
            "stdout_tail": result.stdout[-500:],
            "stderr_tail": result.stderr[-500:],
            "operation_id": operation_id,
        })

        if result.exit_code != 0:
            raise PipelineError(
                "MS-RUN-003",
                self.stage,
                "Processo PowerShell finalizou com erro",
                {"exit_code": result.exit_code, "stderr_tail": result.stderr[-500:], "stdout_tail": result.stdout[-500:]},
            )

        ipc_data = self._parse_ipc(result.stdout)
        if not ipc_data.get("Success", False):
            raise PipelineError(
                ipc_data.get("PipelineErrorCode") or "MS-IPC-005",
                self.stage,
                ipc_data.get("ErrorMessage") or "Worker reportou falha",
                {"ipc": ipc_data},
            )

        return {
            "disk": disk.number,
            "stage": self.stage,
            "status": "success",
            "data": ipc_data,
            "error": None,
        }

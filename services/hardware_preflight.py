import platform
import shutil
import json

from utils.logger import setup_logger
from utils.powershell_runner import run_powershell

logger = setup_logger()


class HardwarePreflight:
    """Valida se o ambiente está apto para operações físicas de disco."""

    @staticmethod
    def ensure_ready() -> None:
        if platform.system() != "Windows":
            raise EnvironmentError(
                "Este pipeline de hardware real requer Windows (PowerShell + Get-Disk)."
            )

        if not (shutil.which("powershell") or shutil.which("pwsh")):
            raise EnvironmentError(
                "PowerShell não encontrado. Instale o PowerShell para operar em hardware real."
            )

        admin_probe = """
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
@{ Output = $isAdmin; Success = $true } | ConvertTo-Json
"""

        result = run_powershell(admin_probe, elevated=False)
        payload = json.loads(result)

        if not payload.get("Output", False):
            raise PermissionError(
                "Permissões insuficientes. Execute o aplicativo como Administrador para operar disco físico."
            )

        logger.info("Preflight de hardware real aprovado.")

from pathlib import Path
import subprocess
import json
import time

from utils.powershell_runner import run_powershell
from utils.logger import setup_logger

logger = setup_logger()


# ============================================================
# Media Stabilization Barrier
# ============================================================

def wait_media_stabilization(seconds=2.0):
    time.sleep(seconds)


# ============================================================
# Execução segura IPC JSON
# ============================================================

def safe_run_json(command, elevated=True, timeout=30):
    start = time.time()

    while True:
        output = run_powershell(command, elevated=elevated)

        if output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                pass

        if time.time() - start > timeout:
            raise TimeoutError("Runner IPC timeout")

        time.sleep(0.3)


# ============================================================
# Real Deterministic Format Service
# ============================================================

class RealFormatterService:

    def format_disk(self, disk, filesystem):

        filesystem = filesystem.upper()

        logger.info(
            f"Pipeline REAL FORMAT iniciado | Disk {disk.number} | FS={filesystem}"
        )

        base_dir = Path(__file__).resolve().parents[1]
        assets_dir = base_dir / "assets"

        fat32_exe = assets_dir / "fat32format.exe"

        # ====================================================
        # Preparation Phase
        # ====================================================

        prepare_command = f"""
$ErrorActionPreference = "Stop"

$diskNumber = {disk.number}
$disk = Get-Disk -Number $diskNumber

if ($disk.IsOffline) {{
    Set-Disk -Number $diskNumber -IsOffline $false
}}

if ($disk.IsReadOnly) {{
    Set-Disk -Number $diskNumber -IsReadOnly $false
}}

if ($disk.PartitionStyle -eq "RAW") {{
    Initialize-Disk -Number $diskNumber -PartitionStyle MBR
}}

Get-Partition -DiskNumber $diskNumber -ErrorAction SilentlyContinue |
Remove-Partition -Confirm:$false -ErrorAction SilentlyContinue
"""

        run_powershell(prepare_command, elevated=True)

        # ====================================================
        # Partition Creation
        # ====================================================

        partition_command = f"""
$partition = New-Partition `
    -DiskNumber {disk.number} `
    -UseMaximumSize `
    -AssignDriveLetter

$letter = ($partition | Get-Volume).DriveLetter

$output = @{{
    Output = $letter
    Success = $true
}}

$output | ConvertTo-Json
"""

        partition_data = safe_run_json(partition_command, elevated=True)

        drive_letter = partition_data.get("Output", "").strip()

        if not drive_letter:
            raise RuntimeError("Falha ao obter letra da unidade.")

        logger.info(f"Unidade atribuída: {drive_letter}:")

        # ====================================================
        # Storage Stabilization Barrier
        # ====================================================

        wait_media_stabilization(2.0)

        # ====================================================
        # Disk Size Probe
        # ====================================================

        size_command = f"""
$disk = Get-Disk -Number {disk.number}
$sizeGB = [math]::Round($disk.Size / 1GB, 2)

$output = @{{
    Output = $sizeGB
    Success = $true
}}

$output | ConvertTo-Json
"""

        size_data = safe_run_json(size_command)
        disk_size_gb = float(size_data.get("Output", 0))

        # ====================================================
        # FORMATTING PHASE
        # ====================================================

        # ---------- FAT32 ----------
        if filesystem == "FAT32":

            logger.info("Delegando preparação FAT32 | run_powershell.ps1")

            wait_media_stabilization(1.5)

            if disk_size_gb <= 32:

                format_command = f"""
Format-Volume `
    -DriveLetter {drive_letter} `
    -FileSystem FAT32 `
    -Confirm:$false -Force
"""

                run_powershell(format_command, elevated=True)

            else:

                if not fat32_exe.exists():
                    raise FileNotFoundError("fat32format.exe não encontrado.")

                logger.info("Usando formatador externo FAT32")

                subprocess.run(
                    [str(fat32_exe), f"{drive_letter}:"],
                    input="Y\n",
                    text=True,
                    check=True
                )

        # ---------- EXFAT ----------
        elif filesystem == "EXFAT":

            logger.info("Delegando pipeline EXFAT | xfat_process.ps1")

            wait_media_stabilization(1.5)

            script_path = assets_dir / "xfat_process.ps1"

            if not script_path.exists():
                raise FileNotFoundError("xfat_process.ps1 não encontrado em assets")

            run_powershell(
                f'-File "{script_path}" -DiskNumber {disk.number} -DriveLetter {drive_letter}',
                elevated=True
            )

        else:
            raise ValueError("Filesystem inválido. Use FAT32 ou EXFAT.")

        # ====================================================
        # Final Cache Barrier
        # ====================================================

        run_powershell("Update-HostStorageCache", elevated=True)
        time.sleep(2)

        # ====================================================
        # Final Snapshot Verification
        # ====================================================

        final_probe_command = f"""
$disk = Get-Disk -Number {disk.number}
$volume = Get-Volume -DriveLetter {drive_letter}

$output = @{{
    DriveLetter = $volume.DriveLetter
    FileSystem = $volume.FileSystem
    PartitionStyle = $disk.PartitionStyle
    Operational = $true
}}

$output | ConvertTo-Json
"""

        final_state = safe_run_json(final_probe_command)

        logger.info("Pipeline formatador executado com sucesso")

        return {
            "DiskNumber": disk.number,
            "DriveLetter": drive_letter,
            "Filesystem": filesystem,
            "Status": "COMPLETED",
            "Snapshot": final_state
        }
import subprocess
import tempfile
import shutil


def _resolve_powershell_binary():
    return shutil.which("powershell") or shutil.which("pwsh") or "powershell"

def run_powershell(command, elevated=True, timeout=60):

    # Remove BOM e limpa comando
    command = command.strip()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ps1", mode="w", encoding="utf-8") as f:
        f.write(command)
        script_path = f.name

    runner = [
        _resolve_powershell_binary(),
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", script_path
    ]

    proc = subprocess.run(
        runner,
        capture_output=True,
        text=True,
        timeout=timeout
    )

    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip())

    return proc.stdout.strip()

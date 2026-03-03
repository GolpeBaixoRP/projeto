import subprocess
import tempfile

def run_powershell(command, elevated=True, timeout=60):

    # Remove BOM e limpa comando
    command = command.strip()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ps1", mode="w", encoding="utf-8") as f:
        f.write(command)
        script_path = f.name

    if elevated:
        runner = [
            "powershell",
            "-ExecutionPolicy", "Bypass",
            "-File", script_path
        ]
    else:
        runner = [
            "powershell",
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
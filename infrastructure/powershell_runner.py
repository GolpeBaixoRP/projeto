import subprocess
import json
import shutil


class PowerShellRunner:

    @staticmethod
    def run(script: str) -> dict:
        shell = shutil.which("powershell") or shutil.which("pwsh") or "powershell"

        process = subprocess.run(
            [shell, "-NoProfile", "-Command", script],
            capture_output=True,
            text=True
        )

        if process.returncode != 0:
            raise RuntimeError(process.stderr)

        return json.loads(process.stdout)

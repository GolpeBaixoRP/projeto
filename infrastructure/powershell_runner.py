
import subprocess
import json

class PowerShellRunner:

    @staticmethod
    def run(script: str) -> dict:
        process = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True
        )

        if process.returncode != 0:
            raise RuntimeError(process.stderr)

        return json.loads(process.stdout)

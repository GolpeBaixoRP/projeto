import subprocess
import tempfile
import os


def run_powershell(command, elevated=True, timeout=60):

    command = command.strip()

    script_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".ps1",
            mode="w",
            encoding="utf-8"
        ) as f:
            f.write(command)
            script_path = f.name

        runner = [
            "powershell",
            "-ExecutionPolicy", "Bypass",
            "-File", script_path
        ]

        proc = subprocess.Popen(
            runner,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            stdout, stderr = proc.communicate(timeout=timeout)

            if proc.returncode != 0:
                raise RuntimeError(stderr.strip())

            return stdout.strip()

        except subprocess.TimeoutExpired:
            proc.kill()
            raise TimeoutError("PowerShell IPC timeout")

    finally:
        if script_path and os.path.exists(script_path):
            try:
                os.remove(script_path)
            except Exception:
                pass
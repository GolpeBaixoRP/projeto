import subprocess
import tempfile
import os


def execute_elevated_ps(command):

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".ps1",
        mode="w",
        encoding="utf-8-sig"
    ) as f:

        f.write(command)
        script_path = f.name

    try:

        runner = [
            "powershell",
            "-ExecutionPolicy", "Bypass",
            "-File", script_path
        ]

        # ⚠ Importante: NÃO usar Verb RunAs aqui
        # Elevação deve ser configurada no launcher do programa

        proc = subprocess.run(
            runner,
            capture_output=True,
            text=True
        )

        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip())

        return proc.stdout.strip()

    finally:
        try:
            os.remove(script_path)
        except:
            pass
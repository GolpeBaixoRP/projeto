import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def run_powershell(
    command: Optional[str] = None,
    *,
    script_path: Optional[str] = None,
    args: Optional[list[str]] = None,
    elevated: bool = True,
    timeout: int = 60,
) -> str:
    """Executa PowerShell de forma determinística.

    Modo principal: executar arquivo .ps1 via script_path.
    Modo compatibilidade: executar conteúdo inline via command.
    """
    del elevated  # Mantido por compatibilidade de assinatura

    if not command and not script_path:
        raise ValueError("Forneça command ou script_path")

    temp_script: Optional[str] = None

    try:
        if script_path:
            ps1_path = Path(script_path).resolve()
            if not ps1_path.exists():
                raise FileNotFoundError(f"Script PowerShell não encontrado: {ps1_path}")
            target_script = str(ps1_path)
        else:
            content = (command or "").strip()
            if not content:
                raise ValueError("Comando PowerShell vazio")
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".ps1",
                mode="w",
                encoding="utf-8",
            ) as handler:
                handler.write(content)
                temp_script = handler.name
            target_script = temp_script

        runner = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            target_script,
        ]

        if args:
            runner.extend(args)

        proc = subprocess.Popen(
            runner,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            proc.kill()
            raise TimeoutError("PowerShell IPC timeout") from exc

        if proc.returncode != 0:
            error = (stderr or "").strip() or "PowerShell execution failed"
            raise RuntimeError(error)

        return (stdout or "").strip()

    finally:
        if temp_script and os.path.exists(temp_script):
            try:
                os.remove(temp_script)
            except OSError:
                pass

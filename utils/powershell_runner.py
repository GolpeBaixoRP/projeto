import os
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from models.pipeline_error import PipelineError


@dataclass
class RunResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int


def _build_runner(target_script: str, args: Optional[list[str]] = None) -> list[str]:
    runner = [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-WindowStyle",
        "Hidden",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        target_script,
    ]
    if args:
        runner.extend(args)
    return runner


def run_powershell_capture(
    command: Optional[str] = None,
    *,
    script_path: Optional[str] = None,
    args: Optional[list[str]] = None,
    elevated: bool = True,
    timeout: int = 60,
) -> RunResult:
    del elevated
    if not command and not script_path:
        raise ValueError("Forneça command ou script_path")

    temp_script: Optional[str] = None
    start = time.perf_counter()
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
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ps1", mode="w", encoding="utf-8") as h:
                h.write(content)
                temp_script = h.name
            target_script = temp_script

        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        proc = subprocess.Popen(
            _build_runner(target_script, args),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creationflags,
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            proc.kill()
            raise PipelineError(
                code="MS-RUN-002",
                stage="runner",
                message="PowerShell IPC timeout",
                details={"timeout": timeout},
            ) from exc

        return RunResult(
            exit_code=int(proc.returncode or 0),
            stdout=(stdout or "").strip(),
            stderr=(stderr or "").strip(),
            duration_ms=int((time.perf_counter() - start) * 1000),
        )
    finally:
        if temp_script and os.path.exists(temp_script):
            try:
                os.remove(temp_script)
            except OSError:
                pass


def run_powershell(
    command: Optional[str] = None,
    *,
    script_path: Optional[str] = None,
    args: Optional[list[str]] = None,
    elevated: bool = True,
    timeout: int = 60,
) -> str:
    result = run_powershell_capture(
        command=command,
        script_path=script_path,
        args=args,
        elevated=elevated,
        timeout=timeout,
    )
    if result.exit_code != 0:
        raise RuntimeError(result.stderr or "PowerShell execution failed")
    return result.stdout

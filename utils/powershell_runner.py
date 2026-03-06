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



def _kill_process_tree(proc: subprocess.Popen) -> None:
    """Best-effort kill of a process and its children (important for storage cmdlets that hang).
    On Windows uses taskkill /T to kill the full tree.
    """
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                capture_output=True,
                text=True,
            )
        else:
            proc.terminate()
    except Exception:
        pass
    finally:
        try:
            proc.kill()
        except Exception:
            pass

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


def _tail(text: Optional[str], size: int = 500) -> str:
    return (text or "")[-size:]


def run_powershell_capture(
    command: Optional[str] = None,
    *,
    script_path: Optional[str] = None,
    args: Optional[list[str]] = None,
    elevated: bool = True,
    timeout: int = 60,
    operation_id: Optional[str] = None,
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
        runner_args = _build_runner(target_script, args)
        try:
            proc = subprocess.Popen(
                runner_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creationflags,
            )
        except OSError as exc:
            raise PipelineError(
                code="MS-RUN-001",
                stage="runner",
                message="Falha ao iniciar processo PowerShell",
                details={
                    "substep": "spawn",
                    "script_path": target_script,
                    "args": args or [],
                    "runner_args": runner_args,
                    "timeout": timeout,
                    "operation_id": operation_id,
                    "error": str(exc),
                },
            ) from exc
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except KeyboardInterrupt:
            _kill_process_tree(proc)
            raise
        except subprocess.TimeoutExpired as exc:
            _kill_process_tree(proc)
            raise PipelineError(
                code="MS-RUN-002",
                stage="runner",
                message="PowerShell IPC timeout",
                details={
                    "substep": "communicate",
                    "timeout": timeout,
                    "pid": proc.pid,
                    "script_path": target_script,
                    "args": args or [],
                    "operation_id": operation_id,
                },
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
    operation_id: Optional[str] = None,
) -> str:
    result = run_powershell_capture(
        command=command,
        script_path=script_path,
        args=args,
        elevated=elevated,
        timeout=timeout,
        operation_id=operation_id,
    )
    if result.exit_code != 0:
        raise PipelineError(
            code="MS-RUN-003",
            stage="runner",
            message="Processo PowerShell retornou erro",
            details={
                "substep": "exit_code",
                "exit_code": result.exit_code,
                "timeout": timeout,
                "operation_id": operation_id,
                "stdout_tail": _tail(result.stdout),
                "stderr_tail": _tail(result.stderr),
                "duration_ms": result.duration_ms,
            },
        )
    return result.stdout

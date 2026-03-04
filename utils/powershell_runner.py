import os
import subprocess
import tempfile
import shutil

try:
    import win32con
    import win32event
    import win32process
    from win32com.shell.shell import ShellExecuteEx
    from win32com.shell import shellcon
except ImportError:  # pragma: no cover - dependência apenas no Windows com pywin32
    win32con = None
    win32event = None
    win32process = None
    ShellExecuteEx = None
    shellcon = None


def _resolve_powershell_binary():
    return shutil.which("powershell") or shutil.which("pwsh") or "powershell"


def _run_elevated(script_path, timeout):
    if os.name != "nt" or not ShellExecuteEx:
        raise RuntimeError(
            "Execução elevada requer Windows com pywin32 instalado (win32com/win32process)."
        )

    shell = _resolve_powershell_binary()
    proc_info = ShellExecuteEx(
        nShow=win32con.SW_HIDE,
        fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
        lpVerb="runas",
        lpFile=shell,
        lpParameters=f'-NoProfile -ExecutionPolicy Bypass -File "{script_path}"',
    )

    handle = proc_info["hProcess"]
    wait_result = win32event.WaitForSingleObject(handle, int(timeout * 1000))

    if wait_result == win32event.WAIT_TIMEOUT:
        raise TimeoutError(f"PowerShell elevado excedeu timeout de {timeout}s")

    exit_code = win32process.GetExitCodeProcess(handle)
    if exit_code != 0:
        raise RuntimeError(f"PowerShell elevado falhou com exit code {exit_code}")

    return ""


def run_powershell(command, elevated=True, timeout=60):
    command = command.strip()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ps1", mode="w", encoding="utf-8") as f:
        f.write(command)
        script_path = f.name

    try:
        if elevated:
            return _run_elevated(script_path=script_path, timeout=timeout)

        runner = [
            _resolve_powershell_binary(),
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", script_path,
        ]

        proc = subprocess.run(
            runner,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip())

        return proc.stdout.strip()
    finally:
        try:
            os.remove(script_path)
        except OSError:
            pass

import subprocess
import uuid
import json
import time
from utils.worker_lock import acquire_worker_lock, release_worker_lock

PIPE_PREFIX = r"\\.\pipe\ultra_storage_worker_"


def run_ultra_powershell(command: str, elevated: bool = False, timeout: int = 90):

    if not acquire_worker_lock():
        raise RuntimeError("Outro worker está executando operação crítica.")

    session = uuid.uuid4().hex
    pipe_name = PIPE_PREFIX + session
    handshake = uuid.uuid4().hex

    worker_ps = f"""
    $pipeName = '{pipe_name}'
    $handshake = '{handshake}'

    $server = New-Object System.IO.Pipes.NamedPipeServerStream(
        $pipeName,
        'InOut',
        1
    )

    $server.WaitForConnection()

    $reader = New-Object System.IO.StreamReader($server)
    $writer = New-Object System.IO.StreamWriter($server)
    $writer.AutoFlush = $true

    try {{

        $payload = $reader.ReadLine() | ConvertFrom-Json

        if ($payload.handshake -ne '{handshake}') {{
            throw "Handshake inválido"
        }}

        $output = powershell -ExecutionPolicy Bypass -Command "{command}" 2>&1 | Out-String

        $response = @{{
            success = $true
            output = $output.Trim()
            checksum = (Get-Date).Ticks
        }} | ConvertTo-Json -Compress

        $writer.WriteLine($response)

    }} catch {{

        $err = @{{
            success = $false
            output = $_.ToString()
        }} | ConvertTo-Json -Compress

        $writer.WriteLine($err)

    }} finally {{
        $writer.Close()
        $server.Close()
    }}
    """

    subprocess.Popen(
        ["powershell", "-ExecutionPolicy", "Bypass", "-Command", worker_ps],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(0.5)

    client_payload = json.dumps({
        "handshake": handshake
    }).replace('"', '\\"')

    client_ps = f"""
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(
        '.',
        '{pipe_name}',
        'InOut'
    )

    $pipe.Connect({timeout * 1000})

    $reader = New-Object System.IO.StreamReader($pipe)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true

    $writer.WriteLine('{client_payload}')

    $response = $reader.ReadLine()

    Write-Output $response

    $writer.Close()
    $pipe.Close()
    """

    runner = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        client_ps
    ]

    if elevated:
        runner = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"Start-Process powershell -Verb RunAs -ArgumentList \"-ExecutionPolicy Bypass -Command \\\"{client_ps}\\\"\""
        ]

    try:
        proc = subprocess.run(
            runner,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout
        )

        if not proc.stdout:
            raise RuntimeError("Worker engine falhou")

        data = json.loads(proc.stdout.strip())

        if not data.get("success"):
            raise RuntimeError(data.get("output"))

        return data.get("output", "")

    finally:
        release_worker_lock()
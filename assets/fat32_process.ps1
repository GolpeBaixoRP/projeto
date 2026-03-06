param(
    [Parameter(Mandatory=$true)]
    [int]$DiskNumber,

    [string]$UniqueId = "",
    [string]$SerialNumber = "",
    [long]$SizeBytes = 0,
    [string]$FriendlyName = "",
    [string]$BusType = "",
    [string]$LocationPath = ""
)

$ErrorActionPreference = "Stop"

function Normalize-String {
    param([object]$Value)
    if ($null -eq $Value) { return "" }
    return [string]$Value
}

function New-Result {
    param(
        [bool]$Success,
        [string]$DriveLetter,
        [string]$FileSystem,
        [string]$PartitionStyle,
        [bool]$RebuildPerformed,
        [int]$ErrorCode,
        [string]$ErrorMessage,
        [string]$PipelineErrorCode,
        [int]$ExecutionTimeMs,
        [int]$BlockSize = 0,
        [string]$Step = $null,
        [string]$Expected = $null,
        [string]$Found = $null
    )

    return @{
        Success = $Success
        DriveLetter = $DriveLetter
        FileSystem = $FileSystem
        PartitionStyle = $PartitionStyle
        RebuildPerformed = $RebuildPerformed
        ErrorCode = $ErrorCode
        ErrorMessage = $ErrorMessage
        PipelineErrorCode = $PipelineErrorCode
        ExecutionTimeMs = $ExecutionTimeMs
        BlockSize = $BlockSize
        Step = $Step
        Expected = $Expected
        Found = $Found
    } | ConvertTo-Json -Compress -Depth 5
}

function Disable-AutoPlayTemporarily {
    $state = @{
        HadExplorer = $false
        OldValue = $null
    }

    try {
        $regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
        if (Test-Path $regPath) {
            $state.HadExplorer = $true
            try {
                $state.OldValue = (Get-ItemProperty -Path $regPath -Name NoDriveTypeAutoRun -ErrorAction Stop).NoDriveTypeAutoRun
            } catch {
                $state.OldValue = $null
            }
        } else {
            New-Item -Path $regPath -Force | Out-Null
            $state.HadExplorer = $false
        }

        Set-ItemProperty -Path $regPath -Name NoDriveTypeAutoRun -Type DWord -Value 255
    } catch {}

    return $state
}

function Restore-AutoPlay {
    param([hashtable]$State)

    try {
        $regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
        if ($null -eq $State) { return }

        if ($State.HadExplorer) {
            if ($null -ne $State.OldValue) {
                Set-ItemProperty -Path $regPath -Name NoDriveTypeAutoRun -Type DWord -Value $State.OldValue
            } else {
                Remove-ItemProperty -Path $regPath -Name NoDriveTypeAutoRun -ErrorAction SilentlyContinue
            }
        } else {
            Remove-ItemProperty -Path $regPath -Name NoDriveTypeAutoRun -ErrorAction SilentlyContinue
        }
    } catch {}
}

function Get-DiskCandidates {
    $all = Get-Disk | ForEach-Object {
        [PSCustomObject]@{
            Number = $_.Number
            FriendlyName = Normalize-String $_.FriendlyName
            SerialNumber = Normalize-String $_.SerialNumber
            UniqueId = Normalize-String $_.UniqueId
            LocationPath = Normalize-String $_.LocationPath
            BusType = Normalize-String $_.BusType
            IsRemovable = [bool]$_.IsRemovable
            Size = [long]$_.Size
        }
    }
    return $all
}

function Resolve-Disk {
    param([int]$Preferred)

    try {
        $direct = Get-Disk -Number $Preferred -ErrorAction Stop
        if ($null -ne $direct) { return $Preferred }
    } catch {}

    $candidates = Get-DiskCandidates
    if ($null -eq $candidates -or $candidates.Count -eq 0) { return $null }

    $best = $null
    $bestScore = -1

    foreach ($c in $candidates) {
        $score = 0
        if ($UniqueId -and $c.UniqueId -and $UniqueId -eq $c.UniqueId) { $score += 100 }
        if ($SerialNumber -and $c.SerialNumber -and $SerialNumber -eq $c.SerialNumber) { $score += 80 }
        if ($LocationPath -and $c.LocationPath -and $LocationPath -eq $c.LocationPath) { $score += 60 }
        if ($FriendlyName -and $c.FriendlyName -and $FriendlyName -eq $c.FriendlyName) { $score += 10 }
        if ($SizeBytes -gt 0 -and $c.Size -eq $SizeBytes) { $score += 10 }

        if ($score -gt $bestScore) {
            $bestScore = $score
            $best = $c
        }
    }

    if ($null -ne $best -and $bestScore -ge 10) {
        return [int]$best.Number
    }

    return $null
}

function Invoke-DiskPartScript {
    param([string[]]$Lines)

    $tmp = [System.IO.Path]::GetTempFileName()
    try {
        [System.IO.File]::WriteAllLines($tmp, $Lines)

        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = "diskpart.exe"
        $psi.Arguments = "/s `"$tmp`""
        $psi.CreateNoWindow = $true
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true

        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = $psi
        [void]$p.Start()
        $stdout = $p.StandardOutput.ReadToEnd()
        $stderr = $p.StandardError.ReadToEnd()
        $p.WaitForExit()

        return @{
            ExitCode = $p.ExitCode
            StdOut = $stdout
            StdErr = $stderr
        }
    }
    finally {
        Remove-Item $tmp -Force -ErrorAction SilentlyContinue
    }
}

function Release-DiskAccess {
    param([int]$DiskNumberToRelease)

    try {
        $parts = Get-Partition -DiskNumber $DiskNumberToRelease -ErrorAction SilentlyContinue
        foreach ($part in $parts) {
            if ($part.DriveLetter) {
                $path = "$($part.DriveLetter):"
                try { mountvol $path /D | Out-Null } catch {}
                try {
                    Remove-PartitionAccessPath -DiskNumber $DiskNumberToRelease -PartitionNumber $part.PartitionNumber -AccessPath $path -ErrorAction SilentlyContinue
                } catch {}
            }
        }
    } catch {}

    try { Update-HostStorageCache } catch {}
    Start-Sleep -Milliseconds 1200
}

function Invoke-DiskPartRebuild {
    param([int]$ResolvedDisk)

    $last = $null

    for ($attempt = 1; $attempt -le 3; $attempt++) {
        Release-DiskAccess -DiskNumberToRelease $ResolvedDisk

        $result = Invoke-DiskPartScript -Lines @(
            "automount enable"
            "rescan"
            "select disk $ResolvedDisk"
            "attributes disk clear readonly"
            "clean"
            "convert mbr"
            "create partition primary"
            "assign"
            "exit"
        )

        $last = $result

        if ($result.ExitCode -eq 0) {
            return $result
        }

        $combined = "$($result.StdOut)`n$($result.StdErr)"
        if ($combined -match "Acesso negado" -or $combined -match "Access is denied") {
            Start-Sleep -Seconds 2
            continue
        }

        return $result
    }

    return $last
}

function Ensure-DriveLetter {
    param(
        [Microsoft.Management.Infrastructure.CimInstance]$Partition,
        [int]$DiskNumberToQuery
    )

    if ($null -eq $Partition) { return $null }
    if ($Partition.DriveLetter) { return $Partition.DriveLetter }

    $used = @()
    try {
        $used = (Get-Volume -ErrorAction SilentlyContinue |
            Where-Object { $_.DriveLetter } |
            Select-Object -ExpandProperty DriveLetter)
    } catch {}

    $preferredLetters = @("P","Q","R","S","T","U","V","W","X","Y","Z","M","N","O","L","K","J","I","H","G","F","E","D")

    foreach ($letter in $preferredLetters) {
        if ($used -notcontains $letter) {
            try {
                Add-PartitionAccessPath -DiskNumber $DiskNumberToQuery -PartitionNumber $Partition.PartitionNumber -AccessPath "$letter`:" -ErrorAction Stop
                Start-Sleep -Milliseconds 800
                return $letter
            } catch {}
        }
    }

    return $null
}

function Wait-PartitionAndLetter {
    param(
        [int]$DiskNumber,
        [int]$Retries = 25,
        [int]$DelayMs = 800
    )

    for ($i=1; $i -le $Retries; $i++) {
        Update-HostStorageCache
        Start-Sleep -Milliseconds $DelayMs

        $resolved = Resolve-Disk -Preferred $DiskNumber
        if ($null -eq $resolved) { continue }

        $part = Get-Partition -DiskNumber $resolved -ErrorAction SilentlyContinue |
            Where-Object { $_.PartitionNumber -ge 1 } |
            Sort-Object PartitionNumber |
            Select-Object -First 1

        if ($null -eq $part) { continue }

        $letter = $part.DriveLetter
        if ([string]::IsNullOrWhiteSpace($letter)) {
            $letter = Ensure-DriveLetter -Partition $part -DiskNumberToQuery $resolved
        }

        if (-not [string]::IsNullOrWhiteSpace($letter)) {
            return @{
                DiskNumber = $resolved
                PartitionNumber = $part.PartitionNumber
                DriveLetter = $letter
            }
        }
    }

    return $null
}

function Start-Fat32Format {
    param(
        [Parameter(Mandatory=$true)][string]$FormatterPath,
        [Parameter(Mandatory=$true)][string]$DriveLetter,
        [int]$TimeoutMs = 240000
    )

    $cmdLine = "echo y|`"$FormatterPath`" -c64 $DriveLetter`:"
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "cmd.exe"
    $psi.Arguments = "/c $cmdLine"
    $psi.CreateNoWindow = $true
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true

    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi
    [void]$p.Start()

    $exited = $p.WaitForExit($TimeoutMs)
    if (-not $exited) {
        try { $p.Kill($true) } catch { try { $p.Kill() } catch {} }
        return @{
            TimedOut = $true
            ExitCode = -1
            StdOut = ""
            StdErr = "Timeout after ${TimeoutMs}ms"
        }
    }

    return @{
        TimedOut = $false
        ExitCode = $p.ExitCode
        StdOut = $p.StandardOutput.ReadToEnd()
        StdErr = $p.StandardError.ReadToEnd()
    }
}

function Get-VolumeEvidence {
    param([string]$DriveLetter)

    $vol = Get-CimInstance Win32_Volume -ErrorAction SilentlyContinue |
        Where-Object { $_.DriveLetter -eq "$DriveLetter`:" } |
        Select-Object -First 1

    if ($null -eq $vol) { return $null }

    return @{
        DriveLetter = $DriveLetter
        FileSystem = Normalize-String $vol.FileSystem
        BlockSize = if ($vol.BlockSize) { [int]$vol.BlockSize } else { 0 }
        Capacity = if ($vol.Capacity) { [int64]$vol.Capacity } else { 0 }
    }
}

$startedAt = Get-Date
$autoPlayState = Disable-AutoPlayTemporarily

try {
    $resolved = Resolve-Disk -Preferred $DiskNumber
    if ($null -eq $resolved) {
        Write-Output (New-Result $false $null $null $null $false 10 "Disk not found or not reacquired" "MS-USB-003" 0)
        return
    }

    try { Set-Disk -Number $resolved -IsOffline $false -ErrorAction SilentlyContinue } catch {}
    try { Set-Disk -Number $resolved -IsReadOnly $false -ErrorAction SilentlyContinue } catch {}

    $diskpartResult = Invoke-DiskPartRebuild -ResolvedDisk $resolved

    if ($diskpartResult.ExitCode -ne 0) {
        $msg = "DiskPart failed."
        if ($diskpartResult.StdErr) { $msg += " STDERR: $($diskpartResult.StdErr.Trim())" }
        elseif ($diskpartResult.StdOut) { $msg += " STDOUT: $($diskpartResult.StdOut.Trim())" }

        Write-Output (New-Result $false $null $null $null $false 31 $msg "MS-DSK-003" 0)
        return
    }

    $ready = Wait-PartitionAndLetter -DiskNumber $resolved -Retries 25 -DelayMs 800
    if ($null -eq $ready) {
        Write-Output (New-Result $false $null $null $null $false 33 "Partition/DriveLetter not found after rebuild" "MS-DSK-006" 0)
        return
    }

    $resolved = [int]$ready.DiskNumber
    $driveLetter = [string]$ready.DriveLetter

    $formatter = Join-Path $PSScriptRoot "fat32format.exe"
    if (!(Test-Path $formatter)) {
        Write-Output (New-Result $false $null $null $null $false 40 "FAT32 formatter not found" "MS-FMT-001" 0)
        return
    }

    $run = Start-Fat32Format -FormatterPath $formatter -DriveLetter $driveLetter -TimeoutMs 240000

    if ($run.TimedOut) {
        Write-Output (New-Result $false $driveLetter "FAT32" "MBR" $true 41 "FAT32 formatter timeout" "MS-RUN-002" 0)
        return
    }

    if ($run.ExitCode -ne 0) {
        $msg = "FAT32 formatter execution failed."
        if ($run.StdErr) { $msg += " STDERR: $($run.StdErr.Trim())" }
        elseif ($run.StdOut) { $msg += " STDOUT: $($run.StdOut.Trim())" }

        Write-Output (New-Result $false $driveLetter "FAT32" "MBR" $true 41 $msg "MS-FMT-001" 0)
        return
    }

    Update-HostStorageCache
    Start-Sleep -Seconds 2

    $evidence = Get-VolumeEvidence -DriveLetter $driveLetter
    if ($null -eq $evidence) {
        Write-Output (New-Result $false $driveLetter "FAT32" "MBR" $true 42 "Volume evidence not found after FAT32 format" "MS-VFY-002" 0)
        return
    }

    $elapsed = [int]((Get-Date) - $startedAt).TotalMilliseconds
    Write-Output (New-Result $true $driveLetter "FAT32" "MBR" $true 0 "" "" $elapsed $evidence.BlockSize)
}
catch {
    $elapsed = [int]((Get-Date) - $startedAt).TotalMilliseconds
    $message = $_.Exception.Message
    Write-Output (New-Result $false $null $null $null $false 99 $message "MS-DSK-003" $elapsed)
}
finally {
    Restore-AutoPlay -State $autoPlayState
}
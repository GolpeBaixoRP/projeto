param(
    [Parameter(Mandatory=$true)]
    [int]$DiskNumber
)

$ErrorActionPreference = "Stop"
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

# =====================================================
# ERROR CODES
# =====================================================
# 0  = Success
# 10 = Disk 0 protected
# 11 = System/Boot disk protected
# 20 = Disk state transition timeout
# 21 = Volume stabilization timeout
# 30 = Drive letter allocation failure
# 40 = FAT32 formatter not found
# 41 = FAT32 formatter execution failure
# 99 = Unhandled exception
# =====================================================

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

# -----------------------------------------------------
# Helpers
# -----------------------------------------------------

function Normalize-String {
    param([string]$Value)

    if ($null -eq $Value) { return $null }

    $trimmed = $Value.Trim()
    if ($trimmed -eq "") { return $null }

    return $trimmed
}

function Normalize-DriveLetter {
    param([object]$Value)

    if ($null -eq $Value) { return $null }

    $s = Normalize-String ([string]$Value)

    if ($null -eq $s) { return $null }

    if ($s.Length -ge 2 -and $s[1] -eq ":") { $s = $s.Substring(0,1) }

    if ($s.Length -gt 1) { $s = $s.Substring(0,1) }

    if ($s -notmatch "^[A-Za-z]$") { return $null }

    return $s.ToUpper()
}

function New-Result {

    param(
        [bool]$Success,
        [string]$DriveLetter,
        [string]$FileSystem,
        [string]$PartitionStyle,
        [bool]$RebuildPerformed,
        [int]$ErrorCode,
        [string]$ErrorMessage
    )

    $stopwatch.Stop()

    @{
        Success          = $Success
        DriveLetter      = Normalize-String $DriveLetter
        FileSystem       = Normalize-String $FileSystem
        PartitionStyle   = Normalize-String $PartitionStyle
        ExecutionTimeMs  = [int]$stopwatch.ElapsedMilliseconds
        RebuildPerformed = $RebuildPerformed
        ErrorCode        = $ErrorCode
        ErrorMessage     = Normalize-String $ErrorMessage
    } | ConvertTo-Json -Compress
}

# -----------------------------------------------------
# Disk state wait
# -----------------------------------------------------

function Wait-DiskState {

    param(
        [int]$DiskNumber,
        [scriptblock]$Condition,
        [int]$TimeoutSeconds = 20
    )

    $start = Get-Date

    do {

        Start-Sleep -Milliseconds 300
        $disk = Get-Disk -Number $DiskNumber -ErrorAction Stop

    } while (-not (& $Condition $disk) -and ((Get-Date) - $start).TotalSeconds -lt $TimeoutSeconds)

    if (-not (& $Condition $disk)) {

        throw [System.Exception]::new(
            "Disk state transition timeout.",
            [System.Exception]::new("20")
        )
    }

    return $disk
}

# -----------------------------------------------------
# Normalize disk
# -----------------------------------------------------

function Normalize-Disk {

    param([int]$DiskNumber)

    $disk = Get-Disk -Number $DiskNumber -ErrorAction Stop

    if ($disk.IsOffline) {

        Set-Disk -Number $DiskNumber -IsOffline $false
        Wait-DiskState -DiskNumber $DiskNumber -Condition { param($d) -not $d.IsOffline }

    }

    if ($disk.IsReadOnly) {

        Set-Disk -Number $DiskNumber -IsReadOnly $false
        Wait-DiskState -DiskNumber $DiskNumber -Condition { param($d) -not $d.IsReadOnly }

    }

    return (Get-Disk -Number $DiskNumber)
}

# -----------------------------------------------------
# Prepare disk
# -----------------------------------------------------

function Prepare-Disk {

    param([int]$DiskNumber)

    Clear-Disk -Number $DiskNumber -RemoveData -Confirm:$false | Out-Null

    Wait-DiskState -DiskNumber $DiskNumber -Condition {
        param($d) $d.PartitionStyle -eq "RAW"
    }

    Initialize-Disk -Number $DiskNumber -PartitionStyle MBR | Out-Null

    Wait-DiskState -DiskNumber $DiskNumber -Condition {
        param($d) $d.PartitionStyle -eq "MBR"
    }

    New-Partition `
        -DiskNumber $DiskNumber `
        -UseMaximumSize `
        -AssignDriveLetter | Out-Null
}

# -----------------------------------------------------
# Wait partition
# -----------------------------------------------------

function Wait-PartitionReady {

    param(
        [int]$DiskNumber,
        [int]$TimeoutSeconds = 60
    )

    $start = Get-Date

    while (((Get-Date) - $start).TotalSeconds -lt $TimeoutSeconds) {

        $p = Get-Partition -DiskNumber $DiskNumber -ErrorAction SilentlyContinue |
             Where-Object { $_.DriveLetter -ne $null } |
             Select-Object -First 1

        if ($p) {

            return (Normalize-DriveLetter $p.DriveLetter)
        }

        Start-Sleep -Milliseconds 400
    }

    throw [System.Exception]::new(
        "Drive letter allocation failed.",
        [System.Exception]::new("30")
    )
}

# -----------------------------------------------------
# Run FAT32 formatter
# -----------------------------------------------------

function Run-FAT32Formatter {

    param([string]$DriveLetter)

    $scriptDir = $PSScriptRoot
    $formatter = Join-Path $scriptDir "fat32format.exe"

    if (!(Test-Path $formatter)) {

        throw [System.Exception]::new(
            "FAT32 formatter not found.",
            [System.Exception]::new("40")
        )
    }

    $target = "$DriveLetter`:"

    $proc = Start-Process `
        -FilePath $formatter `
        -ArgumentList $target `
        -NoNewWindow `
        -Wait `
        -PassThru

    if ($proc.ExitCode -ne 0) {

        throw [System.Exception]::new(
            "FAT32 formatter execution failed.",
            [System.Exception]::new("41")
        )
    }
}

# -----------------------------------------------------
# Wait filesystem stabilization
# -----------------------------------------------------

function Wait-VolumeReady {

    param(
        [string]$DriveLetter,
        [int]$TimeoutSeconds = 90
    )

    $start = Get-Date

    while (((Get-Date) - $start).TotalSeconds -lt $TimeoutSeconds) {

        $v = Get-Volume -DriveLetter $DriveLetter -ErrorAction SilentlyContinue

        if ($v -and $v.FileSystem -eq "FAT32") {

            return $v
        }

        Start-Sleep -Milliseconds 500
    }

    throw [System.Exception]::new(
        "Volume stabilization timeout.",
        [System.Exception]::new("21")
    )
}

# -----------------------------------------------------
# MAIN
# -----------------------------------------------------

try {

    if ($DiskNumber -eq 0) {

        Write-Output (New-Result $false $null $null $null $false 10 "Disk 0 protected.")
        return
    }

    $disk = Get-Disk -Number $DiskNumber -ErrorAction Stop

    if ($disk.IsBoot -or $disk.IsSystem) {

        Write-Output (New-Result $false $null $null $null $false 11 "System disk protected.")
        return
    }

    Normalize-Disk -DiskNumber $DiskNumber | Out-Null

    Prepare-Disk -DiskNumber $DiskNumber

    $driveLetter = Wait-PartitionReady -DiskNumber $DiskNumber

    Run-FAT32Formatter -DriveLetter $driveLetter

    Update-HostStorageCache

    Start-Sleep -Milliseconds 800

    $driveLetter = Wait-PartitionReady -DiskNumber $DiskNumber

    $volume = Wait-VolumeReady -DriveLetter $driveLetter

    $disk = Get-Disk -Number $DiskNumber

    Write-Output (New-Result $true `
        $volume.DriveLetter `
        $volume.FileSystem `
        $disk.PartitionStyle `
        $true `
        0 `
        $null)
}
catch {

    $errorCode = 99

    if ($_.Exception.InnerException -and $_.Exception.InnerException.Message -match "^\d+$") {

        $errorCode = [int]$_.Exception.InnerException.Message
    }

    Write-Output (New-Result $false `
        $null `
        $null `
        $null `
        $false `
        $errorCode `
        $_.Exception.Message)
}
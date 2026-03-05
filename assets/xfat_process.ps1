param(
    [Parameter(Mandatory=$true)]
    [int]$DiskNumber,

    [ValidateSet("ForceRebuild","EnsureState")]
    [string]$Mode = "ForceRebuild"
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
# 99 = Unhandled exception
# =====================================================

$ExpectedLabel = "PS2X FAT"

function Normalize-String {
    param([string]$Value)
    if ($null -eq $Value) { return $null }
    $trimmed = $Value.Trim()
    if ($trimmed -eq "") { return $null }
    return $trimmed
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
        Success           = $Success
        DriveLetter       = Normalize-String $DriveLetter
        FileSystem        = Normalize-String $FileSystem
        PartitionStyle    = Normalize-String $PartitionStyle
        ExecutionTimeMs   = [int]$stopwatch.ElapsedMilliseconds
        RebuildPerformed  = $RebuildPerformed
        ErrorCode         = [int]$ErrorCode
        ErrorMessage      = Normalize-String $ErrorMessage
    } | ConvertTo-Json -Compress
}

function Wait-DiskState {
    param(
        [int]$DiskNumber,
        [scriptblock]$Condition,
        [int]$TimeoutSeconds = 15
    )

    $start = Get-Date
    do {
        Start-Sleep -Milliseconds 300
        $disk = Get-Disk -Number $DiskNumber -ErrorAction Stop
    }
    while (-not (& $Condition $disk) -and ((Get-Date) - $start).TotalSeconds -lt $TimeoutSeconds)

    if (-not (& $Condition $disk)) {
        throw [System.Exception]::new("Disk state transition timeout.", [System.Exception]::new("20"))
    }

    return $disk
}

function Wait-VolumeReady {
    param(
        [char]$DriveLetter,
        [int]$TimeoutSeconds = 30
    )

    $start = Get-Date
    while (((Get-Date) - $start).TotalSeconds -lt $TimeoutSeconds) {
        $v = Get-Volume -DriveLetter $DriveLetter -ErrorAction SilentlyContinue
        if ($v -and (Normalize-String $v.FileSystem) -eq "exFAT") {
            return $v
        }
        Start-Sleep -Milliseconds 500
    }

    throw [System.Exception]::new("Volume stabilization timeout.", [System.Exception]::new("21"))
}

function Normalize-Disk {
    param([int]$DiskNumber)

    $disk = Get-Disk -Number $DiskNumber -ErrorAction Stop

    if ($disk.IsOffline) {
        Set-Disk -Number $DiskNumber -IsOffline $false -ErrorAction Stop
        $disk = Wait-DiskState -DiskNumber $DiskNumber -Condition { param($d) -not $d.IsOffline }
    }

    if ($disk.IsReadOnly) {
        Set-Disk -Number $DiskNumber -IsReadOnly $false -ErrorAction Stop
        $disk = Wait-DiskState -DiskNumber $DiskNumber -Condition { param($d) -not $d.IsReadOnly }
    }

    return $disk
}

function Rebuild-Disk {
    param([int]$DiskNumber)

    Clear-Disk -Number $DiskNumber -RemoveData -Confirm:$false
    Wait-DiskState -DiskNumber $DiskNumber -Condition { param($d) $d.PartitionStyle -eq "RAW" }

    Initialize-Disk -Number $DiskNumber -PartitionStyle MBR
    Wait-DiskState -DiskNumber $DiskNumber -Condition { param($d) $d.PartitionStyle -eq "MBR" }

    $partition = New-Partition -DiskNumber $DiskNumber -UseMaximumSize -AssignDriveLetter

    if (!$partition -or !$partition.DriveLetter) {
        throw [System.Exception]::new("Drive letter allocation failed.", [System.Exception]::new("30"))
    }

    Format-Volume `
        -Partition $partition `
        -FileSystem exFAT `
        -AllocationUnitSize 32768 `
        -NewFileSystemLabel $ExpectedLabel `
        -Confirm:$false | Out-Null

    Update-HostStorageCache

    return Wait-VolumeReady -DriveLetter $partition.DriveLetter
}

# =====================================================
# UI SUPPRESSION (AutoPlay OFF temporarily)
# =====================================================

function Get-RegDword {
    param([string]$Path, [string]$Name)
    try {
        $v = (Get-ItemProperty -Path $Path -Name $Name -ErrorAction Stop).$Name
        return [uint32]$v
    } catch {
        return $null
    }
}

function Set-RegDword {
    param([string]$Path, [string]$Name, [uint32]$Value)
    if (-not (Test-Path $Path)) {
        New-Item -Path $Path -Force | Out-Null
    }
    New-ItemProperty -Path $Path -Name $Name -PropertyType DWord -Value $Value -Force | Out-Null
}

# Saves prior values and restores them
$autoPlayState = @{
    HKCU_Path  = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
    HKLM_Path  = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
    Name       = "NoDriveTypeAutoRun"
    HKCU_Old   = $null
    HKLM_Old   = $null
    HKCU_Had   = $false
    HKLM_Had   = $false
}

function Disable-AutoPlayTemporarily {
    # 0xFF disables AutoRun on all drive types
    $autoPlayState.HKCU_Old = Get-RegDword -Path $autoPlayState.HKCU_Path -Name $autoPlayState.Name
    $autoPlayState.HKLM_Old = Get-RegDword -Path $autoPlayState.HKLM_Path -Name $autoPlayState.Name

    $autoPlayState.HKCU_Had = ($null -ne $autoPlayState.HKCU_Old)
    $autoPlayState.HKLM_Had = ($null -ne $autoPlayState.HKLM_Old)

    Set-RegDword -Path $autoPlayState.HKCU_Path -Name $autoPlayState.Name -Value 255
    Set-RegDword -Path $autoPlayState.HKLM_Path -Name $autoPlayState.Name -Value 255
}

function Restore-AutoPlay {
    try {
        if ($autoPlayState.HKCU_Had) {
            Set-RegDword -Path $autoPlayState.HKCU_Path -Name $autoPlayState.Name -Value $autoPlayState.HKCU_Old
        } else {
            Remove-ItemProperty -Path $autoPlayState.HKCU_Path -Name $autoPlayState.Name -ErrorAction SilentlyContinue
        }

        if ($autoPlayState.HKLM_Had) {
            Set-RegDword -Path $autoPlayState.HKLM_Path -Name $autoPlayState.Name -Value $autoPlayState.HKLM_Old
        } else {
            Remove-ItemProperty -Path $autoPlayState.HKLM_Path -Name $autoPlayState.Name -ErrorAction SilentlyContinue
        }
    } catch {
        # intentionally silent to avoid breaking pipeline return
    }
}

# =====================================================
# MAIN EXECUTION
# =====================================================

try {

    # Proteção crítica
    if ($DiskNumber -eq 0) {
        Write-Output (New-Result $false $null $null $null $false 10 "Disk 0 is protected and cannot be modified.")
        return
    }

    $disk = Get-Disk -Number $DiskNumber -ErrorAction Stop

    if ($disk.IsBoot -or $disk.IsSystem) {
        Write-Output (New-Result $false $null $null $null $false 11 "Refusing to modify system or boot disk.")
        return
    }

    # Disable AutoPlay to avoid UI popups during RAW/partition changes
    Disable-AutoPlayTemporarily

    # Garante online + writable
    $disk = Normalize-Disk -DiskNumber $DiskNumber

    # ✅ SEMÂNTICA: FORMATAR SEMPRE
    $volume = Rebuild-Disk -DiskNumber $DiskNumber
    $disk = Get-Disk -Number $DiskNumber -ErrorAction SilentlyContinue

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

    if ($_.Exception.InnerException -and
        $_.Exception.InnerException.Message -match "^\d+$") {
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
finally {
    Restore-AutoPlay
}
param(
    [Parameter(Mandatory=$true)]
    [int]$DiskNumber,

    [ValidateSet("ForceRebuild","EnsureState")]
    [string]$Mode = "ForceRebuild"
)

$ErrorActionPreference = "Stop"
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

# =====================================================
# ERROR CODES (mesmo padrão)
# =====================================================
# 0  = Success
# 10 = Disk 0 protected
# 11 = System/Boot disk protected
# 20 = Disk state transition timeout
# 21 = Volume stabilization timeout
# 30 = Drive letter allocation failure
# 40 = FAT32 not implemented / unsupported
# 99 = Unhandled exception
# =====================================================

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
        RebuildPerformed  = [bool]$RebuildPerformed
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
        if ($v -and ($v.FileSystem -eq "FAT32" -or $v.FileSystem -eq "FAT")) {
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

    # =====================================================
    # FAT32 no Windows tem limitação de UI (32GB).
    # Format-Volume FAT32 pode falhar em volumes grandes.
    # Aqui deixamos explícito: se falhar, retorna ErrorCode 40.
    # Você pode trocar por fat32format.exe depois.
    # =====================================================

    try {
        Format-Volume `
            -Partition $partition `
            -FileSystem FAT32 `
            -NewFileSystemLabel "PS2 FAT32" `
            -Confirm:$false | Out-Null
    }
    catch {
        # fallback: marca como "não implementado" até plugar o formatter real
        throw [System.Exception]::new("FAT32 formatting not implemented for this disk size. Plug fat32format.exe.", [System.Exception]::new("40"))
    }

    Update-HostStorageCache
    return Wait-VolumeReady -DriveLetter $partition.DriveLetter
}

# =====================================================
# MAIN
# =====================================================

try {
    if ($DiskNumber -eq 0) {
        Write-Output (New-Result $false $null $null $null $false 10 "Disk 0 is protected and cannot be modified.")
        return
    }

    $disk = Get-Disk -Number $DiskNumber -ErrorAction Stop

    if ($disk.IsBoot -or $disk.IsSystem) {
        Write-Output (New-Result $false $null $null $null $false 11 "Refusing to modify system or boot disk.")
        return
    }

    $disk = Normalize-Disk -DiskNumber $DiskNumber

    # Se fosse um EnsureState de verdade, faria o check aqui.
    # Mas seu requisito atual é: se chamou format, formata sempre.
    $volume = Rebuild-Disk -DiskNumber $DiskNumber
    $disk = Get-Disk -Number $DiskNumber

    Write-Output (New-Result $true `
        $volume.DriveLetter `
        "FAT32" `
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
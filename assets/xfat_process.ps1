param(
    [Parameter(Mandatory=$true)][int]$DiskNumber,
    [string]$UniqueId = "",
    [string]$SerialNumber = "",
    [string]$SizeBytes = "",
    [string]$FriendlyName = "",
    [string]$BusType = "",
    [string]$LocationPath = "",
    [ValidateSet("ForceRebuild","EnsureState")][string]$Mode = "ForceRebuild"
)
$ErrorActionPreference = "Stop"
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$ExpectedLabel = "PS2X FAT"

function New-Result([bool]$Success,[string]$DriveLetter,[string]$FileSystem,[string]$PartitionStyle,[bool]$RebuildPerformed,[int]$ErrorCode,[string]$ErrorMessage,[string]$PipelineErrorCode,[int]$BlockSize){
 $stopwatch.Stop(); @{Success=$Success;DriveLetter=$DriveLetter;FileSystem=$FileSystem;PartitionStyle=$PartitionStyle;ExecutionTimeMs=[int]$stopwatch.ElapsedMilliseconds;RebuildPerformed=$RebuildPerformed;ErrorCode=$ErrorCode;ErrorMessage=$ErrorMessage;PipelineErrorCode=$PipelineErrorCode;BlockSize=$BlockSize} | ConvertTo-Json -Compress
}
function Resolve-Disk {
    param([int]$Preferred)
    $d = Get-Disk -Number $Preferred -ErrorAction SilentlyContinue
    if ($d) { return $d.Number }
    foreach ($x in Get-Disk) {
        if ($UniqueId -and $x.UniqueId -eq $UniqueId) { return $x.Number }
        if ($SerialNumber -and $x.SerialNumber -eq $SerialNumber) { return $x.Number }
        if ($LocationPath -and $x.LocationPath -eq $LocationPath) { return $x.Number }
        if ($FriendlyName -and $SizeBytes -and $x.FriendlyName -eq $FriendlyName -and [string]$x.Size -eq [string]$SizeBytes) { return $x.Number }
    }
    return $null
}
function Get-BlockSize([string]$DriveLetter){ try { $v=Get-CimInstance Win32_Volume -Filter "DriveLetter='$DriveLetter`:'" -ErrorAction Stop; return [int]$v.BlockSize } catch { return 0 } }

try {
    $resolved = Resolve-Disk -Preferred $DiskNumber
    if ($null -eq $resolved) { Write-Output (New-Result $false $null $null $null $false 30 "Removable not reacquired" "MS-USB-003" 0); return }
    if ($resolved -eq 0) { Write-Output (New-Result $false $null $null $null $false 10 "Disk 0 is protected" "MS-SEL-002" 0); return }
    $disk = Get-Disk -Number $resolved -ErrorAction Stop
    if ($disk.IsBoot -or $disk.IsSystem) { Write-Output (New-Result $false $null $null $null $false 11 "System/boot disk protected" "MS-SEL-002" 0); return }

    if ($disk.IsOffline) { Set-Disk -Number $resolved -IsOffline $false -ErrorAction Stop }
    if ($disk.IsReadOnly) { Set-Disk -Number $resolved -IsReadOnly $false -ErrorAction Stop }

    $resolved = Resolve-Disk -Preferred $resolved; if ($null -eq $resolved) { Write-Output (New-Result $false $null $null $null $false 30 "Removable not reacquired" "MS-USB-003" 0); return }
    Clear-Disk -Number $resolved -RemoveData -Confirm:$false -ErrorAction Stop
    Start-Sleep -Milliseconds 500

    $resolved = Resolve-Disk -Preferred $resolved; if ($null -eq $resolved) { Write-Output (New-Result $false $null $null $null $false 30 "Removable not reacquired" "MS-USB-003" 0); return }
    Initialize-Disk -Number $resolved -PartitionStyle MBR -ErrorAction Stop
    $partition = New-Partition -DiskNumber $resolved -UseMaximumSize -AssignDriveLetter -ErrorAction Stop
    Format-Volume -Partition $partition -FileSystem exFAT -AllocationUnitSize 32768 -NewFileSystemLabel $ExpectedLabel -Confirm:$false | Out-Null
    Update-HostStorageCache
    $volume = Get-Volume -DriveLetter $partition.DriveLetter -ErrorAction Stop
    $disk = Get-Disk -Number $resolved -ErrorAction Stop
    $bs = Get-BlockSize -DriveLetter $partition.DriveLetter
    Write-Output (New-Result $true $volume.DriveLetter $volume.FileSystem $disk.PartitionStyle $true 0 $null $null $bs)
} catch {
    Write-Output (New-Result $false $null $null $null $false 99 $_.Exception.Message "MS-FMT-002" 0)
}

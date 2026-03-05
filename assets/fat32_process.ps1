param(
    [Parameter(Mandatory=$true)][int]$DiskNumber,
    [string]$UniqueId = "",
    [string]$SerialNumber = "",
    [string]$SizeBytes = "",
    [string]$FriendlyName = "",
    [string]$BusType = "",
    [string]$LocationPath = ""
)
$ErrorActionPreference = "Stop"
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

function New-Result([bool]$Success,[string]$DriveLetter,[string]$FileSystem,[string]$PartitionStyle,[bool]$RebuildPerformed,[int]$ErrorCode,[string]$ErrorMessage,[string]$PipelineErrorCode,[int]$BlockSize){
 $stopwatch.Stop(); @{Success=$Success;DriveLetter=$DriveLetter;FileSystem=$FileSystem;PartitionStyle=$PartitionStyle;ExecutionTimeMs=[int]$stopwatch.ElapsedMilliseconds;RebuildPerformed=$RebuildPerformed;ErrorCode=$ErrorCode;ErrorMessage=$ErrorMessage;PipelineErrorCode=$PipelineErrorCode;BlockSize=$BlockSize} | ConvertTo-Json -Compress
}
function Resolve-Disk { param([int]$Preferred)
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

# autoplay suppression
$autoPlayState=@{HKCU_Path="HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer";HKLM_Path="HKLM:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer";Name="NoDriveTypeAutoRun";HKCU_Old=$null;HKLM_Old=$null;HKCU_Had=$false;HKLM_Had=$false}
function Get-RegDword { param([string]$Path,[string]$Name) try { return [uint32](Get-ItemProperty -Path $Path -Name $Name -ErrorAction Stop).$Name } catch { return $null } }
function Set-RegDword { param([string]$Path,[string]$Name,[uint32]$Value) if(-not(Test-Path $Path)){New-Item -Path $Path -Force|Out-Null}; New-ItemProperty -Path $Path -Name $Name -PropertyType DWord -Value $Value -Force|Out-Null }
function Disable-AutoPlayTemporarily { $autoPlayState.HKCU_Old=Get-RegDword -Path $autoPlayState.HKCU_Path -Name $autoPlayState.Name; $autoPlayState.HKLM_Old=Get-RegDword -Path $autoPlayState.HKLM_Path -Name $autoPlayState.Name; $autoPlayState.HKCU_Had=($null -ne $autoPlayState.HKCU_Old); $autoPlayState.HKLM_Had=($null -ne $autoPlayState.HKLM_Old); Set-RegDword -Path $autoPlayState.HKCU_Path -Name $autoPlayState.Name -Value 255; Set-RegDword -Path $autoPlayState.HKLM_Path -Name $autoPlayState.Name -Value 255 }
function Restore-AutoPlay { try { if($autoPlayState.HKCU_Had){Set-RegDword -Path $autoPlayState.HKCU_Path -Name $autoPlayState.Name -Value $autoPlayState.HKCU_Old}else{Remove-ItemProperty -Path $autoPlayState.HKCU_Path -Name $autoPlayState.Name -ErrorAction SilentlyContinue}; if($autoPlayState.HKLM_Had){Set-RegDword -Path $autoPlayState.HKLM_Path -Name $autoPlayState.Name -Value $autoPlayState.HKLM_Old}else{Remove-ItemProperty -Path $autoPlayState.HKLM_Path -Name $autoPlayState.Name -ErrorAction SilentlyContinue} } catch {} }

try {
    Disable-AutoPlayTemporarily
    $resolved = Resolve-Disk -Preferred $DiskNumber
    if ($null -eq $resolved) { Write-Output (New-Result $false $null $null $null $false 30 "Removable not reacquired" "MS-USB-003" 0); return }
    if ($resolved -eq 0) { Write-Output (New-Result $false $null $null $null $false 10 "Disk 0 protected" "MS-SEL-002" 0); return }
    $disk = Get-Disk -Number $resolved -ErrorAction Stop
    if ($disk.IsBoot -or $disk.IsSystem) { Write-Output (New-Result $false $null $null $null $false 11 "System disk protected" "MS-SEL-002" 0); return }
    if ($disk.IsOffline) { Set-Disk -Number $resolved -IsOffline $false -ErrorAction Stop }
    if ($disk.IsReadOnly) { Set-Disk -Number $resolved -IsReadOnly $false -ErrorAction Stop }

    $resolved = Resolve-Disk -Preferred $resolved; if ($null -eq $resolved) { Write-Output (New-Result $false $null $null $null $false 30 "Removable not reacquired" "MS-USB-003" 0); return }
    Clear-Disk -Number $resolved -RemoveData -Confirm:$false -ErrorAction Stop
    $resolved = Resolve-Disk -Preferred $resolved; if ($null -eq $resolved) { Write-Output (New-Result $false $null $null $null $false 30 "Removable not reacquired" "MS-USB-003" 0); return }
    Initialize-Disk -Number $resolved -PartitionStyle MBR -ErrorAction Stop
    $partition = New-Partition -DiskNumber $resolved -UseMaximumSize -AssignDriveLetter -ErrorAction Stop

    $formatter = Join-Path $PSScriptRoot "fat32format.exe"
    if (!(Test-Path $formatter)) { Write-Output (New-Result $false $null $null $null $false 40 "FAT32 formatter not found" "MS-FMT-001" 0); return }
    $target = "$($partition.DriveLetter):"
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $formatter
    $psi.Arguments = "-c32 $target"
    $psi.CreateNoWindow = $true
    $psi.UseShellExecute = $false
    $p = [System.Diagnostics.Process]::Start($psi)
    $p.WaitForExit()
    if ($p.ExitCode -ne 0) { Write-Output (New-Result $false $null $null $null $false 41 "FAT32 formatter execution failed" "MS-FMT-001" 0); return }

    Update-HostStorageCache
    Start-Sleep -Milliseconds 800
    $volume = Get-Volume -DriveLetter $partition.DriveLetter -ErrorAction Stop
    $disk = Get-Disk -Number $resolved -ErrorAction Stop
    $bs = Get-BlockSize -DriveLetter $partition.DriveLetter
    Write-Output (New-Result $true $volume.DriveLetter $volume.FileSystem $disk.PartitionStyle $true 0 $null $null $bs)
} catch {
    Write-Output (New-Result $false $null $null $null $false 99 $_.Exception.Message "MS-DSK-003" 0)
} finally { Restore-AutoPlay }

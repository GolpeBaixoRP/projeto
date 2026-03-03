param(
    [int]$DiskNumber
)

$ErrorActionPreference = "Stop"

try {

    $disk = Get-Disk -Number $DiskNumber

    if ($disk.IsOffline) {
        Set-Disk -Number $DiskNumber -IsOffline $false
    }

    if ($disk.IsReadOnly) {
        Set-Disk -Number $DiskNumber -IsReadOnly $false
    }

    Get-Partition -DiskNumber $DiskNumber -ErrorAction SilentlyContinue |
        Remove-Partition -Confirm:$false -ErrorAction SilentlyContinue

    Start-Sleep -Milliseconds 500

    # Deterministic MBR Barrier
    if ($disk.PartitionStyle -ne "MBR") {

        $script = @"
select disk $DiskNumber
attributes disk clear readonly
clean
convert mbr
exit
"@

        $temp = Join-Path $env:TEMP "xfat_mbr_$DiskNumber.txt"

        $script | Out-File -Encoding ASCII $temp

        diskpart /s $temp | Out-Null

        Remove-Item $temp -Force -ErrorAction SilentlyContinue

        Start-Sleep -Seconds 1
    }

    $partition = New-Partition `
        -DiskNumber $DiskNumber `
        -UseMaximumSize `
        -AssignDriveLetter

    $letter = ($partition | Get-Volume).DriveLetter

    Format-Volume `
        -DriveLetter $letter `
        -FileSystem exFAT `
        -Confirm:$false `
        -Force

    Update-HostStorageCache
    Start-Sleep -Seconds 2

    $volume = Get-Volume -DriveLetter $letter

    @{
        Success=$true
        DriveLetter=$letter
        FileSystem=$volume.FileSystem
    } | ConvertTo-Json -Compress

}
catch {

    @{
        Success=$false
        ErrorMessage=$_.Exception.Message
    } | ConvertTo-Json -Compress
}
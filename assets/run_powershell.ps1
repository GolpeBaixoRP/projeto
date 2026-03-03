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

    # Barrier Cleanup
    Get-Partition -DiskNumber $DiskNumber -ErrorAction SilentlyContinue |
        Remove-Partition -Confirm:$false -ErrorAction SilentlyContinue

    Start-Sleep -Milliseconds 500

    # Deterministic MBR Rewrite Engine
    if ($disk.PartitionStyle -ne "MBR") {

        $script = @"
select disk $DiskNumber
attributes disk clear readonly
clean
convert mbr
create partition primary
exit
"@

        $temp = Join-Path $env:TEMP "mbrew_$DiskNumber.txt"

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

    @{ Success=$true; DriveLetter=$letter } | ConvertTo-Json -Compress
}
catch {

    @{
        Success=$false
        ErrorMessage=$_.Exception.Message
    } | ConvertTo-Json -Compress
}
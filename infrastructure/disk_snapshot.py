import json
from utils.powershell_runner import run_powershell


class DiskSnapshot:

    @staticmethod
    def collect() -> dict:
        script = r'''
        $disks = Get-Disk | ForEach-Object {
            $disk = $_

            $partitions = Get-Partition -DiskNumber $disk.Number -ErrorAction SilentlyContinue | ForEach-Object {
                $partition = $_

                $volume = Get-Volume -Partition $partition -ErrorAction SilentlyContinue | Select-Object -First 1

                [PSCustomObject]@{
                    PartitionNumber = $partition.PartitionNumber
                    DriveLetter = $partition.DriveLetter
                    Size = $partition.Size
                    Type = $partition.Type
                    Volume = if ($volume) {
                        [PSCustomObject]@{
                            FileSystem = $volume.FileSystem
                            Label = $volume.FileSystemLabel
                            SpaceRemaining = $volume.SizeRemaining
                        }
                    } else {
                        $null
                    }
                }
            }

            [PSCustomObject]@{
                DiskNumber = $disk.Number
                FriendlyName = $disk.FriendlyName
                SerialNumber = $disk.SerialNumber
                Size = $disk.Size
                PartitionStyle = $disk.PartitionStyle
                BusType = $disk.BusType
                IsBoot = $disk.IsBoot
                IsSystem = $disk.IsSystem
                IsOffline = $disk.IsOffline
                OperationalStatus = $disk.OperationalStatus
                HealthStatus = $disk.HealthStatus
                Partitions = @($partitions)
            }
        }

        [PSCustomObject]@{ Disks = @($disks) } | ConvertTo-Json -Depth 8
        '''

        raw_snapshot = run_powershell(command=script)

        if isinstance(raw_snapshot, dict):
            return raw_snapshot

        return json.loads(raw_snapshot)

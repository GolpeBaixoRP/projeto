from infrastructure.disk_snapshot import DiskSnapshot


class DiskCollector:

    @staticmethod
    def collect():
        """Coleta snapshot autoritativo e normaliza para contrato interno legacy."""
        raw = DiskSnapshot.collect() or {}
        disks = raw.get("Disks") or []

        normalized = []

        for disk in disks:
            partitions = disk.get("Partitions") or []
            if isinstance(partitions, dict):
                partitions = [partitions]

            legacy_partitions = []
            legacy_volumes = []

            for p in partitions:
                legacy_partitions.append(
                    {
                        "PartitionNumber": p.get("PartitionNumber"),
                        "DriveLetter": p.get("DriveLetter"),
                        "Size": p.get("Size"),
                        "Type": p.get("Type"),
                    }
                )

                volume = p.get("Volume") or {}
                if volume:
                    legacy_volumes.append(
                        {
                            "DriveLetter": p.get("DriveLetter"),
                            "FileSystem": volume.get("FileSystem"),
                            "Label": volume.get("Label"),
                            "SpaceRemaining": volume.get("SpaceRemaining"),
                        }
                    )

            normalized.append(
                {
                    "Disk": {
                        "Number": disk.get("DiskNumber"),
                        "FriendlyName": disk.get("FriendlyName"),
                        "SerialNumber": disk.get("SerialNumber"),
                        "Size": disk.get("Size"),
                        "PartitionStyle": disk.get("PartitionStyle"),
                        "BusType": disk.get("BusType"),
                        "IsBoot": disk.get("IsBoot", False),
                        "IsSystem": disk.get("IsSystem", False),
                        "IsOffline": disk.get("IsOffline", False),
                        "OperationalStatus": disk.get("OperationalStatus"),
                        "HealthStatus": disk.get("HealthStatus"),
                    },
                    "Partitions": legacy_partitions,
                    "Volumes": legacy_volumes,
                }
            )

        return normalized

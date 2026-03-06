from config.settings import (
    STATUS_BLOCKED,
    STATUS_INCOMPATIBLE,
    STATUS_NEEDS_PREPARATION,
    STATUS_OFFLINE,
    STATUS_READY,
    SUPPORTED_FILESYSTEMS,
)


class DiskEvaluator:

    @staticmethod
    def evaluate(entry):
        disk = entry.get("Disk", {})
        partitions = entry.get("Partitions") or []
        volumes = entry.get("Volumes") or []

        if isinstance(partitions, dict):
            partitions = [partitions]
        if isinstance(volumes, dict):
            volumes = [volumes]

        if disk.get("IsBoot") or disk.get("IsSystem"):
            return STATUS_BLOCKED

        if disk.get("IsOffline") or disk.get("OperationalStatus") != "Online":
            return STATUS_OFFLINE

        partition_style = disk.get("PartitionStyle")

        if partition_style in (None, "RAW"):
            return STATUS_NEEDS_PREPARATION

        if partition_style == "GPT":
            return STATUS_NEEDS_PREPARATION

        if not partitions:
            return STATUS_NEEDS_PREPARATION

        # READY depende de snapshot consistente provido pelo controller.
        # Em dúvida (evidência incompleta), manter estado conservador.
        if not volumes:
            return STATUS_NEEDS_PREPARATION

        primary_partition = partitions[0] if partitions else {}
        primary_volume = volumes[0] if volumes else {}

        filesystem = (primary_volume.get("FileSystem") or "").upper()
        drive_letter = (
            primary_volume.get("DriveLetter")
            or primary_partition.get("DriveLetter")
        )
        has_drive_letter = bool(str(drive_letter or "").strip())

        if partition_style == "MBR":
            if filesystem in SUPPORTED_FILESYSTEMS and has_drive_letter:
                return STATUS_READY
            return STATUS_NEEDS_PREPARATION

        return STATUS_INCOMPATIBLE

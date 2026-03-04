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

        filesystem = None
        if volumes:
            filesystem = (volumes[0].get("FileSystem") or "").upper()

        if partition_style == "MBR":
            if filesystem in SUPPORTED_FILESYSTEMS:
                return STATUS_READY
            return STATUS_NEEDS_PREPARATION

        return STATUS_INCOMPATIBLE

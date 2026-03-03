from config.settings import *

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

        if disk.get("OperationalStatus") != "Online":
            return STATUS_OFFLINE

        partition_style = disk.get("PartitionStyle")

        if partition_style == "GPT":
            return STATUS_NEEDS_PREPARATION

        if not partitions:
            return STATUS_NEEDS_PREPARATION

        filesystem = None
        if volumes:
            filesystem = volumes[0].get("FileSystem")

        if partition_style == "MBR":
            if filesystem in SUPPORTED_FILESYSTEMS:
                return STATUS_READY
            else:
                return STATUS_NEEDS_PREPARATION

        return STATUS_INCOMPATIBLE
def format_disk(disk_info):
    # Lógica de formatação
    print(f"Formatando disco: {disk_info['name']}")
    disk_info['formatted'] = True  # Garantir que 'formatted' seja True
    print(f"Disco {disk_info['name']} formatado.")
    return disk_info
            
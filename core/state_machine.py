from enum import Enum


class DiskState(Enum):
    IDLE = "IDLE"
    SELECTED = "SELECTED"
    READY = "READY"
    NEEDS_PREPARATION = "NEEDS_PREPARATION"
    FORMATTING = "FORMATTING"
    COMPLETED = "COMPLETED"
    CRITICAL_REMOVED = "CRITICAL_REMOVED"

    # Estados arquiteturais determinísticos
    NOT_INITIALIZED = "NOT_INITIALIZED"
    RAW = "RAW"
    WRONG_PARTITION_STYLE = "WRONG_PARTITION_STYLE"
    WRONG_FILESYSTEM = "WRONG_FILESYSTEM"
    READY_FOR_OPL = "READY_FOR_OPL"
    OPL_INSTALLED = "OPL_INSTALLED"
    POPSTARTER_INSTALLED = "POPSTARTER_INSTALLED"
    INVALID_DISK = "INVALID_DISK"
    SYSTEM_DISK = "SYSTEM_DISK"


def format_disk(disk_info):
    print(f"Formatando disco: {disk_info['name']}")
    disk_info['formatted'] = True
    print(f"Disco {disk_info['name']} formatado.")
    return disk_info

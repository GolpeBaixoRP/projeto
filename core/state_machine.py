
from enum import Enum

class DiskState(Enum):
    IDLE = "IDLE"
    SELECTED = "SELECTED"
    READY = "READY"
    NEEDS_PREPARATION = "NEEDS_PREPARATION"
    FORMATTING = "FORMATTING"
    COMPLETED = "COMPLETED"
    CRITICAL_REMOVED = "CRITICAL_REMOVED"

def format_disk(disk_info):
    # Lógica de formatação
    print(f"Formatando disco: {disk_info['name']}")
    disk_info['formatted'] = True  # Garantir que 'formatted' seja True
    print(f"Disco {disk_info['name']} formatado.")
    return disk_info
            
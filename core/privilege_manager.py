class PrivilegeManager:
    def __init__(self):
        pass

def format_disk(disk_info):
    # Lógica de formatação
    print(f"Formatando disco: {disk_info['name']}")
    disk_info['formatted'] = True  # Garantir que 'formatted' seja True
    print(f"Disco {disk_info['name']} formatado.")
    return disk_info
            
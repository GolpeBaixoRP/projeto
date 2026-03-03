# services/format_utils.py


def format_disk(disk_info):
    """
    Marca o disco como preparado logicamente.
    Não altera estrutura física.
    """

    number = disk_info["Disk"]["Number"]

    print(f"Iniciando formatação lógica do disco {number}...")

    # Simulação de formatação
    disk_info["Volumes"] = [{
        "FileSystem": "FAT32",
        "Label": f"DISK_{number}"
    }]

    print(f"Disco {number} formatado logicamente como FAT32.")

    return disk_info
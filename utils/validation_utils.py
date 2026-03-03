import logging

# Supondo que o logger já tenha sido configurado anteriormente
logger = logging.getLogger("MeuSonho")

def validate_disk_integrity(disk_info):
    """
    Valida a integridade do disco com base na estrutura real do snapshot.
    Um disco é considerado íntegro se:
    - Possui estrutura básica.
    - Possui pelo menos um volume.
    - Cada volume possui um tipo de sistema de arquivos válido.
    """

    if not disk_info:
        logger.error("Disk info está vazio.")
        return False

    if "Disk" not in disk_info:
        logger.error("Estrutura de dados do disco não encontrada.")
        return False

    if "Volumes" not in disk_info:
        logger.error("Volumes não encontrados no disco.")
        return False

    if not disk_info["Volumes"]:
        logger.error("Nenhum volume encontrado no disco.")
        return False

    # Validar integridade dos volumes (exemplo de validação mais detalhada)
    for volume in disk_info["Volumes"]:
        if "FileSystem" not in volume or not volume["FileSystem"]:
            logger.warning(f"Volume {volume.get('DriveLetter', 'Desconhecido')} sem sistema de arquivos.")
            return False

    logger.info("Disk integrity validada com sucesso.")
    return True


def recover_data(disk_info):
    """
    Simula a recuperação lógica dos dados do disco.
    Não altera a estrutura real do disco.
    """
    try:
        number = disk_info["Disk"]["Number"]
        logger.info(f"Iniciando recuperação lógica dos dados do disco {number}...")

        # Simulação de recuperação
        print(f"Recuperando estrutura lógica do disco {number}...")
        time.sleep(2)  # Simulação de algum tempo de recuperação
        print(f"Recuperação concluída para disco {number}.")

        # Log após a recuperação
        logger.info(f"Recuperação concluída para disco {number}.")
    except KeyError as e:
        logger.error(f"Erro ao recuperar dados: chave {str(e)} não encontrada em disk_info.")
        print("Erro ao recuperar dados. Detalhes no log.")
    except Exception as e:
        logger.error(f"Erro inesperado durante recuperação: {str(e)}")
        print("Erro inesperado durante recuperação. Detalhes no log.")


def notify_user(message, level="INFO"):
    """
    Notifica o usuário via console e log.
    """
    if level == "ERROR":
        logger.error(message)
    elif level == "WARNING":
        logger.warning(message)
    else:
        logger.info(message)

    # Exibir mensagem no console
    print(f"[{level}] {message}")
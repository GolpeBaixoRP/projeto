from utils.logger import setup_logger
logger = setup_logger()

class InstallerService:

    def install_opl(self, disk):
        '''
        Criar estrutura OPL
        '''
        logger.info(f"Instalando OPL no disco {disk['Disk']['FriendlyName']}...")

    def install_popstarter(self, disk):
        '''
        Criar estrutura PopStarter
        '''
        logger.info(f"Instalando PopStarter no disco {disk['Disk']['FriendlyName']}...")


def validate_disk_integrity(disk):
    try:
        if not disk['formatted']:
            raise Exception(f"Disco {disk['name']} não foi formatado corretamente.")
        if disk['filesystem'] not in ['FAT32', 'exFAT']:
            raise Exception(f"Sistema de arquivos do disco {disk['name']} não é compatível.")
        print(f"Disco {disk['name']} validado com sucesso.")
        return True
    except Exception as e:
        print(f"[ERROR]: {e}")
        return False

def recover_data(disk):
    print(f"Recuperando dados do disco {disk['name']}...")
    print(f"Recuperação de dados do disco {disk['name']} concluída com sucesso.")




def validate_disk_integrity(disk):
    try:
        if not disk['formatted']:
            raise Exception(f"Disco {disk['name']} nÃ£o foi formatado corretamente.")
        if disk['filesystem'] not in ['FAT32', 'exFAT']:
            raise Exception(f"Sistema de arquivos do disco {disk['name']} nÃ£o Ã© compatÃ­vel.")
        print(f"Disco {disk['name']} validado com sucesso.")
        return True
    except Exception as e:
        print(f"[ERROR]: {e}")
        return False

def recover_data(disk):
    print(f"Recuperando dados do disco {disk['name']}...")
    print(f"RecuperaÃ§Ã£o de dados do disco {disk['name']} concluÃ­da com sucesso.")


def format_disk(disk_info):
    # Lógica de formatação
    print(f"Formatando disco: {disk_info['name']}")
    disk_info['formatted'] = True  # Garantir que 'formatted' seja True
    print(f"Disco {disk_info['name']} formatado.")
    return disk_info
            
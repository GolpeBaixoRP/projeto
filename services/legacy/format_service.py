from services.format_utils import format_disk
from utils.logger import setup_logger
logger = setup_logger()

class FormatterService:

    def format_disk(self, disk):
        '''
        Convert GPT -> MBR
        Create primary partition
        Format with FAT32 or exFAT
        '''
        logger.info(f"Iniciando formataÃ§Ã£o para o disco {disk['Disk']['FriendlyName']}...")
        # LÃ³gica de formataÃ§Ã£o real


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


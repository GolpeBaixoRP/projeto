from core.operation_controller import OperationController
from services.hardware_preflight import HardwarePreflight
from utils.logger import setup_logger

logger = setup_logger()


def main():

    logger.info("Inicializando sistema...")

    HardwarePreflight.ensure_ready()

    controller = OperationController()

    snapshot = controller.initialize()

    print("\n=== SNAPSHOT INICIAL ===")

    for disk in snapshot:
        print(
            f"Disco {disk.number} - "
            f"{disk.friendly_name} | "
            f"{disk.partition_style} | "
            f"{disk.status}"
        )

    try:

        disk_number = int(input("Digite o número do disco que deseja selecionar: "))

        controller.select_disk(disk_number)

        filesystem = input(
            "Escolha o sistema de arquivos (FAT32 / exFAT): "
        ).upper()

        if filesystem not in ["FAT32", "EXFAT"]:
            print("Sistema de arquivos inválido.")
            return

        confirm = input(
            "ATENÇÃO: Isso apagará TODOS os dados do disco.\n"
            "Digite FORMATAR para continuar: "
        )

        if confirm != "FORMATAR":
            print("Operação cancelada.")
            return

        controller.execute_full_format(filesystem)

        print("Formatação concluída com sucesso.")

    except Exception as e:
        logger.error(f"Erro: {e}")
        print(f"Erro: {e}")


if __name__ == "__main__":
    main()

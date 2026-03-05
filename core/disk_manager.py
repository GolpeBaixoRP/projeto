from core.disk_collector import DiskCollector
from core.disk_evaluator import DiskEvaluator
from models.disk_model import DiskModel
import logging

logger = logging.getLogger(__name__)

class DiskManager:

    def __init__(self):
        self.snapshot = []

    def refresh(self):
        try:
            collected = DiskCollector.collect()  # Chama o método de coleta de discos
        except Exception as e:
            logger.error(f"Erro ao coletar dados dos discos: {e}")
            return []

        evaluated = []

        for entry in collected:
            disk_data = entry.get("Disk", {})
            partitions = entry.get("Partitions", [])
            volumes = entry.get("Volumes", [])

            # Verifica se as chaves essenciais existem antes de criar o modelo
            number = disk_data.get("Number", None)
            friendly_name = disk_data.get("FriendlyName", "Desconhecido")
            serial_number = disk_data.get("SerialNumber", "UNKNOWN")
            partition_style = disk_data.get("PartitionStyle", "Não definido")
            bus_type = disk_data.get("BusType", "Não especificado")
            size = disk_data.get("Size")
            unique_id = disk_data.get("UniqueId")
            location_path = disk_data.get("LocationPath")
            is_removable = disk_data.get("IsRemovable")
            is_readonly = disk_data.get("IsReadOnly")
            is_boot = disk_data.get("IsBoot", False)
            is_system = disk_data.get("IsSystem", False)
            is_offline = disk_data.get("IsOffline", False)
            operational_status = disk_data.get("OperationalStatus", "Desconhecido")

            # Avalia o status do disco
            status = DiskEvaluator.evaluate(entry)

            # Cria um objeto DiskModel com os dados obtidos
            model = DiskModel(
                number=number,
                friendly_name=friendly_name,
                serial_number=serial_number,
                partition_style=partition_style,
                bus_type=bus_type,
                is_boot=is_boot,
                is_system=is_system,
                is_offline=is_offline,
                operational_status=operational_status,
                size=size,
                unique_id=unique_id,
                location_path=location_path,
                is_removable=is_removable,
                is_readonly=is_readonly,
                partitions=partitions,
                volumes=volumes,
                status=status
            )

            evaluated.append(model)  # Adiciona o modelo à lista de discos avaliados

        self.snapshot = evaluated  # Atualiza o snapshot com os discos avaliados
        return self.snapshot
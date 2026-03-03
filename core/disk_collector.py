import json
from utils.powershell_runner import run_powershell


class DiskCollector:

    @staticmethod
    def _safe_json_load(raw: str):

        if not raw:
            return []

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Proteção BOM UTF-8
            return json.loads(raw.encode().decode("utf-8-sig"))

    @staticmethod
    def collect():

        # Snapshot PowerShell seguro
        command = r"""
        Get-Disk |
        Select-Object Number,
                      FriendlyName,
                      SerialNumber,
                      Size,
                      PartitionStyle,
                      BusType,
                      IsBoot,
                      IsSystem,
                      IsOffline,
                      IsReadOnly,
                      OperationalStatus |
        ConvertTo-Json -Depth 4
        """

        raw = run_powershell(command)

        if not raw:
            return []

        data = DiskCollector._safe_json_load(raw)

        # Normalização de lista
        if isinstance(data, dict):
            data = [data]

        snapshot = []

        for disk in data:

            snapshot.append({
                "Disk": {
                    "Number": disk.get("Number"),
                    "FriendlyName": disk.get("FriendlyName"),
                    "SerialNumber": disk.get("SerialNumber"),
                    "Size": disk.get("Size"),
                    "PartitionStyle": disk.get("PartitionStyle"),
                    "BusType": disk.get("BusType"),
                    "IsBoot": disk.get("IsBoot", False),
                    "IsSystem": disk.get("IsSystem", False),
                    "IsOffline": disk.get("IsOffline", False),
                    "IsReadOnly": disk.get("IsReadOnly", False),
                    "OperationalStatus": disk.get("OperationalStatus")
                },
                "Partitions": [],
                "Volumes": []
            })

        return snapshot


# Compatibilidade legacy (se algum módulo ainda chamar)
def format_disk(disk_info):

    print(f"Formatando disco: {disk_info.get('name', 'unknown')}")

    disk_info["formatted"] = True

    return disk_info
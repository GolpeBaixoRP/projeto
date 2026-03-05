from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ErrorSpec:
    code: str
    domain: str
    name: str
    severity: str
    recoverable: bool
    description: str
    probable_cause: str
    recommended_action: str


ERROR_TABLE: Dict[str, ErrorSpec] = {
    "MS-SNP-001": ErrorSpec("MS-SNP-001", "SNP", "SnapshotPowerShellFailure", "ERROR", True, "Falha ao executar PowerShell do snapshot.", "Runner falhou/timeout/erro de execução.", "Verificar runner, stderr e permissões."),
    "MS-SNP-002": ErrorSpec("MS-SNP-002", "SNP", "SnapshotJsonInvalid", "ERROR", True, "Snapshot retornou JSON inválido.", "Ruído no stdout ou erro no script de snapshot.", "Inspecionar stdout bruto e corrigir serialização."),
    "MS-SEL-002": ErrorSpec("MS-SEL-002", "SEL", "DiskBlockedByPolicy", "ERROR", False, "Disco bloqueado por política.", "Disco 0/boot/system/offline/bloqueado.", "Selecionar disco elegível."),
    "MS-GRD-001": ErrorSpec("MS-GRD-001", "GRD", "DiskIdentityMismatch", "CRITICAL", False, "Violação de identidade física detectada.", "Drift de identidade relevante.", "Revalidar disco e repetir operação."),
    "MS-USB-003": ErrorSpec("MS-USB-003", "USB", "RemovableDeviceNotReacquired", "ERROR", True, "Dispositivo removível não foi re-adquirido.", "Reenumeração/desconexão durante operação.", "Reconectar dispositivo e tentar novamente."),
    "MS-RUN-002": ErrorSpec("MS-RUN-002", "RUN", "PowerShellTimeout", "ERROR", True, "Execução PowerShell excedeu timeout.", "Comando travado/lento.", "Aumentar timeout e investigar IO/disco."),
    "MS-RUN-003": ErrorSpec("MS-RUN-003", "RUN", "WorkerReturnedInvalidJson", "ERROR", True, "Worker retornou JSON inválido.", "Ruído em stdout ou contrato quebrado.", "Padronizar saída JSON compacta."),
    "MS-DSK-003": ErrorSpec("MS-DSK-003", "DSK", "DiskWipeFailed", "ERROR", True, "Falha ao limpar disco.", "Clear-Disk falhou.", "Verificar proteção/read-only/estado do hardware."),
    "MS-DSK-005": ErrorSpec("MS-DSK-005", "DSK", "PartitionCreationFailed", "ERROR", True, "Falha ao criar partição.", "New-Partition falhou.", "Revalidar estado MBR e espaço do dispositivo."),
    "MS-FMT-001": ErrorSpec("MS-FMT-001", "FMT", "Fat32FormatFailed", "ERROR", True, "Falha na formatação FAT32.", "fat32format.exe retornou erro.", "Checar argumentos, letra e integridade do executável."),
    "MS-FMT-002": ErrorSpec("MS-FMT-002", "FMT", "ExFatFormatFailed", "ERROR", True, "Falha na formatação exFAT.", "Format-Volume falhou.", "Checar estado da partição/volume."),
    "MS-FMT-004": ErrorSpec("MS-FMT-004", "FMT", "InvalidFat32ClusterSize", "ERROR", False, "Cluster FAT32 divergente do perfil PS2.", "AUS != 32KB.", "Refazer formatação com -c32 e validar BlockSize."),
    "MS-VFY-001": ErrorSpec("MS-VFY-001", "VFY", "PartitionStyleMismatch", "ERROR", False, "PartitionStyle divergente do esperado.", "Initialize-Disk não resultou em MBR.", "Refazer etapa de inicialização e verificar disco alvo."),
    "MS-VFY-002": ErrorSpec("MS-VFY-002", "VFY", "PartitionMissingAfterSuccess", "ERROR", False, "Partição/volume ausente após sucesso reportado.", "Reenumeração/erro de criação/estado inconsistente.", "Reexecutar pipeline com reaquisição por identidade."),
    "MS-AUD-001": ErrorSpec("MS-AUD-001", "AUD", "AuditWriteFailure", "WARN", True, "Falha ao gravar evento de auditoria.", "IO/log path inválido.", "Corrigir diretório de logs/permissões."),
}

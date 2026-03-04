# Execução em hardware real

Este projeto executa mutações reais de disco via PowerShell (`Get-Disk`, `New-Partition`, `Format-Volume`).

## Pré-requisitos

1. **Windows** (PowerShell com cmdlets de Storage disponíveis).
2. **Execução como Administrador**.
3. `assets/fat32format.exe` presente para FAT32 em discos > 32 GB.

## O que foi blindado

- Preflight obrigatório antes de iniciar o fluxo (`HardwarePreflight.ensure_ready()`):
  - valida sistema operacional;
  - valida presença de PowerShell (`powershell` ou `pwsh`);
  - valida privilégio administrativo.
- Runner de PowerShell com resolução automática de binário (`powershell` / `pwsh`).

## Uso

```bash
python main.py
```

Se o ambiente não estiver apto para hardware real, o programa aborta com erro explícito antes de qualquer mutação.

# Error Codes Taxonomy — Freeze Técnico

## Domínios
- **MS-SNP-***: snapshot/enumeração inicial.
- **MS-RUN-***: execução de processo PowerShell (spawn/timeout/exit code).
- **MS-IPC-***: contrato IPC Python ↔ Worker (stdout/JSON/schema/campos).
- **MS-FMT-***: falhas de formatação.
- **MS-VFY-***: divergências detectadas no verify do controller.
- **MS-VOL-***: problemas de volume/letra/block size indisponível.
- **MS-POL-***: violações de política operacional.
- **MS-SYS-***: requisitos de sistema/ambiente.
- **MS-CFG-***: configuração inválida.
- **MS-SEL-***: seleção de disco.
- **MS-GRD-***: identidade física/guardian.
- **MS-USB-***: reaquisição/dispositivo removível.
- **MS-AUD-***: persistência de auditoria.

## Intenção da taxonomia
- separar claramente camada/fase da falha;
- permitir triagem operacional por domínio;
- manter mensagens técnicas e humanas alinhadas.

## Diretriz de uso
- `MS-RUN-*` e `MS-IPC-*` para execução/contrato de worker.
- `MS-VFY-*` e `MS-VOL-*` para divergências de estado final observado.
- não reinterpretar falha de camada inferior como verify sem evidência observável.

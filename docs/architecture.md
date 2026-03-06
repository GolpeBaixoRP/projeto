# Architecture — Freeze Técnico

## Camadas do núcleo
1. **Workers (PowerShell)**: executam operações de disco (rebuild, partição, formatação, coleta de evidência).
2. **Runner**: encapsula execução PowerShell, timeout/kill tree e classificação de falhas de processo.
3. **Service (IPC)**: interpreta stdout JSON do worker e classifica falhas de contrato IPC.
4. **Controller (VERIFY)**: autoridade de validação pós-execução (expected vs found).
5. **Commit Barrier**: reconfirma estabilidade mínima após verify antes do commit.
6. **Evaluator (READY)**: avalia prontidão mínima conservadora com base em snapshot.
7. **Formatter**: converte `PipelineError` em saída curta/detalhada/estruturada.
8. **Forensic Audit**: trilha append-only JSONL com contexto operacional.

## Responsabilidades por camada
- **Worker**: executor técnico; não define política global.
- **Runner**: lifecycle de subprocesso e erros `MS-RUN-*`.
- **Service**: parser IPC e erros `MS-IPC-*`.
- **Controller**: valida estado final do disco e erros `MS-VFY-*` / `MS-VOL-*`.
- **Commit Barrier**: verificação leve de estabilidade pós-verify.
- **Evaluator**: estado READY conservador (não substitui verify).
- **Audit**: persistência de eventos para reconstrução forense.
- **Formatter**: apresentação humana/técnica de erros.

## Fluxo arquitetural consolidado
**Worker → Runner → Service → Controller → Commit Barrier → Evaluator → Audit/Formatter**

## Princípios de desenho
- simplicidade arquitetural
- separação de responsabilidades
- diagnóstico estruturado
- comportamento determinístico
- robustez com baixo número de arquivos

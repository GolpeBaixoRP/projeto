# Sistema de Provisionamento Determinístico

Versão Arquitetural Integrada **1.0**.

## Filosofia geral

O toolkit funciona como um **orquestrador determinístico** para provisionamento físico de mídia em hardware legado, com três camadas:

- **Inteligência (Python):** decisão e orquestração.
- **Execução física (PowerShell):** atuação operacional, sem regra de negócio.
- **Apresentação (UI):** reflexo de estado interpretado.

## Fonte de verdade

As decisões devem ser baseadas apenas em:

- snapshot físico atual do disco;
- estado observado do hardware;
- metadata real do sistema operacional.

Não confiar em cache, variáveis históricas, estados antigos ou letras de unidade persistidas.

## Identidade estrutural da mídia

A identidade canônica do dispositivo é composta por:

- `DiskNumber`
- `SerialNumber`
- `PartitionNumber`

A letra (`DriveLetter`) é atributo volátil, útil somente para interação humana.

## Snapshot unificado

Coleta obrigatória por níveis:

### Disco

- `DiskNumber`
- `FriendlyName`
- `SerialNumber`
- `Size`
- `PartitionStyle`
- `BusType`
- `IsBoot`
- `IsSystem`
- `IsOffline`
- `OperationalStatus`
- `HealthStatus`

### Partição

- `PartitionNumber`
- `DriveLetter`
- `Size`
- `Type`

### Volume

- `FileSystem`
- `Label`
- `SpaceRemaining`

## Política de atualização

Sem polling contínuo. Fluxo por evento:

1. operação executada;
2. delay controlado;
3. novo snapshot;
4. comparação estrutural;
5. atualização de estado/UI.

## Máquina de estados de disco

Estados arquiteturais:

- `NOT_INITIALIZED`
- `RAW`
- `WRONG_PARTITION_STYLE`
- `WRONG_FILESYSTEM`
- `READY_FOR_OPL`
- `OPL_INSTALLED`
- `POPSTARTER_INSTALLED`
- `INVALID_DISK`
- `SYSTEM_DISK`

Regra: UI nunca decide regras de negócio.

## Segurança de mídia

Bloqueios automáticos:

- disco de sistema;
- disco de boot;
- unidade `C:`;
- `GPT` incompatível com política;
- device offline;
- volume protegido.

## Pipeline hierárquico

`Evento do Usuário -> Controller -> Policy Engine -> Snapshot Validation -> Worker Executor -> Mutação Física -> Post Verification Snapshot -> State Machine Update`

## Estratégia de formatação

Módulo de formatação é exclusivo para preparo físico:

- criar partição;
- definir filesystem;
- não instalar software.

Motores:

- **Windows nativo:** preferencial.
- **FAT32 externo:** obrigatório para FAT32 > 32GB ou falha nativa.

Ferramenta sugerida: `fat32format.exe`.

## Fluxo oficial FAT32 externo

1. criar partição por `DiskNumber`;
2. refresh snapshot;
3. detectar `DriveLetter` real;
4. validar acesso;
5. executar formatador externo;
6. aguardar retorno;
7. refresh snapshot;
8. confirmar filesystem final.

## Instalação OPL / PopStarter

### OPL

Pré-condições:

- `MBR`;
- filesystem compatível;
- volume validado;
- estado `READY_FOR_OPL`.

Estrutura:

- `CD/`
- `DVD/`
- `CFG/`
- `ART/`
- `THM/`

### PopStarter

Opcional. Requer:

- estrutura base existente;
- pasta `POPS/`.

## Modelo de execução de workers

Workers PowerShell são atuadores:

- vida curta;
- sem decisão própria;
- sem persistência;
- apenas execução operacional.

## Vigilante observador

Processo efêmero para:

- monitorar execução;
- registrar caminho do pipeline;
- detectar desvios estruturais;
- reportar superior hierárquico.

Nunca interfere na execução.

## Regra de ouro do pipeline destrutivo

`Validate -> Lock -> Execute -> Verify -> Commit -> Release`

## Logging e auditoria

- rotação de logs;
- compressão GZIP;
- contexto de origem;
- arquivo separado para erros críticos;
- configuração via `LOG_LEVEL`.

## Recuperação de falhas

Ao falhar:

1. validar integridade estrutural;
2. liberar locks;
3. revalidar snapshot;
4. reportar erro formal.

## Diretrizes absolutas

- determinismo operacional;
- serialização da mutação de disco;
- snapshot pós-operação obrigatório;
- isolamento de workers;
- identidade física como fonte de verdade.

## Estado técnico atual

- arquitetura: definida;
- pipeline: parcialmente integrado;
- snapshot core: planejado/crítico;
- watchdog de convergência: próximo passo;
- segurança: alta;
- observabilidade: em expansão.

## Próximas evoluções sugeridas

- guardian de identidade física;
- snapshot autoritativo formal;
- watchdog de convergência storage;
- replay forense de execução;
- trilha de auditoria de decisão.


## Blindagem máxima do pipeline determinístico

Para reduzir janelas temporais de falha silenciosa, o pipeline operacional deve executar em estágios explícitos e auditáveis:

1. `VALIDATE` (snapshot autoritativo + guardrails de segurança);
2. `LOCK` (seleção exclusiva de alvo);
3. `EXECUTE` (mutação física serializada);
4. `VERIFY` (snapshot pós-operação + comparação estrutural);
5. `COMMIT` (aceitação formal do resultado);
6. `RELEASE` (liberação de lock e limpeza de contexto).

Qualquer desvio interrompe o fluxo e dispara recuperação formal.

## Guardian de identidade física (formalização)

O guardian atua como sentinela determinística observacional durante todo o ciclo:

- observa identidade inicial (`DiskNumber`, `SerialNumber`, `PartitionStyle`, `DeviceStatus`);
- detecta deriva estrutural/identitária após mutação;
- reporta sinais forenses para a camada superior;
- nunca decide commit, nunca corrige, nunca executa mutação.

## Redução de superfície de falha silenciosa

Diretrizes mandatórias:

- sem fallback implícito para estados desconhecidos;
- erros estruturais sempre promovidos para exceção formal;
- snapshot ausente pós-operação tratado como falha crítica;
- confirmação explícita de `Status=COMPLETED` antes de commit.

## Modelo de auditoria forense de execução

Todo passo relevante do pipeline deve ser persistido em trilha append-only com:

- timestamp monotônico;
- evento;
- payload contextual (`disk`, `filesystem`, estado de validação, erro).

Eventos mínimos recomendados:

- `SNAPSHOT_REFRESH`
- `SELECTION_LOCKED` / `SELECTION_BLOCKED`
- `PIPELINE_EXECUTE_START`
- `PIPELINE_VERIFY_OK`
- `PIPELINE_COMMIT_RELEASE`
- `PIPELINE_FAILURE`
- `PIPELINE_RECOVERY`


## Guardian de Integridade Física — versão balanceada

Contrato de operação:

- `observe(snapshot)`
- `detect_identity_violation(before, after)`
- `report(event)`
- `shutdown()`

Restrições absolutas:

- não formata disco;
- não cria partição;
- não instala software;
- não gerencia lock;
- não executa recovery;
- não altera decisões do pipeline.

Padrão: **Detectar -> Reportar -> Silenciar**.

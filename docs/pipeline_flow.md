# Pipeline Flow — Freeze Técnico

## Etapas da operação
1. **Seleção de disco**
   - Controller aplica política de elegibilidade e lock de operação.
2. **Execução do worker**
   - Service chama runner com argumentos de identidade do disco.
3. **Captura IPC**
   - Service valida stdout, JSON e contrato mínimo de retorno.
4. **Verify do controller**
   - Controller valida estado observado: MBR, partição, volume, drive letter, filesystem e block size (quando aplicável).
5. **Commit barrier**
   - Pequena espera + refresh + reconfirmação mínima de estabilidade.
6. **READY evaluation**
   - Evaluator decide prontidão mínima conservadora com base em evidência de snapshot.
7. **Auditoria forense**
   - Eventos append-only com contexto operacional e códigos de erro.

## Observações operacionais
- verify é a validação forte pós-execução.
- READY é um estado conservador mínimo; não substitui verify.
- falhas de execução (runner/service) não devem ser mascaradas como verify.

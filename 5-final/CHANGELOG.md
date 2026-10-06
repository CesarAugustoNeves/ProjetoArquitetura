# Changelog

Registro das mudanças aceitas após leitura cruzada. Cada entrada remete à objeção que a motivou (`4-leitura-cruzada/respostas-recebidas.md`) e ao ADR afetado. Em estrita obediência às regras de governança da disciplina: ADR aceito não se edita; substitui-se.

### Adicionado
- **ADR 0006**: separa o dado de identificação do paciente (mutável) do fluxo de eventos clínicos do prontuário (imutável), e define versionamento para os eventos clínicos para guarda de 20 anos. **Substitui a ADR 0004**. Origem: objeções 4 e 7.
- **ADR 0007**: mitiga o custo operacional de N células instituindo um time de plataforma, template único de IaC, provisionamento por onda e teto de novas células por sprint. **Substitui a ADR 0001**. Origem: objeção 3.
- **ADR 0008**: institui etapa explícita de levantamento e validação prévia das regras do legado antes da migração, esclarecendo a desativação da interface nativa legada por capacidade. **Substitui a ADR 0002**. Origem: objeções 1 e 5.
- **ADR 0009**: distribui a integração federal como biblioteca versionada comum, mantendo execução estritamente isolada por célula em tempo de execução. **Substitui a ADR 0003**. Origem: objeção 6.
- **ADR 0010**: implementa telemetria dedicada de volume e tempo de retenção da fila local das UBSs com alerta autônomo de represamento. **Substitui a ADR 0005**. Origem: objeção 8.

### Alterado
- `respostas-às-cinco-perguntas-obrigatórias-do-caso.md` (Pergunta 2): reescrita para esclarecer que a exclusividade do módulo novo de escrita aplica-se apenas a capacidades já migradas, mantendo o legado como autoridade única nas não migradas. Origem: objeção 1.
- `3-spike/exemplo.py`: isolou a triagem da UPA em persistência local offline-first (imune a saturação de rede) e implementou provisionamento automático de nova célula por tenant no gateway sob saturação central, eliminando descarte HTTP 429. Origem: objeção 2.
- `3-spike/saida-esperada.txt`: arquivo regenerado com a saída determinística do novo script, comprovando a elasticidade celular e a ausência de rejeições.

### Status alterado
- `adr/0001`: status alterado para **substituída pela ADR 0007**.
- `adr/0002`: status alterado para **substituída pela ADR 0008**.
- `adr/0003`: status alterado para **substituída pela ADR 0009**.
- `adr/0004`: status alterado para **substituída pela ADR 0006**.
- `adr/0005`: status alterado para **substituída pela ADR 0010**.

### Considerado e não adotado
- **Saga com reserva pendente no legado**: rejeitada pois o estrangulamento com autoridade exclusiva por capacidade (ADR 0008) já impede concorrência. Sagas reintroduziriam consistência eventual em operação clínica crítica (risco de dupla reserva). Registrada na ADR 0008. Origem: objeção 1.
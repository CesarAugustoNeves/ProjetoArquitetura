# Changelog

Registro das mudanças aceitas após leitura cruzada. Cada entrada remete à
objeção que a motivou (`4-leitura-cruzada/respostas-recebidas.md`) e ao ADR
afetado. Mudança que substitui a decisão de um ADR aceito gera um ADR novo;
mudança que só acrescenta detalhe ou mitigação fica registrada como
atualização no próprio ADR.

### Adicionado
- **ADR 0006** (nova): separa dado de identificação do paciente (mutável,
  corrigível) do fluxo de eventos clínicos do prontuário (imutável), e define
  mecanismo de versionamento para os eventos clínicos ao longo dos 20 anos de
  guarda. **Substitui a ADR 0004** nesses dois pontos. Origem: objeções 4 e 7.
- `adr/0001`: mitigação de custo operacional para N células — template único
  de célula, provisionamento automatizado por onda, teto de células novas por
  sprint sob um time de plataforma. Origem: objeção 3.
- `adr/0002`: etapa explícita de levantamento e validação das regras do
  legado, por capacidade, antes da tentativa de migração (não só verificação
  depois). Origem: objeção 5.
- `adr/0005`: monitoramento de quantidade e tempo de espera da fila local de
  atendimentos pendentes por UBS, com alerta próprio, separado do alerta de
  disjuntor aberto. Origem: objeção 8.

### Alterado
- `adr/0002`: esclarecido que "desligar o trecho correspondente do legado"
  ao migrar uma capacidade inclui redirecionar ou desativar o acesso direto
  das unidades à interface nativa do legado para aquela capacidade, não só o
  caminho que passa pela fachada. Origem: objeção 1.
- `adr/0003`: a lógica de integração com cada sistema federal passa a ser
  distribuída como biblioteca/componente versionado comum entre células, mas
  continua **executando isolada dentro de cada célula** — nunca como serviço
  compartilhado em tempo de execução. A garantia de isolamento de falha da
  ADR 0003 não muda; muda só como o código é construído e distribuído.
  Origem: objeção 6.
- `respostas-às-cinco-perguntas-obrigatórias-do-caso.md` (Pergunta 2):
  reescrita para deixar explícito que a exclusividade do módulo de escrita
  novo vale por capacidade já migrada, não para todas as reservas desde o
  primeiro dia da transição. Origem: objeção 1.
- `3-spike/exemplo.py`: separa o caminho de triagem local (sempre aceito,
  nunca sujeito a rejeição por capacidade do backend) do caminho de operação
  central sujeita a saturação; a saturação de uma célula passa a provisionar
  nova célula, alinhado à ADR 0001 e à seção 13.2 do livro, em vez de só
  devolver `HTTP 429`. Origem: objeção 2.

### Status alterado
- `adr/0004`: status passa de **aceito** para **substituída pela ADR 0006**
  nos pontos de modelo de dado e versionamento de evento. O texto original é
  mantido como registro histórico da decisão e do contexto em que foi tomada.

### Considerado e não adotado
- Saga com reserva pendente e confirmação prévia no legado, para a reserva de
  leitos (objeção 1): rejeitada porque a ADR 0002, aplicada corretamente, já
  impede dois autorizadores concorrentes por capacidade, e uma Saga
  reintroduziria a consistência eventual que a matriz já havia descartado
  para essa operação (cap. 9.2). Registrada como alternativa descartada na
  ADR 0002.

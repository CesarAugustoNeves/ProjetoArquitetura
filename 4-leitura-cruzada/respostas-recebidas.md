# Respostas às objeções do Grupo 5

Objeções recebidas em `padroes-e-arquitetura-grupo-5/4-leitura-cruzada/Objeções ao grupo 09.md`. Uma resposta por objeção: aceitamos e dizemos o que muda, ou rebatemos com argumento.

---

## 1 — Reserva de leitos vs. legado (overbooking)

**Veredito: aceitamos em parte.**

O argumento tem razão num ponto preciso: a Pergunta 2 diz "toda reserva nova passa por um único ponto", e essa frase generaliza demais. Isso só é verdade para as capacidades **já migradas**. Vamos reescrever a resposta para deixar isso explícito: durante a transição, há duas fontes de verdade, uma por capacidade, nunca as duas ao mesmo tempo para a mesma capacidade.

Mas a saída proposta — Saga com reserva pendente e confirmação prévia no legado — não é a que vamos adotar, porque o próprio ADR 0002 já resolve o problema de um jeito mais forte, e a Saga seria um retrocesso. O ADR diz: *"uma capacidade só é considerada migrada, e o trecho correspondente do legado desligado, quando o novo sistema comprovar, por função de aptidão, que nenhum leito foi reservado duas vezes durante a transição"*. Ou seja: antes da verificação, o legado continua sendo a única autoridade para aquela capacidade (exatamente a primeira saída que vocês sugerem — chamada síncrona com trava na ACL, que é o que `chamada: reserva no legado, com disjuntor` já representa no componente); depois da verificação, o caminho antigo para aquela capacidade especificamente é desligado, então não sobra um segundo escritor. Uma Saga com reserva pendente reintroduziria consistência eventual numa operação que a nossa própria matriz descartou para isso (cap. 9.2: Sagas aumentam o risco de internação duplicada), sem necessidade, já que o ADR 0002 já impede os dois autorizadores concorrentes.

**O que muda:** vamos deixar explícito no ADR 0002 que "desligar o trecho correspondente do legado" inclui redirecionar ou desativar o acesso direto das unidades à interface nativa do legado para aquela capacidade — não só o caminho que passa pela nossa fachada. Era essa lacuna, não a falta de um mecanismo novo, que deixava a objeção de vocês de pé.

---

## 2 — Load shedding em urgência (HTTP 429)

**Veredito: aceitamos em parte, e corrigimos uma leitura.**

Primeiro, uma correção: o `HTTP 429` existe só no spike (`exemplo.py`), uma prova de conceito simplificada — não é o comportamento real da triagem. Na arquitetura de verdade, o registro de triagem é sempre gravado **localmente primeiro**, pelo Cliente Local (Desktop/SQLite), que é hexagonal e não depende da rede nem da capacidade do backend. Um médico nunca vê a ficha rejeitada na tela por sobrecarga do lado do servidor, porque o servidor nem entra nesse caminho — a ficha já foi salva no dispositivo da unidade. Isso é mais forte que a fila na borda que vocês sugerem (`202 Accepted`), porque sobrevive a uma queda total de rede, não só a uma sobrecarga do backend — e queda de rede, não sobrecarga, é o cenário que o Envelope D descreve para a UPA.

Onde aceitamos o ponto: o spike conflou "evento de triagem" e "chamada síncrona central" num único `Request` genérico, o que faz parecer que a triagem em si pode ser rejeitada. Vamos corrigir o spike para separar os dois caminhos.

Onde não aceitamos a generalização: para operações que **exigem** resposta imediata e exclusiva — reserva de leito é o exemplo central do nosso caso — enfileirar com `202 Accepted` e responder depois pode ser pior que falhar rápido. Uma reserva "aceita" que demora a ser processada passa a sensação de leito garantido quando ele ainda não está garantido, o que é mais perigoso clinicamente do que um sinal imediato de "capacidade esgotada, use o caminho manual". Isso é coerente com o próprio cap. 18 (falhar rápido para lentidão de dependência).

**O que muda:** o spike passa a modelar dois caminhos (triagem local, sempre aceita; operação central, com o mecanismo correto do ADR 0001, item abaixo), e o load shedding deixa de existir para a triagem, mas segue existindo, como válvula de segurança explícita, para reserva síncrona em capacidade saturada.

---

## 3 — N pessoas da equipe vs. células

**Veredito: aceitamos.**

Correto, e a nossa própria ADR 0001 já admite o custo sem propor mitigação: *"N instalações completas para operar, observar e atualizar em vez de uma"*. A Tabela 13.2 do livro (seção 13.7) também já descreve esse custo na dimensão "Operação" e "Time", então não é uma lacuna só nossa — é um custo real do estilo que faltava endereçar.

**O que muda:** adicionamos à ADR 0001 (seção de consequências) a mitigação que vocês propuseram: infraestrutura como código com um template único de célula, provisionamento automatizado por onda (reaproveitando a disciplina de ondas que já existe na ADR 0005) e um teto explícito de células novas por sprint, sob responsabilidade de um time de plataforma. Vamos registrar também o custo que isso implica: tirar pessoas do produto para sustentar operação, como vocês apontaram.

---

## 4 — Correção de dados do prontuário (LGPD, Art. 18, III)

**Veredito: aceitamos.**

Vocês têm razão: a ADR 0004 tratou só do direito de acesso, porque é o que o Caso pede explicitamente, mas a LGPD garante também o direito de correção de dado incompleto ou inexato (Art. 18, III), independente do prazo de retenção, e isso não tem nada a ver com guarda de 20 anos — é sobre corrigir um CPF ou nome digitado errado. Tratar isso como fato clínico imutável nos obrigaria a reescrever o passado ou conviver com o erro por 20 anos, o que não faz sentido para dado de identificação.

Aliás, isso é consistente com uma alternativa que a própria ADR 0004 já tinha descartado por um motivo parecido: *"Aplicar event sourcing ao sistema inteiro... descartada porque generaliza o estilo além do contexto que o justifica"*. Vocês mostraram que a generalização indevida aconteceu dentro do próprio módulo de prontuário, não só entre subdomínios.

**O que muda:** separamos dado de identificação (mutável, numa tabela de estado comum, corrigível por comando direto) do fluxo de eventos clínicos (imutável, como já era). O event sourcing fica só para fato clínico. Custo assumido: dois modelos de dado dentro do mesmo módulo de Prontuário, como vocês descreveram.

---

## 5 — Regras internas do legado não documentadas

**Veredito: aceitamos.**

A própria ADR 0002 admite isso: *"Não há registro público das regras internas do legado além do que a operação observa em produção"*. O risco é real e se multiplica por município, porque cada prefeitura pode ter customizado o legado de um jeito diferente ao longo dos anos.

**O que muda:** adicionamos à ADR 0002 uma etapa explícita de **levantamento e validação antes de migrar cada capacidade** (não só depois, como verificação): observar o legado em produção, converter o comportamento observado em testes de aptidão, e só então iniciar a migração daquela capacidade naquele município. Isso é esforço adicional por capacidade e por cliente, como vocês apontaram, mas reduz o risco de regra escondida aparecer só depois do corte.

---

## 6 — Integração federal duplicada por célula

**Veredito: aceitamos.**

Ponto bom: a ADR 0003 diz que o caso usa a integração federal "da mesma forma" em todos os municípios, então manter a implementação inteira duplicada em N células é esforço de manutenção redundante sem ganho de isolamento adicional — o isolamento já vem de cada célula rodar sua própria instância, não de cada célula ter um código diferente.

**O que muda:** a lógica de integração federal passa a ser distribuída como biblioteca/componente versionado comum, mas continua sendo **executada dentro de cada célula**, nunca como serviço compartilhado em tempo de execução — isso preserva o isolamento de falha que a ADR 0003 existe para garantir. Custo assumido: versionar, distribuir e atualizar essa biblioteca de forma coordenada entre células.

---

## 7 — Versionamento de eventos clínicos por 20 anos

**Veredito: aceitamos.**

A ADR 0004 já lista isso como consequência negativa sem detalhar como resolver: *"a equipe precisa versionar o formato dos eventos clínicos por até 20 anos"*. Sem um mecanismo explícito, isso vira dívida técnica que só aparece como problema quando já for tarde.

**O que muda:** adicionamos à ADR 0004 um mecanismo explícito de versionamento de evento (envelope de evento com número de versão + funções de conversão entre versões), testes de compatibilidade entre versões a cada mudança de esquema, e uma política de arquivamento para formatos muito antigos. Custo assumido: desenvolvimento, armazenamento e manutenção desses testes, como vocês descreveram.

---

## 8 — Disjuntor das UBS com poucas tentativas

**Veredito: aceitamos em parte.**

Rebatemos o ponto central: o disjuntor não usa um limite fixo arbitrário — a decisão já diz *"tempo limite curto **derivado da latência observada**"*, ou seja, calibrado empiricamente por ambiente, não um número de catálogo igual para toda UBS. Então o risco de confundir instabilidade transitória com queda real já é, em princípio, menor do que a objeção sugere.

Mas aceitamos a parte concreta: não tínhamos nada que monitorasse o **tamanho e a idade da fila local de pendências** enquanto o disjuntor está aberto — e isso importa especialmente no pico sazonal que o próprio Envelope D descreve, quando a fila pode crescer rápido.

**O que muda:** adicionamos à ADR 0005 o monitoramento explícito de quantidade e tempo de espera dos atendimentos pendentes por UBS durante a abertura do disjuntor, com alerta separado de acúmulo (diferente do alerta de disjuntor aberto), para diferenciar "rede instável, mas o volume represado está sob controle" de "rede instável e o volume represado está virando risco".

---

## Resumo do que muda nos artefatos

| Arquivo | Mudança |
| --- | --- |
| `respostas-às-cinco-perguntas-obrigatórias-do-caso.md` (Pergunta 2) | Reescrever para deixar explícito que a exclusividade do módulo novo vale por capacidade migrada, não universalmente |
| `adr/0002-...md` | Explicitar que desligar uma capacidade inclui o acesso direto à UI do legado; adicionar etapa de levantamento/validação antes da migração de cada capacidade |
| `adr/0001-...md` | Adicionar mitigação de custo operacional: template de célula, provisionamento por onda, teto de células por sprint |
| `adr/0004-...md` | Separar dado de identificação (mutável) do fluxo de eventos clínicos (imutável); adicionar versionamento de evento, testes de compatibilidade e política de arquivamento |
| `adr/0003-...md` | Mudar implementação para biblioteca versionada comum, mantendo execução isolada por célula |
| `adr/0005-...md` | Adicionar monitoramento de fila de pendências por UBS durante disjuntor aberto |
| `3-spike/exemplo.py` | Separar triagem local (sempre aceita) de operação central (sujeita a backpressure); alinhar saturação de célula com "cria-se outra célula" em vez de só rejeitar |

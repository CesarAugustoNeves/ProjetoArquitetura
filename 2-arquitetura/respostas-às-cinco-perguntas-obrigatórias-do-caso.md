## Respostas às Cincos Perguntas Obrigatórias

### 1. Como a UPA continua triando e atendendo com a internet fora do ar, e o que acontece quando ela volta?

A UPA continua realizando a triagem e o atendimento mesmo quando a internet está indisponível. O atendimento é registrado localmente pelo **Cliente Local Atendimento [Desktop/SQLite]** (diagrama de contêineres), que se comunica com o **Módulo Triagem e Atendimento [hexagonal: portas e adaptadores]** (diagrama de componentes). Como as regras de triagem ficam isoladas da tecnologia de rede, elas operam sem depender da conectividade. 

Conforme definido no **ADR 0005**, o sistema utiliza *timeout* para limitar o tempo de espera por uma conexão, evitando o bloqueio da aplicação e liberando rapidamente a interface para o usuário. Além disso, é utilizado o padrão *Circuit Breaker*. Ao identificar falhas recorrentes de comunicação, o sistema interrompe temporariamente novas tentativas de conexão por um período definido, permitindo que a aplicação continue operando localmente e armazenando os dados gerados.

Quando a conexão é restabelecida, o *Circuit Breaker* permite novamente as tentativas de comunicação. O cliente sincroniza a fila local via `[TCP] Sincroniza fila local quando a internet volta` para o Gateway, que entrega os dados como evento: `sincroniza atendimentos ao módulo de Triagem`. A entrada por sincronização idempotente do módulo garante que o reenvio do mesmo lote não duplique atendimentos.

Esse funcionamento é complementado por outros dois ADRs:
* **ADR 0003 (Outbox):** garante que a notificação seja registrada na mesma transação do evento clínico e armazenada localmente até que a conexão seja restabelecida, evitando a perda de notificações.
* **ADR 0004 (Event Sourcing):** registra cada ação clínica como um evento imutável associado ao fluxo do paciente, preservando a ordem dos acontecimentos e permitindo a reconciliação temporal dos dados após a recuperação da conexão.

Dessa forma, a indisponibilidade da internet não interrompe o atendimento: a UPA continua operando localmente e, quando a conectividade retorna, os dados pendentes são sincronizados de forma controlada e rastreável.


### 2. Como duas unidades disputando o mesmo leito nunca conseguem reservá-lo ao mesmo tempo, com o legado ainda no circuito?

Durante a transição, cada capacidade de reserva (leito de UPA, leito eletivo, transporte) tem exatamente uma fonte de verdade por vez — nunca duas simultaneamente para a mesma capacidade, mas qual sistema é essa fonte muda conforme o status de migração daquela capacidade específica:

Capacidade ainda não migrada: o sistema legado é a única fonte de verdade. **O Módulo Regulação de Leitos e Transporte [CQRS: modelo de escrita]** não decide a reserva sozinho — ele chama o legado de forma síncrona (chamada: reserva no legado, com disjuntor), via Camada Anticorrupção do Serviço de Integração Externa, e repassa a resposta do legado. Isso evita um segundo escritor: o novo sistema nunca confirma uma reserva que o legado não confirmou primeiro.
Capacidade já migrada: aí sim o Módulo Regulação de Leitos e Transporte vira o único ponto responsável por confirmar ou recusar a reserva — mas só porque, ao migrar, o acesso direto das unidades à interface nativa do legado para aquela capacidade é redirecionado ou desativado (ADR 0002). Sem esse fechamento, as unidades ainda poderiam reservar direto no legado por fora do novo sistema, e aí existiriam dois escritores ao mesmo tempo.

Em nenhum momento da transição as duas coisas acontecem juntas para a mesma capacidade: ou é o legado (com acesso direto ainda aberto), ou é o módulo novo (com acesso direto já fechado) — nunca os dois.

As consultas de disponibilidade usam a **Projeção de Vagas [CQRS: modelo de leitura]**, mantida separada da escrita, para que nenhuma unidade decida reservar com base em painel desatualizado. E, antes de qualquer capacidade ser migrada, suas regras são levantadas e convertidas em testes de aptidão (ADR 0008) — reduzindo o risco de uma regra de prioridade clínica desconhecida do legado aparecer só depois do corte.

**Sustentado por:** ADR 0001 (arquitetura celular) · ADR 0002 (*estrangulamento + camada anticorrupção, incluindo o fechamento do acesso direto ao legado por capacidade migrada*) · ADR 0005 (disjuntor na chamada) · ADR 0008 (validação prévia por capacidade) · Diagrama de componentes (*Módulo Regulação de Leitos*, *Projeção de Vagas*) · Diagrama de contêineres (*Serviço de Integração Externa → Sistema de Regulação Legado*).


### 3. Como o prontuário garante que se saiba quem acessou cada registro, e como isso convive com a guarda de 20 anos sob a LGPD?

Cada fato clínico é gravado como um evento imutável pelo **Módulo Prontuário [Event Sourcing]**, diretamente no **Repositório de Longa Guarda [WORM]** (*write-once, read-many*). Dessa forma, a informação de "quem alterou" nunca pode ser reescrita ou apagada, apenas acrescida.

Toda leitura — seja feita por um profissional de saúde ou pelo próprio paciente exercendo seu direito de acesso previsto pela LGPD — passa pela **Projeção do Prontuário [modelo de leitura]**, que alimenta o **Registro de Auditoria** por meio da instrução `chamada: registra quem viu`. 

Ou seja: a identificação de "quem escreveu" deriva do próprio fluxo de eventos (*Event Sourcing*), enquanto a informação de "quem leu" deriva desse log de auditoria separado. Nenhum dos dois mecanismos interfere no cumprimento do prazo de retenção legal de 20 anos.

* **Sustentado por:** ADR 0004 (Event Sourcing + log de acesso à parte) · Diagrama de componentes (*Módulo Prontuário*, *Projeção do Prontuário*, *Registro de Auditoria*) · Diagrama de contêineres (*Repositório de Longa Guarda [WORM]*).


### 4. Como a notificação compulsória chega à vigilância em até 24h mesmo com o sistema federal indisponível?

O **Publicador de Eventos [padrão Outbox]** grava o evento `notificação compulsória` na mesma transação em que o fato clínico é registrado. Assim, a notificação nunca é perdida em razão de uma falha na chamada externa.

O **Serviço de Integração Externa** consome esse evento do barramento e realiza tentativas contínuas de reenvio ao sistema federal — fluxo representado pela etiqueta `[HTTPS] Reenvia notificações retidas no Outbox` no diagrama de contêineres. Como essa fila reside dentro da própria célula do município, uma indisponibilidade federal prolongada acumula pendências exclusivamente para a cidade afetada, sem impactar as notificações dos demais municípios.

* **Sustentado por:** ADR 0003 (Outbox isolado por célula) · Diagrama de componentes (*Publicador de Eventos*) · Diagrama de contêineres (*Serviço de Integração Externa* $\rightarrow$ *Sistemas Federais de Saúde*).


### 5. Como o legado de regulação é substituído aos poucos sem interromper o serviço?

A substituição ocorre capacidade por capacidade, atuando atrás da **Camada Anticorrupção** dentro do **Serviço de Integração Externa** (representado no diagrama de contêineres como `[SOAP/HTTPS] Sincroniza leitos via Camada Anticorrupção`). Enquanto uma capacidade não for migrada, o sistema legado continua sendo acionado com suporte a disjuntor a cada reserva (a mesma instrução `chamada: reserva no legado, com disjuntor` citada na Pergunta 2).

Uma capacidade só é definitivamente desligada do legado após uma **função de aptidão** (*fitness function*) comprovar zero reservas duplicadas durante o período de observação, evitando uma virada única (*Big Bang*).

* **Sustentado por:** ADR 0002 (migração por capacidade + função de aptidão) · Diagrama de contêineres (*Serviço de Integração Externa*) · Diagrama de componentes (*chamada com disjuntor ao legado*).
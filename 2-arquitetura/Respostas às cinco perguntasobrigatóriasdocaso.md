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

Toda reserva nova passa por um único ponto: o **Módulo Regulação de Leitos e Transporte [CQRS: modelo de escrita]**, que é o único componente responsável por confirmar ou recusar uma reserva. As consultas de disponibilidade utilizam a **Projeção de Vagas [CQRS: modelo de leitura]**, mantida de forma separada, garantindo que nenhuma unidade decida reservar com base em um painel desatualizado.

Para leitos ainda não migrados, o próprio módulo de escrita chama o sistema legado de forma síncrona por meio da instrução `chamada: reserva no legado, com disjuntor`, via **Camada Anticorrupção** do **Serviço de Integração Externa**, o que mantém o legado como fonte da verdade enquanto aquela capacidade específica não for migrada.

Adicionalmente, o fato de o sistema ser construído utilizando **Arquitetura Celular por Município (ADR 0001)** auxilia na independência em relação a filas, cache e banco de dados.

* **Sustentado por:** ADR 0001 (arquitetura celular) · ADR 0002 (estrangulamento + camada anticorrupção) · ADR 0005 (disjuntor na chamada) · Diagrama de componentes (*Módulo Regulação de Leitos*, *Projeção de Vagas*) · Diagrama de contêineres (*Serviço de Integração Externa* $\rightarrow$ *Sistema de Regulação Legado*).


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
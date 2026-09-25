# Leitura Cruzada

### Objeção 1:  O "Outbox" não é realmente um Outbox e pode perder a trilha de auditoria

*Trecho atacado:* Diagrama de Contêineres (Nível 2), nas relações entre `Monólito → db_audit` ("Grava Trilha", via TCP) e `Monólito → broker` ("Publica eventos / Outbox", via AMQP), repetidas no Nível 3 pela relação `mod_pronto → db_audit` ("Gera Evento de Auditoria", via TCP) e na Resposta 5, que afirma que "esse evento é salvo assincronamente em um Event Store".

*Argumento:* O livro (cap. 11.2) define o padrão Outbox como a gravação do evento na mesma tabela e na mesma transação da mudança de estado, para que a publicação possa ocorrer posteriormente sem risco de perder o evento. No desenho apresentado, porém, `db_core` (Postgres) e `db_audit` (EventDB) são sistemas distintos e recebem gravações separadas, sendo uma delas assíncrona. Se o processo cair entre essas duas escritas, a dispensação ou alteração do prontuário pode ser efetivada enquanto o respectivo evento de auditoria não é registrado. Isso cria uma lacuna justamente no requisito do Envelope E de que "tudo que acontece precisa ser reconstruível". Portanto, o problema não é apenas de nomenclatura: chamar esse mecanismo de "Outbox" não corresponde ao padrão descrito no livro.

*O que faríamos no lugar:* Gravaríamos o evento de auditoria no mesmo banco e na mesma transação do módulo que produziu a mudança, como fizemos com o publicador de eventos do nosso núcleo. Um processo separado faria a leitura desses eventos e sua publicação posterior. As bases operacional e de auditoria poderiam continuar separadas, mas a garantia de que uma mudança de estado gera seu respectivo evento não dependeria de duas escritas de rede sem atomicidade.

### Objeção 2:  A reserva de leito mantém uma trava de banco enquanto espera uma dependência externa

*Trecho atacado:* Resposta 3 e ADRs 02/03, que descrevem o uso de `SELECT FOR UPDATE` para reservar o leito e, dentro da mesma operação, uma chamada síncrona pela Anti-Corruption Layer (ACL) para verificar a disponibilidade no sistema legado. O texto afirma ainda que, em caso de falha, a transação local realiza rollback imediato.

*Argumento:* O cap. 18.4 trata o timeout como elemento obrigatório de resiliência porque uma dependência lenta pode ser tão problemática quanto uma dependência indisponível: quem chama permanece bloqueado até esgotar seus recursos. O texto apresentado trata apenas do caso em que o legado falha, mas não do caso em que ele simplesmente demora para responder. Nesse cenário, a trava criada pelo `SELECT FOR UPDATE` permanece aberta durante toda a espera pela resposta externa, fazendo com que outras tentativas de reservar o mesmo leito aguardem atrás dela. A instabilidade de um sistema legado já descrito como problemático passa, assim, a afetar diretamente a disponibilidade da própria regulação. Além disso, os ADRs mencionam filas e retentativas nos fluxos assíncronos, mas não estabelecem timeout ou disjuntor para essa chamada síncrona específica.

*O que faríamos no lugar:* Manteríamos a chamada síncrona pela ACL, mas estabeleceríamos explicitamente timeout e circuit breaker para a comunicação com o legado, como fizemos na nossa Integração. Dessa forma, uma trava de banco nunca ficaria condicionada indefinidamente ao tempo de resposta de um sistema externo.

### Objeção 3: O frontend acessa diretamente o broker e contorna o ponto central de autenticação

*Trecho atacado:* Diagrama de Contêineres (Nível 2), na relação `SPA → broker`, descrita como "Sincronia Offline-First" via WebSockets/MQTT, em contraste com a Resposta 2, que afirma que "o Front-end despacha o pacote de dados para o API Gateway que, por sua vez, insere esses eventos no Message Broker".

*Argumento:* O documento apresenta duas topologias diferentes para o mesmo fluxo: em uma, o frontend fala diretamente com o broker; na outra, passa pelo API Gateway. Essa diferença não é apenas de nomenclatura, pois altera o caminho de entrada dos dados no sistema. O problema fica mais relevante porque o próprio documento atribui ao API Gateway a responsabilidade pela autenticação central e pela terminação SSL. Se o PWA realmente se conecta diretamente ao broker por WebSocket/MQTT, os eventos clínicos podem entrar sem passar por essa borda de autenticação. Em um sistema sujeito à fiscalização regulatória e que exige uma trilha de auditoria completa, essa diferença precisa estar resolvida no desenho, pois muda diretamente o ponto em que identidade, autenticação e controle de acesso são aplicados.

*O que faríamos no lugar:* Faríamos toda entrada do cliente, seja síncrona ou assíncrona, passar pelo gateway. Foi essa a abordagem que adotamos: o aplicativo da unidade se comunica com o gateway, e é o gateway que publica no barramento. O cliente nunca acessa o broker diretamente.

### Objeção 4:  O crypto-shredding cobre apenas o Event Store, mas a retenção de 20 anos também envolve o prontuário operacional

*Trecho atacado:* ADR 05 e Resposta 1, que afirmam que os Dados Pessoais Identificáveis (PII) do paciente no Event Store serão criptografados e que, para apagá-los, "apagamos a chave", mantendo os registros históricos no banco.

*Argumento:* O próprio Envelope E questiona como o sistema pode manter os dados pelo período exigido e, ao mesmo tempo, apagar aquilo que a legislação determinar. O `db_core`, especialmente o schema `schema_prontuario`, também contém dados pessoais e participa da operação do prontuário durante o período de retenção. Entretanto, o ADR 05 não esclarece se o PII armazenado no `db_core` também está protegido por uma chave específica ou se permanece em texto claro. Se estiver em texto claro, destruir a chave do KMS utilizada pelo Event Store não elimina o dado pessoal que continua legível na base operacional. A resposta à questão de retenção e eliminação, portanto, fica incompleta justamente porque trata apenas de um dos locais onde o PII é armazenado.

*O que faríamos no lugar:* Aplicaríamos a estratégia de destruição criptográfica aos dois pontos em que o PII é persistido, conforme a abordagem apresentada no cap. 15.7, ou declararíamos explicitamente uma separação entre os dados operacionais e os identificadores pessoais. O importante seria deixar documentado como o mesmo requisito de retenção e eliminação é atendido tanto no Event Store quanto no prontuário operacional.

### Objeção 5:  CQRS aparece na matriz, mas não existe como arquitetura nos diagramas

*Trecho atacado:* `matriz.md`, na linha de CQRS, que o associa às "Consultas do portal cidadão, painéis de gestão e leituras analíticas da vigilância", em contraste com os diagramas de Níveis 2 e 3 e com a Resposta 5, que descreve apenas a alteração do estado atual no schema relacional como "CQRS simplificado".

*Argumento:* A matriz apresenta CQRS como justificativa para três contextos de leitura diferentes, mas nenhum modelo ou componente de leitura separado aparece nos diagramas. O desenho mostra apenas `db_core`, como base transacional, e `db_audit`. Além disso, a única ocorrência de "CQRS" na descrição arquitetural está associada a uma escrita comum no schema relacional. Isso não corresponde ao conceito apresentado no cap. 14, no qual CQRS pressupõe a separação entre os modelos ou responsabilidades de escrita e leitura. Fica, portanto, sem resposta como portal do cidadão, painéis de gestão e vigilância realizariam suas consultas sem disputar os mesmos recursos da operação transacional.

*O que faríamos no lugar:* Ou desenharíamos explicitamente as projeções e modelos de leitura como componentes separados, como fizemos na Regulação e nos Painéis da Vigilância, ou removeríamos CQRS da matriz nos contextos em que ele não está efetivamente representado na arquitetura. A matriz e os diagramas precisam descrever a mesma decisão arquitetural.

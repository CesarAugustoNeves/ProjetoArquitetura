# ADR 0009: distribuir lógica de integração com sistemas federais como biblioteca versionada comum, com execução isolada por célula

**Status:** aceito (substitui o ADR 0003)

**Contexto:** O sistema precisa notificar doenças de notificação compulsória em até 24 horas e enviar dados de convênios federais via APIs do DATASUS[cite: 7, 12]. A interface e os contratos com esses sistemas são padronizados nacionalmente e atendem a todos os municípios da mesma forma[cite: 12, 19]. O ADR 0003 determinou o isolamento total por célula para evitar que instabilidades federais propagassem falhas entre prefeituras. Contudo, manter implementações duplicadas e cópias manuais dessa lógica em N células consome capacidade de manutenção do time sem agregar isolamento adicional em tempo de execução[cite: 19].

**Decisão:** A lógica de integração com os sistemas federais de saúde passa a ser construída e empacotada como uma **biblioteca/componente versionado comum**, mantida de forma padronizada para toda a organização[cite: 2, 19]. No entanto, esse componente **continua executando de forma estritamente isolada dentro do processo de cada célula**, sem nunca se tornar um serviço compartilhado centralizado[cite: 2, 19]. Cada célula mantém sua própria tabela de saída (*outbox*), seu processo de despacho autônomo e seu alerta de proximidade da janela de 24 horas.

**Alternativas consideradas:**
- Manter o código duplicado e mantido separadamente por célula: descartada por introduzir manutenção redundante e risco de divergência de comportamento entre contratos idênticos de API[cite: 19].
- Serviço central de integração em tempo de execução compartilhado por todas as células: descartada porque reintroduziria o ponto único de acoplamento e falha entre clientes que a arquitetura celular do ADR 0001 e o Envelope D proíbem expressamente[cite: 12, 19].

**Consequências:**
- Positivas: Reduz o retrabalho e o custo de manutenção da equipe de 25 pessoas ao unificar a conformidade com as APIs federais em um único artefato[cite: 4, 19]; preserva integralmente o confinamento de raio de impacto (*blast radius*), pois uma indisponibilidade ou travamento na comunicação afeta exclusivamente a fila da célula executora[cite: 4, 12].
- Negativas: Exige governança formal de ciclo de vida e versionamento semântico da biblioteca compartilhada, além de coordenação na esteira de integração contínua para atualizar as células de forma faseada sem quebras de compatibilidade[cite: 19].
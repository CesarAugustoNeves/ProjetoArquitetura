# ADR 0010: adotar implantação em ondas com disjuntor calibrado e telemetria dedicada da fila local das UBSs

**Status:** aceito (substitui o ADR 0005)

**Contexto:** A empresa atende múltiplos municípios (envelope D), cada um com dezenas de UBSs operando sob conectividade instável e quedas diárias de internet[cite: 10, 14]. O ADR 0005 instituiu a implantação em ondas entre células e o isolamento local via disjuntor e fila em banco local (SQLite)[cite: 9, 14]. Contudo, o desenho original monitorava apenas a abertura do disjuntor, sem qualquer visibilidade sobre o volume ou o tempo de retenção dos atendimentos retidos localmente[cite: 14, 19]. Em períodos de pico sazonal ou indisponibilidade prolongada, o acúmulo descontrolado de dados não sincronizados na ponta representa risco de perda de registros e saturação de armazenamento no posto sem aviso prévio[cite: 10, 19].

**Decisão:** Manter a estratégia de implantação progressiva por ondas entre células e as chamadas com timeout calibrado empiricamente por ambiente[cite: 14, 19]. Adicionar obrigatoriamente um mecanismo de telemetria leve no cliente local da UBS para monitorar a **quantidade de itens pendentes e a idade do atendimento mais antigo represado na fila local**[cite: 19, 20]. Configurar um **alerta operacional de represamento dedicado e autônomo**, separado do alarme de disjuntor aberto, disparado quando a fila ultrapassar limites pré-fixados de volume ou de atraso na sincronização[cite: 19, 20].

**Alternativas consideradas:**
- Alerta único atrelado apenas ao estado do disjuntor: descartada porque oscilações efêmeras de rede disparam falso positivo de crise, enquanto uma rede que oscila intermitentemente mas não esvazia a fila represada passaria sem notificação de gravidade[cite: 19].
- Bloqueio de atendimento quando a fila local ultrapassar um patamar: descartada terminantemente porque violaria a prioridade de atendimento clínico da unidade de saúde[cite: 14, 19].

**Consequências:**
- Positivas: O centro de operações ganha distinção imediata entre instabilidade transitória de telecomunicações e crise real de represamento de dados; reduz o risco de conflitos massivos e sobrecarga de banco quando a rede retornar[cite: 19, 20].
- Negativas: Exige a inclusão de um canal secundário/resiliente de telemetria (ex: heartbeat compacto ou métrica encapsulada em protocolo tolerante a falhas) no cliente local[cite: 9]; aumenta a complexidade de regras nos painéis de observabilidade para gerenciar múltiplos limiares de alerta por unidade[cite: 19, 20].
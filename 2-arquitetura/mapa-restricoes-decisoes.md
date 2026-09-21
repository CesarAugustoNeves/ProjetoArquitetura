# Mapa de Restrições — Sistema de Rede Municipal de Atenção à Saúde (Envelope D)

### Mapa de Restrições e Decisões

| Restrição / Requisito | Decisão | Justificativa |
| --- | --- | --- | 
| Existe um sistema de regulação legado que não pode ser desligado antes de dois anos. | **ADR 0002:** Estrangulamento com camada anticorrupção e fachada de roteamento por município. | Permite substituir o legado gradualmente, mantendo-o como fonte de verdade até que cada capacidade seja validada no novo sistema. |
| Funcionar com internet fora do ar; sincronizar depois sem perder nem duplicar. | **ADR 0005:** Tempo limite, disjuntor e fila local por célula. | Permite que a unidade continue registrando atendimentos durante a indisponibilidade e sincronize os dados quando a conexão retornar. |
| Nunca reservar o mesmo leito duas vezes. | **ADR 0002:** Migração gradual da regulação de leitos. | Mantém o controle da reserva em uma única fonte por capacidade durante a transição, evitando dupla reserva. |
| Notificar em até 24 horas. | **ADR 0003:** Outbox e fila de integração por célula. | Garante que a notificação seja registrada junto ao evento clínico e enviada posteriormente, mesmo quando o sistema federal estiver indisponível. |
| Relatórios por bairro e período. | **CQRS / Pipes and Filters:** Modelos de leitura e processamento analítico separados. | Separa consultas analíticas das operações clínicas, permitindo gerar relatórios sem sobrecarregar o sistema transacional. |
| Aguentar campanhas sem derrubar o atendimento. | **ADR 0001:** Arquitetura por município, com escalabilidade própria. | Permite que o município em campanha aumente sua capacidade sem afetar os demais. |
| Não travar a unidade quando um sistema externo cair. | **ADR 0003 + ADR 0005:** Filas, tempo limite e disjuntor. | Impede que a indisponibilidade de um sistema externo bloqueie o atendimento local. |
| Vários clientes no mesmo sistema. | **ADR 0001:** Arquitetura celular por município. | Mantém dados, processamento e filas isolados entre os municípios, permitindo operar vários clientes na mesma solução. |
| Pico sazonal brutal. | **ADR 0001:** Escalabilidade independente por célula. | Permite aumentar os recursos apenas no município que estiver enfrentando o pico. |
| Falha em um cliente não pode afetar os outros. | **ADR 0001:** Isolamento de infraestrutura por município. | Uma falha fica restrita à célula do município afetado, preservando as demais. |
| Falha isolada e equipe enxuta de 25 desenvolvedores. | **ADR 0001:** Células por município com composição interna modular. | Combina isolamento entre municípios com uma estrutura interna que pode ser mantida pelos times existentes. |
| Escalonamento para regiões específicas. | **ADR 0005:** Implantação progressiva por ondas. | Permite atualizar os municípios gradualmente e interromper a implantação caso seja detectado um problema. |
| Prontuário deve manter histórico e rastreabilidade por 20 anos. | **ADR 0004:** Event sourcing no prontuário. | Mantém o histórico das alterações e permite reconstruir o estado do prontuário ao longo do período de retenção. |

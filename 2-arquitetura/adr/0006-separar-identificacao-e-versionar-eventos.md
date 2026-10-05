# ADR 0006: separar dado de identificação do fluxo clínico e instituir versionamento de eventos

**Status:** aceito (substitui a ADR 0004 nos pontos de modelo de dado e versionamento)

**Contexto:** O prontuário eletrônico está sujeito à guarda obrigatória por 20 anos e à LGPD. A ADR 0004 aplicou event sourcing de forma generalizada ao módulo de prontuário. No entanto, a LGPD (Art. 18, III) garante o direito de correção de dados incompletos ou inexatos, como um erro de digitação no nome ou CPF do paciente. Tratar um dado de identificação como um fato clínico imutável obriga o sistema a conviver com o erro cadastral por 20 anos, o que é juridicamente inviável. Paralelamente, a guarda de eventos por duas décadas sem um mecanismo explícito de versionamento transforma o formato do dado em dívida técnica, impossibilitando a leitura de eventos antigos pelo código do futuro.

**Decisão:** Separar os dados de identificação do paciente, que são mutáveis e corrigíveis por comandos diretos de atualização, do fluxo de eventos clínicos, que permanece estritamente imutável (append-only). O event sourcing fica restrito aos fatos clínicos. Para suportar a guarda de 20 anos, institui-se um mecanismo de versionamento obrigatório nos eventos (envelope de evento com número de versão explícito e funções de conversão embutidas), testes de compatibilidade retroativa a cada mudança de esquema e uma política de arquivamento para formatos muito antigos.

**Alternativas consideradas:**
- Usar crypto-shredding para corrigir dados de identificação: descartada porque destruir a chave criptográfica serve para exclusão de registros inteiros, não para a simples correção de um erro de digitação sem perder o restante do histórico.
- Manter o event sourcing para identificação e gerar eventos compensatórios de "nome alterado": descartada porque introduz complexidade desnecessária para dados cadastrais que não possuem valor clínico no seu estado anterior ao erro.

**Consequências:**
- Positivas: garante o cumprimento da LGPD para correção de dados sem corromper a trilha de auditoria clínica; assegura mecanicamente que o software consiga reproduzir estados antigos independentemente da evolução do esquema de dados.
- Negativas: obriga a equipe a sustentar dois modelos de banco de dados (relacional para estado atual e event store para histórico) dentro do mesmo módulo; exige esforço contínuo de desenvolvimento, armazenamento e manutenção de testes de conversão entre as múltiplas versões de eventos ao longo dos 20 anos.
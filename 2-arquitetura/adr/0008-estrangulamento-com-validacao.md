# ADR 0008: substituir a regulação de leitos legada por estrangulamento com camada anticorrupção e validação prévia, célula a célula

**Status:** aceito (substitui o ADR 0002)

**Contexto:** Cada município que contrata o sistema já opera uma regulação de leitos legada, que não pode ser desligada antes de dois anos. A regra primária é que um leito só pode ser reservado por um paciente por vez. Não há registro público das regras internas do legado além do que a operação observa em produção. Substituir tudo de uma vez exigiria manter em paralelo leitos coordenados por dois sistemas, gerando risco extremo de dupla reserva.

**Decisão:** Instalar, em cada célula (por município), uma fachada de roteamento na frente da regulação legada, migrando capacidade por capacidade. **Antes de iniciar a migração de qualquer capacidade, institui-se uma etapa explícita de levantamento e validação**: o comportamento do legado em produção deve ser mapeado e convertido em testes de aptidão (fitness functions). 

A migração só avança com o destino determinístico via camada anticorrupção traduzindo os modelos. Uma capacidade só é considerada migrada quando o novo sistema comprovar, através dos testes de aptidão, que nenhum leito foi reservado duas vezes. Neste ponto, **o trecho correspondente do legado é desligado, o que significa desativar ou redirecionar terminantemente o acesso direto das unidades à interface nativa do legado para aquela capacidade**, garantindo que não existam dois escritores concorrentes.

**Alternativas consideradas:**
- Reescrita completa da regulação de leitos com corte único por município: descartada pelo risco de leitos ficarem sem controle durante a virada e perda de regras ocultas.
- Escrita dupla da aplicação nova gravando também no legado a cada reserva: descartada pela ausência de transação atômica.
- **Saga com reserva pendente e confirmação prévia no legado (sugerida na leitura cruzada):** descartada porque o isolamento e estrangulamento por capacidade já impedem dois autorizadores concorrentes. Uma Saga reintroduziria consistência eventual, aumentando o risco clínico de internações duplicadas.

**Consequências:**
- Positivas: O levantamento prévio reduz drasticamente o risco de regras ocultas quebrarem a operação pós-corte; fechar a interface velha garante que o usuário não drible a transição.
- Negativas: A camada anticorrupção exige manutenção cara; a validação prévia obriga a equipe a gastar tempo de engenharia investigando o legado antes de entregar qualquer valor novo; o salto de rede extra penaliza a latência.
# ADR 0002: substituir a regulação de leitos legada por estrangulamento com camada anticorrupção, célula a célula

**Status:** aceito

**Contexto:** Cada município que contrata o sistema já opera uma regulação de
leitos legada, que hoje não pode ser desligada antes de dois anos, exatamente
para manter a regra de que um leito só pode ser reservado por um paciente por
vez, com leitos disputados em tempo real entre unidades. Não há registro
público das regras internas do legado além do que a operação observa em
produção, e cada município assinado passa a ter seu próprio prazo de dois
anos, escalonado conforme a data de adesão. Substituir tudo de uma vez, por
município, exigiria manter em paralelo os leitos coordenados por dois
sistemas, com risco real de dupla reserva do mesmo leito.

**Decisão:** Instalar, em cada célula (por município), uma fachada de
roteamento na frente da regulação de leitos legada, migrando capacidade por
capacidade (por exemplo: reserva de leito de UPA, depois reserva de leito
eletiva, depois integração com transporte), com destino determinístico por
identificador de unidade solicitante, camada anticorrupção traduzindo entre o
modelo do legado e o modelo novo, e captura de mudanças de dados do legado
para alimentar o novo sistema sem alterar o código legado. Uma capacidade só
é considerada migrada, e o trecho correspondente do legado desligado, quando
o novo sistema comprovar, por função de aptidão, que nenhum leito foi
reservado duas vezes durante a transição.

**Alternativas consideradas:**
- Reescrita completa da regulação de leitos com corte único por município:
  descartada pelo risco de um leito ficar sem controle de disputa durante a
  virada e pela impossibilidade de recuperar por leitura de código todas as
  regras de prioridade clínica hoje só existentes no legado.
- Escrita dupla da aplicação nova gravando também no legado a cada reserva:
  descartada pela ausência de transação atômica entre os dois sistemas, o que
  abriria uma janela real de dupla reserva do mesmo leito sob falha de rede
  ou nova tentativa.
- Manter a regulação de leitos apenas no legado durante todo o contrato,
  integrando o novo sistema só por consulta: descartada porque o legado não
  expõe hoje eventos de liberação de leito em tempo hábil para os 40
  atendimentos por hora de pico da UPA maior, e prolongaria indefinidamente o
  prazo de dois anos já combinado com os municípios.

**Consequências:**
- Positivas: nenhum leito fica sem controle de disputa durante a transição,
  porque o legado continua sendo a fonte de verdade até a capacidade
  específica ser migrada e verificada; a migração pode ser interrompida ou
  revertida capacidade a capacidade sem afetar as demais; cada município
  migra no seu próprio prazo de dois anos, célula a célula, sem sincronizar
  calendários entre cidades.
- Negativas: a camada anticorrupção precisa ser mantida e ajustada a cada
  mudança no legado de cada município, o que multiplica o esforço de
  manutenção pelo número de clientes; a fachada de roteamento acrescenta um
  salto de latência em toda operação de leito, inclusive nas 40 triagens por
  hora de pico; enquanto a captura de mudanças de dados não cobrir 100% das
  operações do legado, existe uma janela de leitura potencialmente
  desatualizada no sistema novo.

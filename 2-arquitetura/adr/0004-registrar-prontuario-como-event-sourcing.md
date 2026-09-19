# ADR 0004: registrar o prontuário eletrônico como fluxo de eventos (event sourcing) dentro de cada célula, para sustentar a trilha de 20 anos exigida pela regulação profissional

**Status:** aceito

**Contexto:** O prontuário eletrônico deve ficar sob guarda obrigatória por 20
anos, premissa da atividade inspirada na regulação profissional, e é dado
sensível sob a LGPD, com direito de acesso do paciente às próprias
informações. Hoje o prontuário não circula entre as unidades de um mesmo
município (UBS, UPA, hospital), e cada unidade grava sua parte de forma
isolada, sem trilha confiável de quem consultou e quem alterou cada registro,
exigência explícita do caso. Diferente de outros contratos possíveis, este
caso não exige exclusão física antecipada do prontuário: o direito do
paciente aqui é de acesso, e convive com a retenção legal de 20 anos.

**Decisão:** Dentro de cada célula (município, ADR 0001), tratar o prontuário
eletrônico como um contexto delimitado próprio, gravado por event sourcing:
cada alteração clínica (evolução, prescrição, resultado de exame) é um evento
imutável, anexado a um fluxo por paciente, e o estado atual do prontuário é
obtido por reprodução desse fluxo, com snapshot periódico para não reproduzir
20 anos de eventos a cada leitura. Complementar a esse fluxo clínico, todo
acesso de leitura (quem consultou, quando, com que papel) é gravado em um log
de auditoria de leitura à parte, mantido pelo mesmo prazo de 20 anos, para
responder tanto quem alterou quanto quem apenas visualizou cada registro.

**Alternativas consideradas:**
- Tabela de auditoria ao lado do modelo de estado atual, registrando valor
  antigo e novo por coluna: descartada porque registra o que mudou e não a
  intenção clínica por trás da mudança, e amarra a auditoria ao esquema
  físico da tabela, que muda com o tempo.
- Guardar apenas o estado atual do prontuário, com campos de última
  atualização e responsável: descartada porque uma atualização sobrescreve o
  motivo da mudança anterior, e não sustenta reconstruir fielmente o estado
  do prontuário em uma data passada, algo que auditoria ou disputa clínica
  podem exigir.
- Aplicar event sourcing ao sistema inteiro, a todos os subdomínios do caso,
  por uniformidade: descartada porque generaliza o estilo além do contexto
  que o justifica; farmácia e agendamento, por exemplo, respondem bem com o
  estado atual e não precisam da história completa.

**Consequências:**
- Positivas: reconstrução fiel do estado do prontuário em qualquer data dos
  últimos 20 anos, incluindo o motivo de cada mudança; nenhuma sobrescrita
  concorrente passa despercebida, porque o acréscimo com versão esperada
  rejeita gravações conflitantes; a trilha de escrita fica pronta para
  auditoria e para disputa clínica sem trabalho adicional de reconstrução.
- Negativas: event sourcing não repõe sozinho quem apenas leu um registro sem
  alterá-lo, exigindo o log de acesso complementar como peça separada a
  manter; toda leitura do prontuário passa a depender de reprodução de
  eventos ou de snapshot, o que exige rotina de reconstrução testada e
  política de intervalo de snapshot; a equipe precisa versionar o formato dos
  eventos clínicos por até 20 anos, porque o código de hoje continua tendo de
  ler o formato de registros gravados há vinte anos.

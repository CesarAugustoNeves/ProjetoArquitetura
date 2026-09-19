# ADR 0003: isolar por célula a integração com os sistemas federais de saúde, para não propagar indisponibilidade entre municípios

**Status:** aceito

**Contexto:** O caso exige integração por API com sistemas federais de saúde,
usados por todos os municípios clientes da mesma forma, com janelas de
indisponibilidade conhecidas e fora do controle da empresa. Duas obrigações
do caso dependem dessa integração: a notificação de doenças de notificação
compulsória à vigilância em até 24 horas, e o envio de dados exigidos por
convênio federal. Como o sistema é particionado em células por município
(ADR 0001), qualquer componente que todas as células chamem em comum é, por
definição, um ponto de acoplamento entre municípios diferentes, o que
contraria diretamente a exigência dominante do envelope D de que a falha de
um cliente não afete outro.

**Decisão:** Implementar a integração com cada sistema federal dentro de cada
célula, nunca como serviço compartilhado entre células: cada célula grava a
notificação a enviar em uma tabela de saída própria (padrão outbox) na mesma
transação em que grava o evento clínico, e um processo de envio, também por
célula, publica para o sistema federal com repetição e prazo até confirmar.
Quando a janela de indisponibilidade do sistema federal se abre, apenas a
fila daquela célula acumula atraso; as demais células continuam notificando
normalmente, e um alerta próprio dispara se uma notificação individual se
aproximar do prazo de 24 horas sem confirmação.

**Alternativas consideradas:**
- Um único serviço central de integração federal, compartilhado por todas as
  células: descartada porque reintroduz exatamente o ponto único de falha
  entre municípios que a arquitetura celular do ADR 0001 foi adotada para
  eliminar; uma lentidão do sistema federal afetaria a notificação de todos
  os clientes ao mesmo tempo.
- Chamada síncrona direta da vigilância epidemiológica ao sistema federal,
  sem fila intermediária: descartada porque a janela de indisponibilidade do
  sistema federal é premissa assumida do caso, e uma chamada síncrona sem
  fila perderia a notificação, ou bloquearia o atendimento, exatamente
  durante essas janelas.
- Postergar toda a integração federal para fora do caminho crítico, com
  sincronização manual periódica: descartada porque não atende ao prazo de
  24 horas exigido para doenças de notificação compulsória, que é regra do
  caso e não uma meta de conforto.

**Consequências:**
- Positivas: a indisponibilidade do sistema federal atrasa notificações
  apenas do município que estava chamando naquele momento, sem afetar os
  demais clientes; o prazo de 24 horas passa a ter alerta antecipado e
  mensurável por célula; a fila de saída sobrevive a reinícios de processo,
  porque a gravação do evento e da notificação pendente acontece na mesma
  transação local.
- Negativas: a lógica de outbox e reenvio precisa ser replicada e operada em
  cada uma das N células, em vez de em um único serviço; cada célula acumula
  sua própria fila de pendências durante uma janela de indisponibilidade
  federal, exigindo capacidade de armazenamento e alerta próprios; a
  reconciliação entre o que foi de fato aceito pelo sistema federal e o que a
  célula acredita ter enviado precisa de verificação periódica por município,
  e não existe hoje uma visão federada única desse status entre células.

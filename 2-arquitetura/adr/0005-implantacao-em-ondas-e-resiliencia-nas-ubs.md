# ADR 0005: adotar implantação progressiva por onda entre células, com tempo limite e disjuntor nas chamadas das UBS para tolerar internet instável

**Status:** aceito

**Contexto:** A empresa opera 3 times de desenvolvimento para todos os
municípios clientes, e uma mudança de código ou de configuração é preparada
uma vez e hoje seria distribuída para todas as células ao mesmo tempo. As UBS
têm internet instável, com quedas diárias de minutos a horas, e uma chamada
de uma UBS para o sistema central não tem hoje prazo nem repetição definidos,
apenas o comportamento padrão da biblioteca de rede usada. O contrato do
envelope D exige que a falha de um cliente não afete outro, mas uma
implantação com defeito, distribuída de uma vez para todas as células,
contornaria o isolamento por dados do ADR 0001 e voltaria a acoplar todos os
municípios pelo mesmo lançamento de software.

**Decisão:** Implantar toda mudança em ondas, uma célula (município) por vez,
com um período mínimo de observação de métricas de erro e latência antes de
avançar para a próxima onda, e capacidade de reverter uma onda isoladamente
sem afetar as células já atualizadas ou as ainda não atualizadas. Nas
chamadas das UBS para os serviços da própria célula, aplicar tempo limite
curto derivado da latência observada, no máximo duas tentativas com recuo
exponencial, e um disjuntor que abre após falhas seguidas; enquanto o
disjuntor estiver aberto, a UBS opera com fila local de atendimentos
pendentes de sincronização, em vez de bloquear o atendimento.

**Alternativas consideradas:**
- Implantação única e simultânea em todas as células, com testes
  automatizados como única proteção: descartada porque um defeito não
  capturado pelos testes atingiria todos os municípios ao mesmo tempo, o que
  é exatamente a falha que a arquitetura celular do ADR 0001 foi adotada
  para conter.
- Adotar malha de serviços (service mesh) para obter tempo limite e
  disjuntor sem código, em todas as células: descartada nesta fase porque a
  organização opera poucas dezenas de serviços por célula e o custo de
  operar um plano de controle de malha em cada uma das N células não se
  justifica na escala atual.
- Aumentar o tempo limite das chamadas das UBS para tolerar a instabilidade,
  sem disjuntor: descartada porque apenas adia o esgotamento de recursos do
  lado do servidor durante uma queda prolongada, em vez de conter o efeito
  dela sobre a própria UBS que está sem internet.

**Consequências:**
- Positivas: uma implantação defeituosa fica contida na primeira célula da
  onda, com tempo de observação suficiente para detectar o problema antes de
  atingir os demais municípios; a UBS continua registrando atendimentos
  durante uma queda de internet, em vez de parar de atender; o estado do
  disjuntor por célula vira sinal de alerta antecipado de degradação de rede.
- Negativas: o ciclo completo de implantação passa de minutos, em um
  lançamento único, para horas ou dias, conforme o número de células e o
  tempo de observação de cada onda; a fila local de atendimentos pendentes na
  UBS exige lógica própria de sincronização e resolução de conflito quando a
  internet volta; os 3 times precisam coordenar entre si a ordem das ondas, o
  que é trabalho de coordenação adicional que não existia com lançamento
  único.

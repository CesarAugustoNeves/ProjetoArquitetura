# ADR 0007: adotar arquitetura celular por município, com composição interna orientada a eventos entre os subdomínios

Status: aceito (substitui o ADR 0001)

Contexto: A empresa vende o mesmo sistema de atenção à saúde para várias prefeituras (envelope D), com 25 desenvolvedores em 3 times distribuídos entre as cidades atendidas e nuvem pública multirregião. Cada município opera sua própria rede: 70 UBS, 5 UPAs e 1 hospital de referência com 400 leitos, com cerca de 12 mil atendimentos por dia e picos de até 40 triagens por hora na UPA maior. O contrato com cada prefeitura exige que uma falha ou um pico de demanda em um município não afete o atendimento de outro, e a base de clientes tende a crescer com sazonalidade forte (campanhas de vacinação com até 20 vezes o acesso normal). Hoje não existe fronteira técnica entre os dados e a capacidade de processamento de diferentes municípios.

Decisão: Particionar o sistema em células por município (identificador do cliente/prefeitura como chave de partição), cada célula com aplicação, filas, cache e banco próprios, atendida por um roteador de células que apenas resolve a chave e encaminha a requisição. Dentro de cada célula, os subdomínios do caso se comunicam por um barramento de eventos local. O roteador e o plano de controle ficam fora do caminho de requisição.
Para mitigar o custo e o risco da explosão de instâncias (N células), institui-se obrigatoriamente um time de plataforma. Este time será o único responsável por manter um template único de infraestrutura como código (IaC), garantir o provisionamento automatizado por onda e impor um teto rigoroso de ativação de novas células por sprint.

Alternativas consideradas:

Multilocação lógica em instância única compartilhada (multi-tenant lógico com linha de banco marcada por cliente): descartada porque um pico de campanha de vacinação de um município, ou uma implantação defeituosa, atingiria todos os demais ao mesmo tempo, violando a exigência de falha isolada do envelope D.

Implantação totalmente separada por município, sem nenhum componente comum (multi-instância independente): descartada porque duplica o custo de operação de forma proporcional ao número de clientes e inviabiliza reaproveitar o roteador e a governança comuns dos 3 times, sem trazer isolamento adicional real.

Arquitetura hexagonal única com fila global compartilhada entre municípios: descartada porque a fila compartilhada é ponto único de acoplamento entre clientes, contrariando exatamente a força que domina o envelope D.

Consequências:

Positivas: uma falha ou pico de demanda em um município fica contido na própria célula; cada cidade pode ser dimensionada e escalada de forma independente conforme seu calendário de campanhas; um cliente com exigência regulatória própria pode receber célula dedicada sem redesenho.

Negativas: N instalações completas para operar, observar e atualizar em vez de uma; o estabelecimento do time de plataforma consome parte da cota restrita de 25 desenvolvedores, sacrificando força de trabalho que entregaria funcionalidades no produto principal para focar estritamente em infraestrutura; relatórios que cruzam vários municípios exigem agregação externa às células; a migração de um município entre células vira projeto e não comando simples; o roteador e o plano de controle de células tornam-se peças de disponibilidade máxima, e seu crescimento além do roteamento puro devolve o acoplamento que o estilo pretende eliminar.
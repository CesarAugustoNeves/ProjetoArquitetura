# ProjetoArquitetura
Github feito para o projeto da matéria de PADRÕES E ARQUITETURA DE SOFTWARE.

/----------------------------------------------------------------------------\

INTEGRANTES:

* ALEX LEANDRO SOARES TORRES RA: 21937693

* CESAR AUGUSTO NEVES RA: 24004118

* ENRYCO SUCOSKI MARTINS RA: 24005483

* ISABELLE ORMO CRENONINI RA: 24007567

* VITOR EUGÊNIO CASTELANO SILVA RA: 24005464

/----------------------------------------------------------------------------\

Grupo 09
Caso:
  Saúde: rede municipal de atenção à saúde
  
/----------------------------------------------------------------------------\

Envelope:
  D. Empresa que vende para várias cidades, 25 desenvolvedores

/----------------------------------------------------------------------------\

Exigência que domina:
  Vários clientes; pico sazonal; falha isolada


### Perguntas Obrigatórias 

1. Como a UPA continua triando e atendendo com a internet fora do ar, e o que acontece quando ela volta?
   
R: Enquanto a internet está fora do ar, o aplicativo da unidade grava a triagem e o atendimento no armazenamento local do próprio aplicativo. Ele não depende de nenhuma chamada de rede para continuar funcionando: a equipe de enfermagem e médica registra tudo localmente. Quando a rede volta, o aplicativo envia os atendimentos ao gateway da célula, que os publica como evento no barramento. O barramento entrega esse evento ao módulo Triagem, que é hexagonal: a entrada por sincronização é um adaptador que trata a mensagem.

3. Como duas unidades disputando o mesmo leito nunca conseguem reservá-lo ao mesmo tempo, com o sistema legado ainda no circuito?
   
R: Dentro do núcleo, a Regulação de leitos é o único lugar que grava reservas, seguindo CQRS: um modelo de escrita e uma projeção de vagas. Duas unidades que competem pelo mesmo leito chamam esse mesmo módulo, dentro do mesmo processo, sobre o mesmo banco transacional — assim a exclusividade é garantida, por transação local, não por travas distribuídas.

5. Como o prontuário garante que se saiba quem acessou cada registro, e como convive a guarda de 20 anos com os direitos do paciente sob a LGPD?
   
R: O módulo Prontuário usa event sourcing: cada fato clínico (evolução, dispensação validada, etc.) é gravado como um evento imutável, nunca sobrescrito. A leitura não é um evento de domínio, então cada consulta ao histórico passa pelo Registro de auditoria, que grava quem acessou. Cada alteração no prontuário também é registrada ali.

7. Como a notificação compulsória chega à vigilância em até 24 horas mesmo se o sistema federal estiver indisponível?
   
R: A notificação segue por fila até a Integração federal e legado, e não chamada direta, porque fila retém a mensagem até haver um consumidor disponível. Se a API federal estiver indisponível, a mensagem fica represada na fila da Integração em vez de se perder, e é reenviada quando a API volta.
 
9. Como o sistema legado de regulação é substituído aos poucos sem interromper o serviço?
    
R:    

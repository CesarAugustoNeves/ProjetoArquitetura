# Prova de Conceito: Arquitetura Celular por Município

## Qual ADR ele prova
**ADR 0001: Adotar arquitetura celular por município, com composição interna orientada a eventos**

Este programa prova a decisão mais arriscada do projeto (ADR 0001): como isolar totalmente a carga e as falhas entre diferentes clientes (Envelope D), garantindo que o pico sazonal brutal de um município não afete os demais. 

Como bônus para demonstrar alinhamento com a arquitetura definida, o código também simula estruturalmente:
- **ADR 0003:** O mock da integração com o sistema federal é instanciado *dentro* de cada célula, provando que se a fila federal travar para uma cidade, não trava para a outra.
- **ADR 0004:** O banco de dados da célula não faz *updates* destrutivos; ele faz *append* em uma lista de eventos (`Event Store`), simulando o Event Sourcing para o prontuário.

## Como rodar
O script foi escrito em Python 3.12 e utiliza apenas a biblioteca padrão. A simulação baseia-se em eventos temporais discretos e é 100% determinística.

1. Execute o script redirecionando a saída para o arquivo de texto:
   ```bash
   python exemplo.py > saida-esperada.txt
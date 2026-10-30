# Roteiro macro — Aula 3: Docker e Docker Compose

Referência para acompanhar o episódio e reproduzir a etapa no próprio laboratório. Os comandos completos, com local de execução e limites, estão no [README](../README.md). O conteúdo de Streamlit foi separado para um [complemento](../COMPLEMENTO_STREAMLIT.md); não faz parte do encerramento desta aula.

## 1. Retomar o laboratório

- Aula 1: TEP e OPC UA com três variáveis do reator.
- Aula 2: Pi 3 como roteador/firewall e Pi 4 na rede Ethernet dedicada.
- Aula 3: organizar a execução do servidor com Docker e Docker Compose.

**Pergunta-guia:** como deixar de depender de um script iniciado manualmente em um terminal, mantendo as dependências e a configuração compreensíveis?

## 2. Entender os componentes

Explique imagem, container, Dockerfile e Compose antes dos comandos. A imagem contém o ambiente da aplicação; o container é sua execução. O Compose descreve a configuração do serviço. O TEP e o servidor OPC continuam integrados no mesmo processo, sem uma segunda simulação independente.

## 3. Conferir o ambiente

Identificar o Pi 4 por SSH com salto, arquitetura, IP, rota de retorno, espaço disponível, Docker e Compose. Conferir o IP atual do notebook e o firewall do Pi 3. Downloads/build podem exigir preparação prévia autorizada; não abrir o firewall inteiro para obter imagens.

**Checkpoint:** ambiente correto e servidor manual identificado, sem alterações indiscriminadas em outros projetos.

## 4. Ler a configuração e construir

Mostrar `docker/Dockerfile`, `docker/requirements-server.txt`, `.env.example` e `docker/compose.yaml`. Separar o endereço de escuta dentro do container do endpoint anunciado ao cliente. Executar `config` e `build tep-opc`.

**Checkpoint:** configuração renderizada com o IP Ethernet correto e build concluído no ambiente utilizado. O serviço Streamlit está em um profile opcional para o complemento.

## 5. Iniciar e observar

Parar somente o servidor manual que ocupa 4840. Executar `up -d tep-opc`, `ps` e `logs`. Explicar que o terminal livre não é prova suficiente de saúde. A publicação da porta no Pi 4 não substitui a regra de encaminhamento no Pi 3.

## 6. Validar no cliente

Executar uma leitura OPC local e conectar o UAExpert ao endpoint Ethernet. Conferir `Pressao`, `Nivel`, `Temperatura`, unidades, qualidade `Good` e avanço de `SourceTimestamp`.

**Checkpoint:** a aplicação organizada em container continua fornecendo os dados esperados pelo caminho de rede do laboratório.

## 7. Mostrar o ciclo operacional

Acompanhar logs, explicar Ctrl+C no visualizador, reiniciar apenas o serviço e mostrar como parar o projeto. Reiniciar o TEP reinicia sua trajetória; a aula não implementa retenção histórica. Política de reinício de container e recuperação da rede após reboot são validações distintas.

## 8. Encerrar e anunciar o complemento

“Hoje organizamos o simulador e o servidor OPC UA com Docker e Docker Compose. No complemento, vamos construir a interface Streamlit para consumir esses dados pelo navegador e controlar seu acesso pelo firewall.”

Thiago conduz; Sol responde apenas quando chamada e entrega comandos pequenos, um passo por vez. Se algum teste não passar, registre a pendência. Não declare persistência após reboot sem verificar as camadas de aplicação, rota, encaminhamento e firewall.

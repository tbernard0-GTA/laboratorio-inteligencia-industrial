# Plano incremental — Aula 3

> Atualização de 29/10/2026: este documento preserva o histórico das etapas anteriores. A Aula 4 e seu estado comprovado ou pendente estão em [aulas/aula-04](../aulas/aula-04/) e nas entradas recentes do diário. Dados e planos históricos abaixo não comprovam o estado atual dos equipamentos.


Em 29/10/2026 o coletor OPC UA com SQLite foi preparado e testado localmente com dados sintéticos. Inspeção do ambiente efetivo, deploy controlado e verificação de dados reais e persistência no Pi ainda estão pendentes. Streamlit continua fora desta etapa.

**Estado:** em 28/10/2026 foram preparados o servidor adaptado, Dockerfile e Compose. O Compose foi validado localmente, mas imagem, execução e descoberta ainda não foram testadas. A infraestrutura foi informada pelo usuário, sem inspeção remota nesta sessão. Preserve as Aulas 1 e 2, registre os resultados no [diário](DIARIO_DE_BORDO.md) e valide cada etapa antes de avançar. Endereços e configurações históricas não substituem inspeção real. Mudanças de rede, firewall ou serviços exigem solicitação explícita e análise prévia.

## Etapa 1 — Inspeção da infraestrutura

- **Objetivo:** identificar o estado efetivo do notebook, dos Raspberry Pi e dos caminhos de acesso.
- **Pré-requisitos:** autorização para a inspeção, acesso apropriado e histórico disponível.
- **Entregáveis:** inventário de sistema, rede, serviços e caminhos de administração, com lacunas registradas.
- **Validação:** confrontar observações com a arquitetura histórica e registrar diferenças e evidências.
- **Riscos:** informação desatualizada, acesso indisponível ou interferência em serviços existentes.

## Etapa 2 — Inventário do código TEP/OPC UA

- **Objetivo:** compreender o código e as dependências existentes antes de qualquer alteração.
- **Pré-requisitos:** base das Aulas 1 e 2 preservada e infraestrutura inventariada.
- **Entregáveis:** mapa de arquivos, dependências, endpoint, sinais e comportamento de execução.
- **Validação:** conferir o inventário contra o código e os resultados conhecidos, sem presumir o estado em execução.
- **Riscos:** diferenças entre cópias locais e dispositivos; dependências incompatíveis com ARM64.

## Etapa 3 — Planejamento da containerização

- **Objetivo:** definir uma abordagem para empacotar e operar os componentes no Pi 4.
- **Pré-requisitos:** inventários das etapas 1 e 2 e requisitos de operação e acesso conhecidos.
- **Entregáveis:** desenho de serviços, dependências, rede, configuração, persistência quando necessária e estratégia de reversão.
- **Validação:** revisar viabilidade ARM64, interfaces, portas, conflitos e preservação dos serviços existentes.
- **Riscos:** incompatibilidade de dependências, colisão de portas e interrupção da operação atual.

## Etapa 4 — Implementação do Dockerfile

- **Objetivo:** preparar uma imagem reproduzível para a aplicação definida no planejamento.
- **Pré-requisitos:** desenho revisado, ambiente e dependências compatíveis identificados.
- **Entregáveis:** Dockerfile e instruções de construção pertinentes.
- **Validação:** construir e verificar a imagem no ambiente adequado e conferir seu comportamento básico.
- **Riscos:** dependências indisponíveis em ARM64, imagem excessiva ou exposição de informações sensíveis.

## Etapa 5 — Configuração do Docker Compose

- **Objetivo:** definir a execução coordenada dos serviços planejados.
- **Pré-requisitos:** imagem validada e decisões de rede, portas e configuração revisadas.
- **Entregáveis:** configuração Compose e instruções de uso e reversão.
- **Validação:** conferir configuração e inicialização controlada, isolamento e ausência de conflitos.
- **Riscos:** interrupção de processos existentes, exposição indevida ou configuração divergente.

## Etapa 6 — Desenvolvimento do cliente OPC UA

- **Objetivo:** consumir pressão, nível e temperatura do servidor OPC UA.
- **Pré-requisitos:** endpoint e nós identificados; servidor de teste disponível.
- **Entregáveis:** cliente e tratamento de conexão, leituras e falhas apropriado.
- **Validação:** comparar as leituras e qualidade dos dados com uma referência conhecida e testar indisponibilidade.
- **Riscos:** identificadores ou endpoints incorretos, dados desatualizados e falhas de conexão.

## Etapa 7 — Desenvolvimento da interface Streamlit

- **Objetivo:** apresentar as variáveis OPC UA para supervisão.
- **Pré-requisitos:** cliente validado e requisitos de atualização e acesso definidos.
- **Entregáveis:** interface e instruções de operação.
- **Validação:** conferir valores, unidades, atualização e indicação de falhas ou dados indisponíveis.
- **Riscos:** apresentação de dados antigos como atuais e exposição indevida da interface.

## Etapa 8 — Integração e testes no Raspberry Pi 4

- **Objetivo:** verificar a operação conjunta dos componentes no hardware alvo.
- **Pré-requisitos:** etapas anteriores validadas, acesso autorizado e plano de reversão.
- **Entregáveis:** resultados de integração, funcionamento e recuperação, com eventuais limitações.
- **Validação:** conferir inicialização, leituras, recursos e recuperação sem interromper serviços sem análise.
- **Riscos:** recursos limitados, incompatibilidade ARM64 e conflito com o servidor existente.

## Etapa 9 — Validação das regras de rede no Pi 3

- **Objetivo:** verificar os fluxos pretendidos e as restrições existentes para OPC UA, supervisão e administração.
- **Pré-requisitos:** configuração efetiva inventariada, testes autorizados e acesso alternativo conhecido.
- **Entregáveis:** registro dos testes de acesso permitido e bloqueado e das regras observadas.
- **Validação:** correlacionar novas conexões e evidências de rede com a política pretendida; investigar divergências.
- **Riscos:** perda de acesso, impacto em outros fluxos e interpretação equivocada de falhas. Nenhuma alteração automática do firewall; alterações dependem de solicitação explícita e análise.

## Etapa 10 — Documentação e encerramento

- **Objetivo:** consolidar a implementação, a operação e os resultados da aula.
- **Pré-requisitos:** testes concluídos e pendências conhecidas.
- **Entregáveis:** documentação atualizada, diário e lista de limitações e próximos passos.
- **Validação:** confrontar instruções com o estado efetivamente testado e revisar os resultados registrados.
- **Riscos:** documentação desatualizada, omissão de limitações ou divulgação de credenciais.

# Plano de implantação — Aula 5 / Ação 5A

**Atualização pós-gravação:** este plano registra o estado anterior à transição. Posteriormente, Thiago relatou carga e subida da Aula 5 no Pi e consultas no banco ativo; a transferência dos três artefatos teve hashes OK. A situação atual dos serviços e o resultado de reboot, backup e restauração não foram confirmados nesta revisão. O volume antigo foi preservado segundo o relato. Instruções e ressalvas atuais estão em [OPERACAO_GRAVACAO.md](../OPERACAO_GRAVACAO.md); qualquer nova alteração exige solicitação específica.

## Arquitetura recomendada

- **PLANEJADO:** projeto Compose independente, por exemplo `iilab-aula05`, com serviço TEP/OPC UA da Aula 5 e serviço historiador usando o coletor da Aula 5. Intervalo inicial: cinco segundos. Não substituir arquivos ou recriar contêineres de `aula-03`.
- **ATUALIZADO:** a proposta inicial sem porta publicada foi substituída pelo pacote em `../compose.yaml`, que prevê bind configurável e, na transição autorizada, `10.77.0.10:4840` para o UAExpert depois da parada controlada do servidor antigo. A descoberta interna e por porta alternativa foi testada apenas localmente; regras e acesso no Pi permanecem a validar. Não alterar firewall por inferência.
- **ATUALIZADO:** o pacote prevê volume dedicado `iilab-aula05_historico`, com `/data/historico_aula05.sqlite3`; nunca reutilizar `aula-03_historico`. Conferir previamente se o nome já existe e garantir acesso do UID `10001` ao diretório e aos arquivos WAL/SHM.
- **PLANEJADO:** imagem própria ARM64 construída de artefatos revisados; avaliar reuso da imagem base identificada no inventário após confirmar ID e versões de Python, TEP, asyncua e NumPy. Preparar `.dockerignore` para não enviar `.env`, chaves, ambientes virtuais, SQLite, WAL ou SHM ao contexto. O Dockerfile deve copiar apenas os arquivos necessários, executar sem privilégios e especificar as dependências verificadas.
- **PENDENTE:** `NoSecurity` e acesso anônimo exigem rede restrita; confirmar limites de isolamento. Executar dois TEPs cria simulações independentes: os dados antigos e novos não representam necessariamente o mesmo estado de processo.

## Pré-requisitos e backup

1. **BLOQUEADOR:** atualizar o inventário via sessão interativa; confirmar roteamento, IP do notebook, portas, Compose e rede Docker. A tentativa automática de SSH foi recusada. Não contornar regras.
2. **PENDENTE:** Thiago informou a sincronização do Pi 4 via Pi 3 já corrigida e comprovada; não refazer. Confirmar estado antes da troca; reboot não foi testado. Analisar impacto nos dados antigos; não reescrever o histórico.
3. **BLOQUEADOR:** confirmar caminho real do SQLite e auxiliares, permissões e espaço. Planejar backup consistente usando SQLite Online Backup API ou ferramenta equivalente capaz de ler banco em WAL; preservar também os dois Compose identificados e configuração necessária em destino seguro, sem divulgar segredos. Verificar integridade do backup e testar restauração em cópia isolada. Não copiar só o arquivo principal de um banco ativo, não sobrescrever backup e não manipular volume original nesta ação.
4. **BLOQUEADOR:** definir limites de espaço, monitoramento, backup e retenção. São até 53 × 12 × 60 × 24 = **915.840 leituras/dia** a cinco segundos; o tamanho diário é desconhecido. Confirmar margem para duas simulações, build e crescimento em armazenamento de aproximadamente 3,9 GiB livres relatados.
5. **PENDENTE:** preparar e validar imagem/Compose e healthchecks apenas após autorização; confirmar isolamento, recursos, compatibilidade ARM64, dependências, endpoint interno, permissões e ausência de colisões. Não executar regras de rede como efeito colateral sem análise.

## Sequência futura sob autorização

Os seguintes passos são **proposta**, não comandos executados. Eles só se aplicam quando os artefatos da Aula 5 existirem, forem revisados e o diretório estiver confirmado:

1. Inspecionar `docker compose ... config --quiet` e sua configuração de portas, rede, volume e imagens sem exibir segredos. Conferir o nome do projeto e não apontar para os arquivos do projeto antigo.
2. O pacote ARM64 já foi construído localmente; verificar ID, hashes e permissões antes de transferir e carregar em etapa autorizada. Iniciar somente o projeto novo depois da demonstração e da parada controlada anterior; não fazer `up`, `down` ou build em `aula-03`.
3. Validar a descoberta interna dos 53 NodeIds canônicos e três legados, valores/qualidade, leitura sem escrita remota e saúde. Um teste TCP indica apenas escuta; saúde operacional exige leitura OPC UA e timestamps válidos.
4. Verificar pelo menos três ciclos de 53 leituras no banco novo, `StatusCode`, qualidade, timestamps e consultas; verificar crescimento, recurso e atualidade. Registrar diferenças entre as duas simulações. Para XMEAS(23–41), timestamp de publicação não comprova uma nova análise física.
5. Reiniciar somente o historiador da Aula 5 em teste explicitamente autorizado, verificar preservação de ciclos anteriores e novos ciclos completos, sem perda ou alteração do volume antigo. Checar logs, espaço, integridade e recuperação a partir de backup separado.

Os comandos exatos e condicionais de build no Windows, transferência, carga, subida sem build/pull, consultas e rollback estão em [OPERACAO_GRAVACAO.md](../OPERACAO_GRAVACAO.md). Este plano foi elaborado antes da gravação; transferência, carga e subida foram relatadas posteriormente, enquanto rollback não foi relatado. Logs podem conter informações sensíveis e devem ser revisados antes de compartilhamento. Saúde do historiador verifica ciclo recente e 53 linhas, mas sua verificação de atualidade depende do relógio correto.

## Rollback e critérios de aceite

- **PLANEJADO:** parar apenas os serviços do projeto `iilab-aula05`, preservando o volume novo para diagnóstico; não executar `down -v`, não remover `aula-03_historico`, não alterar as portas/regras existentes. Depois conferir servidor, coletor, interface e integridade do histórico anterior. Restauração só com procedimento testado em cópia e autorização apropriada.
- **ACEITE FUTURO:** relógio confiável; backup e restauração verificados; projeto antigo inalterado; 53 canônicas e três legadas navegáveis; XMV não gravável; histórico novo com 53 registros por ciclo, qualidades/timestamps corretos, persistência após reinício e consultas válidas; recursos e espaço monitorados; resultados e pendências registrados. Não aceitar teste de porta TCP como prova de dados saudáveis.

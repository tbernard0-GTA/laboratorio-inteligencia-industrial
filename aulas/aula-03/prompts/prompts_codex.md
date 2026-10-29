> **Divisão do conteúdo (29/10/2026):** a Aula 3 cobre Docker/Compose e TEP+OPC. Streamlit e a porta 8501 são material de preparação do vídeo complementar, não etapas do vídeo principal. Para ativá-los, use `docker compose --env-file .env -f docker/compose.yaml --profile complemento ...`. Confira o [README da aula](../README.md).

# Codex em tarefas pequenas — Aula 3

Cole um prompt por vez. Leia a resposta, revise o diff e execute o checkpoint antes de continuar. Os comandos Linux pertencem ao **Pi 4 por SSH**, não ao PowerShell local. O Codex deve trabalhar no checkout autorizado; nesta preparação, somente a nuvem foi usada. Não dê acesso aos Raspberry nem execute mudanças de rede implicitamente.

## Contexto fixo para abrir a sessão

> Estamos no repositório laboratorio-inteligencia-industrial. A aula 1 tem um processo Python integrado: TEPSimulator + servidor asyncua. A aula 2 separa redes com Pi 3 como roteador/firewall e Pi 4 como aplicação. Nesta aula 3 vamos usar Docker Compose no Pi 4 para TEP+OPC. Streamlit como cliente OPC pertence ao complemento e deve ficar em profile opcional. Preserve aulas anteriores. Trabalhe em aulas/aula-03. Não altere firewall, rotas ou configurações do host automaticamente; não publique, faça push ou merge sem autorização específica. Não introduza banco, React ou Kubernetes. Antes de editar, explique a mudança pequena, os arquivos e o teste. Ao terminar, mostre diff, resultado real e pendências. Não diga que testou hardware quando só testou na nuvem.

## 1 — Inventariar, sem alterar

> Leia aulas/aula-01/servidor_opc.py, requirements.txt e os arquivos atuais da aula 3. Identifique: ponto de entrada, API real do TEP, versões, loop de simulação, endpoint, namespace URI, objeto, nomes das tags, índices/unidades e segurança OPC. Liste dependências nativas e riscos ARM64/Python. Não invente NodeIds nem divida TEP e OPC em processos sem transporte implementado. Entregue tabela de inventário e uma proposta mínima, sem modificar arquivos.

**Checkpoint:** namespace `urn:laboratorio-industrial:tep`; `Reator`; `Pressao`, `Nivel`, `Temperatura`; processo integrado identificado. Compare com código, não só com esta lista.

## 2 — Planejar a embalagem, sem código ainda

> Com o inventário confirmado, proponha Dockerfile e Compose com tep-opc como serviço padrão. Reserve streamlit para o profile opcional complemento, sem iniciá-lo na aula principal. TEP+OPC permanece integrado. Explique bind dentro do container, endereço anunciado externo e DNS entre serviços. Planeje PI4_BIND_IP=10.77.0.10 para publicação4840/8501 e OPC_ENDPOINT=opc.tcp://tep-opc:4840/tep/ para o cliente. Liste variáveis, restart policy, healthchecks, limites do healthcheck e arquivos a criar. Nada de host network, privileged ou montagem do socket Docker. Diga quais escolhas requerem teste real no Pi4.

**Checkpoint:** hostname de serviço funciona apenas na rede Compose; navegador usa IP do Pi4. Publicar porta não libera o gateway. Aprove o plano antes de editar.

## 3 — Containerizar o servidor preservando comportamento

> Implemente somente a parte necessária do plano para executar TEP+OPC no serviço tep-opc. Preserve nomes/unidades/timestamps e backend real. Extraia configuração para ambiente sem mudar aulas antigas. Fixe dependências, inclua compilação nativa necessária e .dockerignore. Acrescente .env.example sem segredos e Compose com bind explícito. Faça validação estática/Python e Docker build/Compose config apenas se disponíveis. Se Docker não existir, registre não executado, não simule sucesso. Mostre como evitar conflito com o servidor manual na4840 e como voltar a ele sem matar processos genéricos.

**Checkpoint:** o serviço sobe, logs mostram inicialização, UAExpert lê as três tags. Docker/ARM só passam depois de teste no hardware.

## 4 — Cliente OPC pequeno, independente da interface

> Implemente ou revise um cliente Python OPC testável. Descubra o índice pelo namespace URI urn:laboratorio-industrial:tep e navegue Objects/Reator/Pressao,Nivel,Temperatura; não grave ns=2 nem NodeIds numéricos deduzidos. Leia valores, unidade, status OPC e SourceTimestamp quando disponível. Trate timeout/desconexão, feche conexão, e defina erro de comunicação sem substituir dados reais por números simulados. Separe o resultado do cliente da renderização Streamlit. Adicione teste com servidor OPC de teste explicitamente identificado e reporte como executar.

**Checkpoint:** cliente contra o servidor real e contra fixture de teste; falha de endpoint gera estado de erro, não “0” que pareça medida válida.

## 5 — Interface mínima e honesta

> Usando o cliente existente, implemente ou revise Streamlit com estado de conexão, três valores e unidades, horário de atualização e tendência recente. Frequência configurável e histórico em memória limitado. Não acumule indefinidamente, não crie clientes órfãos a cada rerun e não bloqueie a interface num while infinito. Em desconexão, sinalize dados antigos/indisponíveis e tente reconectar de modo limitado. Preserve diferença entre tempo do modelo, timestamp da medida e horário da tela. Não adicione banco nem autenticação fictícia. Mostre testes da lógica e limitações da demo HTTP.

**Checkpoint:** browser renderiza; status e horário mudam; tendência cresce dentro do limite; queda OPC é visível.

## 6 — Integrar os dois serviços e observar

> Integre cliente/interface ao Compose sem ampliar exposição. Valide DNS tep-opc no container Streamlit, dependências de startup, restart policy e healthchecks. Acrescente comandos config/build/up/ps/logs. Teste indisponibilidade inicial do OPC, reconexão e reinício somente do serviço tep-opc. Não altere nftables nem configure o Pi3: forneça diagnóstico em camadas para serviço, Docker, host, rota e gateway. Diferencie “HTTP responde” de “OPC está saudável”. Entregue evidências reais e pendências do ambiente físico.

**Checkpoint:** `dc ps`, logs, status da tela e UAExpert coerentes; restart deve causar interrupção/reconexão visível, não garantia de continuidade do estado do simulador.

## 7 — Fechar documentação e repetibilidade

> Revise arquivos da aula, requisitos e testes. Execute os testes disponíveis e registre comandos, versão do ambiente, resultado e limitações. Confirme que dados mock são usados apenas nos testes. Documente instalação/preparação prévia, execução, parada sem remover volumes genéricos e recuperação do servidor manual. Confira links e comandos do roteiro. Não apague trabalho existente; não faça push/PR/merge nesta tarefa curta. Liste o que falta testar no Pi4 ARM64 e na rede Pi3/Windows.

**Checkpoint:** outro leitor encontra uma sequência reproduzível; todas as etapas não executadas estão marcadas, sem “validado” genérico.

## Prompts de diagnóstico — use somente o que corresponde ao sintoma

### DNS/rede interna Docker

> O Streamlit não resolve tep-opc. Leia Compose e os logs anexos. Verifique nome do serviço, rede compartilhada, endpoint interno e se o teste foi feito dentro do container correto. Não use localhost para chegar ao outro container. Proponha primeiro comandos somente de leitura; não recrie redes globais nem altere DNS do host.

### Falha OPC ou tags ausentes

> O transporte chega na4840, mas o cliente OPC falha. Compare endpoint/discovery URL, namespace URI, browse path, status, timeout e políticas de segurança do servidor real. Não assuma que TCP aberto significa sessão OPC válida. Não troque por números aleatórios. Peça o traceback mínimo e proponha uma correção pequena com teste.

### Porta publicada, mas navegador não acessa

> HTTP funciona no Pi4, mas não no Windows. Analise bind PI4_BIND_IP, Compose ports, rota Windows, retorno Pi4 e contador do firewall Pi3. Separe INPUT/OUTPUT/FORWARD e o caminho via salto SSH. Não sugira flush, accept geral ou abrir internet. Use rede/firewall_8501.md e identifique a primeira camada que falha.

### Build/instalação sem internet

> O build no Pi4 falha ao baixar dependências. Antes de mudar firewall, verifique se o gateway da aula2 bloqueia egress por projeto. Classifique erro de DNS, rota, TLS, pacote ou arquitetura. Não adicione regra ampla de saída nem ligue Wi-Fi escondido. Proponha pré-carregamento autorizado de imagens ARM64 ou preparação em janela separada; preserve a topologia filmada.

### Startup, healthcheck e logs

> Analise dc ps e dc logs anexos. Diferencie container iniciado, processo vivo, HTTP saudável e OPC conectado. Verifique retries/timeouts e dependências de build. Não use sleep fixo como única garantia de prontidão. Não esconda erro com restart infinito nem diga que restart policy recupera todo container unhealthy automaticamente.

### Dados parados ou gráficos estranhos

> Compare SourceTimestamp, status OPC, horário da coleta e tempo do modelo. Verifique reconexão, cache, limites do histórico e reruns Streamlit. Dado antigo deve estar marcado. Reiniciar o simulador pode reiniciar sua trajetória; não invente continuidade/historiador persistente.

## Regra de apresentação

Thiago explica o objetivo; Sol entrega o comando ou esclarecimento quando chamada; Thiago executa e lê o resultado. Não despejar sete prompts nem todos os comandos de uma vez. O Codex auxilia na implementação; o critério de confiança é evidência e revisão, não o tamanho do prompt.

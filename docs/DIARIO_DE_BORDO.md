# Diário de bordo

## 2026-10-30 — Consultas SQL do historiador da Aula 5

- **Alterações:** criadas sete consultas parametrizadas, executor SQLite somente leitura, testes, roteiro de SQL e instruções para execução local, em contêiner e por SSH. Comparação de pressão, temperatura e XMV(10) usa `ciclo_id`; agregados excluem leituras inválidas.
- **Testes:** seis testes locais de consulta passaram no Windows, incluindo execução pela linha de comando, banco vazio, limites, resultados inválidos e associação por ciclo. Testes em imagem ARM64 local sob emulação passaram para consultas e historiador; o teste integrado usou TEP 2.5.0 e asyncua 2.1.0. Em uma execução dinâmica, o simulador avançou 23 passos durante seis ciclos, que produziram 318 leituras; pressão e temperatura apresentaram seis valores distintos e a pressão seis timestamps de publicação distintos. Os valores são simulados, não medições de campo.
- **Planos:** o SQLite local usou `leituras_tag_coleta` nas buscas por tag e intervalo; na comparação usou a chave `(ciclo_id, tag_id)` para temperatura e água de resfriamento. A agregação por minuto usou B-trees temporárias para agrupamento e ordenação. Esses planos não comprovam desempenho no Pi.
- **Decisões e limitações:** filtros usam horário UTC de coleta; `SourceTimestamp` de publicação não comprova análise nova. Leituras do mesmo ciclo não são necessariamente simultâneas. O acesso por SSH e contêiner é apenas documentado; nenhum Raspberry, banco de produção, servidor, coletor, Compose ou aula anterior foi alterado.
- **Próxima ação:** avaliar os planos e custos com volumes representativos e operação real somente em etapa autorizada; definir retenção e backup antes de uso contínuo.

## 2026-10-30 — Historiador SQLite das 53 tags, incremento 3B

- **Alterações:** criados historiador e testes, com catálogo, ciclos UUID e leituras em banco independente. Gravação atômica, idempotência por ciclo e tag, WAL, chaves estrangeiras, índices e metadados de qualidade; README e contexto atualizados.
- **Testes:** sete testes do historiador passaram com TEP 2.5.0 na revisão fixada e asyncua 2.1.0 em imagem ARM64 local sob emulação; os seis testes locais de banco também passaram no Windows. Verificados rollback após falha, reabertura, repetição de ciclo, leituras iguais em ciclos diferentes, valores inválidos, qualidades, timestamp ausente, banco alheio e leitura concorrente. Os 13 testes anteriores da Aula 4 e 12 da Aula 5 passaram.
- **Experimento integrado:** TEP inicializado e avançado uma vez, servidor OPC UA local, coletor reiniciado e banco temporário reaberto. Cinco ciclos com intervalo alvo de 0,1 s no teste armazenaram 265 registros, preservando leituras iguais; arquivo SQLite após fechamento: 131.072 bytes. Médias: leitura 39,27 ms, transação 12,84 ms e ciclo ativo 59,71 ms. Tempos ativos individuais: 67,48; 60,97; 56,19; 54,91; 59,03 ms. Medições em loopback sob emulação, sem espera, conexão ou descoberta; não representam o Pi nem operação de longa duração.
- **Problemas e decisões:** um timestamp de publicação não prova nova análise das XMEAS(23–41). Ausências e qualidades ruins são preservadas; não há fila durável, recuperação de amostra perdida ou retenção automática. Falha no banco interrompe a operação. Nenhum Raspberry ou banco de produção foi acessado, não houve deploy nem alterações nas Aulas 1 a 4, no servidor ou no Compose.
- **Próxima ação:** definir política de backup, retenção e recuperação e validar capacidade, rede e impacto de implantação apenas em etapa autorizada.

## 2026-10-30 — Coletor OPC UA das 53 tags, incremento 3A

- **Alterações:** criado coletor independente que descobre os grupos por URI de namespace, valida os 53 identificadores, lê em lote e conserva `DataValue`, status, qualidade, valor e timestamps em memória. Documentados uso, reconexão e limites; nenhuma persistência foi implementada.
- **Testes e resultados:** três testes do novo coletor passaram com asyncua 2.1.0 e TEP 2.5.0 na revisão fixada, em imagem ARM64 local sob emulação. Passaram também os nove testes anteriores da Aula 5, incluindo integração com o coletor original da Aula 4. O servidor real e um namespace extra confirmaram leitura dos 53 valores, sem aliases. Foram exercitados nós ausentes e inesperados, status Good/Uncertain/Bad, timestamp ausente e reconexão com falha simulada. Em dez leituras locais de 53 tags, duração média 40,69 ms, mínima 36,60 ms e máxima 45,41 ms; medição inclui leitura e conversão, não conexão ou descoberta, com loopback e emulação.
- **Problemas e decisões:** XMEAS(23–41) permanecem análises amostradas; timestamp de publicação não prova análise nova. Escritas do servidor não são atômicas. O teste de reconexão usa simulação, sem comprovar recuperação de rede real. Nenhum acesso aos Raspberry, deploy, mudança do servidor ou alteração das Aulas 1 a 4.
- **Próxima ação:** em incremento futuro autorizado, definir persistência, validade, deduplicação e recuperação; validar desempenho e reconexão no ambiente real antes de operação.

## 2026-10-30 — Integração do coletor da Aula 4 com servidor da Aula 5

- **Alterações:** criado teste local que executa o servidor real da Aula 5 e o coletor original da Aula 4 em processos separados. Atualizados README e contexto; preservados os arquivos das Aulas 1 a 4.
- **Testes e resultados:** teste de integração passou em imagem local ARM64 sob emulação, com TEP na revisão `9a6c8e5fcef4a2850778704e7793c87b0a187005` e asyncua 2.1.0. O coletor encontrou Pressao, Nivel e Temperatura e gravou pelo menos duas amostras por sinal em SQLite temporário em `/data` montado como tmpfs. Verificados valores finitos, unidades, StatusCode Good, timestamps, esquema, WAL e ausência de duplicatas; a reapresentação de uma amostra real à função original de gravação não criou outra linha. Os 13 testes existentes da Aula 4 e os oito da Aula 5 passaram no mesmo tipo de ambiente.
- **Problemas e decisões:** não foi observada incompatibilidade no cenário local. A comunicação foi limitada a loopback; o banco temporário e os processos foram descartados ao final. O teste não comprova desempenho, operação contínua ou conectividade no Pi.
- **Próxima ação:** realizar eventuais testes no ambiente real apenas em etapa autorizada e após inventário de serviços e riscos. Nenhum Raspberry foi acessado e não houve deploy.

## 2026-10-30 — Publicação OPC UA das tags da Aula 5

- **Alterações:** servidor separado para 41 XMEAS e 12 XMV do catálogo, metadados e três tags legadas; documentação e testes locais. Nenhum arquivo das Aulas 1 a 4 ou Compose foi alterado.
- **Testes:** oito testes passaram em imagem ARM64 local sob emulação, com TEP 2.5.0 na revisão `9a6c8e5fcef4a2850778704e7793c87b0a187005` e asyncua 2.1.0. Cliente local conferiu 53 NodeIds únicos, hierarquia, metadados, valores, timestamps e permissões, com tentativa de escrita rejeitada. Comparadas as três tags legadas e seus NodeIds com a sequência da Aula 4. No Python Windows, cinco testes passaram e três foram ignorados por falta das dependências. `git diff --check` conferido.
- **Problemas e decisões:** a comparação inicial de DataValue completo falhou por diferenças de `ServerTimestamp` entre escritas; o teste foi corrigido para verificar valor, StatusCode e SourceTimestamp. Os nós são atualizados sequencialmente; o timestamp não representa uma nova análise das XMEAS amostradas. Nenhum teste completo do coletor da Aula 4 contra o servidor novo foi realizado.
- **Próxima ação:** em etapa autorizada, validar integração operacional e impacto em recursos e serviços no Pi 4 antes de qualquer implantação. Não houve acesso aos Raspberry, deploy ou alteração de rede.

## 2026-10-30 — Catálogo de variáveis da Aula 5

- **Alterações:** criado catálogo com 41 XMEAS e 12 XMV, leitura validada por nomes e índices, testes e README; adicionadas regras Git para bancos SQLite, WAL e SHM. Atualizado o contexto. As Aulas 1 a 4 não foram modificadas.
- **Testes:** testes locais de estrutura e mapeamento executados no Windows; teste de integração ignorado ali por ausência de `tep`. Na imagem local ARM64 `iilab-aula04-verificacao:local`, sob emulação, os cinco testes passaram com TEP 2.5.0 na revisão `9a6c8e5fcef4a2850778704e7793c87b0a187005`; os 13 testes existentes da Aula 4 também passaram. Foram verificadas as regras de exclusão para `.sqlite`, `.sqlite3`, `.db` e respectivos WAL/SHM.
- **Problemas e decisões:** `%` das XMV representa a escala do modelo, não uma unidade física de vazão ou rotação. Leituras das análises amostradas podem permanecer inalteradas entre ciclos. Não houve acesso aos Raspberry, deploy ou alterações ao servidor OPC UA.
- **Próxima ação:** definir a publicação OPC UA das tags somente em etapa futura autorizada e validar a integração correspondente.

## 2026-10-29 — Publicação do material da Aula 4

- **Alterações:** criada uma branch a partir de `8c142fd`, que contém a Aula 3 publicada; adicionados à pasta `aulas/aula-04` os arquivos locais do servidor, coletor, interface, Compose e testes, adaptando apenas os caminhos de build para a nova pasta. Criados README, roteiro e checklist; índice do repositório e contexto atualizados. O workspace original com alterações não rastreadas foi preservado.
- **Testes:** `docker compose --env-file .env.example config --quiet` passou; sintaxe Python verificada. Treze testes de servidor, coletor e leitor passaram localmente com imagem ARM64 sob emulação, incluindo dados e servidor sintéticos. O Python do Windows não tinha `asyncua`; os testes completos foram executados na imagem que possui a dependência. O build local do Dockerfile adaptado para ARM64 passou sob emulação, incluindo `pip check`; não comprova disponibilidade de downloads ou funcionamento atual nos Raspberry.
- **Problemas e decisões:** a composição usada na preparação difere da composição publicada na Aula 3, portanto a Aula 4 contém composição própria e orienta a inventariar uma instalação existente antes de substituições. O histórico relata dados reais coletados, mas não fornece prova final da reinicialização do coletor, build/healthcheck da interface ou regra corrigida da 8501. O retorno ao prompt após a tentativa com erro não comprovou a liberação. Não houve acesso aos equipamentos ou alterações de rede nesta publicação.
- **Próxima ação:** confirmar as pendências do roteiro no ambiente real quando solicitado e, se desejado, divulgar o link direto da branch publicada.

## 2026-10-29 — Aula 4, preparação da interface

- **Alterações locais:** serviço `interface` Streamlit em `aulas/aula-03/compose.yaml`, leitor SQLite, Dockerfile, dependência fixada e documentação; não altera coletor ou servidor. Volume inteiro é montado somente leitura e consultas usam `mode=ro` e limites; sem alteração de esquema.
- **Testes:** quatro testes sintéticos de leitura concorrente, ausência, esquema inesperado, qualidade e atraso passaram; Compose local validado. AppTest Streamlit com três sinais sintéticos produziu três métricas sem exceções. Build local Linux ARM64 com dependências e `pip check` passou sob emulação; não prova acesso aos pacotes na rede do Pi. Inspeção do estado efetivo do Pi pendente.
- **Estado relatado:** usuário informou duas consultas reais com contagens crescentes e qualidade Good; os resultados ainda não foram apresentados nesta sessão. Tentativa SSH não interativa expirou e foi solicitada inspeção via sessão interativa.
- **Próxima ação:** conferir esquema/índices/volume reais, build e dependências ARM64; validar leitura simultânea real, HTTP local e correspondência da tela, sem alterar firewall.

## 2026-10-29 — Inventário do histórico para a Aula 4

- **Evidências informadas pelo usuário:** `tep-opc` saudável e `coletor` ativo; volume `aula-03_historico` em `/var/lib/docker/volumes/aula-03_historico/_data`, banco `/data/leituras.sqlite3` em WAL. Esquema e índice `amostra_origem` coincidem com o código local. Havia 527 amostras de pressão, 520 de nível e 517 de temperatura; últimas amostras de 28/10/2026, qualidade Good e status 0. Nenhuma escuta em 8501 foi apresentada.
- **Comparação:** hash remoto do Compose `81d2abb27b99554495bd841458e9cc4065e2fecbd2557294621b1a9d8b83d81f` coincide com o local anterior ao serviço de interface. Build ARM64 local e testes sintéticos passaram, mas não se confirmou conectividade para dependências no Pi.
- **Pendências:** confirmar relógio UTC do Pi e arquivos WAL/SHM; preservar backup, enviar arquivos, validar Compose, subir apenas a interface e verificar HTTP, leitura concorrente e correspondência com dados reais. Firewall não foi alterado.

## 2026-10-29 — Transferência da interface informada pelo usuário

- **Evidências:** hashes dos quatro arquivos da interface e do Compose temporário coincidem com os locais; hash do `compose.yaml.antes-interface` coincide com o Compose original. `docker compose -f compose.yaml.interface-novo config --quiet` passou no Pi.
- **Pendências:** conferir relógio UTC, WAL/SHM, bind e volume no Compose expandido antes do build; depois construir/iniciar somente interface e validar dados reais e HTTP. Sem alteração de firewall e sem inicialização da interface até aqui.

## 2026-10-29 — Verificação de volume e relógio para a interface

- **Evidências informadas:** configuração expandida publica somente `10.77.0.10:8501`, interface monta `historico` em `/data` somente leitura e usa o mesmo SQLite do coletor. Arquivos `.sqlite3-wal` e `.sqlite3-shm` existiam e eram legíveis; 4,2 GB disponíveis.
- **Relógio:** o Pi informou `2026-10-28 13:26:44 UTC`; referência da sessão indicava `2026-10-29 22:12 UTC` posteriormente. A diferença exata depende do momento da execução no Pi. O horário UTC real deve ser verificado antes de considerar os timestamps confiáveis; nenhum relógio foi ajustado. Atualidade na interface é relativa ao relógio do próprio Pi.
- **Próxima ação:** build somente de `interface` solicitado na sessão SSH; aguardando resultado e eventual impedimento de downloads. Não houve implantação da interface nem mudança de firewall.

## 2026-10-29 — Coletor OPC UA e SQLite, preparação local

- **Alterações:** acrescentados serviço `coletor`, Dockerfile derivado da imagem existente, código e testes; rede e servidor locais preservados. Documentadas configuração e políticas de qualidade, timestamps e duplicatas.
- **Testes e resultados:** Compose local validado com `.env.example`; sintaxe e dependências asyncua 2.1.0 locais verificadas. Testes sintéticos cobrem gravação, WAL, reabertura, qualidade Bad/Uncertain, timestamp ausente, duplicatas, pausa de reconexão e leitura de três sinais em servidor sintético. Testes anteriores de configuração preservados.
- **Problemas:** SSH BatchMode por salto expirou durante banner; usuário informou conexão interativa bem-sucedida. A inspeção do Pi, o Compose efetivo, imagem ARM64 disponível no Pi, endpoint interno, dados reais, reinício e UAExpert ainda não foram verificados nesta sessão.
- **Decisões:** não executar mudanças remotas sem confirmar caminho, arquivos e serviço em execução; sem Streamlit, alterações de rede ou remoção de volumes.
- **Próxima ação:** obter inventário da sessão SSH interativa, comparar o Compose e a imagem real, preservar cópias e prosseguir com deploy somente do coletor quando o acesso operacional permitir.

## 2026-10-29 — Inventário informado pelo usuário

- **Observações:** usuário executou inspeção no Pi 4: `devcontrol`, `aarch64`, 4,2 GB livres, Compose 2.26.1-4; serviço saudável `aula-03-tep-opc-1`, projeto `aula-03`, Compose em `/home/devadmin/iilab-aula03/aulas/aula-03/compose.yaml`. Docker exige sudo. O identificador da imagem do container é `sha256:67df057d42604ee3af619515afbea237b04df78a263ce5fb165a14be1519af49`, igual ao da imagem local examinada.
- **Testes:** build local ARM64 da imagem do coletor derivada dessa imagem passou; execução local com tmpfs e emulação abriu SQLite 3.46.1 em WAL e importou asyncua 2.1.0. Nova tentativa SSH não interativa expirou; o usuário confirma acesso interativo.
- **Pendências e próxima ação:** examinar conteúdo e permissões do Compose real, rede e dependências no Pi; preservar backup e só então transferir e iniciar o coletor. Descoberta interna, dados reais, persistência e UAExpert seguem sem teste nesta sessão. Nenhuma alteração remota.

## 2026-10-29 — Comparação do Compose em execução

- **Observações informadas pelo usuário:** Compose remoto em `/home/devadmin/iilab-aula03/aulas/aula-03` define `tep-opc` e rede `iilab`; o container usa `aula-03_iilab` com alias `tep-opc`. Imagem `iilab-tep-opc:local` é `linux/arm64`, UID 10001. Dockerfile e servidor têm os mesmos SHA-256 das cópias locais.
- **Verificação:** SHA-256 do Compose remoto `91b186b50386d8d464c7adac02161fa57d1a5abd1c0a383a41d4144b45576815` coincide com o Compose local antes de acrescentar o coletor. O build local do coletor reutilizou a imagem com o mesmo identificador da imagem do Pi e não precisou baixar dependências.
- **Pendências:** pedido ao usuário backup sem sobrescrever e verificação de que arquivos novos não existem; transferência e alterações remotas ainda não foram realizadas. Comprovar descoberta, coleta real, persistência e UAExpert após o deploy.

## 2026-10-29 — Backup informado pelo usuário

- **Alterações:** na sessão interativa, usuário criou `compose.yaml.antes-coletor` no diretório confirmado, após verificar que o backup e os arquivos novos não existiam.
- **Resultado:** SHA-256 do backup e do Compose em execução coincidem: `91b186b50386d8d464c7adac02161fa57d1a5abd1c0a383a41d4144b45576815`. Transferência dos três arquivos por SCP solicitada ao usuário devido à indisponibilidade de SSH não interativo; resultado pendente. Nenhum serviço foi alterado.
- **Próxima ação:** conferir hashes recebidos, validar Compose, substituir o arquivo apenas após validação e iniciar somente o coletor; verificar os dados reais e preservação do servidor.

## 2026-10-29 — Arquivos recebidos e Compose validado no Pi

- **Resultado informado pelo usuário:** hashes de `coletor.py`, `Dockerfile.coletor` e `compose.yaml.coletor-novo` no Pi coincidem com os locais; o backup conserva o hash original. `docker compose -f compose.yaml.coletor-novo config --quiet` passou e a imagem base foi confirmada `linux/arm64`.
- **Próxima ação:** build somente do coletor, substituição do Compose após build bem-sucedido e inicialização de `coletor` com `--no-deps --no-build`; pedido ao usuário para executar na sessão interativa. Dados reais, descoberta interna e persistência permanecem pendentes. Nenhuma inicialização do coletor foi observada até este registro.

## 2026-10-29 — Inicialização do coletor informada pelo usuário

- **Resultado:** usuário informou criação do volume `aula-03_historico` e inicialização de `aula-03-coletor-1`. `docker compose ps` mostrou o servidor `aula-03-tep-opc-1` saudável, com idade de criação anterior, e o coletor ativo. A indicação `4840/tcp` no coletor é metadado herdado da imagem, sem porta publicada no host na saída observada.
- **Pendências:** saída de logs, endpoint descoberto, gravações reais, caminho do volume e contagem crescente ainda não foram apresentados. Depois verificar persistência após reinício do coletor e leitura do UAExpert.

Memória operacional para continuidade entre sessões. Acrescente uma entrada por etapa, com data, etapa, alterações realizadas, testes executados e resultados observados, problemas encontrados, decisões e próxima ação. Não inclua credenciais ou dados secretos.

## 2026-10-28 — Preparação do workspace

- **Alterações realizadas:** clone da branch principal do repositório na raiz vazia; criação da branch local `aula-03-desenvolvimento-ao-vivo`; preparação das instruções e dos documentos de contexto, arquitetura, acesso e plano.
- **Testes e resultados:** inspeção local da árvore e do Git: base `main` no commit `37f5a31`, com material das Aulas 1 e 2 e sem implementação da Aula 3 na árvore clonada. A verificação é documental e não confirma o funcionamento dos equipamentos.
- **Problemas encontrados:** o endpoint original no código da Aula 1 usa `192.168.1.19`, enquanto o exemplo da Aula 2 usa `10.77.0.10`; endereços e configurações atuais precisam ser confirmados. A persistência da configuração da Aula 2 após reinicialização não foi validada no roteiro.
- **Decisões:** preservar integralmente os arquivos das aulas; tratar endereços como históricos; manter a Aula 3 apenas planejada. A branch antecipada mencionada pelo usuário não foi usada.
- **Próxima ação:** aguardar solicitação para iniciar a Aula 3 e, então, começar pela inspeção autorizada da infraestrutura.

## 2026-10-28 — Inventário local e proposta de containerização

- **Alterações realizadas:** leitura dos documentos e inspeção local do código das Aulas 1 e 2; atualização do contexto e do estado do plano. Nenhum código funcional foi alterado e nenhum arquivo de container foi criado.
- **Testes executados e resultados observados:** inspeção estática identificou `servidor_opc.py` como servidor e simulador integrados, as três variáveis e suas unidades, as dependências diretas fixadas e o endpoint histórico. As regras locais da Aula 2 são exemplos e não confirmam o estado real do firewall. Não foram executados testes de aplicação, Docker, SSH ou rede.
- **Problemas encontrados:** endpoint fixo histórico pode ser incompatível com um IP diferente no container; bind e endereço anunciado precisam ser resolvidos e testados. Dependências transitivas, disponibilidade ARM64 e obtenção de imagem e pacotes em rede restrita precisam de verificação. A publicação de portas pode afetar o controle de acesso e exige análise.
- **Decisões:** manter a Aula 1 intacta e propor um serviço TEP/OPC UA separado, com Compose e Streamlit em etapas posteriores. O usuário informou ARM64, versões Docker/Compose, espaço, porta livre e administração supervisionada; não houve confirmação remota nesta sessão.
- **Próxima ação:** aguardar revisão da proposta antes de implementar; definir e validar o mecanismo de endpoint e o fornecimento das dependências.

## 2026-10-28 — Adaptação do endpoint OPC UA

- **Alterações realizadas:** criação de `aulas/aula-03/servidor_opc.py`, testes de configuração e documentação. Atualizados o contexto, plano e README para refletir a etapa. As Aulas 1 e 2 foram preservadas.
- **Testes executados e resultados observados:** revisão estática comparou a lógica TEP e OPC UA com o original; seis testes `unittest` passaram para valores padrão, ambiente, configuração independente e valores inválidos. `git diff --check` passou para alterações rastreadas. A fonte oficial do asyncua v2.1.0 foi consultada para `socket_address` e descoberta.
- **Problemas encontrados:** `asyncua` e `tep` não estão disponíveis no Python local; a inicialização e a descoberta reais não foram testadas. O asyncua pode reescrever o endpoint na descoberta para a URL pedida ou o socket; a resposta de cada caminho precisa de verificação. A mesma porta é usada para escuta e endpoint base.
- **Decisões:** manter padrão histórico, `/tep/` e 4840; aceitar escuta e host base separados e rejeitar `0.0.0.0` como host base. Nenhum Dockerfile, Compose ou Streamlit foi criado; não houve SSH ou instalação.
- **Próxima ação:** aguardar revisão e validar a execução e os endpoints anunciados em ambiente compatível quando autorizado.

## 2026-10-28 — Preparação da imagem e do Compose TEP/OPC UA

- **Alterações realizadas:** criados Dockerfile multi-stage, Compose com um serviço `tep-opc`, `.env.example` e `.dockerignore`; atualizados o README e os documentos de contexto e plano. O código das Aulas 1 e 2 e o servidor adaptado foram preservados.
- **Testes executados e resultados observados:** revisão estática do Dockerfile, das entradas do contexto de build e do servidor; seis testes locais do endpoint passaram. `docker compose config` local, com Compose v5.6.0 e o arquivo de exemplo, resolveu o contexto da raiz, a rede bridge, o único serviço e a publicação `10.77.0.10:4840:4840/tcp`. `git check-ignore` confirmou `.env` ignorado e `.env.example` permitido; `git diff --check` passou para arquivos rastreados.
- **Problemas encontrados:** não houve build nem teste da imagem, do Compose 2.26.1 no Pi, do daemon, da rede Docker, da descoberta OPC UA ou da execução do TEP. Dependências transitivas, fontes de build, imagens e espaço ARM64 seguem a verificar; a descoberta pode devolver URLs diferentes por cliente e o Docker pode interagir com o firewall.
- **Decisões:** Python 3.13 slim trixie por proximidade com o ambiente histórico; imagem final com usuário não privilegiado, bind restrito ao IP de host informado, logs rotativos, `SIGINT` e healthcheck TCP que não atesta medições. Nenhum dispositivo, serviço, firewall ou rede foi alterado.
- **Próxima ação:** aguardar revisão; em etapa autorizada, obter os artefatos, validar build ARM64 e realizar os testes de operação e descoberta documentados.

## Modelo para próximas entradas

```text
## AAAA-MM-DD — Etapa
- Alterações realizadas:
- Testes executados e resultados observados:
- Problemas encontrados:
- Decisões:
- Próxima ação:
```

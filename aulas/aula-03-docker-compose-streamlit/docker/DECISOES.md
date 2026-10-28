# Decisões técnicas e limites

## Evolução, não reescrita

`aulas/aula-01` e `aulas/aula-02` permanecem intactas. `servidor_opc.py` nesta aula é uma evolução mínima do script original: importa `os`, configura o endpoint anunciado por variável de ambiente e separa o socket de escuta (`server.socket_address`, API existente no asyncua 2.1.0). O restante da simulação, semente, passo, índices, unidades e publicação foi preservado. A cópia didática evita alterar retroativamente a aula publicada.

O TEP **já estava integrado ao servidor OPC UA**. Por isso há dois serviços, e não três: `tep-opc` e `streamlit`. Não iniciamos uma segunda simulação independente.

## Contrato OPC real

- Namespace URI: `urn:laboratorio-industrial:tep`.
- Browse path: `Objects → Reator → Pressao / Nivel / Temperatura`.
- Índices do vetor TEP: 6, 7, 8; unidades no servidor: `kPa(g)`, `%`, `C`.
- O cliente lê a propriedade `Unidade`, `StatusCode` e `SourceTimestamp` do servidor; não substitui por suposições.
- NodeIds numéricos são atribuídos dinamicamente pelo servidor. O cliente resolve a URI do namespace e BrowseNames a cada conexão; não fixa `ns=2` nem identificadores numéricos.
- Qualidade ruim, valor não finito e timestamp ausente/desatualizado (>10 s) invalidam a leitura. Relógios devem estar sincronizados; horário de chegada não substitui horário de origem.
- Servidor anunciado: `opc.tcp://10.77.0.10:4840/tep/` no exemplo externo. Escuta dentro do container em `0.0.0.0:4840`. Cliente interno conecta diretamente pelo DNS Compose `tep-opc`; não usa o IP externo para sua conexão.

## Rede e exposição

Usamos uma rede bridge própria do Compose para comunicação entre serviços, **não** `network_mode: host`. Ela não é uma política de bloqueio de saída: não configuramos `internal: true`, pois ambos os serviços precisam publicar portas para clientes externos. A segmentação entre TI e TA continua no Pi 3; Docker roda só no Pi 4.

As portas são publicadas somente no IPv4 de `PI4_BIND_IP`, não em todas as interfaces. Não use `0.0.0.0`, não exponha à internet. A publicação Docker no Pi 4 e a autorização nftables no Pi 3 são controles diferentes. Confirme o IP antes de subir: bind em IP inexistente falha. Confira também rotas, VPNs e caminhos alternativos.

OPC UA segue anônimo/sem criptografia e Streamlit não inclui autenticação. Isso é uma demonstração em rede restrita, não configuração de produção. Docker pode interagir com o firewall **do Pi 4**; não confunda isso com o encaminhamento independente no Pi 3. Não alteramos nenhum daemon, regra ou interface do laboratório durante a preparação cloud.

## Runtime e dados

- Dependências diretas do servidor preservadas: NumPy 2.2.6, asyncua 2.1.0, TEP no commit `9a6c8e5fcef4a2850778704e7793c87b0a187005` (pacote 2.5.0).
- Streamlit 1.50.0; imagem oficial Python 3.12 slim Bookworm multi-arquitetura. O Python do container independe do Python 3.13 instalado no host; escolhemos 3.12 por ser o runtime testado em cloud. Dependências transitivas e imagem base não estão fixadas por digest; reconstruções futuras podem variar. Guarde as imagens validadas para a gravação.
- Compilador/git/pkg-config somente no estágio de build do TEP. A imagem Python oficial inclui headers do Python; não usar o pacote de desenvolvimento de outra versão.
- Ambos os serviços executam como UID 10001, sem privilégios adicionais; capacidades removidas e `no-new-privileges` habilitado.
- Uma thread coletora por processo Streamlit, conexão OPC persistente, amostra por segundo, reconexão exponencial de 1 a 15 segundos. UI atualiza a cada 2 s enquanto aberta; o coletor compartilha dados entre sessões, sem criar um cliente por aba.
- Buffer circular de 600 amostras em RAM. Não há banco, volume de dados, historiador nem retenção após reinício. Reiniciar TEP reinicia o processo simulado na semente; reiniciar Streamlit perde tendências.
- Estado desconectado não mostra última leitura como valor atual. Tendências antigas permanecem visíveis, com aviso explícito.
- Logs no stdout com rotação Docker (2 arquivos de até 5 MB por serviço). `restart: unless-stopped` reinicia processos encerrados, mas **não** reinicia automaticamente um processo apenas marcado `unhealthy`.
- Healthcheck OPC faz leitura real, além de testar porta. Healthcheck HTTP Streamlit apenas confirma aplicação web: não prova comunicação OPC. `depends_on: service_healthy` ordena a partida; a reconexão do cliente resolve quedas posteriores.

## Pré-build e instalação

O firewall da aula 2 bloqueia novas saídas do Pi 4 por padrão. Não prometa que `apt`, `pip`, `git clone`, `docker build` ou `pull` funcionarão atravessando essa política. Prepare Docker/Compose e imagens ARM64 antes da gravação, em caminho de manutenção autorizado, ou transfira imagens ARM64 previamente construídas com `docker save`/`load` pelo salto SSH. Não abra internet genérica nem instale Docker no Pi 3 para contornar isso.

Antes de subir, pare de forma controlada o servidor Python manual da aula anterior para liberar a porta 4840. Não use `killall python` nem remova containers/volumes de outros projetos. Valide espaço com `df -h` e `docker system df`: 5 GB livres é uma observação histórica, não garantia de capacidade para build e cache.

## Referências oficiais consultadas

- https://docs.docker.com/reference/compose-file/services/
- https://docs.docker.com/compose/how-tos/networking/
- https://docs.docker.com/engine/network/port-publishing/
- https://docs.docker.com/engine/install/debian/
- https://docs.streamlit.io/develop/concepts/architecture/fragments
- https://github.com/jkitchin/tennessee-eastman-profbraatz/tree/9a6c8e5fcef4a2850778704e7793c87b0a187005

Validação ARM64 e funcionamento Docker devem ser conferidos no preflight; não foram demonstrados por execução do código Python x86 em cloud.

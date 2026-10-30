# Aula 5 — catálogo, servidor e coleta OPC UA TEP

O catálogo organiza 41 medições `XMEAS(1)` a `XMEAS(41)` e 12 variáveis manipuladas `XMV(1)` a `XMV(12)`. O servidor desta pasta publica essas 53 variáveis e três variáveis legadas a partir de um único simulador. O coletor independente lê as 53 tags canônicas; um historiador separado pode gravá-las em SQLite. A implementação da Aula 4 continua independente.

`CATALOGO` é uma tupla de registros imutáveis com identificador estável, categoria (`medicao` ou `manipulada`), índice Python base zero, descrição original da biblioteca e unidade. Em cada vetor, o índice é o número da variável menos um: `XMEAS(7)` usa índice 6; `XMV(12)` usa índice 11. A ordem das medições e manipuladas é independente.

`ler_tags(simulador)` usa `get_measurement_names()`, `get_mv_names()`, `get_measurements()` e `get_manipulated_vars()`. Confere os nomes, a ordem e os tamanhos antes de retornar um dicionário de identificadores e valores `float`. Uma biblioteca incompatível gera `ValueError`. O chamador inicializa e avança o simulador; a leitura não altera os valores. O dicionário é um retrato, não uma garantia de simultaneidade, qualidade ou atualização das análises amostradas.

```python
from tep import TEPSimulator
from catalogo_tags import CATALOGO, ler_tags

simulador = TEPSimulator(backend="python", random_seed=1234)
simulador.initialize()
valores = ler_tags(simulador)
print(CATALOGO[6], valores["XMEAS(7)"])
```

As descrições seguem os nomes da revisão TEP fixada nas aulas. As unidades das medições seguem a [referência da API dessa revisão](https://github.com/jkitchin/tennessee-eastman-profbraatz/blob/9a6c8e5fcef4a2850778704e7793c87b0a187005/docs/api.md#measurement-index-reference): `kPa(g)` explicita pressão manométrica, e `mol%` é porcentagem molar. As manipuladas usam `%` da escala normalizada do modelo, não uma unidade física de vazão ou velocidade; a escala dos 12 valores é indicada nos modos operacionais em [constants.py](https://github.com/jkitchin/tennessee-eastman-profbraatz/blob/9a6c8e5fcef4a2850778704e7793c87b0a187005/src/tep/constants.py). Isso não caracteriza uma medição física direta. O [Fortran original](https://github.com/jkitchin/tennessee-eastman-profbraatz/blob/9a6c8e5fcef4a2850778704e7793c87b0a187005/teprob.f) documenta a ordem e unidades de medição.

## Servidor OPC UA

O namespace é `urn:laboratorio-industrial:tep`. Em `Objects`, o servidor mantém `Reator/Pressao`, `Reator/Nivel` e `Reator/Temperatura`, inclusive a propriedade legada `Unidade`, e cria `TEP/XMEAS` e `TEP/XMV`. Cada variável nova usa NodeId string `TEP.XMEAS(1)` a `TEP.XMEAS(41)` ou `TEP.XMV(1)` a `TEP.XMV(12)` no namespace da URI acima. O índice numérico do namespace é atribuído pelo servidor; resolva-o pela URI. As variáveis novas possuem propriedades `Unidade`, `Descricao`, `Categoria` e `IndicePython`, conforme o catálogo. As 56 variáveis de dados são somente leitura para clientes, inclusive as XMV.

O simulador avança uma vez por ciclo e o mesmo retrato alimenta as tags novas e legadas. `Reator/Pressao`, `Nivel` e `Temperatura` correspondem a `XMEAS(7)`, `XMEAS(8)` e `XMEAS(9)`. A publicação usa `StatusCode Good` e o mesmo `SourceTimestamp` UTC para um ciclo, como horário de leitura/publicação no servidor. `Good` identifica a publicação bem-sucedida pelo servidor, sem avaliar a qualidade física ou a idade da análise. As escritas são sequenciais: um cliente que leia durante o ciclo pode observar valores de ciclos diferentes. O intervalo procura ser de um segundo, sem garantia de tempo real.

**XMEAS(23–41) são análises amostradas**: seus valores podem permanecer iguais entre ciclos. Um novo timestamp de publicação não comprova que uma nova análise física ocorreu nem indica a idade real da amostra no modelo. O relógio do computador precisa estar correto para interpretar os timestamps.

### Execução local no Windows

Use um ambiente Python compatível e as dependências fixadas da Aula 4. No PowerShell, a partir da raiz do repositório:

```powershell
python -m venv aulas/aula-05/.venv
.\aulas\aula-05\.venv\Scripts\Activate.ps1
python -m pip install --only-binary=:all: numpy==2.2.6
python -m pip install -r aulas/aula-04/requirements-servidor.txt
python -m pip check
cd aulas/aula-05
$env:OPC_UA_BIND_HOST = '127.0.0.1'
$env:OPC_UA_ADVERTISE_HOST = '127.0.0.1'
$env:OPC_UA_PORT = '14840'
python servidor_opc.py
```

Conecte um cliente local a `opc.tcp://127.0.0.1:14840/tep/` e use Ctrl+C para encerrar. Confirme que a porta escolhida está livre. Se as variáveis de ambiente não forem definidas, o endpoint padrão é o histórico da Aula 4, `192.168.1.19:4840`; esse endereço não representa uma configuração atual verificada.

O servidor usa `NoSecurity` e acesso anônimo, como a Aula 4: limite-o a uma rede de laboratório autorizada e não o exponha à internet. O exemplo acima usa somente loopback. Esta etapa não inclui Docker Compose ou implantação. Antes de qualquer uso no Pi 4, será necessário verificar compatibilidade ARM64, recursos, endpoint, portas, acesso e impacto sobre o servidor existente; estes aspectos não foram testados no equipamento.

## Coletor das 53 tags

Com o servidor local em execução e o mesmo ambiente Python ativo, abra outro PowerShell, ative o ambiente e execute a partir de `aulas/aula-05`:

```powershell
python coletor_opc.py opc.tcp://127.0.0.1:14840/tep/
```

O coletor resolve o namespace pela URI e navega somente `TEP/XMEAS` e `TEP/XMV`. Ele exige exatamente os 53 identificadores do catálogo, sem duplicatas ou nós extras; as três variáveis em `Reator` não são coletadas. A versão asyncua 2.1.0 lê os atributos em um lote com `Client.read_attributes`, preservando o `DataValue` recebido. Cada `Leitura` expõe identificador, valor, `SourceTimestamp`, código numérico e qualidade `Good`, `Uncertain`, `Bad` ou `Desconhecida`, horário UTC da coleta e o objeto `DataValue` original. Valores, timestamps ou status ausentes permanecem ausentes. O horário de coleta é registrado ao receber o lote; a duração usa relógio monotônico e inclui a leitura e a conversão, sem incluir descoberta ou conexão.

`ciclos(url)` fornece ciclos ao consumidor, com período alvo de um segundo. Após falha, encerra a sessão e tenta reconectar e redescobrir os nós a cada cinco segundos; uma divergência persistente do catálogo também provoca tentativas espaçadas. O programa de linha de comando mostra cada lote em JSON. Use Ctrl+C para encerrar. O coletor, isoladamente, não possui fila nem persistência; o historiador descrito abaixo é um consumidor separado.

Uma leitura em lote reduz chamadas, mas não garante que o servidor tenha atualizado todas as variáveis atomicamente. `SourceTimestamp` continua sendo o horário de publicação do servidor da Aula 5, inclusive para XMEAS(23–41), e não indica a realização ou idade de uma nova análise do processo. O coletor mantém o `StatusCode` recebido; não transforma qualidade ruim em valor válido.

## Historiador SQLite

Com o servidor local ativo, no ambiente Python da Aula 5, escolha explicitamente um arquivo **dedicado** e execute:

```powershell
python historico_sqlite.py opc.tcp://127.0.0.1:14840/tep/ --banco .\historico_aula05.sqlite3 --intervalo 5
```

O intervalo alvo é configurável e, se omitido, é de cinco segundos. O arquivo é independente do banco da Aula 4. O historiador rejeita bancos com tabelas que não tenham a identificação e a versão próprias da Aula 5; não migra nem modifica intencionalmente outros esquemas. A pasta escolhida deve existir. Use Ctrl+C para encerrar.

O esquema possui `tags` (identificador estável, categoria, índice, descrição e unidade), `ciclos` (UUID, horário e hash do conteúdo) e `leituras` (ciclo, tag, valor, timestamps, StatusCode, qualidade e validade). Chaves estrangeiras ligam as leituras ao catálogo e ao ciclo; a chave `(ciclo_id, tag_id)` é única, com índices por tag e horário de coleta ou origem. Cada ciclo completo de 53 tags é gravado em uma transação; falha faz rollback. São usados WAL, `busy_timeout` de 5 segundos e foreign keys. Na reabertura, o esquema e catálogo são verificados sem apagar o histórico; divergências exigem migração futura, não são sobrescritas.

Uma nova aquisição recebe um UUID diferente mesmo se valor ou `SourceTimestamp` não mudar. Reapresentar o mesmo ID com o mesmo conteúdo é idempotente; com outro conteúdo, é erro. Essa garantia depende de reutilizar o mesmo UUID: o processo não possui fila durável para recuperar uma aquisição não gravada após falha, nem assegura entrega exatamente uma vez entre reinicializações. Erros de banco interrompem o historiador para não ocultar perda; não há retenção automática. Monitore armazenamento e planeje backup consistente com WAL antes de uso operacional.

Valores não numéricos, booleanos e não finitos são gravados como `NULL` com `valor_invalido`. Um valor numérico finito de qualidade `Bad` ou `Uncertain` é preservado com `qualidade_nao_good`; a qualidade e o StatusCode originais continuam disponíveis. Status ausente é `Desconhecida`, sem inventar um código. Um valor Good sem timestamp de origem recebe `source_timestamp_ausente`. `valido` indica número finito, qualidade Good e timestamp de origem presente; não prova que o processo é saudável ou que uma nova análise foi realizada. Timestamps presentes devem informar fuso horário e são registrados em UTC.

Cada ciclo concluído mostra um JSON com UUID, contagem e tempos de leitura, gravação e ciclo ativo. O tempo de gravação mede a transação; o total soma a leitura ao processamento e gravação, sem incluir espera pelo próximo ciclo, conexão ou descoberta. As escritas das tags no servidor podem ocorrer entre leituras, mesmo em uma requisição em lote.

## Consultas SQL

As consultas predefinidas e o executor somente leitura estão em [sql/consultas.sql](sql/consultas.sql) e [consultar_historico.py](consultar_historico.py). O [roteiro de consultas](sql/README.md) apresenta exemplos locais, em contêiner e por SSH, parâmetros, planos de execução e uma sequência didática. As comparações relacionam as tags pelo ciclo de aquisição; médias por minuto usam apenas leituras válidas e o horário UTC de coleta. Os testes e exemplos locais utilizam bancos temporários e dados simulados.

## Testes

Na pasta `aulas/aula-05`, execute `python -m unittest -v test_catalogo_tags test_servidor_opc test_coletor_opc test_historico_sqlite test_consultas_sql`. Os testes de estrutura usam simulador sintético; os de integração usam o simulador TEP e cliente OPC UA local e são ignorados se faltarem dependências. Use o ambiente com a revisão fixada em `aulas/aula-04/requirements-servidor.txt` para executá-los integralmente. O teste do historiador usa arquivo temporário, coleta cinco ciclos, reabre o banco e informa os tempos e o tamanho final do arquivo. O teste das consultas também avança o simulador durante a coleta. Essas medidas não representam o desempenho em rede ou no Pi.

O teste `test_integracao_coletor_aula04` inicia os programas reais das Aulas 4 e 5 em processos locais e usa um banco temporário sob `/data`, como exigido pelo coletor. Execute-o em um container POSIX com `/data` descartável e a revisão fixada do TEP; ele não usa o banco do laboratório. Por exemplo, no PowerShell, a partir da raiz, com a imagem local `iilab-aula04-verificacao:local` já disponível:

```powershell
docker run --rm --platform linux/arm64 --mount "type=bind,source=${PWD},target=/trabalho,readonly" --tmpfs /data:rw,nosuid,nodev,size=32m,mode=1777 --workdir /trabalho/aulas/aula-05 --entrypoint python iilab-aula04-verificacao:local -B -m unittest -v test_integracao_coletor_aula04
```

O teste usa loopback e uma porta efêmera, requer asyncua 2.1.0 e verifica a revisão instalada do TEP. Em ambientes sem as dependências ou sem `/data` POSIX ele é ignorado; um resultado ignorado não comprova compatibilidade. A imagem local e a emulação ARM64 não substituem testes no Raspberry Pi.

# Guia de estudo do código — Aula 5

Para Thiago estudar e usar com o VS Code aberto. Base da primeira versão, lida em 30/10/2026: repositório `C:\dev\lab-ii`, branch `feat/aula-05-tags-sql`, HEAD `eab3cd446972082ec7710cb4bfec01857a081bc0`. Naquele momento, além dos commits, a base incluía alterações não commitadas no README da Aula 5, contexto e diário, e arquivos novos de empacotamento, operação, preflight, healthchecks e testes. Este guia descreve **essa combinação**, não apenas o commit original; consulte o Git para o estado atual.

Antes da criação deste guia, o Git indicava modificados `aulas/aula-05/README.md`, `docs/CONTEXTO_PROJETO.md` e `docs/DIARIO_DE_BORDO.md`. Estavam não rastreados `.dockerignore`, `Dockerfile`, `OPERACAO_GRAVACAO.md`, `compose.yaml`, `consultar_sql_stdin.py`, `healthcheck_aula05.py`, `requirements.txt`, a pasta `preflight/`, `sql/consulta_ao_vivo.sql`, `test_consultar_sql_stdin.py` e `test_healthcheck_aula05.py`, todos sob `aulas/aula-05/`. O guia e sua entrada no diário foram acrescentados posteriormente.

**Como ler as evidências:** “código” significa inspeção dos arquivos; “teste anterior” significa resultado registrado no [diário](../../docs/DIARIO_DE_BORDO.md); “relato” significa informação apresentada por Thiago. Na gravação posterior à primeira versão deste guia, Thiago relatou carga e operação da imagem no Pi, 53 tags cadastradas e observadas e crescimento de 14 ciclos/742 leituras para 17/901. A transferência teve três hashes OK apresentados. A auditoria relatada não encontrou ciclos com contagem diferente de 53; isso não prova ausência de falhas ou lacunas. O historiador foi relatado como `Exited` após parada; os demais estados não foram confirmados. O teste local anterior usou emulação ARM64; a revisão atual não acessou o Pi. Painel novo das 53 tags fica para outra aula.

## 1. Visão geral em uma página

```text
TEP: TEPSimulator(backend="python") e sim.step()
       |
       v
servidor_opc.py + catalogo_tags.py
  ├─ Reator/Pressao, Nivel, Temperatura: aliases legados
  └─ TEP/XMEAS e TEP/XMV: 53 variáveis canônicas OPC UA
       |
       v
coletor_opc.py — descobre pela URI, lê DataValue em lote
       |
       v
historico_sqlite.py — 53 leituras por ciclo em tags/ciclos/leituras
       |
       v
consultar_historico.py + sql/consultas.sql — consultas predefinidas
consultar_sql_stdin.py — uma consulta recebida por stdin, somente leitura
```

O [catálogo](catalogo_tags.py) descreve a variável; o [servidor](servidor_opc.py) publica; o [coletor](coletor_opc.py) recebe dados; o [historiador](historico_sqlite.py) valida e persiste; as [consultas](sql/consultas.sql) fazem perguntas ao histórico. A interface da Aula 4 serve à retomada da aula anterior; não é o painel novo de 53 tags.

[Dockerfile](Dockerfile) monta uma imagem a partir de uma base local ARM64 identificada e verifica versões. [Compose](compose.yaml) usa essa única imagem em dois serviços: `tep-opc` e `historiador`. Apenas o primeiro cria um `TEPSimulator`; o historiador é cliente. O volume novo guarda o banco. [OPERACAO_GRAVACAO.md](OPERACAO_GRAVACAO.md) contém condições e comandos da transição e da consulta; não os execute automaticamente.

## 2. O que mudou da Aula 4 para a Aula 5

| Aspecto | Aula 4 no código do repositório | Aula 5 no código lido |
| --- | --- | --- |
| Variáveis | Três medidas em `Reator`. | 41 `XMEAS` e 12 `XMV` em grupos, mais três aliases legados. |
| Identidade | Coletor tem mapa `SINAIS` para pressão, nível e temperatura. | Catálogo comum com ID, categoria, índice, descrição e unidade. |
| Aquisição | Lê cada um dos três nós em sequência. | Descobre os grupos e usa `read_attributes` em lote para as 53 canônicas. |
| SQLite | Uma tabela `leituras`; índice único por sinal e timestamp de origem quando presente. | Tabelas `tags`, `ciclos` e `leituras`; chave por ciclo e tag; preserva repetições em ciclos diferentes. |
| Qualidade e tempo | Já registrava qualidade, status, timestamps e valores inválidos. | Mantém esses conceitos e acrescenta validação de qualidade/status e indicação específica de timestamp ausente. |
| Robustez | Já possuía WAL, `busy_timeout` e reconexão com pausa. | Esses conceitos foram mantidos/ampliados; cada ciclo de 53 leituras é uma transação. |
| Consulta/visualização | Coletor grava e interface Streamlit lê histórico de três sinais. | Executor e consultas SQL para o novo esquema; o painel das 53 tags não está neste pacote. |

Compare [coletor da Aula 4:26](../aula-04/coletor.py#L26), [servidor da Aula 4:51](../aula-04/servidor_opc.py#L51) e os arquivos da Aula 5 abaixo. A Aula 4 já tinha histórico e tratamento de falhas: não apresente SQLite, qualidade ou reconexão como invenções da Aula 5.

## 3. Guia por arquivo

### 3.1 `catalogo_tags.py` — o endereço e o significado de cada sinal

**Problema, entrada e saída.** Sem uma referência comum, o número do vetor, o nome publicado e a unidade poderiam se desencontrar. `CATALOGO` é uma tupla de `Tag` imutáveis. `ler_tags(simulador)` recebe um simulador inicializado e devolve um dicionário `identificador → float`; é chamado pelo servidor.

**Estruturas:** `Tag`, `_MEDIDAS`, `_MANIPULADAS`, `CATALOGO` e `ler_tags`. A descrição da temperatura aparece em [catalogo_tags.py:26](catalogo_tags.py#L26).

Trecho 1 — [catalogo_tags.py:60](catalogo_tags.py#L60):

```python
CATALOGO = tuple(
    Tag(f"XMEAS({indice + 1})", "medicao", indice, nome, unidade)
    for indice, (nome, unidade) in enumerate(_MEDIDAS)
) + tuple(
```

O trecho é o começo da expressão completa, que também concatena as `XMV`. `enumerate` gera índices base zero; `indice + 1` constrói a identidade do TEP. `f"..."` insere o número no texto.

Trecho 2 — [catalogo_tags.py:75](catalogo_tags.py#L75):

```python
    nomes_medidas = tuple(simulador.get_measurement_names())
    nomes_manipuladas = tuple(simulador.get_mv_names())
    if nomes_medidas != tuple(nome for nome, _ in _MEDIDAS):
        raise ValueError("Nomes ou ordem das medições TEP incompatíveis com o catálogo")
```

Antes de associar dados aos índices, o código compara nomes e ordem. Depois chama `get_measurements()` e `get_manipulated_vars()`, confere 41 e 12 posições e constrói o dicionário. A validação evita aceitar silenciosamente uma biblioteca com ordem diferente.

**No VS Code:** abra primeiro a temperatura na linha 26; depois pule para a construção na linha 60 e o retorno na linha 85.

**Fala sugerida:** “Na Aula 4 eu usava diretamente os índices de três medições. Agora criei um catálogo que une nome, unidade e posição. A temperatura é a nona variável do TEP, mas no vetor Python ela está no índice oito. Antes de ler, eu comparo a ordem informada pela biblioteca com a ordem esperada. Assim, se eu trocar a versão e a lista mudar, prefiro receber um erro a publicar uma variável com o nome errado.”

**Apoio:** detalhes de `dataclass`, geradores e anotações `Any` podem ficar para perguntas. `frozen=True` impede alterar os campos de uma instância.

**Limites:** o catálogo descreve a revisão fixada; não descobre unidades de um equipamento físico. `XMV` está em percentual da escala do modelo, não em vazão física.

### 3.2 `servidor_opc.py` — expor os valores

**Problema, entrada e saída.** Um cliente precisa de nós com endereço e tipo estáveis. `main()` configura endpoint, inicializa o simulador, cria o servidor asyncua e executa ciclos. `criar_nos` recebe servidor/simulador; `publicar_valores` recebe nós e valores; `executar_ciclo` avança e publica.

Trecho 1 — [servidor_opc.py:77](servidor_opc.py#L77):

```python
    for tag in CATALOGO:
        grupo = "XMEAS" if tag.categoria == "medicao" else "XMV"
        nodeid = ua.NodeId(f"TEP.{tag.identificador}", ns)
```

O loop percorre o catálogo. Para temperatura, o identificador string é `TEP.XMEAS(9)` no namespace registrado. O código cria variável `Double` e propriedades de unidade, descrição, categoria e índice.

Trecho 2 — [servidor_opc.py:97](servidor_opc.py#L97):

```python
        dado = ua.DataValue(ua.Variant(valores[identificador], ua.VariantType.Double))
        dado.StatusCode = ua.StatusCode(ua.StatusCodes.Good)
        dado.SourceTimestamp = horario
        await no.write_value(dado)
```

Um número é convertido em `Variant`, envolvido em `DataValue` e publicado com qualidade e horário. Em [linha 101](servidor_opc.py#L101), se houver alias, ele recebe esse mesmo dado. `await` espera a operação assíncrona.

Trecho 3 — [servidor_opc.py:106](servidor_opc.py#L106):

```python
    if not simulador.step():
        raise RuntimeError("O modelo interrompeu a simulacao.")
    valores = ler_tags(simulador)
```

O simulador avança uma vez por ciclo e esse retrato alimenta as variáveis. O laço em `main` busca um ciclo por segundo de relógio, sem tempo real garantido.

**No VS Code:** mostre `LEGADAS`, a construção do NodeId e `executar_ciclo`; evite abrir cada nó um por um.

**Fala sugerida:** “Aqui eu não faço 53 simuladores. Eu avanço uma única simulação, pego um retrato e percorro o catálogo para publicar os nós. O endereço de cada variável inclui sua identidade; pressão, nível e temperatura antigos continuam existindo para um cliente que já navegava em Reator. A escrita é feita pelo servidor. O cliente OPC UA não recebe permissão de atuação nas manipuladas.”

**Apoio:** validação de nomes DNS e bind em `_validar_host` pode ficar fora da fala principal.

**Limites:** `NoSecurity`/anônimo é para rede restrita, não segurança de produção. Publicações são sequenciais; `Good` não prova saúde física nem uma nova análise em `XMEAS(23–41)`.

### 3.3 `coletor_opc.py` — encontrar e ler sem misturar aliases

**Problema, entrada e saída.** O cliente não deve depender do número do namespace nem coletar os aliases junto às canônicas. `descobrir_tags(client)` retorna nós na ordem do catálogo; `ler_ciclo(client, nos)` retorna `Ciclo` com `Leitura`; `ciclos(url, intervalo, espera_reconexao)` é um gerador assíncrono usado pelo historiador.

Trecho 1 — [coletor_opc.py:39](coletor_opc.py#L39):

```python
    ns = await client.get_namespace_index(NAMESPACE)
    tep = await client.nodes.objects.get_child([f"{ns}:TEP"])
```

A URI é estável, mas o número de namespace pode mudar. O código navega `XMEAS`/`XMV` e compara os nomes encontrados com o catálogo, recusando ausentes, extras e duplicados.

Trecho 2 — [coletor_opc.py:66](coletor_opc.py#L66):

```python
    inicio = time.monotonic()
    dados = await client.read_attributes([nos[nome] for nome in identificadores])
    coleta = datetime.now(timezone.utc)
```

Uma chamada lê os atributos em lote; `monotonic` mede duração e o relógio UTC marca a coleta após a resposta. A montagem em [linha 72](coletor_opc.py#L72) preserva valor, `SourceTimestamp`, código, qualidade e `DataValue`.

Trecho 3 — [coletor_opc.py:97](coletor_opc.py#L97):

```python
        except asyncio.CancelledError:
            raise
        except Exception:
            LOG.exception("Falha de conexão, descoberta ou leitura; nova tentativa em %.1f s", espera_reconexao)
            await asyncio.sleep(espera_reconexao)
```

Cancelamento passa adiante; outras falhas fecham a sessão e aguardam antes de tentar de novo. O padrão de reconexão é cinco segundos.

**No VS Code:** comece na resolução de namespace, mostre `read_attributes` e termine no retry.

**Fala sugerida:** “O servidor me entrega o endereço, mas eu não fixo o número do namespace: eu peço o índice a partir da URI. Depois comparo os grupos com o catálogo, para não misturar os três aliases com as 53 variáveis. Em vez de solicitar um valor por vez, leio os atributos em lote e preservo o DataValue. Se a conexão cair, a sessão é refeita com uma pausa; isso não significa que eu recuperei o que passou durante a queda.”

**Apoio:** implementação de `asyncio`, `zip` e detalhes do gerador podem ser explicados apenas se perguntarem. `yield` entrega um ciclo ao consumidor.

**Limites:** lote não é fotografia atômica do simulador; não há fila durável. A reconexão em rede real no Pi ainda precisa ser demonstrada.

### 3.4 `historico_sqlite.py` — transformar cada aquisição em histórico

**Problema, entrada e saída.** O código precisa guardar ciclos inteiros e preservar qualidade sem transformar dados inválidos em bons. `abrir_banco` recebe o caminho e inicializa/verifica o esquema. `_utc` e `_linha` normalizam; `gravar_ciclo` recebe conexão, ID e `Ciclo`; `registrar` consome o gerador OPC UA e grava continuamente. `main` recebe URL, `--banco` e `--intervalo`.

Trecho 1 — [historico_sqlite.py:34](historico_sqlite.py#L34):

```python
    db = sqlite3.connect(caminho, timeout=5, isolation_level=None)
    try:
        db.execute("PRAGMA busy_timeout=5000")
        db.execute("PRAGMA foreign_keys=ON")
```

O arquivo é independente; a função verifica identificação e versão e ativa WAL. Chaves estrangeiras relacionam dados ao catálogo e ao ciclo. O esquema começa em [linha 49](historico_sqlite.py#L49).

Trecho 2 — [historico_sqlite.py:95](historico_sqlite.py#L95):

```python
    origem = _utc(leitura.source_timestamp)
    validade = ("valor_invalido" if valor is None else
                "qualidade_nao_good" if qualidade != "Good" else
                "source_timestamp_ausente" if origem is None else "valido")
```

A qualidade OPC UA e a validade calculada são campos diferentes. Número inválido vira `NULL`; qualidade ruim não é transformada em válida. Um timestamp ausente é sinalizado.

Trecho 3 — [historico_sqlite.py:126](historico_sqlite.py#L126):

```python
        db.execute("INSERT INTO ciclos VALUES (?, ?, ?)", (ciclo_id, linhas[0][3], digest))
        db.executemany("INSERT INTO leituras VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ((ciclo_id, *linha) for linha in linhas))
        db.execute("COMMIT")
```

A transação começou com `BEGIN IMMEDIATE`. Um ciclo recebe um UUID e 53 linhas; erro provoca `ROLLBACK`. Se o mesmo ID retornar com mesmo hash, não duplica; com conteúdo diferente, gera erro.

**No VS Code:** mostre `abrir_banco`, `_linha`, validação das 53 tags em [linha 110](historico_sqlite.py#L110) e `COMMIT`/`ROLLBACK`.

**Fala sugerida:** “O coletor me entrega um lote, mas eu quero poder consultar depois. Crio uma identidade para a coleta e guardo as 53 leituras juntas. Se alguma inserção falha, a transação volta: não quero um ciclo que pareça completo com metade dos sinais. O valor pode ser igual ao anterior e continuar sendo uma coleta diferente. Qualidade e validade ficam visíveis para que uma média não esconda um dado ruim.”

**Apoio:** SHA-256, `application_id`, `user_version` e `BEGIN IMMEDIATE` podem ser aprofundados só se fizerem diferença na pergunta.

**Limites:** UUID não cria fila durável; ciclo perdido antes do commit não é recuperado automaticamente. Erro de banco interrompe o historiador. Cinco segundos são alvo configurável, não garantia de tempo real. Os arquivos WAL/SHM precisam ser considerados em backup e leitura.

### 3.5 `consultar_historico.py` — perguntas prontas sem escrever

**Problema, entrada e saída.** A pessoa precisa consultar o banco existente sem criar ou modificar dados. `carregar_consultas` lê blocos nomeados; `abrir_leitura` recebe caminho; `executar` recebe nome, tag, período, limite e opção de plano; `main` apresenta JSON.

Trecho 1 — [consultar_historico.py:29](consultar_historico.py#L29):

```python
    uri = Path(caminho).resolve().as_uri() + "?mode=ro"
    db = sqlite3.connect(uri, uri=True, timeout=5)
```

`mode=ro` evita criar banco e impede escrita nele. Em seguida o código habilita `query_only` e confere versão e identificação da Aula 5.

Trecho 2 — [consultar_historico.py:64](consultar_historico.py#L64):

```python
    params = {"tag": tag, "inicio": inicial.isoformat(timespec="microseconds"),
              "fim": final.isoformat(timespec="microseconds"), "limite": limite}
    sql = carregar_consultas()[nome]
```

Os parâmetros são vinculados ao SQL em `db.execute(sql, params)`; não é necessário montar uma instrução concatenando a tag. O padrão é tag temperatura, limite 100; consulta de temperatura usa 30 minutos, demais janelas usam 24 horas.

**No VS Code:** mostre `abrir_leitura` e a ligação entre parâmetros e nomes dos blocos SQL.

**Fala sugerida:** “Depois de gravar, eu quero fazer perguntas sem correr o risco de criar outro banco por engano. Aqui abro o arquivo existente em modo de leitura e escolho uma consulta já definida. O programa fornece a tag e a janela como parâmetros. A consulta de 30 minutos usa o relógio de coleta, então a confiabilidade do horário da máquina continua sendo parte da resposta.”

**Apoio:** `Path.as_uri()`, expressão regular e `row_factory` podem ficar para perguntas.

**Limites:** o executor exige banco da Aula 5 com identificação e versão esperadas; não serve para assumir o esquema da Aula 4. Um banco WAL ativo pode precisar de arquivos auxiliares e permissões.

### 3.6 `sql/consultas.sql` — perguntas que a operação pode fazer

**Problema, entrada e saída.** Reúne consultas nomeadas; `consultar_historico.py` lê os blocos após `-- consulta: ...`. Entrada: parâmetros `:tag`, `:inicio`, `:fim` e `:limite`. Saída: linhas de tags, ciclos, amostras, resumo, comparação ou anomalias.

Trecho 1 — [sql/consultas.sql:22](sql/consultas.sql#L22):

```sql
SELECT ciclo_id, valor, source_timestamp, coleta_utc, qualidade, validade
FROM leituras
WHERE tag_id = 'XMEAS(9)' AND coleta_utc >= :inicio AND coleta_utc < :fim
ORDER BY coleta_utc DESC
LIMIT :limite;
```

A janela é inclusiva no início e exclusiva no fim. Mostra as temperaturas mais recentes pela hora de coleta.

Trecho 2 — [sql/consultas.sql:44](sql/consultas.sql#L44):

```sql
FROM leituras AS p
JOIN leituras AS t ON t.ciclo_id = p.ciclo_id AND t.tag_id = 'XMEAS(9)'
JOIN leituras AS a ON a.ciclo_id = p.ciclo_id AND a.tag_id = 'XMV(10)'
```

Os aliases `p`, `t` e `a` são três papéis da mesma tabela. A associação é por `ciclo_id`; não depende de igualdade dos timestamps.

**No VS Code:** mostre primeiro a consulta de temperatura e depois `resumo_minuto` e `comparacao`.

**Fala sugerida:** “Agora o dado já está registrado e eu consigo fazer perguntas diferentes sem mexer no processo. Aqui peço a temperatura numa janela. Depois agrupo as leituras válidas por minuto para calcular média, mínima e máxima. Na comparação, reúno pressão, temperatura e manipulada pelo identificador da mesma aquisição. Isso ajuda a observar sinais em conjunto, mas não demonstra que um causou o outro.”

**Apoio:** detalhes de planejamento SQLite e árvores temporárias de agrupamento podem ficar para quem perguntar sobre desempenho.

**Limites:** filtros e minutos usam `coleta_utc`; um relógio incorreto afeta a interpretação. O resumo ignora registros não válidos.

### 3.7 `consultar_sql_stdin.py` e `sql/consulta_ao_vivo.sql` — uma pergunta editada ao vivo

**Problema, entrada e saída.** A consulta pode ser editada no VS Code e enviada via SSH ao processo Python que abre o banco ativo, sem copiar o banco para o Windows. `consultar(caminho, sql)` retorna lista de dicionários; o programa recebe caminho como argumento e uma instrução no stdin.

Trecho 1 — [consultar_sql_stdin.py:11](consultar_sql_stdin.py#L11):

```python
    with closing(abrir_leitura(caminho)) as db:
        permitidos = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION,
                      sqlite3.SQLITE_RECURSIVE}
```

Ele reutiliza a abertura somente leitura e instala um autorizador SQLite. `db.execute(sql)` executa uma instrução; ações fora da lista são negadas.

Trecho 2 — [sql/consulta_ao_vivo.sql:2](sql/consulta_ao_vivo.sql#L2):

```sql
SELECT tag_id, COUNT(*) AS registros, MAX(coleta_utc) AS ultima_coleta
FROM leituras
GROUP BY tag_id
ORDER BY tag_id;
```

O resultado mostra tags observadas, contagem e última coleta. Não garante que todas estejam atuais.

**No VS Code:** mostre o arquivo SQL editável e a linha de `abrir_leitura`; use o procedimento de cópia do arquivo de consulta, não do banco, em [operação](OPERACAO_GRAVACAO.md).

**Fala sugerida:** “Eu posso escrever a pergunta no VS Code, mandar essa pergunta para o Pi e deixar o banco lá. O processo dentro do contêiner abre o arquivo em modo de leitura e devolve o resultado. Assim eu exploro o histórico ativo sem precisar baixar uma cópia a cada consulta. A contagem me mostra o que já chegou; depois eu ainda preciso olhar a última coleta e a qualidade.”

**Apoio:** callback `set_authorizer` e códigos internos SQLite não precisam ser decorados.

**Limites:** apenas uma instrução por execução; o caminho e contêiner da Aula 5 só serão reais depois da transição autorizada. O arquivo de consulta enviado pode ser substituído; não sobrescrever arquivo remoto desconhecido.

### 3.8 `Dockerfile` e `requirements.txt` — empacotar o ambiente

**Problema, entrada e saída.** O Pi não deve depender de baixar pacotes durante a troca. O Dockerfile parte da imagem local ARM64 `iilab-tep-opc:local`, valida dependências, copia código e prepara diretório; a saída é uma imagem usada pelos dois serviços. `requirements.txt` documenta versões diretas.

Trecho 1 — [Dockerfile:2](Dockerfile#L2):

```dockerfile
FROM iilab-tep-opc:local

USER root
WORKDIR /app
```

Trecho 2 — [Dockerfile:9](Dockerfile#L9):

```dockerfile
COPY catalogo_tags.py servidor_opc.py coletor_opc.py historico_sqlite.py consultar_historico.py consultar_sql_stdin.py healthcheck_aula05.py /app/
COPY sql/consultas.sql /app/sql/consultas.sql
USER 10001
```

O build valida versões instaladas e revisão TEP, prepara `/data` e termina com UID não privilegiado. A imagem base precisa ser identificada pelo ID antes do build; o Dockerfile não baixa pacotes.

Trecho 3 — [requirements.txt:2](requirements.txt#L2):

```text
numpy==2.2.6
asyncua==2.1.0
```

A linha seguinte fixa a revisão Git do TEP. Trecho 4 — [requirements.txt:4](requirements.txt#L4):

```text
tep @ git+https://github.com/jkitchin/tennessee-eastman-profbraatz.git@9a6c8e5fcef4a2850778704e7793c87b0a187005
```

Esse arquivo documenta dependências; o Dockerfile verifica a imagem base existente, sem executar `pip install` nesta construção. O contexto de build é filtrado pelo Docker automaticamente. Trecho 5 — [.dockerignore:1](.dockerignore#L1):

```text
*
!Dockerfile
!requirements.txt
```

Trecho 6 — [.dockerignore:11](.dockerignore#L11):

```text
!sql/
sql/*
!sql/consultas.sql
```

O primeiro padrão exclui tudo e as exceções permitem arquivos necessários; no diretório SQL, somente a consulta predefinida é incluída. Não é uma auditoria geral de segurança de arquivos fora desse contexto.

**No VS Code:** destaque a base, as versões e `USER 10001`; indique a transferência da imagem, sem apresentar o ID como senha.

**Fala sugerida:** “O Pi está em uma rede em que o download externo não é uma premissa confiável. Por isso eu construo fora dele, usando uma base ARM64 cuja identidade eu confiro, valido as dependências e levo a imagem pronta. Isso torna o procedimento mais repetível, mas não é prova automática de funcionamento no Raspberry. A imagem é uma só; quem decide qual programa iniciar é o Compose.”

**Apoio:** detalhes de camadas e cache de build podem ficar para perguntas.

**Limites:** a tag da imagem base pode mudar: verificar o ID conforme [operação](OPERACAO_GRAVACAO.md). O teste local foi emulado; a execução no Pi foi relatada por Thiago, sem inspeção remota nesta revisão.

### 3.9 `compose.yaml` — separar processos e persistência

**Problema, entrada e saída.** Define serviços, portas e volume. Recebe `PI4_BIND_IP`, `PI4_PORTA_OPC` e `OPC_UA_ADVERTISE_HOST`; usa uma imagem carregada localmente. Não cria um dashboard.

Trecho 1 — [compose.yaml:4](compose.yaml#L4):

```yaml
  tep-opc:
    image: iilab-aula05:1
    pull_policy: never
    command: ["python", "/app/servidor_opc.py"]
```

Trecho 2 — [compose.yaml:28](compose.yaml#L28):

```yaml
  historiador:
    image: iilab-aula05:1
    pull_policy: never
    command: ["python", "/app/historico_sqlite.py", "opc.tcp://tep-opc:4840/tep/", "--banco", "/data/historico_aula05.sqlite3", "--intervalo", "5"]
```

Dois contêineres partem da mesma imagem, mas executam comandos diferentes. `historiador` monta o volume `historico` e aguarda `tep-opc` saudável. O projeto `iilab-aula05` gera o volume esperado `iilab-aula05_historico`; confirme o nome efetivo no host.

**No VS Code:** mostre os dois `command`, o endpoint interno e o volume, depois a publicação de porta na linha 12.

**Fala sugerida:** “A imagem é o pacote; o contêiner é o processo em execução. Uso a mesma imagem para duas responsabilidades: o servidor mantém o simulador, e o historiador conecta como cliente. O banco fica em um volume próprio, independente dos contêineres e do histórico da Aula 4. Eu preparo a imagem antes e mando o Compose não baixar outra. A troca da porta só acontece depois da demonstração antiga e da autorização.”

**Apoio:** YAML, rotação de logs e sinais podem ficar como apoio.

**Limites:** o uso no Pi durante a gravação foi relatado pelo usuário; o estado atual da publicação TCP deve ser conferido. Persistência após reiniciar o Pi não foi testada.

### 3.10 `healthcheck_aula05.py` — sinal de saúde com alcance limitado

**Problema, entrada e saída.** O Compose precisa de sinal automático para servidor e historiador. `verificar_servidor()` e `verificar_historico()` não recebem argumentos; o programa seleciona `servidor` ou `historico` pelo argumento e retorna código de saída.

Trecho 1 — [healthcheck_aula05.py:15](healthcheck_aula05.py#L15):

```python
        nos = await descobrir_tags(client)
        ciclo = await ler_ciclo(client, nos)
        if len(ciclo.leituras) != 53 or any(x.qualidade != "Good" or x.source_timestamp is None for x in ciclo.leituras):
            raise RuntimeError("OPC UA não retornou 53 tags Good com timestamp")
```

Trecho 2 — [healthcheck_aula05.py:27](healthcheck_aula05.py#L27):

```python
        idade = (datetime.now(timezone.utc) - datetime.fromisoformat(ultima[1])).total_seconds()
        total, bons = db.execute("SELECT COUNT(*), SUM(CASE WHEN qualidade='Good' AND validade='valido' THEN 1 ELSE 0 END) FROM leituras WHERE ciclo_id=?", (ultima[0],)).fetchone()
        if not 0 <= idade <= 60 or total != 53 or bons != 53:
            raise RuntimeError("Último ciclo incompleto, não Good ou desatualizado")
```

**No VS Code:** compare as duas funções e pergunte o que cada uma efetivamente verifica.

**Fala sugerida:** “Saúde não é só saber se a porta abriu. Neste pacote, o primeiro teste tenta descobrir as 53 variáveis com qualidade e timestamp. O segundo olha o último ciclo do banco, conta as linhas válidas e verifica sua idade. Isso ajuda a perceber uma coleta parada, mas não me diz se todo o histórico está íntegro nem se o processo físico está saudável. O relógio correto é parte dessa verificação.”

**Apoio:** código de saída e detalhes de `closing` podem ficar para perguntas.

**Limites:** teste do servidor exige timestamp presente, não verifica sua idade. Teste do banco depende do relógio, verifica apenas o último ciclo e considera ruim uma leitura não Good.

## 4. Temperatura de ponta a ponta: `XMEAS(9)`

1. **Simulador → vetor:** `TEPSimulator` é inicializado em [servidor_opc.py:119](servidor_opc.py#L119); `executar_ciclo` chama `step()`. A nona medição está no índice Python **8**. [catalogo_tags.py:69](catalogo_tags.py#L69) obtém nomes e vetor pela API TEP.
2. **Vetor → catálogo:** [catalogo_tags.py:26](catalogo_tags.py#L26) contém `"Reactor Temperature", "deg C"`. Em [linha 60](catalogo_tags.py#L60), `indice + 1` forma `XMEAS(9)`.
3. **Catálogo → nó:** [servidor_opc.py:77](servidor_opc.py#L77) cria `TEP.XMEAS(9)` como NodeId string em namespace registrado pela URI. Criação do nó acontece na inicialização; publicação de valor acontece depois.
4. **Número → OPC UA:** [servidor_opc.py:96](servidor_opc.py#L96) envolve o float em `Variant(Double)` e `DataValue` com `Good` e `SourceTimestamp` UTC. O mesmo valor alimenta `Reator/Temperatura`, com unidade legada `C`, enquanto a canônica usa `deg C`.
5. **OPC UA → leitura:** [coletor_opc.py:39](coletor_opc.py#L39) resolve namespace pela URI, descobre `XMEAS(9)` e lê o lote em [linha 67](coletor_opc.py#L67). O `DataValue` vira `Leitura` com valor, código, qualidade, origem e `coleta_utc`.
6. **Leitura → histórico:** [historico_sqlite.py:73](historico_sqlite.py#L73) transforma a leitura em uma tupla SQL e marca validade. [registrar:147](historico_sqlite.py#L147) cria UUID; [gravar_ciclo:126](historico_sqlite.py#L126) grava o ciclo e suas 53 linhas.
7. **Histórico → pergunta:** [sql/consultas.sql:21](sql/consultas.sql#L21) seleciona últimas temperaturas; [linha 28](sql/consultas.sql#L28) agrega registros válidos por minuto de coleta. O SQL devolve linhas, e `consultar_historico.py` as converte em JSON.

## 5. Conceitos para explicar

- **XMEAS × XMV:** `XMEAS` são medições do modelo; `XMV` são variáveis manipuladas do modelo. Publicar `XMV` para leitura não habilita escrita ou atuação por cliente.
- **ID × índice:** `XMEAS(9)` é a identidade; `8` é a posição em Python. O catálogo junta ambos e confere a ordem da biblioteca.
- **URI × índice do namespace:** `urn:laboratorio-industrial:tep` identifica logicamente o namespace. O índice numérico é atribuído pelo servidor e o cliente o resolve na conexão.
- **Canônica × alias:** `TEP/XMEAS(9)` é a tag canônica; `Reator/Temperatura` mantém compatibilidade. O coletor da Aula 5 descobre apenas canônicas.
- **Criar nó × publicar valor:** criar estrutura ocorre na inicialização; escrever `DataValue` acontece no ciclo de execução.
- **Lote × simultaneidade:** `read_attributes` reduz chamadas, mas o servidor atualiza nós em sequência; o lote não é garantia de mesmo instante físico.
- **Valor, qualidade e validade:** valor é o conteúdo; `StatusCode`/qualidade vêm do OPC UA; `validade` é a interpretação do historiador. `SourceTimestamp` é origem/publicação do servidor; `coleta_utc` marca a recepção do lote.
- **UUID × relógio:** UUID identifica o ciclo; horário dá contexto temporal. Usar apenas horário como chave pode colidir ou refletir relógio incorreto.
- **Transação, chave e WAL:** `BEGIN`/`COMMIT` gravam o ciclo inteiro ou `ROLLBACK` desfaz. A chave `(ciclo_id, tag_id)` impede repetição da mesma tag no mesmo ciclo; chaves estrangeiras ligam tabelas. WAL permite leitura concorrente, mas backup deve incluir o estado consistente do WAL.
- **Repetição × duplicação:** valor igual em dois UUIDs é histórico de duas coletas. Repetir mesmo UUID e mesmo conteúdo não adiciona linhas; mesmo UUID com conteúdo diferente é erro.
- **Docker:** imagem é pacote; contêiner é execução; Compose descreve serviços; volume guarda dados fora do ciclo de vida do contêiner. Não significa que o volume foi testado no Pi.

## 6. SQL explicado progressivamente

Execute em banco da **Aula 5 identificado**, com acesso somente leitura. As consultas a seguir são exemplos didáticos e não foram executadas para este guia.

### 6.1 Quais tags estão cadastradas e quais já apareceram?

```sql
SELECT t.identificador, t.descricao, COUNT(l.tag_id) AS leituras
FROM tags AS t
LEFT JOIN leituras AS l ON l.tag_id = t.identificador
GROUP BY t.identificador, t.descricao
ORDER BY t.identificador;
```

`LEFT JOIN` conserva tags sem leitura; `COUNT` mostra zero quando não houve correspondência. Se todas foram observadas, cada uma deve ter pelo menos uma linha. Isso não prova atualização recente nem qualidade.

### 6.2 Quantos ciclos, quantas leituras e quando foi a última coleta?

```sql
SELECT (SELECT COUNT(*) FROM ciclos) AS ciclos,
       (SELECT COUNT(*) FROM leituras) AS leituras,
       (SELECT MAX(coleta_utc) FROM leituras) AS ultima_coleta;
```

`COUNT` mede volume; `MAX` encontra o maior horário textual UTC gravado. Banco vazio retorna zero, zero e `NULL`; isso **não valida integridade**. Relógio incorreto compromete “última”.

### 6.3 Quais as últimas temperaturas?

```sql
SELECT ciclo_id, valor, coleta_utc, source_timestamp, qualidade, validade
FROM leituras
WHERE tag_id = 'XMEAS(9)'
ORDER BY coleta_utc DESC
LIMIT 10;
```

`WHERE` escolhe temperatura; `ORDER BY` e `LIMIT` restringem a apresentação. Se houver dados, aparecem até dez linhas. Não prova que o valor esteja atual ou que todas as outras tags chegaram.

### 6.4 Qual média, mínima e máxima por minuto?

```sql
SELECT substr(coleta_utc, 1, 16) AS minuto_utc,
       COUNT(*) AS amostras, AVG(valor) AS media,
       MIN(valor) AS minima, MAX(valor) AS maxima
FROM leituras
WHERE tag_id = 'XMEAS(9)' AND validade = 'valido' AND valor IS NOT NULL
GROUP BY substr(coleta_utc, 1, 16)
ORDER BY minuto_utc DESC
LIMIT 30;
```

`GROUP BY` agrupa coleta UTC por minuto; `AVG/MIN/MAX` resumem valores válidos. O resultado depende dos dados; se não houver válidos, fica vazio. Não demonstra frequência uniforme nem causalidade.

### 6.5 Como comparar pressão, temperatura e água do reator?

```sql
SELECT p.ciclo_id, p.coleta_utc, p.valor AS pressao_kpa_g,
       t.valor AS temperatura_c, a.valor AS agua_reator_percentual,
       p.validade AS pressao_validade, t.validade AS temperatura_validade,
       a.validade AS agua_validade
FROM leituras AS p
JOIN leituras AS t ON t.ciclo_id = p.ciclo_id AND t.tag_id = 'XMEAS(9)'
JOIN leituras AS a ON a.ciclo_id = p.ciclo_id AND a.tag_id = 'XMV(10)'
WHERE p.tag_id = 'XMEAS(7)'
ORDER BY p.coleta_utc DESC
LIMIT 20;
```

O `JOIN` usa o mesmo ciclo; as colunas de validade precisam ser lidas junto com os valores. Se houver ciclos completos, há até vinte linhas. Comparação não demonstra causalidade nem simultaneidade física.

### 6.6 Existe algum ciclo incompleto?

```sql
SELECT c.id, COUNT(DISTINCT l.tag_id) AS tags_no_ciclo
FROM ciclos AS c
LEFT JOIN leituras AS l ON l.ciclo_id = c.id
GROUP BY c.id
HAVING COUNT(DISTINCT l.tag_id) <> 53;
```

`HAVING` filtra grupos depois da contagem. Nenhuma linha pode significar ciclos completos **ou banco vazio**: faça a contagem de ciclos primeiro. Cobertura histórica não comprova atualização recente; compare contagens ou coletas em momentos distintos.

## 7. Roteiro de navegação no VS Code — 6 a 8 minutos

| Tempo | Arquivo e trecho | Mensagem e transição |
| --- | --- | --- |
| 0:00–0:40 | `catalogo_tags.py:26` | “Temperatura é XMEAS(9).” Em seguida, mostrar como o nome vira identidade. |
| 0:40–1:30 | `catalogo_tags.py:60` e `:75` | Índice 8, identidade 9, nome e unidade; conferir ordem. Ir para criação do nó. |
| 1:30–2:40 | `servidor_opc.py:77` e `:96` | NodeId, `Double`, `DataValue`; alias legado. Ir para o cliente. |
| 2:40–3:35 | `coletor_opc.py:39` e `:66` | URI, descoberta e lote; origem versus coleta. Ir para persistência. |
| 3:35–4:50 | `historico_sqlite.py:95` e `:106` | Validade, UUID, 53 linhas, transação. Ir para a pergunta. |
| 4:50–5:50 | `sql/consultas.sql:21` e `:28` | Últimas temperaturas e resumo válido por minuto. |
| 5:50–6:40 | `sql/consultas.sql:39` | Comparar por ciclo, sem alegar causalidade. Ir para execução segura. |
| 6:40–8:00 | `consultar_sql_stdin.py:10` e `compose.yaml:28` | Consulta no banco ativo, serviço e volume; encerrar com limites e evidências. |

Abertura antes do passeio: mostrar a aplicação da Aula 4 no UAExpert e Streamlit, se estiver funcionando e confirmada. A troca para a Aula 5 é controlada e só ocorre após os pré-requisitos e autorização descritos em [operação](OPERACAO_GRAVACAO.md). Não faça rollback de código para criar artificialmente o começo da aula.

## 8. Perguntas do público — respostas curtas

**Por que SQLite?** É um banco em arquivo que atende ao experimento e simplifica as consultas locais. A escolha não comprova capacidade para escala ou alta disponibilidade de produção.

**Por que 53 tags e três aliases?** São 41 medições e 12 manipuladas canônicas. Os três aliases em `Reator` mantêm o caminho de clientes anteriores; o coletor novo não grava os aliases novamente.

**Por que catálogo?** Para manter identidade, posição, descrição e unidade consistentes e detectar diferença de ordem na biblioteca.

**Se OPC UA falhar?** O coletor registra erro, espera e tenta reconectar/redescobrir. Se o banco falhar, o historiador interrompe a operação e a transação é revertida quando aplicável.

**Perde dados durante interrupção?** Pode perder. Não há fila durável nem recuperação automática dos períodos desconectados.

**Como sabemos que todas chegaram?** O coletor exige o conjunto esperado na descoberta e o historiador exige 53 identidades por ciclo. No banco, compare tags cadastradas com observadas e conte as tags em cada ciclo; catálogo sozinho não prova coleta atual.

**Por que juntar por ciclo e não só timestamp?** O ciclo identifica a aquisição; timestamps podem faltar, repetir ou ser diferentes. A associação por ciclo também não garante simultaneidade física.

**Como consultar o banco ativo sem copiar para Windows?** Envie uma instrução SQL ao Pi por SSH e execute `consultar_sql_stdin.py` no contêiner, em `mode=ro`. O comando e as condições estão em [operação](OPERACAO_GRAVACAO.md); Thiago relatou que a consulta funcionou no Pi durante a gravação.

**Por que ARM64 e build fora do Pi?** O Pi informado é ARM64 e houve falha de DNS externo. A imagem é construída e exportada no Windows para não depender de downloads no Pi. O build e a carga foram testados localmente sob emulação, não no Raspberry.

**O que fica para a próxima aula?** O painel novo das 53 tags. Backup, retenção, segurança de produção, recuperação durável e validação operacional também não estão resolvidos apenas por este código.

## 9. Cola final para a gravação

| Arquivo → responsabilidade | Trecho → frase natural |
| --- | --- |
| `catalogo_tags.py` → identidade | `:26, :60, :75` → “Temperatura é XMEAS(9), índice oito; confiro a ordem antes de ler.” |
| `servidor_opc.py` → publicar | `:77, :96, :105` → “Uma simulação, 53 nós, mesmo retrato e três aliases.” |
| `coletor_opc.py` → descobrir e ler | `:39, :67, :97` → “Resolvo o namespace e leio o DataValue em lote; queda não cria fila.” |
| `historico_sqlite.py` → persistir | `:95, :106, :126` → “Validade fica explícita e cada ciclo inteiro entra numa transação.” |
| `sql/consultas.sql` → perguntar | `:21, :28, :39` → “Filtro temperatura, agrupo por minuto e comparo pelo ciclo.” |
| `consultar_sql_stdin.py` → consultar ativo | `:10` → “Envio a pergunta ao Pi; o banco permanece lá e é aberto só para leitura.” |
| `Dockerfile` / `compose.yaml` → executar | `Dockerfile:2, :9; compose:4, :28` → “Uma imagem, dois processos e volume próprio.” |

**Ordem:** retomar Aula 4 → catálogo → servidor → coletor → historiador → SQL → empacotamento → transição autorizada → verificação no Pi.

**Três testes para sustentar a explicação:**

1. `test_catalogo_tags.CatalogoTest.test_correspondencia_de_todos_os_indices`: mapeamento das 53 posições com simulador sintético.
2. `test_servidor_opc.ServidorIntegracaoTest.test_hierarquia_leituras_acesso_e_ciclos`: hierarquia, valores, timestamps e acesso em teste local com cliente OPC UA.
3. `test_historico_sqlite.HistoricoTest.test_ciclo_completo_idempotencia_e_amostras_iguais`: mesmo ciclo idempotente e valores iguais preservados em ciclos diferentes.

Os resultados anteriores estão no [diário](../../docs/DIARIO_DE_BORDO.md); testes não foram executados ao escrever este guia. O teste integrado de persistência e as consultas são apoio adicional.

**Para uma próxima demonstração:** reconfirmar acesso, IPs, regras, sincronização e estado dos contêineres; validar backup e restauração; confirmar espaço, volume, 53 leituras e consultas antes de mostrar dados. Persistência após reboot, firewall após reinício e estado atual dos serviços seguem pendentes. O painel novo das 53 tags é assunto da próxima aula.

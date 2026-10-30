# Consultas SQL — Aula 5

Os exemplos em [consultas.sql](consultas.sql) usam o esquema versão 1 criado por `historico_sqlite.py`. `consultar_historico.py` executa somente essas consultas, com parâmetros SQL e conexão SQLite `mode=ro` e `query_only`; não cria banco nem aceita SQL arbitrário. Ele verifica a identificação e versão do banco. Não aponta automaticamente para o banco de nenhuma instalação.

As consultas são `tags`, `contagem`, `amostras`, `temperatura_30min`, `resumo_minuto`, `comparacao` e `anomalias`. Por padrão, `temperatura_30min` usa os últimos 30 minutos e as demais consultas temporais usam as últimas 24 horas; `--inicio` e `--fim` substituem a janela. Os limites são inclusivo no início e exclusivo no fim. Datas são ISO 8601 com fuso e convertidas para UTC. O limite padrão de linhas é 100, configurável entre 1 e 10.000; `tags` lista o catálogo inteiro e `contagem` retorna os totais globais, sem filtro de tempo. `--tag` vale para `amostras`, `resumo_minuto` e `anomalias` e deve ser um identificador do catálogo.

O horário de filtro e de agrupamento é **coleta UTC**, não `SourceTimestamp`. `resumo_minuto` inclui apenas registros `validade='valido'` e calcula estatísticas sobre valores numéricos; unidades permanecem as do catálogo. `anomalias` encontra qualidade diferente de Good, validade diferente de `valido` ou timestamp de origem ausente, para a tag escolhida. `comparacao` liga pressão `XMEAS(7)` em kPa(g), temperatura `XMEAS(9)` em °C e `XMV(10)` em percentual do modelo pelo `ciclo_id`, retornando também a validade de cada leitura. O mesmo ciclo indica uma aquisição em lote, não simultaneidade física: o servidor atualiza os nós sequencialmente.

XMEAS(23–41) são análises amostradas. Um novo ciclo de coleta ou timestamp de publicação não comprova uma nova análise física. `Good` não prova que um processo real está saudável.

## Execução local no Windows

Ative o ambiente da Aula 5 e, na pasta `aulas/aula-05`, aponte para **um banco existente da Aula 5**:

```powershell
python consultar_historico.py .\historico_aula05.sqlite3 tags
python consultar_historico.py .\historico_aula05.sqlite3 contagem
python consultar_historico.py .\historico_aula05.sqlite3 temperatura_30min --limite 20
python consultar_historico.py .\historico_aula05.sqlite3 amostras --tag 'XMEAS(7)' --inicio 2026-10-30T12:00:00Z --fim 2026-10-30T13:00:00Z --limite 20
python consultar_historico.py .\historico_aula05.sqlite3 resumo_minuto --tag 'XMEAS(9)'
python consultar_historico.py .\historico_aula05.sqlite3 comparacao --plano
python consultar_historico.py .\historico_aula05.sqlite3 anomalias --tag 'XMV(10)'
```

Os horários acima são exemplos de parâmetros, não uma indicação de que existam dados nesse período. A saída é JSON; `--plano` troca os resultados pelo `EXPLAIN QUERY PLAN`.

## Dentro de um contêiner Linux

Exemplo para um host Linux com Python 3.11+ disponível na imagem e caminhos confirmados. Monte tanto o diretório da aplicação quanto o **diretório inteiro do banco**, não somente o arquivo SQLite:

```bash
docker run --rm \
  --mount type=bind,source=/CAMINHO/aulas/aula-05,target=/app,readonly \
  --mount type=bind,source=/CAMINHO/dados-aula05,target=/dados,readonly \
  --workdir /app --entrypoint python IMAGEM_COM_PYTHON \
  consultar_historico.py /dados/historico_aula05.sqlite3 temperatura_30min
```

O banco em WAL pode depender dos arquivos `-wal` e `-shm` legíveis. Uma montagem somente leitura pode não funcionar se os arquivos auxiliares necessários não existirem ou não estiverem acessíveis. Não use `immutable=1` para um banco em atualização: isso poderia ocultar dados ainda no WAL. Para uma cópia ou backup, use um procedimento consistente com SQLite/WAL.

## Por terminal SSH no Raspberry Pi

Este é um roteiro para uma etapa futura autorizada, **não executado nesta sessão**. Confirme usuários, endereços, autenticação, jump host, caminhos, permissões e estado do banco antes de usar. Os nomes abaixo são marcadores, não endereços verificados:

```bash
ssh -J USUARIO_PI3@ENDERECO_PI3 USUARIO_PI4@ENDERECO_PI4
cd /CAMINHO/CONFIRMADO/aulas/aula-05
python3 consultar_historico.py /CAMINHO/CONFIRMADO/historico_aula05.sqlite3 contagem
python3 consultar_historico.py /CAMINHO/CONFIRMADO/historico_aula05.sqlite3 comparacao --limite 10
python3 consultar_historico.py /CAMINHO/CONFIRMADO/historico_aula05.sqlite3 resumo_minuto --tag 'XMEAS(9)' --plano
```

Esses comandos pressupõem que os arquivos e o banco da Aula 5 já estejam presentes; este incremento não os implanta. Não substitua o banco da Aula 4 pelo exemplo.

## Roteiro didático

1. Comece com `tags`: `SELECT` escolhe colunas; `FROM` indica a tabela. Mostre a diferença entre índice Python e número da tag.
2. Execute `amostras`: `WHERE` limita tag e janela, `ORDER BY` apresenta as mais recentes e `LIMIT` restringe linhas.
3. Execute `comparacao`: `JOIN` relaciona as três leituras pelo `ciclo_id`. Compare com os timestamps de origem e explique por que não são uma chave de associação.
4. Execute `resumo_minuto`: `GROUP BY` reúne as coletas por minuto UTC; `AVG`, `MIN` e `MAX` resumem somente leituras válidas. Mostre também a quantidade de amostras.
5. Execute `anomalias` para examinar `Bad`, `Uncertain`, dados inválidos e timestamps ausentes antes de interpretar tendências.
6. Acrescente `--plano` a uma consulta e identifique o índice usado; contagens globais e agrupamentos podem exigir trabalho adicional.

## Planos observados nos testes locais

O esquema inclui `leituras_tag_coleta(tag_id, coleta_utc)`, `leituras_tag_origem(tag_id, source_timestamp)` e a chave primária `(ciclo_id, tag_id)`. Para janelas de coleta, `EXPLAIN QUERY PLAN` usou `leituras_tag_coleta`; a comparação usou essa busca para pressão e a chave primária para as outras duas tags. O agrupamento por minuto também criou B-trees temporárias para agrupar e ordenar. A contagem global percorre dados/índices; `LIMIT` após agrupamento não limita quantas linhas da janela precisam ser lidas. Os planos dependem de versão, estatísticas e tamanho do banco; não medem desempenho no Raspberry.

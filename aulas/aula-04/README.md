# Aula 4 — coleta OPC UA, histórico SQLite e Streamlit

Nesta aula, ampliamos o laboratório com um coletor independente e uma interface para consultar os dados históricos do reator. O TEP e o servidor OPC UA continuam juntos; o coletor lê `Pressao`, `Nivel` e `Temperatura`, armazena cada sinal no SQLite e o Streamlit consulta esse banco, sem fazer outra coleta.

```text
TEP + servidor OPC UA :4840 → coletor → volume SQLite → Streamlit :8501
                                    Pi 4                       │
Notebook (UAExpert / navegador) ← Pi 3: roteador e firewall ←─┘
```

O projeto fornece uma composição independente nesta pasta; a [Aula 3](../aula-03/) publicada continua intacta. **A composição desta aula reflete a implementação usada na preparação da gravação, que difere da composição publicada da Aula 3**. Não execute as duas simultaneamente nas mesmas portas. Se já tiver serviços ativos, inventarie Compose, imagens, portas, volume e configuração efetivos antes de escolher como integrar. Não substitua arquivos ou recrie serviços de um ambiente existente sem fazer backup e analisar o impacto.

## Conteúdo

| Arquivo | Finalidade |
| --- | --- |
| `compose.yaml`, `Dockerfile*`, `.env.example` | Serviços e configuração Docker |
| `servidor_opc.py` | Simulação TEP e publicação OPC UA |
| `coletor.py` | Coleta, reconexão e escrita no SQLite |
| `leitor_sqlite.py`, `interface.py` | Consulta somente leitura e painel |
| `test_*.py` | Testes locais com dados sintéticos |
| [Roteiro](ROTEIRO.md) e [checklist](CHECKLIST.md) | Sequência e verificações para a aula |

## Fluxo e dados

O coletor conecta a `opc.tcp://tep-opc:4840/tep/` pela rede interna do Compose e resolve o namespace pela URI `urn:laboratorio-industrial:tep`, sem fixar seu índice. Tenta ler os três sinais aproximadamente a cada segundo e aguarda cinco segundos após uma falha antes de reconectar. O endpoint externo de referência do laboratório é `opc.tcp://10.77.0.10:4840/tep/`; confirme os endereços reais no seu ambiente.

Cada linha de `leituras` representa uma amostra de um sinal: valor, unidade, `source_timestamp`, `coleta_utc`, `status_code`, `qualidade` e `validade`. A primeira amostra de cada par sinal e timestamp de origem é preservada; valores iguais em timestamps diferentes não são descartados. Sem timestamp de origem, o campo fica NULL e cada leitura é gravada. Valores inválidos são NULL, com validade indicada, sem ocultar a qualidade OPC UA. Erros sem DataValue são registrados no log, não como amostras. O banco não possui retenção automática e crescerá com o tempo.

O volume `historico` armazena `/data/leituras.sqlite3` por padrão; o nome no host depende do projeto Compose. O coletor usa WAL, `busy_timeout` de cinco segundos e transações curtas. A interface monta o diretório inteiro somente para leitura, incluindo os arquivos auxiliares WAL/SHM, e abre o banco em modo somente leitura. Verifique permissões e leitura concorrente no ambiente real. O painel atualiza a cada três segundos e indica desatualização quando a coleta ou origem ultrapassa dez segundos, além de sinalizar erro, qualidade ruim e timestamp ausente. Gráficos limitam a 1.200 amostras por sinal e mostram apenas valores válidos e Good.

## Preparar um ambiente novo

Requisitos: Docker e Compose compatíveis, espaço em disco, dependências disponíveis para a arquitetura do host e uma rede de laboratório restrita. A construção da imagem do servidor requer acesso às fontes das dependências; a da interface instala Streamlit. Verifique acesso e permissões antes do build. A imagem base das duas aplicações auxiliares é `iilab-tep-opc:local`, portanto construa o servidor primeiro. Não altere o firewall ou a rede automaticamente.

No Pi 4, na pasta `aulas/aula-04` de uma cópia do repositório, confira os IPs de publicação e anúncio. Crie o `.env` somente se ainda não existir, e ajuste os valores ao seu ambiente:

```bash
test ! -e .env && cp .env.example .env
# Edite .env e confirme PI4_ETH_IP e OPC_UA_ADVERTISE_HOST.
sudo docker compose config
sudo docker compose build tep-opc
sudo docker compose build coletor interface
sudo docker compose up -d tep-opc
sudo docker compose up -d --no-deps coletor interface
sudo docker compose ps
sudo docker compose logs --tail 60 coletor interface
```

O exemplo usa `sudo` para Docker, como no Pi da gravação. Em instalações com outro acesso ao daemon, ajuste-o conforme seu ambiente. A porta 4840 e a 8501 são publicadas somente no IP configurado, mas o caminho real e o firewall precisam ser verificados. Não exponha SQLite; não remova volumes nem use `down -v` para reiniciar o coletor.

Para um projeto já implantado com outro arquivo Compose, **não** presuma que o diretório ou o nome do projeto coincide: um nome diferente cria outro volume e outra rede. No ambiente relatado, havia projeto `aula-03`, volume `aula-03_historico` e Compose em `/home/devadmin/iilab-aula03/aulas/aula-03`; também foi usado um arquivo temporário `compose.yaml.interface-novo`. Confirme o estado atual e os hashes, preserve `.env` e banco, e analise as diferenças antes de qualquer transferência ou `up`. O código aqui é referência, não uma atualização automática do Pi.

## Conferir o histórico

Com o serviço em execução, consulte o banco real em modo de leitura. O comando falha se o banco não existir, sem criar outro. Execute dentro da pasta e com o mesmo arquivo e nome de projeto Compose usados para a implantação:

```bash
sudo docker compose exec -T coletor python - <<'PY'
import os, sqlite3
from pathlib import Path
p = Path(os.environ.get('SQLITE_PATH', '/data/leituras.sqlite3')).resolve()
if not p.is_file():
    raise SystemExit(f'Banco não encontrado: {p}')
db = sqlite3.connect(p.as_uri() + '?mode=ro', uri=True, timeout=5)
print('Banco:', p)
print('Total:', db.execute('SELECT count(*) FROM leituras').fetchone()[0])
for row in db.execute('SELECT sinal, count(*) FROM leituras GROUP BY sinal'):
    print('Por sinal:', row)
for sinal in ('Pressao', 'Nivel', 'Temperatura'):
    row = db.execute('''SELECT sinal, valor, unidade, qualidade, status_code,
        source_timestamp, coleta_utc FROM leituras WHERE sinal=? ORDER BY id DESC LIMIT 1''', (sinal,)).fetchone()
    print('Última:', row)
db.close()
PY
```

Repita após alguns ciclos e compare contagens e timestamps; deduplicação significa que nem todo ciclo necessariamente acrescenta três linhas. Para demonstrar persistência, registre a contagem, reinicie **somente** o coletor com `sudo docker compose restart coletor` e repita a consulta: os registros anteriores devem permanecer e novos dados podem ser acrescentados. Para descobrir o volume correto, confira `sudo docker compose config` e `sudo docker volume inspect NOME_DO_VOLUME`; nunca substitua o banco para preparar a demonstração.

## Conferir painel e rede

No próprio Pi, com o IP de publicação confirmado:

```bash
curl -i --connect-timeout 5 --max-time 10 http://10.77.0.10:8501/_stcore/health
```

HTTP 200 / `ok` indica que o processo responde, não que a coleta esteja saudável. Compare valores, qualidade e horários UTC do painel com o banco e com `Objects → Reator` no UAExpert. O relógio do host deve estar correto: dados antigos não são corrigidos ao acertá-lo. A URL de referência é `http://10.77.0.10:8501`; do notebook, o acesso depende da rota e de uma regra específica no Pi 3. Confirme o estado das regras, o IP do notebook e o caminho de recuperação antes de qualquer alteração autorizada. Uma falha TCP sozinha não distingue firewall de serviço indisponível.

O servidor OPC UA usa acesso anônimo e sem criptografia. Este é um ambiente didático com dados simulados, não uma configuração pronta para produção. Veja [o roteiro](ROTEIRO.md) para o estado observado e suas limitações.

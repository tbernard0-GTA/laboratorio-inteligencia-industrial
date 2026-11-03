# Aula 6 — preparação da API FastAPI

## Incremento de gravação — catálogo de tags

`GET /api/v1/tags` consulta o catálogo SQLite da Aula 5 com `abrir_leitura()` e `executar(db, "tags")`. A resposta inclui identificador, categoria, índice, descrição e unidade; o cadastro não comprova leituras recentes. Banco inacessível ou incompatível retorna HTTP 503 sem expor o caminho. Thiago confirmou 53 tags no Swagger; uma consulta HTTP posterior também retornou 53 tags.

## Incremento de gravação — histórico

Preparado localmente `GET /api/v1/historico?tag=XMEAS(9)&limite=5`, usando a consulta predefinida `amostras` em SQLite somente leitura. `tag` é obrigatória e deve constar no catálogo; `limite` varia de 1 a 200 (padrão 10). O resultado é uma lista com `ciclo_id`, `tag_id`, `valor`, `source_timestamp`, `coleta_utc`, `status_code`, `qualidade` e `validade`. A ordem é decrescente por horário de coleta; empates não possuem desempate definido. A janela abrange o histórico disponível, com limite superior exclusivo; uma resposta 200 não atesta atualização recente. A versão no Pi ainda depende de atualização e verificação.

Além das duas consultas, a API oferece `GET /health`, `/docs` e `/openapi.json`. `health` confirma que a API responde, não verifica o banco. Sem autenticação ou TLS, limite o acesso à rede de laboratório autorizada; não exponha à internet.

## Arquitetura e leitura

Notebook TI → gateway Pi 3 → Pi 4 TA → API HTTP 8000. Na rede Docker da Aula 5, o historiador grava em WAL e a API montará o mesmo diretório de volume como somente leitura. A imagem inclui os módulos e SQL da Aula 5 em `/app`, acessíveis por `PYTHONPATH`; `abrir_leitura()` usa `mode=ro`, `query_only` e verifica `application_id` e `user_version`, e `executar()` aceita apenas consultas predefinidas. Para o desenvolvimento futuro, abrir por requisição e fechar com `contextlib.closing`; não receber SQL arbitrário. A imagem monta o diretório inteiro, necessário para SQLite acessar arquivos WAL/SHM; não usar `immutable`. SQLite em WAL somente leitura depende da existência e permissões adequadas dos auxiliares; validar concorrência no ambiente real antes de usar. Nenhuma conexão é aberta pelo health.

## Imagem e desenvolvimento

A imagem `iilab-aula06-api:0.1` deriva da imagem local ARM64 `iilab-aula05:1`. O TAR v1 exportado contém a aplicação inicial com apenas `/health`, além de dependências e módulos da Aula 5; não foi reconstruído após a criação dos endpoints. A cópia inicial está em `/opt/aula06-default`. Os endpoints posteriores estão no código Python deste repositório e podem ser montados em `/opt/api` somente leitura; altere os arquivos no host e reinicie somente a API para aplicar. O processo não instala pacotes no Pi. Mudanças que exijam novas dependências exigem nova imagem preparada e validada no notebook.

O Compose complementar requer ambos arquivos no Pi e um caminho absoluto para `AULA06_API_DIR`. Como Compose resolve caminhos relativos a partir do primeiro arquivo, use caminhos absolutos e verifique sempre a configuração expandida:

```bash
export PI4_BIND_IP=IP_ETHERNET_CONFIRMADO OPC_UA_ADVERTISE_HOST=HOST_OPC_CONFIRMADO
export AULA06_API_DIR=/CAMINHO/ABSOLUTO/api
sudo env PI4_BIND_IP="$PI4_BIND_IP" OPC_UA_ADVERTISE_HOST="$OPC_UA_ADVERTISE_HOST" AULA06_API_DIR="$AULA06_API_DIR" docker compose -p iilab-aula05 -f /CAMINHO/aula-05/compose.yaml -f /CAMINHO/aula-06/compose.api.yaml config
```

Confira serviços, bind, rede, volume e caminhos antes de qualquer operação; este incremento não iniciou o Compose. Para a gravação com transferência apenas do tar, siga [ROTEIRO_IMPLANTACAO.md](ROTEIRO_IMPLANTACAO.md), que usa `docker run` e extrai o código da imagem. Não execute os dois métodos ao mesmo tempo.

## Sequência planejada para gravação

1. Criar `/api/v1/tags` — implementado; 53 tags relatadas e observadas.
2. Criar `/api/v1/historico` — implementado e testado localmente; validação no Pi pendente.
3. Testar requisições no Postman.
4. Criar cliente Python com `requests`.
5. Demonstrar OPC UA direto e HTTP via API.
6. Modificar o firewall de forma controlada, após análise e autorização específicas.
7. Demonstrar bloqueio do OPC UA externo com HTTP funcionando.

Os itens 3 a 7 são planos; não há evidência suficiente nesta revisão de sua execução ou de novas regras de firewall. A operação real, política de firewall e persistência após reboot continuam a validar.

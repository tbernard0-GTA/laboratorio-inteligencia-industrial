# Aula 6 — API para histórico industrial

A aula apresenta uma API REST com FastAPI para consultar o histórico SQLite da Aula 5, com Swagger, Postman e Python `requests`, e demonstra o controle da comunicação entre TI e TA. O código publicado implementa os três endpoints abaixo e reutiliza o historiador, seu esquema e suas consultas.

## Resultados da gravação

Thiago informou que, no Pi 4, a imagem ARM64 foi transferida e carregada; a API rodou em contêiner independente com código editável montado, usando a rede Docker e o volume da Aula 5 em modo de leitura. Relatou `/health`, `/docs`, 53 tags no Swagger e consulta ao histórico real, incluindo temperatura `XMEAS(9)`; também relatou servidor OPC UA e historiador preservados. Não recebemos logs ou saídas completas dessas operações nesta revisão. O catálogo cadastrado não comprova leituras recentes.

Thiago também relatou acesso OPC UA direto antes da restrição, bloqueio de novas conexões externas OPC UA ao Pi 4, HTTP 8000 funcional após a alteração e coleta interna preservada. Não inspecionamos as regras ou os Pi nesta etapa; os detalhes e persistência das regras após reboot não foram demonstrados. HTTP sem TLS e OPC UA sem segurança de mensagem são configurações didáticas para rede isolada, não configurações recomendadas para produção.

## Arquitetura

```text
Notebook TI ── Pi 3 (gateway/firewall) ── Pi 4 TA
       │                                  ├─ TEP / OPC UA ── historiador
       └────────── HTTP 8000 ────────────► API ── SQLite da Aula 5 (leitura)
```

Antes da restrição, o cliente TI alcançava OPC UA TCP 4840 por meio do Pi 3. Depois, segundo o relato, novas conexões OPC UA externas foram restringidas e o cliente continuou consultando por HTTP 8000. O historiador continuou usando OPC UA internamente na rede Docker. Endereços e estado atual devem ser confirmados antes de operação.

FastAPI associa URLs e métodos HTTP a funções Python, valida parâmetros e serializa os resultados em JSON; `/docs` é a interface Swagger gerada a partir de `/openapi.json`.

## Endpoints e SQLite

| Método e caminho | Uso |
| --- | --- |
| `GET /health` | Estado da API e versão; não testa o banco. |
| `GET /api/v1/tags` | Lista metadados cadastrados: identificador, categoria, índice, descrição e unidade. |
| `GET /api/v1/historico?tag=XMEAS(9)&limite=5` | Lista leituras da tag; `tag` é obrigatória e `limite` vai de 1 a 200, padrão 10. |

Tag desconhecida retorna 404; parâmetros inválidos retornam 422; banco indisponível ou incompatível retorna 503 genérico. As leituras contêm `ciclo_id`, `tag_id`, `valor` (que pode ser `null`), `source_timestamp`, `coleta_utc`, `status_code`, `qualidade` e `validade`, ordenadas por coleta decrescente, sem desempate definido. HTTP 200 não garante dados recentes.

O código usa `abrir_leitura` e `executar` da Aula 5 com as consultas parametrizadas `tags` e `amostras`, sem aceitar SQL do cliente. O banco de `BANCO_HISTORICO` é aberto com `mode=ro` e `query_only`; identificação e versão do esquema são verificadas e a conexão é fechada após a consulta. O diretório inteiro do volume é montado somente leitura para permitir acesso aos auxiliares WAL/SHM; suas permissões e leitura concorrente dependem do ambiente. O endpoint de histórico usa janela ampla para incluir amostras anteriores às 24 horas padrão da consulta.

## Imagem ARM64 e execução

A imagem original `iilab-aula06-api:0.1` e seu TAR v1 contêm somente `/health`; as rotas foram adicionadas posteriormente pelo código montado. A imagem consolidada `iilab-aula06-api:1.0` incorpora o código final em `/opt/api` e `/opt/aula06-default`; não necessita de montagem de código para iniciar, mas aceita uma montagem para desenvolvimento. Ambas usam a imagem da Aula 5 como origem indireta e incluem seus módulos SQL. O build local da versão 1.0 usou a imagem 0.1 como base, sem rede. Veja hashes, comandos de transferência, inspeção e execução em [ROTEIRO_IMPLANTACAO.md](ROTEIRO_IMPLANTACAO.md). A 1.0 foi testada localmente, não implantada no Pi.

O Compose complementar deve ser combinado com o da Aula 5, com `PI4_BIND_IP`, `OPC_UA_ADVERTISE_HOST` e `AULA06_API_DIR` confirmados. O caminho de bind deve ser absoluto: Compose resolve caminhos relativos a partir do primeiro arquivo. Antes de qualquer operação autorizada, confira `docker compose -p iilab-aula05 -f .../aula-05/compose.yaml -f .../aula-06/compose.api.yaml config`; a configuração preparada usa a imagem 0.1 com código montado, rede existente e volume `historico` somente leitura. O roteiro também descreve `docker run` e a reprodução sem montagem com a 1.0.

## Swagger, Postman e Python

No navegador, acesse `http://HOST_CONFIRMADO:8000/docs`, abra os três GETs e use **Try it out**. Para histórico, informe `XMEAS(9)` e `5`. No Postman, importe [Aula06.postman_collection.json](postman/Aula06.postman_collection.json), ajuste a variável `base_url` para a URL do laboratório e, se desejar, `tag` e `limite`; execute as três requisições. Não há evidência de que esta coleção tenha sido usada na gravação.

No computador cliente, instale `requests` em um ambiente Python apropriado e execute:

```powershell
python -m pip install requests
python aulas/aula-06/exemplos/cliente_requests.py http://HOST_CONFIRMADO:8000 --tag 'XMEAS(9)' --limite 5
```

O exemplo usa timeout, trata falhas HTTP e mostra valor, qualidade, validade e timestamps. A URL é escolhida pelo aluno. O exemplo não é evidência de execução na gravação.

## Firewall e validação

Numa topologia roteada, a cadeia de encaminhamento nftables do Pi 3 pode diferenciar novas conexões destinadas a 4840 ou 8000. Regras `ct state established,related` podem permitir tráfego de conexões já estabelecidas mesmo após bloquear novos fluxos: feche a sessão OPC UA e teste uma **nova** conexão para validar a restrição; também teste HTTP e a coleta interna. Analise ordem, prioridades e demais regras: o resultado depende da configuração efetiva e da interação do Docker com o firewall.

Antes de qualquer alteração futura, mantenha SSH administrativo pelo salto e acesso alternativo; documente a tabela, cadeia e regra existentes e o caminho de recuperação. Para inspeção autorizada, `sudo nft -a list ruleset` mostra regras e handles atuais. Para reverter somente a regra identificada, primeiro confirme família, tabela, cadeia, conteúdo e handle na configuração corrente; uma operação específica tem formato `sudo nft delete rule FAMILIA TABELA CADEIA handle HANDLE_ATUAL`. Handles podem mudar e a remoção deve ser autorizada e analisada, não copiada automaticamente. Não restaurar regras inteiras ou alterar roteamento por inferência. Regras em memória não comprovam persistência após reboot; confirme separadamente configuração persistida e teste de recuperação.

## Próximos passos

Em uma etapa autorizada, verificar persistência após reboot, integridade e restauração de backup, proteção de acesso e TLS adequados ao ambiente, e estado efetivo dos serviços e regras. O crescimento das amostras deve ser verificado por timestamps e ciclos, não apenas pela resposta HTTP. Não foram adicionadas funcionalidades da Aula 7.

# Aula 3 — Docker, Docker Compose e a primeira interface industrial

Empacotar o **TEP+OPC UA já existente** e adicionar uma interface **Streamlit**, sem desfazer a separação TI/TA da aula2. Dois serviços no Pi4; Pi3 continua somente gateway/firewall. Projeto didático com dados simulados, sem garantia de segurança de produção.

## Comece aqui

1. [Checklist de preparação e gravação](CHECKLIST_GRAVACAO.md) — pré-build, acesso, hardware e rede.
2. [Roteiro de60min](roteiro/roteiro_gravacao.md) — sequência, falas, comandos e checkpoints.
3. [Sete prompts unitários + diagnóstico](prompts/prompts_codex.md) — desenvolvimento guiado, sem prompts gigantes.
4. [Procedimento reversível TCP8501](rede/firewall_8501.md) — baseline, backup, regra estreita, rollback e persistência controlada.
5. `apresentacao/` — apresentação e notas, quando incluídas no pacote final.
6. [testes/RELATORIO_VALIDACAO.md](testes/RELATORIO_VALIDACAO.md) — resultados reais, evidências e limites cloud/ARM/Docker.

## Arquitetura

```text
Windows / navegador e UAExpert (192.168.1.16, confirmar DHCP)
    │ Wi-Fi TI 192.168.1.0/24
Pi3 (192.168.1.17 / 10.77.0.1)
    │ encaminhamento nftables:4840 permitida;8501 só após exceção;22 direto bloqueada
    │ Ethernet OT 10.77.0.0/24
Pi4 (10.77.0.10; Wi-Fi desativado)
    └─ Docker Compose
        ├─ tep-opc: TEP Python + servidor asyncua integrado
        │   publicação:10.77.0.10:4840 → container:4840
        └─ streamlit: cliente OPC + interface
            publicação:10.77.0.10:8501 → container:8501
            OPC interno:opc.tcp://tep-opc:4840/tep/
```

A administração usa `ssh -J admin@192.168.1.17 devadmin@10.77.0.10`; não é o mesmo fluxo de SSH direto encaminhado. ICMP de diagnóstico pode estar permitido. Não afirmar “só existem pacotes OPC”. IPs históricos, rotas e persistência precisam ser reconfirmados.

## Contrato dos dados

Servidor usa o namespaceURI `urn:laboratorio-industrial:tep`. Cliente descobre o índice do namespace e navega `Objects/Reator`:

| Variável | Índice do vetor TEP (base0) | Unidade |
|---|---:|---|
| `Pressao` |6|`kPa(g)`|
| `Nivel` |7|`%`|
| `Temperatura` |8|`C`|

Não fixar NodeIds numéricos nem assumir `ns=2`. O cliente verifica qualidade, timestamp e valores finitos; rejeita dado com qualidade ruim ou horário inválido/desatualizado. Mock está reservado a testes identificados, não ao dashboard.

## Arquivos de aplicação

- `servidor_opc.py`: versão da aula3 baseada no servidor integrado da aula1, com configuração adequada ao container.
- `docker/Dockerfile`: alvos `server` e `dashboard`.
- `docker/compose.yaml`: serviços `tep-opc`, `streamlit`, redebridge, healthchecks e reinício.
- `docker/requirements-server.txt`, `streamlit/requirements.txt`: dependências.
- `streamlit/opc_client.py`: leitura CLI e coleta/reconexão.
- `streamlit/collector.py`: armazenamento recente limitado em memória.
- `streamlit/app.py`: estado/valores/timestamps/tendências.
- `.env.example`: bind externo e endpoint anunciado; `.dockerignore`: contexto enxuto.

## Execução no Pi4 — após checklist

Os comandos seguintes são Bash na pasta desta aula no checkout do **Pi4**. A preparação desta entrega foi feita somente na nuvem. Não executar no Pi3 ou PowerShell local.

```bash
if [ ! -f .env ]; then cp .env.example .env; fi
# Revise .env: PI4_BIND_IP deve existir na interface Ethernet do Pi4.
docker compose --env-file .env -f docker/compose.yaml config
docker compose --env-file .env -f docker/compose.yaml build
```

Antes de subir, pare somente o servidor manual identificado que ocupa4840. Preserve seu script/venv para rollback. Build pode exigir internet indisponível pela política daOT; prepare imagensARM64 antes, sem liberar egress geral.

```bash
docker compose --env-file .env -f docker/compose.yaml up -d
docker compose --env-file .env -f docker/compose.yaml ps
docker compose --env-file .env -f docker/compose.yaml logs --tail=50
docker compose --env-file .env -f docker/compose.yaml exec streamlit python opc_client.py --endpoint opc.tcp://tep-opc:4840/tep/ --once
```

Cliente externo UAExpert: `opc.tcp://10.77.0.10:4840/tep/`.
Browser: **`http://10.77.0.10:8501`**, somente depois do [teste/liberação no Pi3](rede/firewall_8501.md).

Docker publica portas no Pi4; a liberação entre zonas é outra configuração, no Pi3. A rede Compose resolve serviços pelo nome; o browserWindows não resolve `tep-opc`. [Referência oficial de rede Compose](https://docs.docker.com/compose/how-tos/networking/).

### Reinício e parada

```bash
docker compose --env-file .env -f docker/compose.yaml restart tep-opc
docker compose --env-file .env -f docker/compose.yaml logs --tail=50 tep-opc
# Quando desejar parar SOMENTE esta aplicação:
docker compose --env-file .env -f docker/compose.yaml down
```

Não usar prune, `down -v` ou parar outros containers. `restart: unless-stopped` não é persistência de dados nem cura automática para todo estado unhealthy. Streamlit e suas tendências são efêmeros; reiniciar o modelo reinicia sua trajetória. HealthHTTP não garante leiturasOPC atuais.

## Testar sem confundir ambientes

Testes da lógica usam um servidorOPC de teste explicitamente rotulado. `testes/smoke_real.py` cobre o simulador real quando dependências estão disponíveis. Confira o relatório entregue para versões, comandos, resultados e limitações. Para testesPython em ambiente de desenvolvimento separado:

```bash
python -m venv .venv-test
. .venv-test/bin/activate
python -m pip install -r streamlit/requirements.txt pytest pytest-asyncio pyyaml
python -m pytest testes/ -q
```

Não instalar pacotes globalmente no Raspberry. O teste estrutural do YAML não equivale a `docker compose config`; nenhum deles equivale a buildARM64, boot físico ou tráfego passando pelo firewall. A ausência de Docker na nuvem limita build/runtime do container; validar no Pi antes da gravação.

## Operação segura e limites

- OPC UA atual usa `NoSecurity`/acesso de laboratório; StreamlitHTTP sem autenticação de produção. Não publicar portas na internet.
- Nenhuma regra global de firewall é substituída; novo acesso é uma exceção específica e removível.
- Não instalar Docker no gateway para “facilitar”. Não alterar backend de firewall do Docker durante a aula.
- Não presumir internet naOT. Dependências pré-carregadas devem ser compatíveisARM64.
- Não presumir que reboot preserva rota Windows temporária, forwarding, regras e todos os serviços. Verificar cada camada em janela controlada.
- Não apresentar testes da nuvem como validação dos Raspberry.

## Referências oficiais

- [Docker Engine — instalação Debian](https://docs.docker.com/engine/install/debian/)
- [Compose — redes e nomes dos serviços](https://docs.docker.com/compose/how-tos/networking/)
- [Docker — regras de rede e firewall](https://docs.docker.com/engine/network/packet-filtering-firewalls/)
- [nftables — manual de comandos](https://netfilter.org/projects/nftables/manpage.html)

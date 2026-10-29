# Aula 03 — Docker e Docker Compose para TEP e OPC UA

Nesta aula, organizamos a execução do simulador TEP e do servidor OPC UA em um container no Raspberry Pi 4. O Raspberry Pi 3 continua como roteador e firewall da [aula 02](../aula-02/). A proposta é entender imagem, container, dependências, publicação de portas, logs e ciclo de execução com Docker Compose.

**A interface Streamlit ficou para um vídeo complementar.** O código preparado está disponível, mas não sobe por padrão e não é necessário para acompanhar este episódio. A Aula 3 principal termina com TEP+OPC em container e a conferência no UAExpert, sem liberar uma porta web adicional.

> Material didático com dados simulados. Adapte IPs, usuários e interfaces ao seu laboratório. OPC UA está sem criptografia/autenticação de produção. Não exponha a porta 4840 à internet. Os comandos são uma referência reproduzível, não uma transcrição exata de todos os comandos do vídeo.

## Topologia de exemplo

```text
Notebook Windows / UAExpert       Pi 3 (roteador/firewall)           Pi 4
192.168.1.14 ───── Wi-Fi ──────── 192.168.1.17 (wlan0)
                                  10.77.0.1 (eth0) ── Ethernet ── 10.77.0.10
                                                                  Docker Compose
                                                                  └─ tep-opc :4840
```

Em 29/10/2026, o notebook recebeu `192.168.1.14` por DHCP; na aula anterior era `.16`. Confirme o IP atual e as regras de origem antes de testar. O servidor é acessado pelo IP Ethernet `10.77.0.10`, não pelo antigo IP Wi-Fi do Pi 4. O salto SSH administrativo continua separado do tráfego encaminhado pelo firewall.

## Material de apoio

- [Roteiro macro da Aula 3](roteiro/roteiro_gravacao.md).
- [Checklist e critérios de conferência](CHECKLIST_GRAVACAO.md).
- [Prompts de apoio](prompts/prompts_codex.md): etapas 1–3 para o núcleo desta aula; 4–6 pertencem ao complemento.
- [Decisões técnicas](docker/DECISOES.md) e [relatório de validação](testes/RELATORIO_VALIDACAO.md).
- [Complemento preparado: Streamlit](COMPLEMENTO_STREAMLIT.md), separado do episódio principal.

A pasta foi padronizada para `aulas/aula-03`, seguindo as aulas anteriores. Se você baixou o pacote de preparação antigo, ele usava `aulas/aula-03-docker-compose-streamlit`; ajuste seu diretório de trabalho. Os slides em `apresentacao/` representam o planejamento original mais amplo, não a versão final do vídeo dividido.

## 1. Confirmar acesso e ambiente

No **PowerShell do notebook**, confirme sua rede e conecte ao Pi 4 pelo Pi 3:

```powershell
ipconfig
route print 10.77.*
ssh -J admin@192.168.1.17 devadmin@10.77.0.10
```

Substitua usuários e IPs pelos seus. A rota do notebook para `10.77.0.0/24` deve usar o Pi 3. A rede, o encaminhamento IPv4 e o firewall precisam estar operacionais conforme a aula 2. Não habilite o encaminhamento sem conferir o filtro; não use uma liberação geral para contornar falhas.

No **terminal SSH do Pi 4**, execute:

```bash
whoami
hostname
uname -m
ip -4 -br addr
ip -4 route get 192.168.1.14
df -h /
docker version
docker compose version
```

O exemplo pressupõe ARM64 (`aarch64`), Ethernet `10.77.0.10` e retorno ao notebook por `10.77.0.1`. Se Docker/Compose não estiverem instalados, siga a [instalação oficial para Debian](https://docs.docker.com/engine/install/debian/) adequada ao seu sistema. Não reinstale por rotina. Se o usuário não tiver acesso ao daemon, use `sudo docker ...` nos comandos após conferir o ambiente; não torne o socket público. O grupo `docker` concede privilégios elevados.

## 2. Obter o código e preparar as imagens

Use a branch desta publicação enquanto ela não estiver integrada à principal. Em um ambiente autorizado com acesso ao GitHub, para um novo checkout:

```bash
git clone --branch feat/aula-03-docker-compose-streamlit --single-branch https://github.com/tbernard0-GTA/laboratorio-inteligencia-industrial.git
cd laboratorio-inteligencia-industrial/aulas/aula-03
```

Se já existe um checkout, confira `git status` antes de trocar de branch ou atualizar. Preserve suas mudanças locais e não sobrescreva a pasta do servidor manual da aula 1.

**A política da rede OT pode bloquear downloads.** `git clone`, `apt`, `pip`, `docker pull` e `build` podem precisar de uma janela de preparação autorizada. Alternativamente, transfira código e imagens ARM64 previamente construídas. Não abra o firewall inteiro para baixar dependências. Imagens x86 não substituem imagens ARM64.

Na pasta `aulas/aula-03`, no **Pi 4**:

```bash
if [ ! -f .env ]; then cp .env.example .env; fi
```

Revise `.env`: `PI4_BIND_IP` deve ser o IP Ethernet existente no Pi 4. O endpoint anunciado deve apontar para esse IP. Não coloque segredos no Git.

```bash
docker compose --env-file .env -f docker/compose.yaml config
docker compose --env-file .env -f docker/compose.yaml build tep-opc
```

O Dockerfile usa Python 3.12 no container, independentemente do Python instalado no host. O simulador e o servidor continuam integrados no mesmo processo; não é necessário iniciar `simular_tep.py` em paralelo.

## 3. Migrar do servidor manual para o container

Confira quem ocupa a porta no **Pi 4**:

```bash
sudo ss -ltnp 'sport = :4840'
```

Se o servidor manual estiver ativo, pare **somente o processo identificado**, por exemplo com Ctrl+C no terminal que o executa. Preserve o script e a `.venv` para retorno. Não use `pkill python`, não pare todos os containers e não apague volumes de outros projetos.

Agora inicie o serviço:

```bash
docker compose --env-file .env -f docker/compose.yaml up -d tep-opc
docker compose --env-file .env -f docker/compose.yaml ps
docker compose --env-file .env -f docker/compose.yaml logs --tail=50 tep-opc
```

`up -d` libera o terminal; não prova, sozinho, que a comunicação funciona. A publicação liga `10.77.0.10:4840` do host à porta `4840` do container. A permissão para atravessar o Pi 3 continua sendo uma regra separada.

## 4. Conferir as medidas

No **Pi 4**, o cliente de diagnóstico incluído na imagem faz uma leitura local do OPC:

```bash
docker compose --env-file .env -f docker/compose.yaml exec tep-opc python opc_client.py --endpoint opc.tcp://127.0.0.1:4840/tep/ --once
```

No **UAExpert do notebook**, conecte a:

```text
opc.tcp://10.77.0.10:4840/tep/
```

Expanda `Objects → Reator` e arraste as três variáveis para a visualização de dados:

| Variável | Índice TEP (base zero) | Unidade |
| --- | ---: | --- |
| Pressao | 6 | kPa(g) |
| Nivel | 7 | % |
| Temperatura | 8 | C |

Confira valores finitos, qualidade `Good` e avanço de `SourceTimestamp`. O namespace é `urn:laboratorio-industrial:tep`. O cliente resolve a URI e os nomes das variáveis; não depende de um índice fixo `ns=2`.

Se a leitura local funcionar e a remota não, confira em camadas: IP do notebook, rota, serviço, publicação da porta, caminho de retorno e regras/contadores do Pi 3. Não substitua uma regra específica por `accept` geral.

## 5. Acompanhar, reiniciar e parar

```bash
# Acompanhar logs; Ctrl+C encerra a visualização, não o container.
docker compose --env-file .env -f docker/compose.yaml logs -f --tail=50 tep-opc

# Reiniciar apenas o serviço desta aula.
docker compose --env-file .env -f docker/compose.yaml restart tep-opc

# Parar os recursos deste projeto quando terminar.
docker compose --env-file .env -f docker/compose.yaml down
```

Não use `down -v` ou `docker system prune` como rotina. Reiniciar o servidor reinicia a trajetória do simulador; não há histórico persistente nesta aula. A política `restart: unless-stopped` não reinicia automaticamente todo container apenas marcado como `unhealthy` e não comprova que a rede inteira se recupera após reboot.

Para retornar ao modo manual, pare o projeto, confira que a porta 4840 está livre e execute o servidor anterior no ambiente preservado, com seu endpoint Ethernet correto.

## Limites e evidências

A preparação foi testada na nuvem com execução Python e validações do Compose, conforme o [relatório](testes/RELATORIO_VALIDACAO.md). Isso não equivale a build/execução Docker ARM64 ou validação física do firewall. Registre separadamente os resultados no seu Raspberry.

Nos logs enviados em 29/10, o Pi 3 apresentou `ip_forward=1`, serviço nftables habilitado e regras para o notebook `.14`. Esses dados não demonstram, sozinhos, restauração correta após reinicialização. A rota Windows observada era temporária. Verifique persistência de cada camada em uma janela controlada.

Streamlit, acesso HTTP 8501 e o cliente de visualização são continuação preparada. Banco temporal, retenção histórica e diagnóstico continuam em etapas futuras da série.

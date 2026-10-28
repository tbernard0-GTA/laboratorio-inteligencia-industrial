# Checklist de gravação — Aula 3

**Não começar a gravação longa enquanto os itens bloqueantes estiverem pendentes.** Endereços abaixo são os observados; confirmar DHCP. Documentação e testes na nuvem não substituem o ensaio no Pi4 ARM64.

## Preparação demorada — antes de apertar REC

- [ ] Fonte adequada, cabo Ethernet e espaço livre: Pi3 sem alerta de baixa tensão; Pi4 `df -h /` e `free -h`. Os5GB livres antigos não garantem espaço para camadas de build; conferir novamente. Não rodar `docker system prune` indiscriminadamente.
- [ ] Código da branch/commit revisado no Pi4; pasta da aula identificada. Não sobrescrever o antigo `~/laboratorio-industrial/tep-opc` sem backup.
- [ ] Docker e Compose **somente no Pi4**: `docker version`, `docker compose version`, `docker info`. Histórico tinha Docker, portanto não reinstalar por rotina.
- [ ] Se ausentes/incompatíveis, preparar instalação fora da gravação seguindo [Docker Engine no Debian](https://docs.docker.com/engine/install/debian/), verificando versão do SO, arquitetura suportada e possíveis conflitos com pacotes existentes. Sem `curl | sh`. Revisar remoções propostas antes de aprovar.
- [ ] Acesso Docker resolvido. Usar `sudo docker ...` se necessário; adicionar usuário ao grupo docker concede privilégio equivalente a root e não é simples “conserto de permissão”.
- [ ] Dependências/imagens **ARM64** construídas/carregadas antes, com tempo medido. Pi4 isolado pode não ter egress de internet pelo Pi3: isso é esperado no firewall atual, não motivo para permitir tudo.
- [ ] Se necessário, construir para `linux/arm64` em ambiente autorizado e transferir imagens via SSH com salto (`docker save`/`docker load`); imagem x86_64 não é substituto. Verificar nomes/tags usados pelo Compose antes de exportar. Ensaio completo no Pi continua obrigatório.
- [ ] `.env` criado a partir de `.env.example`, `PI4_BIND_IP=10.77.0.10` confirmado, sem segredos em commit. Validar `dc config`.
- [ ] Identificar servidor manual da aula1 e seu modo de inicialização. Parar **somente** esse processo/serviço no momento da migração, sem `pkill python` ou parar todos os containers.
- [ ] Script antigo e instrução de retorno disponíveis; endpoint antigo Wi-Fi192.168.1.19 pode precisar da configuração OT já feita na aula2.
- [ ] Ensaio: containers, cliente OPC real, UAExpert, dashboard, reconexão e restart no Pi4. Registrar o que passou, não antecipar sucesso.
- [ ] Ler [procedimento de firewall](rede/firewall_8501.md), backups e rollback; não persistir antes da validação.

## Preflight rápido — 5 a 10 minutos fora dos60 da aula

### Windows

```powershell
ipconfig
route print 10.77.*
ssh admin@192.168.1.17
# Outra janela:
ssh -J admin@192.168.1.17 devadmin@10.77.0.10
```

- [ ] Notebook IP atual corresponde à regra de origem. Se mudou, revisar e adaptar, não abrir toda a sub-rede por conveniência.
- [ ] Rota10.77.0.0/24 via.17 presente; índice de interface conferido se for necessário recriar rota temporária.
- [ ] Uma janela claramente identificada **Pi3**, outra **Pi4 via salto**, e PowerShell separado.

### Pi3

```bash
ip -4 -br addr
sysctl net.ipv4.ip_forward
sudo nft -a list chain inet iilab_filter forward
```

- [ ] Wi-Fi.17 e Ethernet10.77.0.1 confirmados; forwarding1.
- [ ] Regras4840/22 e drop final presentes;8501 ainda não liberada para a demonstração inicial.
- [ ] Sem Docker instalado como parte desta aula; não alterar INPUT/OUTPUT.
- [ ] Persistência de firewall/forwarding anotada como confirmada ou pendente; não presumir após reinício.

### Pi4

```bash
whoami
hostname
uname -m
ip -4 -br addr
ip -4 route get 192.168.1.16
nmcli radio wifi
df -h /
docker compose version
```

- [ ] `devadmin`, host correto, ARM64/aarch64,10.77.0.10, retorno via10.77.0.1, Wi-Fi OFF.
- [ ] VPN/Tailscale observados separadamente; não usar hostname que resolva por caminho alternativo.
- [ ] Portas4840/8501 sem conflito de processos não identificados.

## Durante a gravação — checkpoints de evidência

- [ ] `dc config` → configuração renderizada com binds corretos.
- [ ] `dc up -d`, `dc ps`, `dc logs --tail=50` → ambos serviços executando, sem afirmar que “running” prova comunicação.
- [ ] Cliente `opc_client.py --once` lê três tags reais e status/timestamps.
- [ ] UAExpert acessa endpoint OT; dashboard saudável no próprio Pi4.
- [ ] Windows8501 falha **com serviço saudável e rota comprovada**;22 direto falha;4840 funciona.
- [ ] Regra8501 específica inserida antes do drop final e seu handle registrado.
- [ ] Browser mostra valores/atualização/tendência; contadores/captura evidenciam tráfego.
- [ ] Remover regra, abrir NOVA conexão e comprovar bloqueio; established pode continuar.
- [ ] Readicionar somente se desejar encerrar com dashboard acessível; persistência fica para validação controlada.
- [ ] `dc restart tep-opc` → queda/reconexão observadas; histórico em memória não é historiador.

## Cena e plano B

- [ ] OBS: cinco slides de contexto e demais usados apenas como apoio; fonte terminal legível, ganho de áudio testado.
- [ ] Sol fala apenas no gancho; comandos pequenos no chat, sem antecipar etapas.
- [ ] Logs limpos de segredos, notificações ocultas, apenas dados simulados.
- [ ] Se build levar tempo, mostrar comando e cortar espera na edição; não encenar build aprovado.
- [ ] Se hardware falhar, mostrar arquitetura/código e anunciar ensaio pendente; mock só em seção de testes explicitamente rotulada.
- [ ] Se houver risco de perder administração, parar mudanças e usar console físico/rollback; não improvisar flush.

## Critério de encerramento

A aula está demonstrada quando TEP+OPC e Streamlit rodam no Pi4, o cliente usa a rede Compose, o notebook só atravessa o gateway nas exceções autorizadas, o ciclo8501 bloqueia→permite→remove foi observado e o salto administrativo permanece disponível. Buildcloud, testes unitários, HTTP saudável, restart de container e persistência após reboot são evidências diferentes: registre cada uma separadamente.

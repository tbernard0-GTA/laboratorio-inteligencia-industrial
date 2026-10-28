# TCP 8501 — liberar, observar e reverter sem trocar o firewall

**Executar somente no laboratório, presencialmente, depois de revisar os valores.** Este documento foi preparado na nuvem; não comprova o estado atual dos Raspberry Pi. Mantenha uma sessão SSH no Pi 3, uma sessão de salto no Pi 4 e acesso físico. Não altere regras `input`/`output` durante esta demonstração. Não use `flush ruleset`, não desative o firewall, não limpe conntrack globalmente e não carregue um arquivo genérico por cima da configuração existente.

## 1. Conferir o caminho e identificar os terminais

| Terminal | Uso | Endereço observado na aula 2 — confirmar |
|---|---|---|
| Windows / PowerShell | navegador e testes do cliente | `192.168.1.16` |
| Pi 3 / `admin` | roteamento e firewall | Wi-Fi `192.168.1.17`; Ethernet `10.77.0.1` |
| Pi 4 / `devadmin` | Docker, TEP/OPC e Streamlit | Ethernet `10.77.0.10` |

**Windows:**

```powershell
ipconfig
route print 10.77.*
ssh -J admin@192.168.1.17 devadmin@10.77.0.10
```

A rota da aula 2 era temporária. Se estiver ausente, confirme o índice atual da interface Wi-Fi com `Get-NetIPInterface -AddressFamily IPv4`; só então, em PowerShell **como administrador**, adapte e execute:

```powershell
# 8 é apenas o índice observado anteriormente; substitua se mudou.
route add 10.77.0.0 mask 255.255.255.0 192.168.1.17 metric 5 if 8
route print 10.77.*
```

Não adicione rota duplicada nem use `-p` automaticamente. O destino é a sub-rede OT; o próximo salto é o Wi-Fi do Pi 3. Para remover APENAS a rota adicionada nesta preparação, depois da aula: `route delete 10.77.0.0 mask 255.255.255.0 192.168.1.17`.

**Pi 3:**

```bash
whoami
hostname
ip -4 -br addr
ip -4 route
sysctl net.ipv4.ip_forward
sudo nft -a list ruleset
```

Esperado: `net.ipv4.ip_forward = 1`, Ethernet `10.77.0.1/24`, Wi-Fi na rede do notebook. Se forwarding estiver 0, pare e recupere a configuração da aula 2 conscientemente; ativação transitória não prova persistência.

**Pi 4, via salto:**

```bash
printf '%s\n' "$SSH_CONNECTION"
ip -4 -br addr
ip -4 route get 192.168.1.16
nmcli radio wifi
```

Esperado: cliente SSH `10.77.0.1`; resposta ao notebook via `10.77.0.1 dev eth0`; Wi-Fi desabilitado. Tailscale/VPN, caso presentes, exigem revisão: não são eliminados por desligar Wi-Fi. Use IP OT explícito para a demonstração.

## 2. Baseline: serviço ativo, acesso ainda bloqueado

Primeiro o Compose deve estar saudável no Pi 4. A porta publicada no Pi 4 **não libera** o encaminhamento no Pi 3. A ausência de serviço, rota ou resposta não é prova de bloqueio por firewall.

No Pi 4, na pasta da aula:

```bash
docker compose --env-file .env -f docker/compose.yaml ps
curl --fail --max-time 5 http://10.77.0.10:8501/_stcore/health
```

Se `curl` não estiver disponível, verifique com o cliente HTTP já disponível ou prepare-o antes da gravação. O health endpoint apenas confirma o servidor web, não a qualidade das tags OPC.

No Windows, com a regra 8501 ainda ausente:

```powershell
Test-NetConnection 10.77.0.10 -Port 8501
Test-NetConnection 10.77.0.10 -Port 4840
Test-NetConnection 10.77.0.10 -Port 22
```

Esperado: TCP8501 `False`, TCP4840 `True`, TCP22 direto `False`. Se 8501 já estiver permitido, investigue a regra existente; não apague regras desconhecidas para produzir um efeito visual. O teste SSH direto não é o mesmo que SSH com `-J`.

## 3. Backup do estado em execução e da configuração de inicialização

**Pi 3:**

```bash
BACKUP="$HOME/iilab-firewall/backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP"
chmod 700 "$BACKUP"
sudo nft -a list ruleset > "$BACKUP/ruleset-live-handles.nft"
sudo nft -s list ruleset > "$BACKUP/ruleset-live-stateless.nft"
systemctl cat nftables > "$BACKUP/nftables-service.txt"
systemctl is-enabled nftables > "$BACKUP/nftables-enabled.txt" 2>&1 || true
if sudo test -f /etc/nftables.conf; then
  sudo cp -a /etc/nftables.conf "$BACKUP/nftables.conf.before"
fi
if test -f "$HOME/iilab-firewall/iilab-forward.nft"; then
  cp -a "$HOME/iilab-firewall/iilab-forward.nft" "$BACKUP/iilab-forward.nft.before"
fi
printf 'Backup: %s\n' "$BACKUP"
sudo nft -a list chain inet iilab_filter forward
```

Leia o serviço e os `include` de `/etc/nftables.conf`. Copie também cada arquivo incluído relevante antes de editá-lo. Arquivo da aula 2 em `$HOME` não significa configuração carregada no boot. O backup completo é evidência e recuperação assistida: **não o recarregue automaticamente sobre um ruleset vivo**, pois isso pode duplicar regras/objetos ou alterar outros serviços.

## 4. Inserção única e estreita, antes do descarte final

Na aula 2 a chain era `inet iilab_filter forward`, com `policy drop`, `invalid drop`, `established,related accept`, exceção4840, bloqueio22, ICMP de diagnóstico e descarte final comentado. Confira isso novamente. Se os nomes ou ordem divergirem, pare e adapte com revisão.

Os handles mudam. Leia o handle da regra **`Demais encaminhamentos bloqueados`** agora, não reutilize o número7 da gravação passada.

**Pi 3, mesmo terminal:**

```bash
NOTEBOOK_IP=192.168.1.16
PI4_IP=10.77.0.10
sudo nft -a list chain inet iilab_filter forward
read -r -p 'Handle atual do drop final: ' DROP_HANDLE
case "$DROP_HANDLE" in ''|*[!0-9]*) echo 'Handle invalido';; *) echo "Conferir handle: $DROP_HANDLE";; esac
```

Confirme visualmente que é o descarte terminal, que não existe `AULA3_STREAMLIT_8501` e que os IPs correspondem ao preflight. **Só prossiga com número válido.** Gere um arquivo com uma única operação:

```bash
case "$DROP_HANDLE" in ''|*[!0-9]*) echo 'PARE: handle invalido';;
*)
  printf 'insert rule inet iilab_filter forward handle %s iifname "wlan0" oifname "eth0" ip saddr %s ip daddr %s tcp dport 8501 counter accept comment "AULA3_STREAMLIT_8501"\n' \
    "$DROP_HANDLE" "$NOTEBOOK_IP" "$PI4_IP" > "$BACKUP/add-8501.nft"
  cat "$BACKUP/add-8501.nft"
  sudo nft -c -f "$BACKUP/add-8501.nft"
  ;;
esac
```

Após revisão e sucesso de `-c`, aplique **uma vez**, não repetidamente:

```bash
sudo nft -f "$BACKUP/add-8501.nft"
sudo nft -a list chain inet iilab_filter forward
```

`insert ... handle` insere antes da regra indicada. Uma regra acrescentada depois do descarte terminal não é alcançada. Anote o novo handle associado a `AULA3_STREAMLIT_8501`.

## 5. Demonstrar com evidências

Windows:

```powershell
Test-NetConnection 10.77.0.10 -Port 8501
Test-NetConnection 10.77.0.10 -Port 22
```

Abra **`http://10.77.0.10:8501`**. Esperado: página carregada, conexão OPC identificada, pressão/nível/temperatura e horários se atualizando; SSH direto ainda bloqueado. Mantenha UAExpert usando `opc.tcp://10.77.0.10:4840/tep/`.

Pi 3, outra sessão:

```bash
sudo tcpdump -ni wlan0 -c 30 'host 192.168.1.16 and host 10.77.0.10 and tcp port 8501'
# Em uma segunda captura, compare o lado Ethernet:
sudo tcpdump -ni eth0 -c 30 'host 192.168.1.16 and host 10.77.0.10 and tcp port 8501'
sudo nft -a list chain inet iilab_filter forward
```

Se esperar indefinidamente por30 pacotes, gere tráfego abrindo a página ou interrompa com Ctrl+C. Não divulgue capturas de tráfego corporativo. A regra8501 pode contar apenas pacotes iniciais: os demais passam pela regra anterior `established,related`. Contador de pacotes não é contador de usuários. TCP22 entre Pi3 e Pi4 corresponde à administração via salto; não prova falha no bloqueio do tráfego encaminhado do notebook.

## 6. Rollback da mudança desta aula

Pi 3: releia handles e remova **apenas** a regra com comentário exclusivo:

```bash
sudo nft -a list chain inet iilab_filter forward
read -r -p 'Handle da regra AULA3_STREAMLIT_8501: ' ALLOW_HANDLE
case "$ALLOW_HANDLE" in ''|*[!0-9]*) echo 'PARE: handle invalido';;
*) sudo nft delete rule inet iilab_filter forward handle "$ALLOW_HANDLE";;
esac
sudo nft -a list chain inet iilab_filter forward
```

Confirme visualmente o handle antes de executar: validação numérica não confirma a identidade da regra.

**Sessões TCP já estabelecidas podem continuar** por causa de `established,related accept`. Feche as abas do dashboard e use um **novo** `Test-NetConnection 10.77.0.10 -Port 8501` no Windows. Esperado: novo TCP bloqueado. Uma página congelada em cache não prova conexão ativa. Não use `conntrack -F` para forçar a demonstração.

Verifique que4840 continua acessível, SSH direto22 segue bloqueado e SSH com salto ainda funciona. Se não, pare a aula e compare o estado com o backup; não substitua todo o firewall para tentar consertar uma regra.

## 7. Persistir somente a configuração aprovada

Ao terminar o ciclo bloquear→permitir→remover, decida se o laboratório deve terminar com8501 aberta. Se sim, repita a inserção com **handle atual** e valide outra vez. A persistência é uma etapa distinta, não necessária para a demonstração curta.

1. Identifique o mecanismo efetivo (`systemctl cat nftables`, includes e automações existentes). Não presuma que `/etc/nftables.conf` é a única fonte.
2. Faça backup da fonte efetiva e de seus includes.
3. Edite **somente a chain existente** na fonte efetiva, adicionando antes do descarte final a linha abaixo, com IPs conferidos; sem `handle` salvo:

   ```nft
   iifname "wlan0" oifname "eth0" ip saddr 192.168.1.16 ip daddr 10.77.0.10 tcp dport 8501 counter accept comment "AULA3_STREAMLIT_8501"
   ```

4. Revise o diff: apenas a exceção autorizada. Valide o arquivo de entrada efetivo com `sudo nft -c -f CAMINHO_REAL`. `CAMINHO_REAL` é um campo a substituir após inspeção, não um comando pronto. Não acrescente um flush para fazer a validação passar.
5. Não reinicie/recarregue o serviço remotamente sem entender seu comportamento. Runtime já está correto. Reserve o teste de boot para janela de manutenção, acesso físico e plano de restauração das fontes originais.
6. Após boot, confirme regra, forwarding IPv4, perfis NetworkManager, rota Windows, containers,4840,8501,22 e salto SSH. Persistência de uma parte não comprova a das outras.

Se não houver fonte persistente identificável, registre **persistência pendente** em vez de inventar um serviço/arquivo genérico. Para reverter uma persistência, remova apenas a linha adicionada na fonte e valide; no runtime use a remoção por handle acima.

## Limites e referências

HTTP8501 e OPC UA sem segurança são didáticos; não abrir portas no roteador de internet. O Pi3 controla tráfego encaminhado; Docker implementa publicação/regras próprias no Pi4. Não desative a gestão de firewall do Docker para simplificar a aula. A porta permitida não valida conteúdo de aplicação nem substitui autenticação/criptografia.

Sintaxe de `insert`, handles, `delete` e `-c`: [manual oficial nftables](https://netfilter.org/projects/nftables/manpage.html). Comportamento de redes/publicação do Docker: [Docker — packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/).

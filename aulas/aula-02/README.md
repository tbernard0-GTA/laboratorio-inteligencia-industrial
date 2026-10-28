# Aula 02 — Separação de redes com roteamento e nftables

Nesta aula, o Raspberry Pi 3 fica entre o notebook e o Raspberry Pi 4, que executa o simulador TEP e o servidor OPC UA da [aula 01](../../README.md#aula-01--do-zero-ao-opc-ua-com-tep). O objetivo é observar a comunicação entre duas redes e controlar o tráfego encaminhado pelo Pi 3. Os comandos abaixo são um roteiro reproduzível para um laboratório semelhante; adapte endereços, interfaces e conexões ao seu ambiente.

> Use uma rede de laboratório autorizada e mantenha acesso local aos dois Raspberry Pi durante as mudanças. O servidor da aula 1 aceita conexões anônimas sem criptografia; não exponha a porta 4840 à internet nem use essa configuração como solução de produção.

## Topologia de exemplo

```text
Notebook (Wi-Fi)           Raspberry Pi 3                  Raspberry Pi 4
192.168.1.16  ── Wi-Fi ──  192.168.1.17 (wlan0)
                           10.77.0.1 (eth0) ─ Ethernet ─ 10.77.0.10 (eth0)
                                     roteador/firewall       TEP + OPC UA :4840
```

Os endereços dos Raspberry Pi e as interfaces acompanham o exemplo do vídeo. O endereço do notebook (`192.168.1.16`) também foi observado no firewall da aula. Os nomes de usuários e os nomes das conexões abaixo são exemplos. Adapte todos os valores ao seu ambiente. O notebook e a interface Wi-Fi do Pi 3 estão na rede `192.168.1.0/24`; a Ethernet dedicada usa `10.77.0.0/24`, uma sub-rede diferente e que não deve se sobrepor a outras redes ou VPNs. Use endereços livres ou reservas DHCP para notebook e Pi 3. Confira máscara, IPs e nomes antes de substituir os exemplos. Os comandos Linux a seguir pressupõem NetworkManager, `nmcli`, `nft` e `tcpdump`; adapte-os se a sua instalação usar outro gerenciador de rede.

## 1. Identificar interfaces e preservar o acesso

Conecte os dois Raspberry Pi por cabo Ethernet. No **notebook**, identifique seu endereço Wi-Fi e o endereço do Pi 3. No Windows, use `ipconfig`; no Linux, `ip -br address` e `ip route`. Em cada Raspberry, use:

```bash
hostname -I
ip -br address
ip route
nmcli device status
nmcli -f NAME,UUID,TYPE,DEVICE connection show
nmcli -f NAME,UUID,TYPE,DEVICE connection show --active
```

A primeira lista de conexões inclui perfis salvos, inclusive os inativos; a segunda mostra apenas os ativos. Identifique a interface Ethernet de cada Pi e a conexão Wi-Fi do Pi 4. Se já houver um perfil Ethernet adequado para a interface dedicada, anote seu nome ou UUID e suas configurações anteriores. Caso não exista, a etapa seguinte mostra como criar um. Use UUID se houver nomes duplicados. Os comandos abaixo usam `eth0` e `wlan0` como exemplos. Não confunda o IP Wi-Fi antigo do Pi 4 com o novo IP Ethernet.

Antes de alterar qualquer conexão, confirme que você consegue acessar o Pi 3 e que, a partir dele, consegue acessar o Pi 4. A partir do notebook, o salto usa o Pi 3 como intermediário:

```bash
ssh -J USUARIO_PI3@192.168.1.17 USUARIO_PI4@10.77.0.10
```

O destino Ethernet passa a funcionar após a etapa seguinte. `-J` abre SSH para o Pi 3 e, por dentro dessa sessão, acessa o Pi 4; ambos precisam ter SSH habilitado e autenticação configurada. Mantenha uma sessão administrativa aberta e uma forma de acesso local. Alterar uma conexão remota pode derrubá-la; confirme o acesso por salto em uma segunda sessão antes de desligar o Wi-Fi do Pi 4.

## 2. Configurar a Ethernet entre os Raspberry Pi

Use um perfil Ethernet adequado para a interface dedicada em cada Pi. Caso precise criar um, os comandos a seguir são uma alternativa: execute somente o comando correspondente em cada máquina, depois de confirmar que o nome não está em uso. Substitua `eth0` pela interface identificada e adapte os endereços:

```bash
# No Pi 3
sudo nmcli connection add type ethernet ifname eth0 con-name iilab-ot-fw ipv4.method manual ipv4.addresses '10.77.0.1/24' ipv4.never-default yes connection.autoconnect no

# No Pi 4
sudo nmcli connection add type ethernet ifname eth0 con-name iilab-ot-fabrica ipv4.method manual ipv4.addresses '10.77.0.10/24' ipv4.never-default yes connection.autoconnect no
```

Os perfis criados aqui não são ativados automaticamente; a ativação é feita abaixo. Com `connection.autoconnect no`, eles também não voltarão automaticamente após reinicialização, a menos que essa opção seja alterada. Se já existir um perfil adequado, não é necessário criar outro. Nos comandos seguintes, substitua `CONEXAO_ETH` pelo nome ou UUID do perfil escolhido em cada Pi. A ativação altera a configuração da interface Ethernet; mantenha uma forma alternativa de acesso.

No **Pi 3**, configure a conexão Ethernet com endereço fixo, sem criar rota padrão por ela:

```bash
CONEXAO_ETH='NOME_DA_CONEXAO_ETHERNET_PI3'
sudo nmcli connection modify "$CONEXAO_ETH" ipv4.method manual ipv4.addresses '10.77.0.1/24' ipv4.never-default yes
sudo nmcli connection up "$CONEXAO_ETH"
ip -br address
ip route
```

No **Pi 4**, antes de ativar um perfil existente, confira suas rotas e gateway. Se ele já configurar uma rota para o notebook, não prossiga com sua ativação nesta etapa: use um perfil dedicado sem essa rota ou ajuste-o com acesso local, depois de registrar a configuração original.

```bash
CONEXAO_ETH='NOME_DA_CONEXAO_ETHERNET_PI4'
nmcli -f ipv4.routes,ipv4.gateway connection show "$CONEXAO_ETH"
```

Configure apenas o endereço Ethernet por enquanto:

```bash
sudo nmcli connection modify "$CONEXAO_ETH" ipv4.method manual ipv4.addresses '10.77.0.10/24' ipv4.never-default yes
sudo nmcli connection up "$CONEXAO_ETH"
ip -br address
```

No Pi 3, teste `ping -c 3 10.77.0.10`; no Pi 4, teste `ping -c 3 10.77.0.1`. Agora, em outra janela do notebook, abra o `ssh -J` mostrado na etapa 1. **Mantenha essa sessão de salto aberta** e, no Pi 4, confira `echo "$SSH_CONNECTION"`: no exemplo, a origem deve ser `10.77.0.1` e o endereço local, `10.77.0.10`. Assim, a administração segue pelo cabo antes da mudança na rota de retorno. Se o teste falhar, resolva o acesso antes de continuar.

## 3. Habilitar o caminho entre as redes

No **Pi 3**, verifique a interface Wi-Fi e habilite temporariamente o encaminhamento IPv4:

```bash
ip -br address
ip route
sudo sysctl -w net.ipv4.ip_forward=1
sysctl net.ipv4.ip_forward
```

Na **sessão de salto aberta para o Pi 4**, adicione uma rota temporária de retorno somente para o notebook, depois de conferir que não existe outra rota para o mesmo destino:

```bash
ip -4 route show exact 192.168.1.16/32
ip route get 192.168.1.16
sudo ip route add 192.168.1.16/32 via 10.77.0.1 dev eth0
ip route get 192.168.1.16
```

A última resposta deve indicar `via 10.77.0.1 dev eth0`. Se já existir uma rota para `192.168.1.16/32`, inspecione-a e resolva o conflito antes de adicionar outra; não substitua uma rota existente sem conhecer seu uso. A mudança pode interromper uma sessão direta anterior pelo Wi-Fi. Se o IP do notebook mudar, adapte esta rota e as regras do firewall. A rota é temporária; remova-a na etapa «Desfazer as mudanças» ou ela desaparecerá após reinicialização.

No **notebook**, adicione uma rota para a rede Ethernet via IP Wi-Fi do Pi 3. No Linux:

```bash
sudo ip route add 10.77.0.0/24 via 192.168.1.17
ip route get 10.77.0.10
```

No Windows, em PowerShell ou Prompt de Comando **como administrador**:

```powershell
route ADD 10.77.0.0 MASK 255.255.255.0 192.168.1.17
route PRINT 10.77.0.0
```

Essas rotas não usam NAT: o Pi 4 enxerga o IP real do notebook e precisa da rota de retorno configurada acima. O exemplo de rota no notebook e o `ip_forward` são temporários; a persistência após reinício não é validada nesta aula. Regras preexistentes, isolamento de clientes no Wi-Fi ou VPNs podem impedir o teste. Antes do firewall, teste a conectividade a `10.77.0.10` e uma nova conexão SSH direta para estabelecer uma referência; o sucesso depende também do firewall do Pi 4.

## 4. Publicar o servidor OPC UA na Ethernet

No **Pi 4**, no arquivo `aulas/aula-01/servidor_opc.py`, ajuste `ENDPOINT` para o IP Ethernet do próprio Pi 4:

```python
ENDPOINT = "opc.tcp://10.77.0.10:4840/tep/"
```

Ative o ambiente virtual e execute o servidor conforme a [aula 01](../../README.md#2-executar-o-servidor-opc-ua). Reinicie o processo caso já esteja rodando. Confira no Pi 4 se há um serviço escutando:

```bash
sudo ss -lntp | grep ':4840'
```

No notebook, conecte o UAExpert a `opc.tcp://10.77.0.10:4840/tep/`, com as opções de segurança da aula 1. Confira as variáveis e atualização dos valores. Falha no serviço ou no cliente não demonstra, por si só, um bloqueio do firewall.

## 5. Aplicar regras de encaminhamento no Pi 3

O exemplo usa uma tabela dedicada, temporária, e controla pacotes **encaminhados** entre interfaces. Primeiro, instale as ferramentas se necessário e inspecione as regras existentes:

```bash
sudo apt update
sudo apt install nftables tcpdump
sudo nft list ruleset
```

Não apague o conjunto de regras existente. A cadeia a seguir tem política `drop` para o tráfego encaminhado que não se enquadrar nas regras; ela pode afetar outros dispositivos ou serviços que atravessem o Pi 3. Outras cadeias de firewall existentes também podem bloquear tráfego, mesmo quando esta tabela o aceita. Em um laboratório dedicado, use o arquivo [aula02.nft](aula02.nft), ajustando os IPs e nomes das interfaces. Ele é uma versão adaptável das regras mostradas na aula:

```nft
table inet aula02 {
    chain forward {
        type filter hook forward priority filter; policy drop;
        ct state invalid counter drop
        ct state established,related counter accept
        iifname "wlan0" oifname "eth0" ip saddr 192.168.1.16 ip daddr 10.77.0.10 tcp dport 4840 ct state new counter accept
        iifname "wlan0" oifname "eth0" ip saddr 192.168.1.16 ip daddr 10.77.0.10 tcp dport 22 ct state new counter drop
        iifname "wlan0" oifname "eth0" ip saddr 192.168.1.16 ip daddr 10.77.0.10 ip protocol icmp counter accept
        counter drop
    }
}
```

No **Pi 3**, obtenha o repositório se ainda não estiver disponível. Entre na pasta da aula e edite `aula02.nft` para os endereços e interfaces do seu laboratório antes de aplicá-lo:

```bash
git clone https://github.com/tbernard0-GTA/laboratorio-inteligencia-industrial.git
cd laboratorio-inteligencia-industrial/aulas/aula-02
nano aula02.nft
```

Se já houver um clone atualizado no Pi 3, entre na pasta correspondente em vez de cloná-lo novamente. Valide e carregue o arquivo uma vez, e confira a tabela:

```bash
sudo nft -c -f aula02.nft
sudo nft -f aula02.nft
sudo nft -a list table inet aula02
```

O primeiro comando verifica a sintaxe; o segundo aplica as regras. Se a tabela `aula02` já existir, inspecione-a e remova-a somente se for a tabela deste laboratório antes de reaplicar. As regras permitem que o notebook inicie OPC UA para o Pi 4 e que pacotes de conexões estabelecidas retornem; registram e descartam novas tentativas SSH diretas; permitem ICMP do notebook para o Pi 4; descartam o restante do tráfego encaminhado. Tráfego destinado ao próprio Pi 3 e conexões iniciadas pelo próprio Pi 3 usam outros caminhos (`input` e `output`), não essa cadeia `forward`.

## 6. Testar OPC UA, SSH direto e salto

Para testar a regra OPC UA com uma conexão nova, no **Pi 3** anote o contador da regra TCP 4840 antes do teste:

```bash
sudo nft -a list table inet aula02
```

No **notebook**, desconecte o servidor no UAExpert e conecte novamente ao endpoint `opc.tcp://10.77.0.10:4840/tep/`. Confira as leituras e, no Pi 3, consulte a tabela outra vez. O contador da regra TCP 4840 deve aumentar durante a nova conexão; uma sessão que já estava aberta pode continuar passando pela regra `established,related`, sem demonstrar a regra de abertura.

Em seguida, no notebook, tente uma **nova** conexão SSH direta, sem reutilizar uma sessão existente:

```bash
ssh -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=5 USUARIO_PI4@10.77.0.10
```

Ela deve expirar. Na sequência, teste o salto:

```bash
ssh -J USUARIO_PI3@192.168.1.17 USUARIO_PI4@10.77.0.10
```

O salto ainda pode funcionar: o notebook conecta ao próprio Pi 3, e o Pi 3 abre outra conexão ao Pi 4. Essas conexões não atravessam a cadeia `forward` como SSH direto do notebook. Uma sessão direta estabelecida antes das regras também pode permanecer ativa por causa da regra `established`; feche-a e faça um novo teste para verificar o bloqueio.

Com o salto confirmado pelo endereço Ethernet e uma forma de acesso local disponível, no **Pi 4**, desative o rádio Wi-Fi e confira seu estado:

```bash
sudo nmcli radio wifi off
nmcli radio wifi
nmcli device status
ip -br address
```

A saída de `nmcli radio wifi` deve indicar `disabled`. O comando desliga o rádio para todos os perfis Wi-Fi do Pi 4. Confirme em uma nova sessão que o salto continua funcionando e que o OPC UA ainda responde pelo endereço Ethernet. A persistência desse estado após reinicialização não foi validada.

## 7. Observar pacotes e contadores

No **Pi 3**, em terminais separados, capture as duas interfaces enquanto executa novos testes a partir do notebook:

```bash
sudo tcpdump -ni wlan0 'host 192.168.1.16 and host 10.77.0.10 and (tcp port 22 or tcp port 4840)'
sudo tcpdump -ni eth0 'host 192.168.1.16 and host 10.77.0.10 and (tcp port 22 or tcp port 4840)'
```

Para observar também o SSH por salto, cuja origem na Ethernet é o próprio Pi 3, use o filtro mostrado na gravação:

```bash
sudo tcpdump -ni eth0 'host 10.77.0.10 and (tcp port 4840 or tcp port 22)'
```

Use Ctrl+C para encerrar. Compare as tentativas que chegam pela Wi-Fi com o tráfego visto na Ethernet e consulte os contadores do firewall antes e depois de cada teste:

```bash
sudo nft -a list table inet aula02
```

O contador na regra de SSH direto registra pacotes que corresponderam àquela regra; retransmissões podem produzir mais de um pacote por tentativa. A regra de OPC UA conta pacotes de abertura que corresponderem a ela, enquanto os demais pacotes da conexão podem ser contados pela regra `established,related`. O resumo de pacotes descartados pelo `tcpdump` refere-se a perdas da captura, não ao total bloqueado pelo nftables. Capture nas duas interfaces e interprete os contadores das regras em conjunto.

## Desfazer as mudanças

No **Pi 3**, remova somente a tabela deste exercício e restaure o valor anterior de encaminhamento (por exemplo, `0` se estava desativado):

```bash
sudo nft delete table inet aula02
sudo sysctl -w net.ipv4.ip_forward=0
```

No **notebook**, remova a rota criada neste exercício. Linux:

```bash
sudo ip route del 10.77.0.0/24 via 192.168.1.17
```

Windows, como administrador:

```powershell
route DELETE 10.77.0.0 MASK 255.255.255.0 192.168.1.17
```

No **Pi 4**, remova a rota temporária criada na etapa 3 e, se necessário, reative o rádio e o perfil Wi-Fi identificado na etapa 1:

```bash
sudo ip route del 192.168.1.16/32 via 10.77.0.1 dev eth0
sudo nmcli radio wifi on
sudo nmcli connection up 'NOME_DA_CONEXAO_WIFI_PI4'
```

Adapte o IP e a interface aos valores usados. Restaure o estado anterior do rádio e as configurações de Ethernet dos dois Pis com o gerenciador de rede; remova apenas perfis criados para este exercício e que não sejam mais necessários. Antes de alterar conexões remotamente, mantenha acesso local ou um caminho alternativo confirmado. Reponha também o endpoint do servidor, se necessário. Não há validação de persistência do firewall, das rotas ou do encaminhamento após reinicialização nesta etapa.

## Relação com a gravação

Na gravação, as conexões Ethernet criadas no NetworkManager receberam os nomes `iilab-ot-fw` no Pi 3 e `iilab-ot-fabrica` no Pi 4. O arquivo de firewall mostrado era `~/iilab-firewall/iilab-forward.nft`, com tabela `inet iilab_filter`. [iilab-forward-video.nft](iilab-forward-video.nft) reconstitui as regras a partir da listagem exibida, sem os contadores acumulados e identificadores; não é uma cópia do arquivo original. Este repositório também oferece `aula02.nft` como uma versão adaptável: usa uma tabela própria e restringe as regras de abertura de TCP ao estado `new`.

O Pi 4 apareceu com a rota padrão via `10.77.0.1`; para limitar o efeito sobre outras rotas, o roteiro acima usa uma rota específica para o notebook. No Windows, o vídeo especificou também uma métrica e um índice de interface que dependem do computador. Assim como na gravação, o roteiro desliga o rádio Wi-Fi do Pi 4 após confirmar a sessão SSH pelo caminho cabeado. Para evitar interromper a administração, a rota de retorno é adicionada depois que o salto e o encaminhamento foram conferidos.

## Limites e referências

Este exercício controla o encaminhamento no Pi 3; não substitui uma arquitetura de segurança industrial completa. A conectividade IPv6, os demais caminhos entre redes e as regras de outros dispositivos precisam ser avaliados separadamente. O servidor OPC UA da aula 1 permanece sem criptografia e autenticação de usuário.

- [Encaminhamento IPv4 no kernel Linux](https://docs.kernel.org/networking/ip-sysctl.html)
- [Cadeias e hooks no nftables](https://wiki.nftables.org/wiki-nftables/index.php/Configuring_chains)
- [Estados de conexão no nftables](https://wiki.nftables.org/wiki-nftables/index.php/Matching_connection_tracking_stateful_metainformation)
- [Opção `-J` do OpenSSH](https://man.openbsd.org/ssh.1)
- [Configurações do NetworkManager](https://networkmanager.pages.freedesktop.org/NetworkManager/NetworkManager/nm-settings-nmcli.html)

A configuração não foi validada após reinicialização nesta etapa.

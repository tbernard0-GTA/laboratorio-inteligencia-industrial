# Acessos e segurança

> Atualização de 29/10/2026: este documento preserva o histórico das etapas anteriores. A Aula 4 e seu estado comprovado ou pendente estão em [aulas/aula-04](../aulas/aula-04/) e nas entradas recentes do diário. Dados e planos históricos abaixo não comprovam o estado atual dos equipamentos.


Os comandos desta página são **exemplos para uso futuro**, após autorização e verificação do ambiente. Nenhum deles foi executado durante a preparação. Não altere automaticamente firewall, roteamento, interfaces ou serviços, nem interrompa serviços existentes sem análise. Confirme endereços, usuários, interfaces, autenticação, rotas e regras reais antes de qualquer operação. Preserve um caminho de recuperação.

## Referências históricas

| Componente | Endereço histórico | Uso relatado |
| --- | --- | --- |
| Notebook | `192.168.1.16` | Zona TI |
| Pi 3 Wi-Fi | `192.168.1.17` | Gateway na zona TI |
| Pi 3 Ethernet | `10.77.0.1` | Gateway na zona TA |
| Pi 4 Ethernet | `10.77.0.10` | TEP e OPC UA na zona TA |

Os valores são exemplos, não descoberta da rede atual. O código da Aula 1 contém outro endpoint histórico, `192.168.1.19`. O servidor OPC UA documentado usa TCP 4840, acesso anônimo e sem criptografia; limite-o à rede de laboratório. A porta TCP 8501 é apenas prevista para uma futura interface Streamlit e não está autorizada nem comprovadamente aberta.

## Administração por salto

O Pi 4 deve ser administrado por SSH usando o Pi 3 como jump host. Substitua os marcadores pelos usuários e endereços verificados; não salve credenciais no repositório. A partir do PowerShell, exemplos futuros são:

```powershell
# Conectar ao gateway, após validar usuário e endereço
ssh USUARIO_PI3@IP_PI3_WIFI

# Administrar o Pi 4 através do Pi 3
ssh -J USUARIO_PI3@IP_PI3_WIFI USUARIO_PI4@IP_PI4_ETHERNET
```

O acesso direto do notebook ao Pi 4 era bloqueado no cenário da Aula 2; confirme a configuração real e o salto em vez de presumir esse comportamento. O SSH ao próprio Pi 3 e o salto têm caminhos diferentes do tráfego direto encaminhado pelo gateway. Não alterar o arquivo de configuração SSH do Windows como parte desta preparação.

## Inspeção futura, somente leitura

Depois de confirmar o escopo e obter acesso autorizado, os seguintes exemplos podem apoiar o inventário. Sua execução não comprova por si só que todo o caminho está protegido ou funcional:

```powershell
# No notebook Windows: interfaces e rotas locais
ipconfig
route print

# Consulta TCP a partir do notebook; substitua o endereço pelo valor confirmado
Test-NetConnection -ComputerName IP_PI4_ETHERNET -Port 4840
```

```bash
# Em cada Pi, após conexão autorizada: endereços e rotas
ip -br address
ip route

# No Pi 3: consultar as regras existentes, sem alterá-las
sudo nft list ruleset

# No Pi 4: consultar sockets TCP em escuta
sudo ss -lntp
```

Os comandos remotos dependem das ferramentas e permissões existentes. Antes de qualquer mudança de rede, solicite autorização explícita, avalie efeitos em outras cadeias e serviços, preserve acesso local ou alternativo e planeje recuperação. Leia o roteiro da Aula 2 como referência, não como autorização para aplicá-lo.

## Credenciais e registro

Não armazene senhas, tokens, chaves privadas ou outros segredos no repositório, na documentação ou no diário. Evite registrar dados sensíveis em saídas e capturas. Documente somente evidências necessárias, decisões, limitações e resultados em [DIARIO_DE_BORDO.md](DIARIO_DE_BORDO.md).

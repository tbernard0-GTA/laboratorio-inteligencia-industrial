# Aula 5 — pacote, gravação e operação

**Gravação concluída, por relato de Thiago:** a Aula 4 foi mostrada, seus três contêineres foram parados preservando o volume e o pacote da Aula 5 foi transferido, carregado e executado no Pi 4. A saída de `sha256sum -c` confirmou os três arquivos; carga e subida foram relatadas. O historiador chegou a 17 ciclos/901 leituras depois de 14/742, e seu healthcheck foi relatado como aprovado. Após parada, somente o estado `Exited` do historiador foi relatado; o estado atual dos demais não foi confirmado.

Esta revisão não acessou o Pi. Não suba, pare ou recrie serviços apenas por seguir esta página: reconfirme estado e autorização. O procedimento abaixo foi preparado antes da gravação e permanece como referência condicional; arquivos, imagem e volume da Aula 5 já podem existir. O pacote também foi testado anteriormente no Docker Desktop sob emulação ARM64.

## Componentes

- Compose `aulas/aula-05/compose.yaml`; projeto `iilab-aula05`; serviços `tep-opc` e `historiador`; imagem única `iilab-aula05:1`, sem imagem auxiliar ou painel novo.
- Contêineres previstos: `iilab-aula05-tep-opc-1` e `iilab-aula05-historiador-1`. Volume previsto: `iilab-aula05_historico`. Banco no contêiner: `/data/historico_aula05.sqlite3`. O caminho do volume no host deve ser obtido por inspeção após a criação.
- Em produção o exemplo publica `10.77.0.10:4840`; o historiador conecta a `opc.tcp://tep-opc:4840/tep/`. O servidor anuncia o IP configurado e o namespace é resolvido pela URI `urn:laboratorio-industrial:tep`. `NoSecurity`/Anonymous é restrito à rede de laboratório; não expor à internet.
- Healthcheck do servidor descobre 53 tags e confere Good/timestamp. O do historiador lê SQLite sem escrita e exige um ciclo recente com 53 registros válidos Good. Não prova nova análise física nem integridade de todo o histórico. Depende do relógio correto.
- Sem retenção automática ou fila durável: até 915.840 leituras/dia a cinco segundos. Monitorar espaço e definir backup.

## Estado informado por Thiago

Pi 3 sincronizado via chrony, com `bindaddress 10.77.0.1` e atendimento NTP restrito a `allow 10.77.0.10/32`, e Pi 4 com timesyncd apontado para `10.77.0.1`, segundo o usuário. A saída apresentada informou `synchronized: yes`, UTC `2026-10-30 22:49:04` e offset estimado de `-876 µs` naquela amostra. **Não refazer a configuração de tempo.** Persistência após reboot e sincronização automática do Windows não foram comprovadas.

A aplicação anterior usa os contêineres `aula-03-tep-opc-1`, `aula-03-coletor-1` e `aula-03-interface-1`, portas `10.77.0.10:4840` e `10.77.0.10:8501` e volume `aula-03_historico` em `/var/lib/docker/volumes/aula-03_historico/_data`, montado em `/data`. Banco anterior: `/data/leituras.sqlite3`; coletor RW, interface RO. Uma pasta de backup anterior foi relatada, mas sua integridade não foi comprovada. A regra 8501 foi relatada em memória; persistência e teste final Windows permanecem pendentes. DNS externo do Pi falhou; não mudar DNS, Tailscale, firewall, rotas ou tempo por inferência.

## Artefatos finais já preparados no Windows

Diretório `C:\dev\iilab-aula05-export`:

```text
iilab-aula05-arm64-v2.tar
compose.yaml
consulta_ao_vivo.sql
SHA256SUMS-v2-lf
```

O arquivo sem `v2` e os manifestos anteriores `SHA256SUMS` e `SHA256SUMS-v2` são artefatos preservados: **não usá-los para a transição**. O manifesto `SHA256SUMS-v2` tem finais CRLF incompatíveis com a verificação Linux testada; use `SHA256SUMS-v2-lf`. A imagem final foi carregada novamente no Docker Desktop, com arquitetura `arm64` e ID `sha256:6b64ca0effc7e6360a9483bbc3072ecfcb82c9c656d062338def1ca1fe15bee2`.

```text
05c55ed1126373c9b22ea5a82626215d0134adb667b58565c63f55615bf60e8c  iilab-aula05-arm64-v2.tar
dac7c60b40fcadb974c825cbc397a623d0fb0b79d4d10e2e8b434f3f657be6b6  compose.yaml
8805a0a9cb9bc6af357540fb5e590314e50b964d6a8d626863a08133892164d8  consulta_ao_vivo.sql
```

### Reproduzir build no Windows

A base local `iilab-tep-opc:local` precisa ter ID `sha256:67df057d42604ee3af619515afbea237b04df78a263ce5fb165a14be1519af49` e arquitetura ARM64. Ela contém Python 3.13.18, NumPy 2.2.6, asyncua 2.1.0 e TEP 2.5.0 na revisão `9a6c8e5fcef4a2850778704e7793c87b0a187005`. O Dockerfile verifica as versões, mas a reprodução depende dessa base específica; não é garantia de imagem byte a byte idêntica.

```powershell
cd C:\dev\lab-ii\aulas\aula-05
$baseId = docker image inspect iilab-tep-opc:local --format '{{.Id}}'
if ($baseId -ne 'sha256:67df057d42604ee3af619515afbea237b04df78a263ce5fb165a14be1519af49') { throw 'Imagem base diferente ou ausente; pare.' }
docker buildx build --platform linux/arm64 --network=none --load -t iilab-aula05:1 .
if (Test-Path -LiteralPath C:\dev\iilab-aula05-export\iilab-aula05-arm64-rebuild.tar) { throw 'Arquivo já existe; não sobrescrever.' }
docker image save -o C:\dev\iilab-aula05-export\iilab-aula05-arm64-rebuild.tar iilab-aula05:1
Get-FileHash -Algorithm SHA256 C:\dev\iilab-aula05-export\iilab-aula05-arm64-rebuild.tar
```

Uma nova imagem exige novo manifesto e nova validação; não usar `SHA256SUMS-v2-lf` para ela.

## Transferência inicial — referência histórica, não repetir automaticamente

O SSH não interativo via salto expirou na preparação local; posteriormente, Thiago comprovou a transferência do pacote v2 com três hashes OK. Para qualquer operação futura, confirme a sessão interativa e as identidades no Windows:

```powershell
ssh -t -J admin@192.168.1.17 devadmin@10.77.0.10
```

No Pi 4, consulte o estado sem alterá-lo:

```bash
date -u
timedatectl status
sudo docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
sudo docker volume ls
sudo docker image ls iilab-aula05
ls -ld /home/devadmin/iilab-aula05
```

Se o diretório, a imagem `iilab-aula05:1` ou o volume `iilab-aula05_historico` já existirem, pare e inspecione; não sobrescreva dados ou configurações desconhecidos. Se não existirem e a transferência estiver autorizada, crie no Pi 4 o diretório novo; `mkdir` falha se ele já existir:

```bash
mkdir -m 700 /home/devadmin/iilab-aula05
```

No Windows, transfira os quatro arquivos pelo Pi 3:

```powershell
scp -o ProxyJump=admin@192.168.1.17 C:\dev\iilab-aula05-export\iilab-aula05-arm64-v2.tar C:\dev\iilab-aula05-export\compose.yaml C:\dev\iilab-aula05-export\consulta_ao_vivo.sql C:\dev\iilab-aula05-export\SHA256SUMS-v2-lf devadmin@10.77.0.10:/home/devadmin/iilab-aula05/
```

No Pi 4, confira os três hashes e o conflito de imagem/volume antes de carregar. `docker load` altera as imagens locais. Execute primeiro estas consultas; se o daemon não estiver disponível ou a tag ou o volume já existirem, pare:

```bash
cd /home/devadmin/iilab-aula05
sha256sum -c SHA256SUMS-v2-lf
sudo docker image ls iilab-aula05
sudo docker volume ls
```

Esperado: três hashes OK e nenhuma imagem ou volume da Aula 5 com esses nomes. Somente após conferir essas saídas, execute este bloco, que repete as verificações antes de carregar:

```bash
if ! sudo docker info >/dev/null 2>&1; then
  echo 'Docker indisponível; pare.'
elif sudo docker image inspect iilab-aula05:1 >/dev/null 2>&1; then
  echo 'A tag já existe; pare e inspecione.'
elif sudo docker volume inspect iilab-aula05_historico >/dev/null 2>&1; then
  echo 'O volume já existe; pare e inspecione.'
else
  sha256sum -c SHA256SUMS-v2-lf && sudo docker load -i /home/devadmin/iilab-aula05/iilab-aula05-arm64-v2.tar
fi
sudo docker image inspect iilab-aula05:1 --format 'arquitetura={{.Architecture}} id={{.Id}}'
```

Esperado após carregamento: arquitetura `arm64` e ID `sha256:6b64ca0effc7e6360a9483bbc3072ecfcb82c9c656d062338def1ca1fe15bee2`. Se qualquer verificação falhar, pare. `docker load` não precisa de DNS externo.

## Transição — referência histórica para operação autorizada no Pi 4

Antes de parar qualquer serviço: mostrar a Aula 4 no UAExpert e no painel; confirmar nomes/estado dos contêineres, IPs, porta 4840, sincronização e regras sem alterá-las; validar backup consistente do SQLite anterior com WAL e testar recuperação em cópia; verificar espaço, nova imagem, Compose e volume. Não foi verificada a integridade da pasta de backup relatada. Se algum item falhar, não trocar.

Somente após mostrar a Aula 4 e receber autorização explícita, pare os contêineres anteriores identificados. A ordem preserva os volumes:

```bash
sudo docker stop aula-03-coletor-1 && sudo docker stop aula-03-interface-1 && sudo docker stop aula-03-tep-opc-1
```

Confirme que a porta 4840 está livre. No mesmo terminal do Pi 4, defina a função e valide/suba o projeto novo. `sudo env` não depende de preservação do ambiente pelo sudo:

```bash
cd /home/devadmin/iilab-aula05
aula5() { sudo env PI4_BIND_IP=10.77.0.10 PI4_PORTA_OPC=4840 OPC_UA_ADVERTISE_HOST=10.77.0.10 docker compose -p iilab-aula05 -f /home/devadmin/iilab-aula05/compose.yaml "$@"; }
aula5 config --quiet && aula5 up -d --no-build --pull never
aula5 ps
aula5 logs --tail=100
```

Não usar `docker compose down -v`, `prune`, `git reset/clean`, nem apagar bancos ou volumes. A Aula 5 não monta `aula-03_historico`. Se houver falha, não insistir nem mudar firewall; preservar logs e avaliar rollback.

## Verificação e consultas no Pi 4 após subida autorizada

```bash
sudo docker ps --filter label=com.docker.compose.project=iilab-aula05 --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
sudo docker exec iilab-aula05-tep-opc-1 python /app/healthcheck_aula05.py servidor
sudo docker exec iilab-aula05-historiador-1 python /app/healthcheck_aula05.py historico
sudo docker exec iilab-aula05-historiador-1 python /app/consultar_historico.py /data/historico_aula05.sqlite3 contagem
sudo docker exec iilab-aula05-historiador-1 python /app/consultar_historico.py /data/historico_aula05.sqlite3 tags
```

Healthchecks sem saída e código 0 cumprem os critérios indicados. Repetir a contagem após pelo menos cinco segundos para verificar crescimento. No Windows, UAExpert: `opc.tcp://10.77.0.10:4840/tep/`, None/Anonymous; navegar em `Objects/TEP/XMEAS` e `XMV`. A descoberta interna e pela porta local alternativa foi testada no Docker Desktop; o usuário relatou coleta e consultas no Pi. Navegação das 53 tags no UAExpert contra o servidor novo não foi demonstrada por saída independente nesta revisão.

### Consulta no banco ativo usando VS Code e SSH

No Windows, edite `C:\dev\iilab-aula05-export\consulta_ao_vivo.sql` no VS Code. Na transferência inicial, confira o hash. Para futura edição, somente após confirmar que `/home/devadmin/iilab-aula05/consulta_ao_vivo.sql` é a cópia conhecida do pacote, envie novamente; isso substitui o arquivo de consulta, não o banco:

```powershell
scp -o ProxyJump=admin@192.168.1.17 C:\dev\iilab-aula05-export\consulta_ao_vivo.sql devadmin@10.77.0.10:/home/devadmin/iilab-aula05/consulta_ao_vivo.sql
```

No Pi 4, execute uma consulta SQL por vez no banco ativo:

```bash
sudo docker exec -i iilab-aula05-historiador-1 python /app/consultar_sql_stdin.py /data/historico_aula05.sqlite3 < /home/devadmin/iilab-aula05/consulta_ao_vivo.sql
```

O executor abre SQLite com `mode=ro` e `query_only` e autoriza somente consultas; `DELETE`, `ATTACH` e alterações de PRAGMA são recusados. Verifique 53 tags observadas: cadastro de 53 não prova coleta.

As consultas completas da gravação estão em [guia, seção 6](GUIA_ESTUDO_CODIGO_AULA_05.md#6-sql-explicado-progressivamente): cadastro e observadas, contagem/última coleta, últimas temperaturas, agregação válida por minuto, comparação de `XMEAS(7)`, `XMEAS(9)` e `XMV(10)` por `ciclo_id`, e auditoria de ciclos incompletos. Salve uma única consulta de cada vez no arquivo de entrada e execute o comando acima. Retorno vazio da auditoria só tem significado acompanhado da contagem de ciclos; não demonstra ausência de lacunas temporais ou qualidade perfeita. Antes de enviar uma nova versão do arquivo, confirme o destino: o `scp` sobrescreve essa cópia SQL.

## Rollback futuro — Pi 4

Se a Aula 5 falhar, pare somente seus dois contêineres sem remover volumes. Confirme que a porta 4840 foi liberada; então inicie os três contêineres anteriores previamente inspecionados:

```bash
sudo docker stop iilab-aula05-historiador-1
sudo docker stop iilab-aula05-tep-opc-1
sudo docker start aula-03-tep-opc-1
sudo docker start aula-03-coletor-1
sudo docker start aula-03-interface-1
sudo docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

Confirme endpoint, logs, volume e painel anteriores. Não restaurar por cima do banco; se os contêineres originais não existirem ou não subirem, pare e reavalie com backup verificado. Este rollback não foi relatado como executado na gravação.

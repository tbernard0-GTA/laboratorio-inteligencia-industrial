# Roteiro para implantação futura — não executado neste incremento

## Reprodução futura com imagem consolidada 1.0

A primeira implantação da imagem 0.1 e a execução com código montado foram relatadas pelo usuário como concluídas na gravação. Os comandos abaixo são uma referência para uma nova operação autorizada; o estado atual dos Pi, regras e serviços não foi inspecionado nesta revisão. A imagem 1.0 foi construída e testada somente no notebook e ainda não foi implantada no Pi.

A imagem local `iilab-aula06-api:1.0` incorpora os endpoints em `/opt/api` e `/opt/aula06-default`. Exportação: `C:\dev\iilab-aula06-export\iilab-aula06-api-arm64-v2.tar`, 285.293.568 bytes; SHA-256 `c33de100d7beb4c72c4a0dd4e45836beeabe4328743f260e2d42868e03ad8214`; ID `sha256:c0999745951fd8422ba72e64d76e4da25fa176018478c16bc88b19788a48d7f5`; `linux/arm64`. Manifesto `SHA256SUMS-v2` está no mesmo diretório externo ao Git. Cinco testes da Aula 6 passaram sob emulação com banco temporário e sem montar o código; 16 testes de regressão selecionados da Aula 5 passaram. O TAR inclui as camadas e foi carregado novamente no notebook.

Build reproduzível a partir da base local identificada no pacote anterior, sem rede, após verificar a identidade da base e que a tag 1.0 não conflita:

```powershell
docker image inspect iilab-aula06-api:0.1 --format '{{.Id}} {{.Os}}/{{.Architecture}}'
# Esperado: sha256:bc8bc3e951a14c388cdbf34dec2ec348531f0cb981363c2bbbc9522a72a73faa linux/arm64
docker buildx build --platform linux/arm64 --network none --load -f aulas/aula-06/Dockerfile.final -t iilab-aula06-api:1.0 aulas/aula-06
```

Para um novo Pi autorizado, confirme recursos, identidades SSH, rede, volume, permissões WAL/SHM e ausência de conflitos conforme o inventário histórico abaixo. Transfira o TAR v2 por salto, confira o hash no destino antes de `docker load`, e confira ID e arquitetura. A carga modifica imagens locais; não substitua uma tag diferente já existente. Sem montagem de código, com `IP`, `REDE` e `VOLUME` realmente confirmados e o nome de contêiner livre, a execução isolada seria:

```bash
sudo docker network inspect "$REDE" >/dev/null && sudo docker volume inspect "$VOLUME" >/dev/null && \
sudo docker run -d --pull never --name iilab-aula06-api --init --restart unless-stopped \
  --network "$REDE" -p "$IP:8000:8000/tcp" \
  --mount "type=volume,src=$VOLUME,dst=/data,readonly,volume-nocopy" \
  -e BANCO_HISTORICO=/data/historico_aula05.sqlite3 iilab-aula06-api:1.0
```

Verifique o `docker inspect` do contêiner, saúde e consultas. Não execute esse exemplo sobre o contêiner da gravação, nem deixe Docker criar um volume desconhecido. O código interno pode ser extraído de `/opt/aula06-default` com o procedimento histórico abaixo e montado em `/opt/api` para edição futura; a montagem substitui o código interno. Não altere outros serviços, firewall ou dados por inferência.

## Instalação original da gravação — referência histórica

A autorização para esta preparação não autoriza executar os comandos abaixo. Antes de uma implantação, confirme identidades SSH e o acesso via Pi 3; inventarie serviços, imagem, rede, volume, porta, espaço e permissões, sem parar ou alterar a Aula 5. Os nomes e endereços anteriores são históricos, não prova do estado atual. Confirme um caminho de recuperação. Se algum item divergir, pare. A API não tem autenticação ou TLS; mantenha acesso limitado à rede autorizada.

## Pacote local preparado

O TAR v1 abaixo contém a aplicação inicial com `/health`, não os endpoints `tags` e `historico` desenvolvidos depois. Para usá-los, forneça o código atualizado separadamente ao diretório montado e valide-o; o TAR não foi reconstruído. Esta seção descreve o pacote original, não confirma o estado atual do Pi.

- `C:\dev\iilab-aula06-export\iilab-aula06-api-arm64-v1.tar`: 285.279.744 bytes.
- SHA-256: `941c583c32c6f1d196e9c94c4549a202003a99517089cd2390295aec5128815e`.
- ID: `sha256:bc8bc3e951a14c388cdbf34dec2ec348531f0cb981363c2bbbc9522a72a73faa`; plataforma `linux/arm64`.
- Python 3.13.18, FastAPI 0.115.12, Uvicorn 0.34.2. O tar de `docker save` inclui as camadas da imagem; não é necessário baixar a base no Pi.
- Manifesto local `C:\dev\iilab-aula06-export\SHA256SUMS-v1`; não é necessário transferi-lo, pois o hash está abaixo.

## 1. Inspeção e transferência

No Windows, confirme hash e identidades. Substitua os marcadores por valores confirmados, sem copiar os colchetes:

```powershell
Get-FileHash -Algorithm SHA256 C:\dev\iilab-aula06-export\iilab-aula06-api-arm64-v1.tar
ssh -t -J USUARIO_PI3@IP_PI3 USUARIO_PI4@IP_PI4
```

Na sessão do Pi 4 confirme `uname -m` (`aarch64`), espaço em disco e estado da instalação. Inspecione sem mudar serviços:

```bash
df -h /home /var/lib/docker
sudo docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
sudo docker network ls
sudo docker volume ls
sudo docker image inspect iilab-aula06-api:0.1
sudo ss -ltnp | grep ':8000 ' || true
```

Se a tag já existir, confirme o ID antes de qualquer carga; não substitua imagem diferente. Confirme que a porta 8000 está livre, e que o usuário e diretório de destino estão corretos. No Pi, crie um diretório novo, sem sobrescrever arquivos; pare se já existir:

```bash
mkdir -m 700 /home/devadmin/iilab-aula06
```

Use o caminho somente se `devadmin` e `/home/devadmin` tiverem sido confirmados; caso contrário substitua-o nos comandos. Encerre a sessão e transfira **somente o tar** no Windows, sem sobrescrever arquivo existente:

```powershell
scp -o ProxyJump=USUARIO_PI3@IP_PI3 C:\dev\iilab-aula06-export\iilab-aula06-api-arm64-v1.tar USUARIO_PI4@IP_PI4:/home/devadmin/iilab-aula06/
```

## 2. Conferir e carregar imagem

No Pi, via jump host:

```bash
cd /home/devadmin/iilab-aula06
printf '%s  %s\n' '941c583c32c6f1d196e9c94c4549a202003a99517089cd2390295aec5128815e' 'iilab-aula06-api-arm64-v1.tar' | sha256sum -c -
```

Prossiga somente com `OK` e ausência de conflito de tag. O comando seguinte altera as imagens Docker locais:

```bash
sudo docker load -i /home/devadmin/iilab-aula06/iilab-aula06-api-arm64-v1.tar
sudo docker image inspect iilab-aula06-api:0.1 --format 'id={{.Id}} arquitetura={{.Os}}/{{.Architecture}}'
```

Confirme ID e `linux/arm64` conforme acima. Não é preciso instalar dependências nem baixar a base.

## 3. Código editável e inventário

No Pi, crie um diretório novo e extraia a cópia inicial da imagem, sem contêiner persistente e sem rede:

```bash
mkdir -m 755 /home/devadmin/iilab-aula06/api
sudo docker run --rm --pull never --network none --entrypoint tar iilab-aula06-api:0.1 -C /opt/aula06-default -cf - . | tar -xf - -C /home/devadmin/iilab-aula06/api
ls -la /home/devadmin/iilab-aula06/api
```

Verifique a presença e leitura de `main.py`. O volume histórico e rede informados eram `iilab-aula05_historico` e provavelmente `iilab-aula05_iilab`; **confirme pelo inventário**, inclusive a rede de ambos os contêineres e o volume montado pelo historiador:

```bash
sudo docker inspect iilab-aula05-historiador-1 --format '{{json .Mounts}} {{json .NetworkSettings.Networks}}'
sudo docker inspect iilab-aula05-tep-opc-1 --format '{{json .NetworkSettings.Networks}}'
sudo docker network inspect iilab-aula05_iilab
sudo docker volume inspect iilab-aula05_historico
ip -br address
```

Se nomes divergirem, identifique os corretos; não crie ou substitua volume/rede. Verifique que UID 10001 consegue ler o banco e os arquivos WAL/SHM no volume e que o historiador está saudável; permissões e acesso concorrente real ainda precisam ser testados. Não altere permissões ou banco sem análise. Confirme o IP Ethernet do Pi 4, o estado do firewall e que `iilab-aula06-api` não existe:

```bash
sudo docker container inspect iilab-aula06-api
```

## 4. Iniciar apenas API

Somente depois das verificações, substitua os valores pelos efetivamente confirmados; os nomes abaixo são exemplos históricos. O comando cria apenas a API; não recria os serviços anteriores nem cria um novo volume. Se a rede ou volume não existirem, **pare** antes de executar, pois Docker pode criá-los ou falhar dependendo da opção.

```bash
PI4_IP='IP_ETHERNET_CONFIRMADO'
REDE='REDE_CONFIRMADA'
VOLUME='VOLUME_CONFIRMADO'
sudo docker network inspect "$REDE" >/dev/null && sudo docker volume inspect "$VOLUME" >/dev/null && \
sudo docker run -d --pull never --name iilab-aula06-api --init --restart unless-stopped \
  --network "$REDE" -p "$PI4_IP:8000:8000/tcp" \
  --mount "type=volume,src=$VOLUME,dst=/data,readonly,volume-nocopy" \
  --mount type=bind,src=/home/devadmin/iilab-aula06/api,dst=/opt/api,readonly \
  -e BANCO_HISTORICO=/data/historico_aula05.sqlite3 iilab-aula06-api:0.1
sudo docker logs iilab-aula06-api
```

Do notebook, usando o IP confirmado, teste a conexão autorizada; `/health` não testa SQLite:

```powershell
Test-NetConnection IP_ETHERNET_CONFIRMADO -Port 8000
Invoke-RestMethod http://IP_ETHERNET_CONFIRMADO:8000/health
```

Abra `http://IP_ETHERNET_CONFIRMADO:8000/docs` e `/openapi.json` no navegador. Uma falha pode indicar bind, serviço, rota ou firewall; não altere rede ou firewall automaticamente. Para editar ao vivo, use sessão SSH autorizada ou sincronize apenas `api/main.py` com o diretório confirmado; preserve uma cópia antes de sobrescrever. Depois reinicie apenas a API:

```bash
sudo docker restart iilab-aula06-api
sudo docker logs --tail 100 iilab-aula06-api
```

Valide novamente HTTP. Os endpoints de dados e a demonstração de firewall foram relatados como concluídos na gravação; a validação futura do estado atual e qualquer mudança exigem autorização específica.

Para sincronizar uma edição futura a partir do notebook, após confirmar que o destino é a cópia editável conhecida e preservar sua versão anterior, execute no PowerShell:

```powershell
scp -o ProxyJump=USUARIO_PI3@IP_PI3 C:\dev\lab-ii\aulas\aula-06\api\main.py USUARIO_PI4@IP_PI4:/home/devadmin/iilab-aula06/api/main.py
```

O comando sobrescreve `main.py` no destino; depois reinicie apenas a API conforme acima. Alternativamente, edite o arquivo no Pi pela sessão SSH autorizada.

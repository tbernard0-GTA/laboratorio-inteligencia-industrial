> **Escopo editorial atualizado em 29/10/2026:** o vídeo principal cobre Docker/Compose e TEP+OPC. Os testes de Streamlit abaixo pertencem ao material preparado para o complemento. As evidências de 28/10 são preservadas como histórico da preparação, não como execução observada no Raspberry. A pasta atual é `aulas/aula-03`; caminhos antigos em logs históricos identificam a execução original.

# Validação — 28/10/2026

## Resultado e alcance

Preparação executada **exclusivamente em cloud Linux x86_64**, Python **3.12.14**. Não houve acesso ao notebook do usuário, Pi 3 ou Pi 4. Nenhuma regra, interface, rota ou serviço desses equipamentos foi alterado.

| Verificação | Resultado | O que demonstra |
|---|---|---|
| Instalação do TEP no commit fixado | PASSOU | Wheel compilada x86_64; pacote TEP2.5.0 |
| NumPy2.2.6, asyncua2.1.0, Streamlit1.50.0 | PASSOU | Dependências instaladas na venv cloud |
| `pip check` | PASSOU | Sem requisitos quebrados no ambiente testado |
| `compileall` | PASSOU | Sintaxe dos scripts Python |
| Pytest | **11 passaram** | Contrato, falhas, reconexão e UI descritos abaixo |
| TEP real + servidor OPC + cliente TCP | **PASSOU** | Três tags Good, unidades, valores e timestamps avançando |
| Streamlit HTTP `/_stcore/health` | PASSOU,200ok | Serviço web inicia; não prova conexão OPC por si só |
| CLI Compose v5.6.1, `config --quiet` | PASSOU | Interpolação `.env.example`, modeloCompose válido |
| Resolução/download wheels Python3.12ARM64 | PASSOU | Deps binárias de NumPy,asyncua,Streamlit disponíveis; não execuçãoARM |
| Build Docker e Compose `up` | **NÃO EXECUTADOS** | Não há Docker Engine/daemon no ambiente cloud |
| TEP compilado/executado ARM64 | **NÃO EXECUTADO** | Requer build e teste no destino/prebuildARM autorizado |
| UAExpert, browserWindows e firewallPi3 | **NÃO EXECUTADOS** | Etapas do preflight/gravação |
| Reinício físico/persistência das redes | **NÃO EXECUTADOS** | Não inferir persistência de runtime |

A CLI Compose foi obtida do repositório oficial Docker (`https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64`) apenas na nuvem para validar o arquivo; nenhuma instalação no laboratório. Ter CLI não significa ter daemon. Não apresentamos a validação de configuração como build ou execução de containers.

Tentativa adicional de usar Python3.13 do sistema cloud encontrou ausência dos headers de desenvolvimento (`Python dependency not found` no Meson). Não alteramos o sistema nem contornamos a falha com mock. Escolhemos **Python3.12 no container**, runtime efetivamente testado, independente do Python3.13 do host Raspberry. A imagem oficial é multi-arquitetura; isso não substitui testeARM.

## O que os 11 testes cobrem

- Descoberta via URI de namespace com índice alterado, sem NodeIds fixos.
- Leitura real do protocolo em servidor de teste explicitamente simulado.
- Rejeição de valorNaN, timestampantigo e qualidadeBadSensorFailure.
- Recuperação quando o servidor está inicialmente indisponível.
- Desconexão e reconexão após parar e reiniciar o servidorOPC de teste.
- Cliente mantém conexão pelo endereço interno mesmo com endpoint externo anunciado.
- UI normal exibe três métricas e tendências; UI em falha não apresenta dados antigos como atuais.
- Contrato estruturalCompose, bindespecífico, healthchecks, ausênciahostnetwork/privileged e política de restart.
- Aula1 não foi refatorada retroativamente.

**Os valores de fixture não são dados do TEP.** O smoke separado usa `TEPSimulator` real e o servidor desta aula, via subprocesso e TCP local. Ele recusa porta4840 ocupada e verifica que o subprocesso segue ativo. A leitura real observada inclui Pressao≈2705.28kPa(g), Nivel≈75.16% e Temperatura≈120.39C; esses números são evidência de uma execução, não referências operacionais nem limites de alarme.

## Reproduzir em ambiente de desenvolvimento separado

Na pasta da aula, crie ambiente isolado:

```bash
python3 -m venv .venv-test
source .venv-test/bin/activate
python -m pip install -r docker/requirements-server.txt -r streamlit/requirements.txt -r testes/requirements-test.txt
python -m pip check
python -m compileall -q servidor_opc.py streamlit testes
python -m pytest testes/ -q
python testes/smoke_real.py
```

O smoke requer porta4840 **livre**; não o rode contra o sistema operacional da aula. A venv-test está excluída do Git e do contextoDocker. Para apenas testes com servidor simulado, TEP não é necessário; instale `streamlit/requirements.txt` e `testes/requirements-test.txt`. Compilar TEP exige ferramentas de desenvolvimento e headers da versãoPython usada.

Com ComposeCLI disponível, validar sem daemon:

```bash
docker compose --env-file .env.example -f docker/compose.yaml config --quiet
```

Na preparação real, copiar `.env.example` para `.env`, conferir IPs, depois build/up e smoke interno conforme README. Não usar os comandos de testecloud como evidência de que o Raspberry já foi preparado.

## Gates antes da gravação

1. Conferir versõesDocker/Compose, arquiteturaARM64, espaço livre real e plano de obtenção de imagens sem abrir egress indiscriminado.
2. Construir/carregar imagensARM64 e executarCompose no Pi4, com porta4840 liberada do processo manual anterior.
3. Validar healthchecks e leituraOPC interna; confirmar UI não fica conectada com timestamps parados.
4. Ler tags noUAExpert pelo endereçoOT e conferir browser após liberação estreita8501 noPi3.
5. Conferir nova tentativaSSHdireta bloqueada, saltoadministrativo preservado, contadores/capturas e rollback.
6. Testar `docker compose ... restart tep-opc` e recuperação do dashboard no runtime real; não confundir com teste de reconexãoPython.
7. Persistência após boot é um gate separado, com acesso físico e janela segura.

## Evidências retidas

Arquivos em [evidencias/](evidencias/): saídaPytest, smokeTEPreal, pipcheck, versãoCompose, healthHTTP e lista das dependências instaladas. `dependencias-cloud.txt` é registro do ambiente validado, **não um lock portátil ARM**. Logs de warnings de política sem criptografia são esperados nesta demonstração; não significam configuração segura para produção.

## Revisão de escopo em 29/10/2026

Pasta padronizada para `aulas/aula-03`, roteiro principal restrito a Docker/Compose e TEP+OPC. Streamlit preservado no profile opcional `complemento`. A suíte passou com **12 testes**. A CLI oficial Compose validou as duas configurações: o modo padrão seleciona apenas `tep-opc` e o profile seleciona também `streamlit`. Links relativos e `git diff --check` passaram; aulas 1 e 2 não foram alteradas. Veja [evidência da revisão](evidencias/revisao-20261029.txt). Build e execução Docker/ARM64 não foram realizados nesta revisão.

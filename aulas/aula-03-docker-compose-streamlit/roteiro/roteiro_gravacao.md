# Roteiro de gravação — Aula 3 (60 minutos)

## Objetivo e ritmo

**Do script manual a dois serviços reproduzíveis, mantendo a rede segregada.** Ao final: TEP+OPC integrado em um container, Streamlit em outro no Pi4, comunicação OPC interna e acesso HTTP8501 autorizado pontualmente pelo Pi3. Não é implantação industrial de produção.

Thiago conduz e interpreta; Sol entra somente quando chamada, entrega um comando pequeno e espera a saída. Os prompts são material de apoio, não um teleprompter para despejar código. Reserve instalação, downloads e primeiro build fora dos60min. Use [checklist](../CHECKLIST_GRAVACAO.md) e [prompts completos](../prompts/prompts_codex.md).

## Preparar os terminais

- **A — Windows PowerShell:** rota, SSH e testesTCP.
- **B — Pi3 SSH `admin@192.168.1.17`:** firewall e captura.
- **C — Pi4 por salto:** aplicação e Docker. `ssh -J admin@192.168.1.17 devadmin@10.77.0.10`.
- **D — Windows:** navegador e UAExpert.

Confirmar IPs antes. Clone/checkout e dependências já preparados, entre no diretório `aulas/aula-03-docker-compose-streamlit` do checkout real. Não confundir com a pasta antiga do servidor manual.

No Bash do **Pi4**, nesta pasta, defina atalho opcional:

```bash
dc() { docker compose --env-file .env -f docker/compose.yaml "$@"; }
```

Válido só nesta sessão/pasta. Se o usuário não tem acesso ao daemon, use `sudo docker compose` na função após revisão; não “corrija” permissões tornando o socket público.

## Sequência alinhada aos20 slides

| Relógio | Slide | Ação e fala-guia | Checkpoint / corte possível |
|---|---:|---|---|
|00–01|1|“Hoje vamos organizar a aplicação em containers e criar nossa primeira interface, sem desfazer a separação de redes.”|Promessa: funcionamento demonstrável, não produção pronta.|
|01–03|2|Recap aula1 TEP/OPC; aula2 gatewayPi3/OTPi4. Pedir à Sol uma síntese curta.|Mostrar topologia, não repetir instalações antigas.|
|03–05|3|Explicar dificuldade do terminal manual, ambiente e dependências.|Docker não elimina testes nem configura rede sozinho.|
|05–07|4|Imagem é receita empacotada; container é processo isolado usando kernel do host.|Não chamar de VM leve como equivalência exata.|
|07–10|5|Dockerfile, imagem, container, porta, rede e configuração.|Explicar bind0.0.0.0 dentro versus IP10.77.0.10 publicado.|
|10–12|6|Compose descreve dois serviços, rede, env e ciclo operacional.|TEP+OPC continuam juntos; Streamlit é cliente.|
|12–15|7|Desenhar Windows→Pi3→Pi4:8501; Streamlit→tep-opc:4840 interno.|Pi3 não recebe Docker; porta publicada≠regra de gateway.|
|15–17|8|Mostrar o caminho de execução: inventário→container→cliente→UI→rede→testes.|Sete prompts pequenos, uma evidência por etapa.|
|17–21|9|Preflight rápido: identificar host, rota/retorno, Docker, disco e regra atual.|Se errado, interromper antes de configurar. Não filmar atualização longa.|
|21–24|10|Prompt1, inventário; confirmar namespace, tags/unidades e processo integrado.|Mostrar trechos reais do repo e resposta do Codex.|
|24–27|11|Prompt2, plano; ler Dockerfile e `.env.example`.|Separar código, dependências, configuração e responsabilidade do host.|
|27–31|12|Prompt3, containerização; revisar diff e preservação do simulador.|Build pré-aquecido; edição pode cortar download, não esconder erro.|
|31–36|13|`dc config`, build, up, ps, logs, UAExpert.|Parar servidor manual identificado antes de ocupar4840.|
|36–40|14|Prompts4 e5: cliente pequeno, depois UI; mostrar browse por namespaceURI.|Não hardcode `ns=2`; falha vira erro, não zero falso.|
|40–43|15|Dashboard no Pi4, três tags, timestamps, tendência recente; prompt6 integração.|Se browserWindows bloqueado, mostrar saúde viaPi4; não abrir túnel como se fosse teste do firewall.|
|43–45|16|Provar serviço ativo e8501 bloqueada;4840 liberada;22 direto bloqueada.|FalhaTCP isolada não prova qual camada bloqueou.|
|45–50|17|Backup+inserção8501 estreita antes do drop; abrir página.|Consultar procedimento completo; handle obtido agora.|
|50–55|18|Contadores/captura; apagar exceção; nova conexão bloqueada; readicionar se desejado.|Sessão já estabelecida pode continuar, explicar sem alarmismo.|
|55–58|19|RestartTEP/OPC e reconexão; prompt7 documentação; plano de retorno.|Restart não preserva estado do simulador nem histórico efêmero.|
|58–60|20|2min síntese: limites, aprendizados e próximos passos.|Não prometer persistência de boot que não foi ensaiada.|

**Observação de duração:** os20 blocos totalizam60min. Se houver incidentes, corte esperas de instalação/build na edição ou reduza a revisão de código; não apresse a revisão das regras de rede.

## Comandos no momento certo

### Preflight (slide9, Pi4)

```bash
whoami
hostname
uname -m
ip -4 route get 192.168.1.16
df -h /
docker version
docker compose version
```

Esperado: Pi4ARM64, retorno viaPi3, espaço suficiente e daemon acessível. Imagens podem ocupar mais que o código. Não limpar armazenamento sem inventário.

### Configurar e subir (slides11–13, Pi4)

Criar `.env` somente se ainda não existir, sem sobrescrever configuração:

```bash
if [ ! -f .env ]; then cp .env.example .env; fi
cat .env
dc config
```

Não mostrar `cat .env` na gravação se contiver qualquer segredo. Verifique bind externo10.77.0.10, OPC interno `opc.tcp://tep-opc:4840/tep/`, duas publicações explícitas.

```bash
sudo ss -ltnp 'sport = :4840'
```

Se servidor manual estiver ativo, identificar o terminal/processo/serviço. Encerrar com Ctrl+C no terminal dono ou parar a unidade identificada. Não matar todos os Python. Manter código e ambiente anteriores para retorno.

```bash
dc build
dc up -d
dc ps
dc logs --tail=50
```

`build` pode requerer internet ausente naOT. Use preparação prévia ou imagensARM64 carregadas; não altere firewall para resolver download ao vivo. `up -d` libera terminal, mas não garante app saudável.

### Cliente e integração (slides14–15, Pi4)

```bash
dc exec streamlit python opc_client.py --endpoint opc.tcp://tep-opc:4840/tep/ --once
```

Comparar Pressao/Nivel/Temperatura e unidades com UAExpert; valores não precisam coincidir no mesmo milissegundo. Confirmar fonte/horário/status, não só número. Namespace descoberto porURI, browse de `Objects/Reator`; IDs gerados não são contrato estável.

```bash
curl --fail --max-time 5 http://10.77.0.10:8501/_stcore/health
```

SaúdeHTTP não garante conexãoOPC. Interface trabalha com histórico recente em memória, não historiador.

### Exceção de rede (slides16–18)

Seguir exatamente [rede/firewall_8501.md](../rede/firewall_8501.md). Não colocar o procedimento longo em uma linha no slide. Thiago lê estado; Sol ajuda interpretar:

> “O serviço já responde dentro do Pi4. Agora vamos permitir somente este notebook, para este destino, nesta porta, sem liberar SSH direto nem substituir as regras existentes.”

Windows:

```powershell
Test-NetConnection 10.77.0.10 -Port 8501
Test-NetConnection 10.77.0.10 -Port 22
```

Depois da exceção: abrir `http://10.77.0.10:8501`; confirmar dashboard. Depois de remover: testar uma NOVA conexão; manter acesso administrativo por salto. Se quiser terminar com a página acessível, aplicar novamente de forma consciente. Persistir é etapa posterior de revisão/boot controlado.

### Reinício e encerramento (slide19)

```bash
dc restart tep-opc
dc logs --tail=50 tep-opc
dc ps
```

Esperado a verificar: painel detecta indisponibilidade e reconecta; trajetória do simulador recomeça. Não prometer “zero perda”. Para observar ao vivo: `dc logs -f --tail=50`; Ctrl+C encerra visualização, não containers.

Para **parar o laboratório**, fora da demonstração se quiser mantê-lo acessível:

```bash
dc down
```

Sem `-v`, sem prune. Depois disso, para retornar ao servidor manual, conferir4840 livre e executar o comando original no ambiente anterior já preservado, com endpointOT válido. Não inventar unidade systemd.

## Falhas comuns e decisão de gravação

| Sintoma | Primeira checagem | Não fazer / saída honesta |
|---|---|---|
|Build não baixa imagem|Egress permitido? DNS? arquitetura?|Não abrir internet geral. Cortar espera, usar imagemARM64 preparada.|
|Port4840 em uso|`ss` + processo dono|Não parar todos containers nem `pkill python`.|
|Container sai|`dc logs`, versões/traceback|Não afirmar sucesso só porque imagem construiu.|
|UI abre mas dados não|Cliente `--once`, endpoint/DNS/namespace/status|Não trocar TEP por números mock silenciosos.|
|8501 continua bloqueada|Serviço local, rota, handle/ordem, IPfonte|Não adicionar accept geral.|
|8501 continua aberta após rollback|Conexão established ou outra regra|Nova conexão; conferir ruleset; não apagar conntrackglobal.|
|SSH direto funciona|Destino e origem corretos? conexão antiga? rota alternativa?|Não confundir salto com FORWARD; revisar antes de afirmar segurança.|
|Dashboard perde histórico|Reinício/rerun/estado em memória|Explicar limite; persistência/historiador é futura aula.|

## Fechamento sugerido

“Hoje organizamos a aplicação, conectamos uma interface aos dados OPC e controlamos o acesso entre as redes. O mais importante não foi só a tela funcionar: foi conseguir explicar o caminho, observar o tráfego, testar uma falha e voltar atrás. Este é um laboratório de aprendizagem; produção exige controles e validações adicionais.”

Se algo não passar, nomeie a etapa pendente. Não fechar dizendo “tudo validado” quando só rodou teste mock ou sintaxe na nuvem.

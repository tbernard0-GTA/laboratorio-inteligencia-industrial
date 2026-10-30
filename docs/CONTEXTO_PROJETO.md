# Contexto do projeto

## 2026-10-30 — Catálogo local da Aula 5

Foi preparado um catálogo local de 41 medições e 12 manipuladas da revisão TEP fixada, com leitura e testes de correspondência. A integração com o simulador foi testada localmente em imagem ARM64 sob emulação. A publicação dessas variáveis por OPC UA permanece futura; não houve alteração ou inspeção dos equipamentos nesta etapa. Detalhes em [aulas/aula-05](../aulas/aula-05/).

> Atualização de 29/10/2026: este documento preserva o histórico das etapas anteriores. A Aula 4 e seu estado comprovado ou pendente estão em [aulas/aula-04](../aulas/aula-04/) e nas entradas recentes do diário. Dados e planos históricos abaixo não comprovam o estado atual dos equipamentos.


## Incremento de coleta — 29/10/2026

Localmente foi preparado um serviço `coletor` OPC UA e SQLite em `aulas/aula-03`. O Compose local usa `tep-opc`; a correspondência com o serviço em execução no Pi ainda não foi inspecionada. Os testes locais usam servidor e amostras sintéticos; o deploy, a descoberta interna e a persistência de dados reais no Pi permanecem a validar. O usuário relatou servidor Docker validado pelo UAExpert e acesso SSH interativo; a tentativa não interativa desta sessão expirou. Streamlit e mudanças de rede não integram o incremento.

Na inspeção interativa relatada pelo usuário, o container saudável pertence ao serviço `tep-opc` e projeto `aula-03`, usando `/home/devadmin/iilab-aula03/aulas/aula-03/compose.yaml`. O Pi informou `aarch64`, 4,2 GB disponíveis e Compose 2.26.1-4; Docker requer sudo. A inspeção do conteúdo do Compose e da rede permanece pendente.

Memória técnica do Industrial Intelligence Lab, série educacional de automação industrial, redes, Python e inteligência artificial. O laboratório é desenvolvido em etapas, preservando as aulas anteriores. Este documento distingue evidências locais, informações relatadas e objetivos futuros; não comprova o estado atual dos equipamentos.

## CONFIRMADO — material presente na base local

- A base `main`, no commit `37f5a31`, contém os materiais das Aulas 1 e 2. A inspeção foi local, sem acesso aos Raspberry Pi.
- **Aula 1:** `aulas/aula-01/simular_tep.py` executa o Tennessee Eastman Process (TEP) com backend Python. `servidor_opc.py` integra uma simulação própria a um servidor OPC UA com `asyncua`, publicando `Pressao`, `Nivel` e `Temperatura` no objeto `Reator`. `requirements.txt` registra as dependências da aula. O README original descreve a validação das leituras com UAExpert.
- O servidor da Aula 1 usa TCP 4840, namespace `urn:laboratorio-industrial:tep` e política `NoSecurity`; seu endpoint fixado, `192.168.1.19`, é histórico e precisa ser conferido no ambiente real. A configuração descrita no README usa acesso anônimo e não possui criptografia; é limitada a rede de laboratório restrita.
- **Aula 2:** `aulas/aula-02/README.md` documenta a segmentação TI/TA, roteamento, firewall nftables, liberação de OPC UA e bloqueio de novas conexões SSH diretas do notebook ao Pi 4, com administração por salto no Pi 3. `aula02.nft` contém regras adaptáveis e `iilab-forward-video.nft` reconstitui regras exibidas na gravação. Os arquivos não comprovam as regras carregadas atualmente.
- O README da Aula 2 registra que a persistência das configurações após reinicialização não foi validada. O roteiro contém operações de rede que **não foram executadas nesta preparação**.
- A base original não contém Dockerfile, Compose, aplicação Streamlit ou diretório da Aula 3. A adaptação local do servidor foi acrescentada posteriormente em `aulas/aula-03/`.

## CONFIRMADO — contexto relatado para o laboratório

Segundo o contexto fornecido, o notebook Windows com PowerShell, Codex CLI, Git, navegador e UAExpert é o ambiente principal; o Pi 3 B+ conecta Wi-Fi da zona TI à Ethernet da zona TA e atua como gateway/firewall; o Pi 4 Linux ARM64 executa TEP e OPC UA. As Aulas 1 e 2 foram realizadas conforme descrito acima. Essas informações são o histórico relatado, não uma verificação atual dos dispositivos.

Em 28/10/2026, o usuário confirmou para o Pi 4: arquitetura `aarch64`, Docker 26.1.5, Docker Compose 2.26.1, aproximadamente 4,8 GB livres, porta TCP 4840 livre e acesso externo restrito. O usuário SSH não tem acesso direto ao daemon Docker; a administração será supervisionada. Estes dados foram informados pelo usuário, sem inspeção remota nesta sessão; a disponibilidade de imagens e dependências e o comportamento real de rede ainda não foram testados.

O notebook consome OPC UA do Pi 4 através do Pi 3; para administração, conecta-se ao Pi 4 por SSH com o Pi 3 como jump host. A documentação detalhada está em [ARQUITETURA.md](ARQUITETURA.md) e [ACESSOS_E_SEGURANCA.md](ACESSOS_E_SEGURANCA.md).

## AULA 3 — adaptação local e próximos passos

Foi criada uma adaptação local do servidor em `aulas/aula-03/servidor_opc.py`, com configuração independente de escuta e endpoint base. A configuração foi testada localmente sem as dependências da aplicação; inicialização e descoberta OPC UA ainda precisam ser validadas. A biblioteca pode reescrever o endpoint na descoberta. Veja `aulas/aula-03/README.md`.

Foram preparados Dockerfile e Compose para o serviço TEP/OPC UA, com rede bridge e porta publicada no IP informado. O Compose foi expandido localmente, mas a imagem ainda não foi construída nem executada. Continuam planejados: validar a execução no Pi 4, criar cliente OPC UA e interface Streamlit, e validar comunicação, acesso segmentado, segurança e operação. A porta TCP 8501 é prevista para a interface, sujeita à validação e às decisões futuras. As dez etapas e seus critérios estão em [PLANO_AULA_03.md](PLANO_AULA_03.md).

Existe uma branch remota antecipada, `feat/aula-03-docker-compose-streamlit`, mencionada como referência futura. Ela não foi usada como base, copiada ou mesclada nesta preparação.

## A VALIDAR antes de operações reais

- Endereços, máscaras, interfaces, rotas, usuários e acesso por salto. Referências históricas: notebook `192.168.1.16`, Wi-Fi do Pi 3 `192.168.1.17`, Ethernet do Pi 3 `10.77.0.1` e Ethernet do Pi 4 `10.77.0.10`. O endereço `192.168.1.19` fixado no código da Aula 1 é outro exemplo histórico, não uma confirmação do endereço atual.
- Estado dos serviços TEP/OPC UA, endpoint efetivo, variáveis, qualidade das leituras, versão do sistema e dependências no Pi 4.
- Encaminhamento, regras nftables efetivamente carregadas, outras cadeias e persistência após reinicialização no Pi 3; conectividade e bloqueio SSH devem ser verificados sem presumir que o arquivo local foi aplicado.
- Disponibilidade de imagens e dependências para ARM64 e seu fornecimento em rede restrita; compatibilidade da imagem, estratégia de acesso à porta 8501, exposição do serviço e critérios de segurança antes de qualquer mudança.
- Identificar serviços existentes e preservar um caminho de administração e recuperação antes de qualquer alteração autorizada.

Registre evidências, decisões e pendências de cada sessão em [DIARIO_DE_BORDO.md](DIARIO_DE_BORDO.md).

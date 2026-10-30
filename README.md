# Industrial Intelligence Lab

Laboratório de inteligência industrial construído passo a passo, com Raspberry Pi, Python e apoio de IA no desenvolvimento. A proposta da série é acompanhar o caminho do dado: **processo simulado → comunicação industrial → coleta → histórico e contexto → visualização → análise e diagnóstico**.

Este repositório reúne as aulas do laboratório. É o início do projeto: a ideia é desenvolver um pouco a cada dia, compartilhar os comandos e as decisões e ampliar o laboratório de forma incremental.

## Aulas

- **Aula 01:** Do zero ao OPC UA com TEP — instruções nesta página e [códigos](aulas/aula-01/).
- **Aula 02:** [Segmentação de redes e controle de acesso com Raspberry Pi e nftables](aulas/aula-02/).
- **Aula 03:** [Docker e Docker Compose para TEP e OPC UA](aulas/aula-03/) — comandos, código e roteiro; Streamlit separado como complemento.

## Aula 01 — Do zero ao OPC UA com TEP

Nesta primeira aula, executamos o Tennessee Eastman Process (TEP) no Raspberry Pi com o backend Python e publicamos três medidas do reator por OPC UA. Em outro computador, o UAExpert permite conferir as leituras.

O resultado desta etapa é uma simulação com leitura remota de **pressão, nível e temperatura**. Coleta persistente, banco de dados, telas e análises fazem parte das próximas etapas.

Os dois scripts foram copiados do Raspberry Pi e preservados como utilizados na aula. O endereço de rede em `servidor_opc.py` é um exemplo do ambiente original e precisa ser ajustado para cada instalação.

```text
laboratorio-inteligencia-industrial/
├── README.md
└── aulas/
    ├── aula-01/
    │   ├── requirements.txt
    │   ├── simular_tep.py     # Simulação e leituras no terminal
    │   └── servidor_opc.py    # Simulação integrada ao servidor OPC UA
    ├── aula-02/
    │   ├── README.md          # Redes, roteamento e firewall
    │   ├── aula02.nft         # Regras adaptáveis do laboratório
    │   └── iilab-forward-video.nft # Reconstituição das regras exibidas
    └── aula-03/
        ├── README.md          # Docker/Compose para TEP + OPC UA
        ├── servidor_opc.py
        ├── docker/            # Dockerfile e Compose
        └── COMPLEMENTO_STREAMLIT.md # Continuação separada do vídeo
```

## Preparar o Raspberry Pi

Ambiente de referência da aula: Raspberry Pi 4 com 8 GB de RAM, Debian 13 ARM64 e Python 3.13.5. O UAExpert é executado em outro computador na mesma rede de laboratório.

No terminal do computador, conecte por SSH usando o usuário e o IP do seu Raspberry:

```bash
ssh SEU_USUARIO@IP_DO_RASPBERRY
```

Os comandos seguintes são executados **no Raspberry Pi**. Primeiro, prepare os pacotes do sistema:

```bash
sudo apt update
sudo apt install git build-essential python3-dev python3-venv pkg-config
```

Clone o repositório e crie um ambiente virtual para esta aula:

```bash
git clone https://github.com/tbernard0-GTA/laboratorio-inteligencia-industrial.git
cd laboratorio-inteligencia-industrial/aulas/aula-01
python3 -m venv .venv
source .venv/bin/activate
```

Instale primeiro o NumPy com um pacote pré-compilado. Depois, instale as dependências da aula. A revisão fixada do TEP já desativa a compilação Fortran por padrão; os scripts selecionam o backend Python:

```bash
python -m pip install --only-binary=:all: "numpy==2.2.6"
python -m pip install -r requirements.txt
python -m pip check
```

O TEP é instalado a partir de uma revisão fixada do [projeto de origem](https://github.com/jkitchin/tennessee-eastman-profbraatz/tree/9a6c8e5fcef4a2850778704e7793c87b0a187005). O arquivo `requirements.txt` registra essa revisão e as versões confirmadas no Raspberry: **TEP 2.5.0, NumPy 2.2.6 e asyncua 2.1.0**. As dependências transitivas são resolvidas pelo pip. Se a instalação falhar, resolva o erro antes de executar os scripts; a mensagem `Python dependency not found`, por exemplo, exige conferir a instalação de `python3-dev`.

## 1. Conferir a simulação no terminal

Com a `.venv` ativa e dentro de `aulas/aula-01`, execute:

```bash
python simular_tep.py
```

O script inicializa o TEP com backend Python e semente `1234`. A cada ciclo, avança um passo do modelo e mostra o horário UTC, o tempo do modelo e as três medidas. Use **Ctrl+C** para encerrar antes de seguir.

## 2. Executar o servidor OPC UA

Edite `servidor_opc.py` e substitua o IP na linha `ENDPOINT` pelo IP do seu Raspberry. O arquivo original contém:

```python
ENDPOINT = "opc.tcp://192.168.1.19:4840/tep/"
```

Depois, execute e mantenha o terminal aberto:

```bash
python servidor_opc.py
```

**Este script já executa sua própria simulação.** Não é necessário manter `simular_tep.py` rodando em paralelo. Cada script inicia uma instância independente do modelo.

O servidor usa o namespace `urn:laboratorio-industrial:tep` e cria as variáveis em `Objects → Reator`:

| Variável | Medida do TEP no código | Propriedade `Unidade` |
| --- | --- | --- |
| `Pressao` | `medidas[6]` | `kPa(g)` |
| `Nivel` | `medidas[7]` | `%` |
| `Temperatura` | `medidas[8]` | `C` |

As variáveis são disponibilizadas para leitura, sem habilitar escrita pelo cliente. Cada atualização recebe um `SourceTimestamp` com o horário UTC do Raspberry.

## 3. Conferir no UAExpert

Com o servidor em execução, no computador cliente:

1. Abra **Server → Add** e adicione o endereço configurado em `ENDPOINT`.
2. Selecione **Security Policy: None**, **Message Security: None** e autenticação **Anonymous**.
3. Conecte e expanda **Objects → Reator** no painel **Address Space**.
4. Arraste `Pressao`, `Nivel` e `Temperatura` para **Data Access View**.
5. Confira valores presentes, `StatusCode = Good` e `SourceTimestamp` avançando. Expanda cada variável para consultar a propriedade personalizada `Unidade`.

As variações podem ser pequenas porque o processo inicia próximo de um regime estável. O cliente precisa alcançar o IP do Raspberry e a porta TCP `4840` na rede do laboratório.

Na conferência de 27/10/2026, os scripts originais foram executados no Raspberry e um cliente OPC UA confirmou as três unidades, valores finitos, qualidade `Good` e avanço dos valores e de `SourceTimestamp` entre duas leituras. Os arquivos publicados conferem com os originais por SHA-256.

## Tempo de execução e limites desta etapa

Os scripts tentam executar um ciclo por segundo de relógio. Na revisão e configuração utilizadas, cada passo do modelo avança **um segundo simulado**, conferido no Raspberry. O tempo do modelo e o horário UTC continuam sendo referências distintas: atrasos no cálculo ou no sistema operacional podem afastá-los, sem garantia de tempo real.

Esta aula trabalha com dados simulados. Na aula 1 não há coletor independente, armazenamento histórico, banco de contexto, dashboard ou diagnóstico. A [aula 3](aulas/aula-03/) organiza TEP e OPC UA em container com Docker Compose. A interface Streamlit fica para um vídeo complementar; armazenamento persistente e diagnóstico continuam fora de escopo.

**Use o servidor somente em uma rede de laboratório restrita:** esta configuração permite acesso anônimo e não usa criptografia. Não exponha a porta `4840` à internet nem utilize esta configuração diretamente em produção.

## Próximas etapas da série

O laboratório será ampliado conforme cada etapa for desenvolvida e conferida:

- Coleta dos sinais OPC UA com Python.
- Armazenamento e consulta de séries temporais.
- Contextualização dos dados de processo.
- Telas de processo e visualização dos históricos.
- Exploração de dados, diagnóstico e aplicações de ciência de dados.

As próximas aulas serão adicionadas em novas pastas dentro de `aulas/`, preservando o material de cada etapa.

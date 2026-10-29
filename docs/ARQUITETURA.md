# Arquitetura do laboratório

> Atualização de 29/10/2026: este documento preserva o histórico das etapas anteriores. A Aula 4 e seu estado comprovado ou pendente estão em [aulas/aula-04](../aulas/aula-04/) e nas entradas recentes do diário. Dados e planos históricos abaixo não comprovam o estado atual dos equipamentos.


Em 29/10/2026 foi preparado localmente um coletor separado na rede Compose `iilab`, que consulta `tep-opc:4840` e grava SQLite em volume Docker persistente. Esta topologia ainda precisa ser confrontada com o Compose e rede efetivos no Pi 4; a interface Streamlit permanece planejada.

Este documento descreve a topologia registrada nas aulas e a direção pretendida para a Aula 3. A presença dos arquivos no repositório e o histórico da aula não comprovam o estado atual dos dispositivos. **Todos os endereços, interfaces, rotas, regras e serviços precisam ser verificados antes de qualquer operação real.**

## Topologia de referência das Aulas 1 e 2

```text
Zona TI                                  Zona TA
Notebook Windows                         Raspberry Pi 4 (Linux ARM64)
192.168.1.16                             10.77.0.10 (Ethernet)
 PowerShell, Git, Codex CLI,              TEP + servidor OPC UA :4840
 navegador e UAExpert                           ^
      |                                        | Ethernet
      | Wi-Fi                            10.77.0.1
      +------ 192.168.1.17 (Wi-Fi) ---- Raspberry Pi 3 B+
                                         gateway / nftables
```

Os IPs são **referências históricas**, não valores garantidos. O roteiro da [Aula 2](../aulas/aula-02/README.md) descreve redes distintas, encaminhamento e regras adaptáveis no Pi 3. A persistência de rotas, encaminhamento e firewall após reinicialização não foi validada naquela aula. O código original da Aula 1 usa `192.168.1.19` em seu endpoint; a Aula 2 mostra um endpoint Ethernet diferente. Ambos são exemplos a verificar, não uma confirmação da configuração atual.

## Fluxos documentados

- **Processo e dados:** o simulador TEP e o servidor OPC UA da Aula 1 estão integrados no Pi 4; o servidor publica pressão, nível e temperatura. O UAExpert no notebook é o cliente de validação descrito.
- **OPC UA:** notebook na zona TI → Pi 3 → Pi 4 na zona TA, TCP **4840**, sujeito a rotas, serviço e regras efetivas. O servidor de exemplo usa política sem segurança; a segmentação não substitui autenticação e criptografia.
- **Administração:** notebook → SSH no Pi 3 → SSH no Pi 4, com o Pi 3 como jump host. A regra exemplificada na Aula 2 bloqueia novas conexões SSH diretas do notebook ao Pi 4; a situação atual deve ser verificada. O salto envolve duas conexões, não o mesmo fluxo encaminhado de SSH direto.
- **Supervisão web futura:** notebook → Pi 3 → interface no Pi 4, TCP **8501 previsto**. Porta, exposição, origem permitida e regras dependem de projeto e validação posteriores; não se presume que o tráfego esteja liberado.

## Arquitetura pretendida para a Aula 3 — planejada

```text
Notebook (navegador) -- TCP 8501 previsto --> Pi 3 --> Pi 4
                                                        Docker Compose
                                                        ├─ TEP / OPC UA :4840
                                                        └─ cliente OPC UA / Streamlit
```

Essa é uma visão conceitual, não uma implementação existente. A divisão de serviços, a comunicação entre containers, os endpoints, a publicação de portas, a compatibilidade ARM64 e o controle de acesso ainda serão definidos e testados. A interface deverá visualizar as mesmas variáveis OPC UA, respeitando a segmentação. Consulte [PLANO_AULA_03.md](PLANO_AULA_03.md) antes de iniciar qualquer etapa futura.

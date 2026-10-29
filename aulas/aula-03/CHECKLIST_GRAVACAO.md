# Checklist — Aula 3 principal

Use junto com o [README](README.md). Este checklist cobre **Docker/Compose + TEP/OPC**. Streamlit e TCP 8501 ficam no [complemento](COMPLEMENTO_STREAMLIT.md).

## Preparação

- [ ] Pi 3 com fonte adequada e Ethernet conectada ao Pi 4.
- [ ] Identificar IP atual do notebook; o exemplo de 29/10 é `192.168.1.14`, não `.16`.
- [ ] Rota do notebook para `10.77.0.0/24` via Pi 3 e caminho de retorno confirmados.
- [ ] Regras do Pi 3 presentes antes de habilitar encaminhamento; origem, destino e portas corretos.
- [ ] SSH com salto funcionando e acesso local disponível para recuperação.
- [ ] Confirmar Docker/Compose, ARM64, armazenamento e permissões no Pi 4.
- [ ] Código desta branch obtido sem sobrescrever mudanças locais.
- [ ] Imagens ARM64 e dependências preparadas, considerando egress restrito da rede OT.
- [ ] `.env` revisado, IP Ethernet existente e nenhum segredo em commit ou na gravação.
- [ ] Servidor manual e modo de retorno identificados; preservar script e ambiente.

## Execução e evidência

- [ ] `docker compose ... config` válido.
- [ ] Build do serviço `tep-opc` concluído no ambiente usado.
- [ ] Porta 4840 livre após parar somente o processo manual identificado.
- [ ] `up -d tep-opc`, `ps` e logs conferidos.
- [ ] Leitura OPC local funciona.
- [ ] UAExpert remoto mostra três tags, unidades, `Good` e timestamps avançando.
- [ ] Comunicação passa pela rede pretendida; não usar Tailscale ou Wi-Fi alternativo sem perceber.
- [ ] Comandos de logs, restart e parada compreendidos; não apagar volumes ou outros projetos.
- [ ] Streamlit não é exigido e a porta 8501 não precisa ser liberada nesta parte.

## Limites a registrar

- [ ] Separar testes de sintaxe, Python em cloud, Docker local e ARM64 físico.
- [ ] Registrar a persistência de regras, forwarding e rota como verificada ou pendente. `is-enabled nftables` sozinho não valida o conteúdo restaurado após reboot.
- [ ] Explicar que restart do modelo perde sua trajetória e que não existe historiador nesta etapa.
- [ ] Identificar slides de planejamento mais amplo como apoio, não como prova de etapas realizadas.
- [ ] Sol entra apenas no gancho; comandos curtos e uma saída verificada por vez.

# Checklist operacional — Aula 5

Este checklist é para uma **nova apresentação autorizada**; não é uma afirmação do estado atual dos equipamentos. A gravação relatada está resumida no [README](README.md#gravação-concluída--evidências-e-material).

- [ ] Confirmar o IP do notebook, a identidade dos Pi, SSH via salto e as regras de rede vigentes sem alterá-las.
- [ ] Conferir relógio UTC/sincronização e espaço no Pi; sincronização antes da gravação foi relatada, persistência após reboot não foi testada.
- [ ] Inspecionar os contêineres, imagem, portas e volumes antes de qualquer operação; não presumir que todos estão parados.
- [ ] Confirmar backup SQLite consistente com WAL e teste de restauração em cópia; não substituir banco ou volume.
- [ ] Comparar os hashes do pacote que será utilizado e verificar o ID da imagem; não sobrescrever arquivos ou imagens desconhecidos.
- [ ] Obter autorização específica antes de qualquer parada, subida ou rollback; conferir impacto sobre a Aula 4 e porta 4840.
- [ ] Após uma eventual subida autorizada, verificar healthchecks, contagens em momentos distintos, tags observadas e consultas; distinguir valor, qualidade e timestamp.
- [ ] Conferir auditoria de ciclos com a contagem total; banco vazio ou ausência de ciclos incompletos não prova continuidade nem qualidade perfeita.
- [ ] Preservar bancos, WAL e volumes. `docker compose down -v` e operações de limpeza podem apagar histórico; não usá-los como rotina.

Comandos e limitações: [operação](OPERACAO_GRAVACAO.md), [riscos](preflight/RISCOS.md) e [consultas](GUIA_ESTUDO_CODIGO_AULA_05.md#6-sql-explicado-progressivamente).

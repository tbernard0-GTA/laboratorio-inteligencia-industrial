# Checklist — Aula 6, incremento 01

## Estado no fechamento

- [x] `/health`, catálogo e histórico implementados; testes locais com SQLite temporário.
- [x] `/health` e 53 tags confirmados por HTTP no Pi em sessão anterior.
- [ ] Confirmar a versão do histórico no Pi e comparar respostas com o banco ativo.
- [ ] Validar acesso concorrente ao WAL no ambiente real, backup/restauração e persistência após reboot.
- [ ] Confirmar qualquer alteração de firewall e executar futuras demonstrações somente quando autorizadas.

## Checklist histórico da preparação inicial

- [x] API inicial: `/health`, `/docs`, `/openapi.json`; sem endpoints SQL.
- [x] Compose complementar e código editável preparados.
- [x] Leitura prevista com funções e SQL da Aula 5, banco e WAL preservados.
- [ ] Verificar no Pi identidades, recursos, imagem, rede, volume, permissões do banco/WAL, IP e porta.
- [ ] Transferir e validar o tar e iniciar apenas API, em incremento autorizado.
- [ ] Testar acesso HTTP a partir do notebook e leitura concorrente do banco real.
- [ ] Desenvolver endpoints, clientes e demonstração de firewall em etapas autorizadas.

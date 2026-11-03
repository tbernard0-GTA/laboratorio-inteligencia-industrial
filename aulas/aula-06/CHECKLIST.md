# Checklist — Aula 6

## Concluído conforme relato da gravação

- [x] Imagem ARM64 original transferida e carregada no Pi 4; API independente e código editável montado.
- [x] `/health`, Swagger, 53 tags e histórico SQLite real, incluindo `XMEAS(9)`.
- [x] OPC UA externo antes da restrição; novas conexões externas bloqueadas depois, com HTTP e coleta interna preservados.
- [x] Serviços da Aula 5, rede Docker e volume histórico reutilizados conforme relato do usuário.

Esses itens são relatos do usuário, não inspeção independente nesta revisão.

## Confirmado localmente

- [x] Código da API reutiliza consultas da Aula 5 em conexão somente leitura; testes com bancos temporários.
- [x] Imagem ARM64 consolidada 1.0 preparada com os endpoints; veja roteiro para os resultados e hash.
- [x] Exemplos Python requests e coleção Postman preparados; uso na gravação não comprovado.

## Ainda a validar

- [ ] Persistência das regras e dos serviços após reboot.
- [ ] Integridade de backup e restauração em cópia.
- [ ] Autenticação, HTTPS/TLS e segurança adequados ao ambiente de produção.
- [ ] Estado atual efetivo dos equipamentos, regras, permissões de WAL/SHM e recuperação.

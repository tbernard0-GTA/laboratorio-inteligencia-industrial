# Checklist de gravação e reprodução

- [ ] Confirmar endereços, rota, relógio UTC, acesso por salto e caminho de recuperação.
- [ ] Inventariar serviços, arquivo Compose, nome do projeto, imagens e volume efetivos; preservar dados e configurações existentes.
- [ ] Verificar dependências, arquitetura, espaço e acesso necessário ao build.
- [ ] Confirmar servidor OPC UA e as três variáveis no UAExpert, com qualidade e timestamps.
- [ ] Conferir logs e últimas linhas reais do SQLite; repetir a contagem após alguns ciclos.
- [ ] Reiniciar somente o coletor e comprovar que dados anteriores permanecem e novas leituras são acrescentadas.
- [ ] Conferir o healthcheck HTTP local do Streamlit e comparar dados do painel com banco e UAExpert.
- [ ] Conferir acesso do notebook e regra específica de firewall, sem presumir persistência após reboot.
- [ ] Registrar pendências e evidências observadas; não publicar segredos ou o banco de dados.

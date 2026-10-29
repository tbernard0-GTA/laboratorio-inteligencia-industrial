# Instruções para o Codex

O Industrial Intelligence Lab é uma série educacional de automação industrial, redes, Python e inteligência artificial. Desenvolva o laboratório em etapas pequenas e verificáveis, preservando o material e o funcionamento das Aulas 1 e 2. Não antecipe etapas sem solicitação.

## Início de cada sessão

1. Leia `README.md`, `docs/CONTEXTO_PROJETO.md`, `docs/ARQUITETURA.md`, `docs/ACESSOS_E_SEGURANCA.md`, `docs/PLANO_AULA_03.md` e as entradas recentes de `docs/DIARIO_DE_BORDO.md`.
2. Inspecione o estado local do Git e as alterações existentes antes de trabalhar. Preserve alterações do usuário e confira se as informações ainda são válidas.
3. Identifique o objetivo e os limites da etapa solicitada. Registre incertezas e não apresente planos como fatos implementados.

## Arquitetura e acesso

O notebook Windows fica na zona TI; o Raspberry Pi 3 B+ é o gateway e firewall entre TI e TA; o Raspberry Pi 4 hospeda o TEP e o servidor OPC UA na zona TA. A Aula 3 prevê Docker Compose e Streamlit no Pi 4. A topologia, os serviços e os endereços históricos devem ser verificados antes de operações reais.

Administre o Pi 4 por SSH usando o Pi 3 como jump host, após verificar endereços, identidades, autenticação e acesso. Não acesse os equipamentos sem que a tarefa autorize; mantenha um caminho de recuperação adequado. Não armazene senhas, tokens ou chaves privadas no repositório.

Não altere firewall, roteamento, interfaces ou outras configurações de rede sem solicitação explícita. Analise o impacto antes de interromper ou alterar qualquer serviço existente. Nunca aplique automaticamente exemplos de regras ou comandos de configuração.

## Trabalho e documentação

- Inspecione e preserve as aulas anteriores, sua documentação e as mudanças existentes antes de modificar qualquer coisa.
- Planeje e execute somente a etapa autorizada. Valide cada etapa com verificações proporcionais, registre os resultados observados e pare diante de falhas ou incertezas relevantes.
- Atualize `docs/DIARIO_DE_BORDO.md` ao concluir trabalho: data, etapa, alterações, testes e resultados, problemas, decisões e próxima ação. Atualize também os documentos de contexto afetados, distinguindo confirmado, planejado e a validar.
- Não faça deploy, mudanças remotas ou operações destrutivas fora do escopo solicitado.

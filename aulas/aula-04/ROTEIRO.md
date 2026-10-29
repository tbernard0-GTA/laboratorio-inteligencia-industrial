# Roteiro da Aula 4

1. Retomar o caminho dos sinais: TEP → servidor OPC UA → coletor → SQLite → Streamlit. Apresentar Pi 3 como gateway/firewall e Pi 4 como host dos serviços.
2. Explicar o serviço `coletor`, resolução do namespace, sinais e unidades. Mostrar logs e reconexão; consultar as últimas amostras e comparar contagens e timestamps em dois momentos.
3. Explicar o volume persistente, WAL e o que significa uma linha por sinal. Reiniciar apenas o coletor e comparar as contagens, preservando o volume.
4. Mostrar a interface lendo o banco em modo somente leitura: qualidade, hora da origem, hora da coleta, estados de erro e desatualização, e janela de histórico.
5. Validar HTTP no Pi 4, depois o acesso pelo notebook apenas com regra autorizada. Comparar as leituras com o UAExpert e o banco; healthcheck HTTP sozinho não valida dados.

## Evidências e limites conhecidos

No histórico da preparação, o usuário relatou servidor e coletor ativos e informou consultas com contagens crescentes para os três sinais. O diário registra uma inspeção com 527 amostras de pressão, 520 de nível e 517 de temperatura, qualidade Good e origem em 28/10/2026. Isso não demonstra, por si só, a persistência após reiniciar o coletor.

Na preparação, havia projeto Docker `aula-03`, volume `aula-03_historico` e arquivos WAL/SHM legíveis. Um ajuste manual do relógio do Pi 4 foi executado, mas a variável de horário havia sido atualizada depois do comando; a diferença para UTC deve ser medida novamente. O build da interface foi solicitado e o usuário mostrou o comando, sem saída final de build ou healthcheck nesta conversa. Também houve tentativa de liberar 8501 com erro de sintaxe; a saída posterior da regra corrigida e a visualização da interface não foram apresentadas. Confirme esses pontos antes de afirmá-los como resultados.

As regras temporárias de download haviam aparecido em uma listagem, e uma listagem posterior da cadeia já não as apresentava. Essa última listagem não confirma a remoção da tabela NAT temporária; confira o ruleset completo atual. A persistência das regras e encaminhamento após reboot também depende de teste específico. Endereços, rotas, relógio, volumes, serviços e firewall podem ter mudado desde a gravação.

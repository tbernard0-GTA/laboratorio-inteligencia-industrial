# Complemento preparado — Primeira interface com Streamlit

Esta parte foi separada da gravação principal da Aula 3 para manter o conteúdo em etapas. **Não é uma afirmação de que a interface já foi demonstrada no vídeo.** O núcleo Docker/Compose está no [README da Aula 3](README.md).

## Objetivo

Executar um segundo serviço no Pi 4: um cliente OPC UA que lê o serviço `tep-opc` pela rede Compose e apresenta pressão, nível e temperatura no navegador. A tendência recente fica em memória; não há historiador nem retenção após reinício.

O código está em `streamlit/`. O serviço tem o profile `complemento`, portanto não sobe com o comando padrão da aula principal.

## Execução explícita no Pi 4

Na pasta `aulas/aula-03`, com `.env` revisado e as imagens/dependências disponíveis:

```bash
docker compose --env-file .env -f docker/compose.yaml --profile complemento config
docker compose --env-file .env -f docker/compose.yaml --profile complemento build
docker compose --env-file .env -f docker/compose.yaml --profile complemento up -d
docker compose --env-file .env -f docker/compose.yaml --profile complemento ps
docker compose --env-file .env -f docker/compose.yaml --profile complemento logs --tail=50
```

> Se um container Streamlit de um teste anterior já estiver rodando, omitir o profile não o desliga automaticamente. Confira `ps -a`; se desejar voltar ao núcleo da aula, pare apenas esse serviço com `docker compose --env-file .env -f docker/compose.yaml --profile complemento stop streamlit`.

Teste o cliente dentro da aplicação:

```bash
docker compose --env-file .env -f docker/compose.yaml --profile complemento exec streamlit python opc_client.py --endpoint opc.tcp://tep-opc:4840/tep/ --once
```

A interface publica `10.77.0.10:8501` e o navegador utiliza `http://10.77.0.10:8501`. Publicar essa porta no Pi 4 **não** libera o tráfego no gateway. Siga o [procedimento de liberação restrita e reversível](rede/firewall_8501.md), conferindo o IP atual do notebook e a ordem das regras. Não abra a porta para a internet.

## Conferências

- Qualidade e timestamp das leituras, além do valor numérico.
- Erro visível quando o OPC fica indisponível, sem substituir medidas por zero.
- Recuperação após reinício do servidor OPC.
- Buffer de tamanho limitado e perda esperada do histórico em memória ao reiniciar.
- Serviço HTTP local funcionando antes de atribuir falhas ao firewall.
- Nova conexão de rede bloqueada/permitida conforme a regra específica.

O [planejamento original](roteiro/planejamento_original_completo.md) reúne a sequência mais ampla da preparação; ele inclui as duas partes e não deve ser usado como lista do que aconteceu no episódio principal.

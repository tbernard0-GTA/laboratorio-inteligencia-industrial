# Roteiro da Aula 5

Este roteiro descreve a gravação concluída e pode orientar uma futura apresentação. As verificações no Pi abaixo são relatadas por Thiago, não uma inspeção remota realizada nesta revisão. Não altere serviços sem confirmar o estado e receber autorização.

1. **Retomada:** mostrar a Aula 4 no UAExpert e no Streamlit; o usuário relata que isso foi feito. Explicar as três variáveis e o histórico existente.
2. **Evolução do código:** mostrar `catalogo_tags.py`, `servidor_opc.py`, `coletor_opc.py` e `historico_sqlite.py`; seguir `XMEAS(9)` do índice 8 ao banco. Usar o [guia de estudo](GUIA_ESTUDO_CODIGO_AULA_05.md) para falas e trechos.
3. **Transição controlada:** Thiago relatou parada dos três contêineres antigos com volume preservado e execução do pacote da Aula 5. O pacote chegou ao Pi e a saída do manifesto apresentou três hashes OK. A execução da imagem, carga e subida foram relatadas; a situação atual deve ser inspecionada antes de outra transição.
4. **Aquisição:** explicar 41 medições, 12 manipuladas e três aliases, namespace pela URI e leitura em lote. Thiago relatou healthcheck do historiador aprovado e avanço de 14 ciclos/742 leituras para 17/901.
5. **SQL no banco ativo:** trabalhar as seis consultas do [guia](GUIA_ESTUDO_CODIGO_AULA_05.md#6-sql-explicado-progressivamente), com o comando de stdin da [operação](OPERACAO_GRAVACAO.md#consulta-no-banco-ativo-usando-vs-code-e-ssh). Thiago relatou 53 tags cadastradas e observadas, temperaturas, agregação por minuto, comparação por ciclo e nenhuma contagem diferente de 53. Isso não prova ausência de lacunas ou falhas.
6. **Encerramento:** registrar que o historiador foi relatado como `Exited` depois da parada; os outros estados não têm confirmação independente. O painel das 53 tags pertence à próxima aula.

Não demonstrar um novo deploy, rollback, teste de falha ou parada como se tivesse acontecido. Persistência do volume após reboot do Pi e persistência das regras de firewall permanecem a verificar.

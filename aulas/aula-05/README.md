# Aula 5 — catálogo de variáveis TEP

Este primeiro incremento organiza 41 medições `XMEAS(1)` a `XMEAS(41)` e 12 variáveis manipuladas `XMV(1)` a `XMV(12)`. Não publica OPC UA, grava dados ou altera o simulador da Aula 4.

`CATALOGO` é uma tupla de registros imutáveis com identificador estável, categoria (`medicao` ou `manipulada`), índice Python base zero, descrição original da biblioteca e unidade. Em cada vetor, o índice é o número da variável menos um: `XMEAS(7)` usa índice 6; `XMV(12)` usa índice 11. A ordem das medições e manipuladas é independente.

`ler_tags(simulador)` usa `get_measurement_names()`, `get_mv_names()`, `get_measurements()` e `get_manipulated_vars()`. Confere os nomes, a ordem e os tamanhos antes de retornar um dicionário de identificadores e valores `float`. Uma biblioteca incompatível gera `ValueError`. O chamador inicializa e avança o simulador; a leitura não altera os valores. O dicionário é um retrato, não uma garantia de simultaneidade, qualidade ou atualização das análises amostradas.

```python
from tep import TEPSimulator
from catalogo_tags import CATALOGO, ler_tags

simulador = TEPSimulator(backend="python", random_seed=1234)
simulador.initialize()
valores = ler_tags(simulador)
print(CATALOGO[6], valores["XMEAS(7)"])
```

As descrições seguem os nomes da revisão TEP fixada nas aulas. As unidades das medições seguem a [referência da API dessa revisão](https://github.com/jkitchin/tennessee-eastman-profbraatz/blob/9a6c8e5fcef4a2850778704e7793c87b0a187005/docs/api.md#measurement-index-reference): `kPa(g)` explicita pressão manométrica, e `mol%` é porcentagem molar. As manipuladas usam `%` da escala normalizada do modelo, não uma unidade física de vazão ou velocidade; a escala dos 12 valores é indicada nos modos operacionais em [constants.py](https://github.com/jkitchin/tennessee-eastman-profbraatz/blob/9a6c8e5fcef4a2850778704e7793c87b0a187005/src/tep/constants.py). Isso não caracteriza uma medição física direta. O [Fortran original](https://github.com/jkitchin/tennessee-eastman-profbraatz/blob/9a6c8e5fcef4a2850778704e7793c87b0a187005/teprob.f) documenta a ordem e unidades de medição.

## Testes

Na pasta `aulas/aula-05`, execute `python -m unittest -v test_catalogo_tags`. Os testes de estrutura usam um simulador sintético. O teste de integração usa a biblioteca TEP instalada e é marcado como ignorado se ela não estiver disponível. Para executá-lo, utilize o ambiente com a revisão fixada em `aulas/aula-04/requirements-servidor.txt`. Instalação, deploy e acesso a equipamentos não fazem parte deste incremento.

"""Catálogo e leitura das variáveis da revisão TEP usada no laboratório."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Tag:
    identificador: str
    categoria: str
    indice: int
    descricao: str
    unidade: str


# Nomes e ordem da revisão fixada da biblioteca, não nomes gerados por tradução.
_MEDIDAS = (
    ("A Feed (stream 1)", "kscmh"),
    ("D Feed (stream 2)", "kg/hr"),
    ("E Feed (stream 3)", "kg/hr"),
    ("A and C Feed (stream 4)", "kscmh"),
    ("Recycle Flow (stream 8)", "kscmh"),
    ("Reactor Feed Rate (stream 6)", "kscmh"),
    ("Reactor Pressure", "kPa(g)"),
    ("Reactor Level", "%"),
    ("Reactor Temperature", "deg C"),
    ("Purge Rate (stream 9)", "kscmh"),
    ("Product Sep Temp", "deg C"),
    ("Product Sep Level", "%"),
    ("Prod Sep Pressure", "kPa(g)"),
    ("Prod Sep Underflow (stream 10)", "m3/hr"),
    ("Stripper Level", "%"),
    ("Stripper Pressure", "kPa(g)"),
    ("Stripper Underflow (stream 11)", "m3/hr"),
    ("Stripper Temperature", "deg C"),
    ("Stripper Steam Flow", "kg/hr"),
    ("Compressor Work", "kW"),
    ("Reactor Cooling Water Outlet Temp", "deg C"),
    ("Separator Cooling Water Outlet Temp", "deg C"),
    *((f"Reactor Feed Component {c}", "mol%") for c in "ABCDEF"),
    *((f"Purge Gas Component {c}", "mol%") for c in "ABCDEFGH"),
    *((f"Product Component {c}", "mol%") for c in "DEFGH"),
)

_MANIPULADAS = (
    "D Feed Flow (stream 2)",
    "E Feed Flow (stream 3)",
    "A Feed Flow (stream 1)",
    "A and C Feed Flow (stream 4)",
    "Compressor Recycle Valve",
    "Purge Valve (stream 9)",
    "Separator Pot Liquid Flow",
    "Stripper Liquid Product Flow",
    "Stripper Steam Valve",
    "Reactor Cooling Water Flow",
    "Condenser Cooling Water Flow",
    "Agitator Speed",
)

CATALOGO = tuple(
    Tag(f"XMEAS({indice + 1})", "medicao", indice, nome, unidade)
    for indice, (nome, unidade) in enumerate(_MEDIDAS)
) + tuple(
    Tag(f"XMV({indice + 1})", "manipulada", indice, nome, "%")
    for indice, nome in enumerate(_MANIPULADAS)
)


def ler_tags(simulador: Any) -> dict[str, float]:
    """Lê um retrato dos vetores, recusando tamanho ou ordem incompatível.

    O chamador é responsável por inicializar e avançar o simulador. Os valores
    são acessados uma vez por vetor, sem escrever ou publicar nada no processo.
    """
    nomes_medidas = tuple(simulador.get_measurement_names())
    nomes_manipuladas = tuple(simulador.get_mv_names())
    if nomes_medidas != tuple(nome for nome, _ in _MEDIDAS):
        raise ValueError("Nomes ou ordem das medições TEP incompatíveis com o catálogo")
    if nomes_manipuladas != _MANIPULADAS:
        raise ValueError("Nomes ou ordem das manipuladas TEP incompatíveis com o catálogo")
    medidas = simulador.get_measurements()
    manipuladas = simulador.get_manipulated_vars()
    if len(medidas) != 41 or len(manipuladas) != 12:
        raise ValueError("Vetores TEP devem conter 41 medições e 12 manipuladas")
    return {
        tag.identificador: float((medidas if tag.categoria == "medicao" else manipuladas)[tag.indice])
        for tag in CATALOGO
    }

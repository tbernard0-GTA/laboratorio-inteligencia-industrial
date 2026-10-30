"""Leitura OPC UA das tags canônicas TEP, sem persistência."""

import argparse
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
import time
from typing import Any

from asyncua import Client

from catalogo_tags import CATALOGO

NAMESPACE = "urn:laboratorio-industrial:tep"
LOG = logging.getLogger("coletor_opc")


@dataclass(frozen=True)
class Leitura:
    identificador: str
    valor: Any
    source_timestamp: datetime | None
    status_code: int | None
    qualidade: str
    coleta_utc: datetime
    data_value: Any  # DataValue original, inclusive campos adicionais do servidor.


@dataclass(frozen=True)
class Ciclo:
    leituras: tuple[Leitura, ...]
    duracao_segundos: float


async def descobrir_tags(client):
    """Navega somente TEP/XMEAS e TEP/XMV e rejeita divergências do catálogo."""
    ns = await client.get_namespace_index(NAMESPACE)
    tep = await client.nodes.objects.get_child([f"{ns}:TEP"])
    encontrados = {}
    nodeids = set()
    for grupo, categoria in (("XMEAS", "medicao"), ("XMV", "manipulada")):
        esperado = {t.identificador for t in CATALOGO if t.categoria == categoria}
        pasta = await tep.get_child([f"{ns}:{grupo}"])
        nomes = set()
        for no in await pasta.get_children():
            browse = await no.read_browse_name()
            if browse.NamespaceIndex != ns or browse.Name not in esperado or browse.Name in nomes:
                raise ValueError(f"Nó inesperado ou duplicado no grupo {grupo}: {browse}")
            if no.nodeid in nodeids:
                raise ValueError(f"NodeId duplicado no grupo {grupo}: {no.nodeid}")
            nomes.add(browse.Name)
            nodeids.add(no.nodeid)
            encontrados[browse.Name] = no
        if nomes != esperado:
            raise ValueError(f"Grupo {grupo} incompleto: {sorted(esperado - nomes)}")
    return {tag.identificador: encontrados[tag.identificador] for tag in CATALOGO}


async def ler_ciclo(client, nos) -> Ciclo:
    """Lê um lote de DataValue; duração inclui a conversão em registros."""
    identificadores = [tag.identificador for tag in CATALOGO]
    if set(nos) != set(identificadores):
        raise ValueError("Nós descobertos não correspondem ao catálogo")
    inicio = time.monotonic()
    dados = await client.read_attributes([nos[nome] for nome in identificadores])
    coleta = datetime.now(timezone.utc)
    if len(dados) != len(identificadores):
        raise ValueError("Resposta OPC UA incompleta")
    leituras = []
    for nome, dado in zip(identificadores, dados):
        status = dado.StatusCode
        qualidade = ("Desconhecida" if status is None else
                     "Good" if status.is_good() else
                     "Uncertain" if status.is_uncertain() else "Bad")
        leituras.append(Leitura(nome, dado.Value.Value if dado.Value is not None else None,
                                dado.SourceTimestamp, status.value if status is not None else None,
                                qualidade, coleta, dado))
    return Ciclo(tuple(leituras), time.monotonic() - inicio)


async def ciclos(url: str, intervalo: float = 1.0, espera_reconexao: float = 5.0):
    """Produz ciclos até cancelamento; reabre sessão e redescobre após falha."""
    if intervalo <= 0 or espera_reconexao < 1:
        raise ValueError("intervalo deve ser positivo e espera_reconexao ao menos 1 segundo")
    while True:
        try:
            async with Client(url, timeout=5) as client:
                nos = await descobrir_tags(client)
                LOG.info("Conectado; %d tags canônicas descobertas", len(nos))
                while True:
                    inicio = time.monotonic()
                    ciclo = await ler_ciclo(client, nos)
                    yield ciclo
                    await asyncio.sleep(max(0.01, intervalo - (time.monotonic() - inicio)))
        except asyncio.CancelledError:
            raise
        except Exception:
            LOG.exception("Falha de conexão, descoberta ou leitura; nova tentativa em %.1f s", espera_reconexao)
            await asyncio.sleep(espera_reconexao)


async def main():
    parser = argparse.ArgumentParser(description="Lê as 53 tags canônicas TEP sem persistir dados.")
    parser.add_argument("url", help="endpoint OPC UA, por exemplo opc.tcp://127.0.0.1:14840/tep/")
    args = parser.parse_args()
    async for ciclo in ciclos(args.url):
        print(json.dumps({"duracao_segundos": ciclo.duracao_segundos,
                          "leituras": [{"tag": item.identificador, "valor": item.valor,
                                        "source_timestamp": item.source_timestamp,
                                        "status_code": item.status_code, "qualidade": item.qualidade,
                                        "coleta_utc": item.coleta_utc}
                                       for item in ciclo.leituras]}, default=str, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

"""Verificações limitadas: OPC UA canônico e ciclo SQLite recente."""
import asyncio
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import sys


async def verificar_servidor():
    from asyncua import Client
    from coletor_opc import descobrir_tags, ler_ciclo

    async with Client("opc.tcp://127.0.0.1:4840/tep/", timeout=5) as client:
        nos = await descobrir_tags(client)
        ciclo = await ler_ciclo(client, nos)
        if len(ciclo.leituras) != 53 or any(x.qualidade != "Good" or x.source_timestamp is None for x in ciclo.leituras):
            raise RuntimeError("OPC UA não retornou 53 tags Good com timestamp")


def verificar_historico():
    caminho = Path("/data/historico_aula05.sqlite3")
    with closing(sqlite3.connect(caminho.as_uri() + "?mode=ro", uri=True, timeout=3)) as db:
        ultima = db.execute("SELECT id, coleta_utc FROM ciclos ORDER BY coleta_utc DESC LIMIT 1").fetchone()
        if ultima is None:
            raise RuntimeError("Ainda não há ciclos gravados")
        idade = (datetime.now(timezone.utc) - datetime.fromisoformat(ultima[1])).total_seconds()
        total, bons = db.execute("SELECT COUNT(*), SUM(CASE WHEN qualidade='Good' AND validade='valido' THEN 1 ELSE 0 END) FROM leituras WHERE ciclo_id=?", (ultima[0],)).fetchone()
        if not 0 <= idade <= 60 or total != 53 or bons != 53:
            raise RuntimeError("Último ciclo incompleto, não Good ou desatualizado")


if __name__ == "__main__":
    try:
        if sys.argv[1:] == ["servidor"]:
            asyncio.run(verificar_servidor())
        elif sys.argv[1:] == ["historico"]:
            verificar_historico()
        else:
            raise ValueError("Escolha servidor ou historico")
    except Exception as exc:
        print(f"healthcheck: {exc}", file=sys.stderr)
        raise SystemExit(1)

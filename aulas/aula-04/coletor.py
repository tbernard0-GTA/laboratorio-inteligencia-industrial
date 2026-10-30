"""Coleta OPC UA para SQLite; nenhum dado sintético é produzido aqui."""
import asyncio
from datetime import datetime, timezone
import logging
import math
import os
from pathlib import Path
import sqlite3
from urllib.parse import urlparse

from asyncua import Client

LOG = logging.getLogger("coletor")
SINAIS = {"Pressao": "kPa(g)", "Nivel": "%", "Temperatura": "C"}
NAMESPACE = "urn:laboratorio-industrial:tep"


def utc_text(value):
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


def abrir_banco(path):
    path = Path(path)
    if not path.is_absolute() or not path.is_relative_to('/data'):
        raise ValueError('SQLITE_PATH deve ser um caminho absoluto dentro de /data')
    db = sqlite3.connect(path, timeout=5)
    db.execute('PRAGMA busy_timeout=5000')
    if db.execute('PRAGMA journal_mode=WAL').fetchone()[0].lower() != 'wal':
        raise RuntimeError('SQLite não ativou WAL')
    db.executescript('''
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY, sinal TEXT NOT NULL, valor REAL,
            unidade TEXT NOT NULL, source_timestamp TEXT,
            coleta_utc TEXT NOT NULL, status_code INTEGER NOT NULL,
            qualidade TEXT NOT NULL, validade TEXT NOT NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS amostra_origem
            ON leituras(sinal, source_timestamp) WHERE source_timestamp IS NOT NULL;
    ''')
    return db


def gravar(db, nome, unidade, dado, coleta):
    status = dado.StatusCode
    if status is None:
        raise ValueError('DataValue sem StatusCode')
    raw = dado.Value.Value if dado.Value is not None else None
    valor = float(raw) if isinstance(raw, (int, float)) and not isinstance(raw, bool) else None
    if valor is not None and not math.isfinite(valor):
        valor = None
    qualidade = 'Good' if status.is_good() else ('Uncertain' if status.is_uncertain() else 'Bad')
    with db:
        db.execute('''INSERT INTO leituras
            (sinal, valor, unidade, source_timestamp, coleta_utc, status_code, qualidade, validade)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING''',
            (nome, valor, unidade, utc_text(dado.SourceTimestamp), utc_text(coleta),
             status.value, qualidade, 'valido' if valor is not None else 'valor_invalido'))


async def verificar_endpoints(client):
    endpoints = await client.connect_and_get_server_endpoints()
    acessivel = False
    for endpoint in endpoints:
        url = endpoint.EndpointUrl
        LOG.info('Endpoint anunciado: %s', url)
        parsed = urlparse(url)
        if parsed.scheme != 'opc.tcp' or not parsed.hostname or not parsed.port:
            continue
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(parsed.hostname, parsed.port), 3)
            writer.close()
            await writer.wait_closed()
            acessivel = True
        except (OSError, asyncio.TimeoutError):
            LOG.warning('Endpoint anunciado inacessível: %s', url)
    if not acessivel:
        raise ConnectionError('Nenhum endpoint anunciado acessível a partir do coletor')


async def coletar(db, url):
    client = Client(url, timeout=5)
    await verificar_endpoints(client)
    async with client:
        ns = await client.get_namespace_index(NAMESPACE)
        reator = await client.nodes.objects.get_child([f'{ns}:Reator'])
        nodes = {nome: await reator.get_child([f'{ns}:{nome}']) for nome in SINAIS}
        LOG.info('Conectado a %s; namespace=%s; sinais=%s', url, ns, list(nodes))
        while True:
            inicio = asyncio.get_running_loop().time()
            for nome, node in nodes.items():
                dado = await node.read_data_value(raise_on_bad_status=False)
                gravar(db, nome, SINAIS[nome], dado, datetime.now(timezone.utc))
            await asyncio.sleep(max(0.01, 1 - (asyncio.get_running_loop().time() - inicio)))


async def executar(db, url):
    while True:
        try:
            await coletar(db, url)
        except asyncio.CancelledError:
            raise
        except Exception:
            LOG.exception('Falha de coleta; nova tentativa em 5 segundos')
            await asyncio.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    caminho = os.environ.get('SQLITE_PATH', '/data/leituras.sqlite3')
    with abrir_banco(caminho) as banco:
        asyncio.run(executar(banco, os.environ.get('OPC_UA_URL', 'opc.tcp://tep-opc:4840/tep/')))

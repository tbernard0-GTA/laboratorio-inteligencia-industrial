"""Cliente real OPC UA: descobre BrowseNames/URI, sem NodeIds presumidos."""
import argparse
import asyncio
import json
import math
from datetime import datetime, timezone
from asyncua import Client

NAMESPACE = "urn:laboratorio-industrial:tep"
TAGS = ("Pressao", "Nivel", "Temperatura")

async def discover(client):
    ns = await client.get_namespace_index(NAMESPACE)
    reactor = await client.nodes.objects.get_child(f"{ns}:Reator")
    result = {}
    for name in TAGS:
        node = await reactor.get_child(f"{ns}:{name}")
        unit = await (await node.get_child(f"{ns}:Unidade")).read_value()
        result[name] = (node, unit)
    return result

async def read_values(nodes, max_age=10):
    now = datetime.now(timezone.utc)
    values = {}
    for name, (node, unit) in nodes.items():
        data = await node.read_data_value()
        data.StatusCode.check()
        value = float(data.Value.Value)
        timestamp = data.SourceTimestamp
        if not math.isfinite(value):
            raise ValueError(f"{name}: valor nao finito")
        if timestamp is None:
            raise ValueError(f"{name}: SourceTimestamp ausente")
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        age = (now - timestamp).total_seconds()
        if age > max_age or age < -max_age:
            raise ValueError(f"{name}: timestamp desatualizado ou relogios divergentes ({age:.1f}s)")
        values[name] = {"value": value, "unit": unit, "timestamp": timestamp.isoformat(), "quality": data.StatusCode.name}
    return {"received_at": now.isoformat(), "values": values}

async def read_once(endpoint):
    async with Client(endpoint, timeout=4) as client:
        return await read_values(await discover(client))

async def collect(endpoint, publish, stop, interval=1.0):
    """Conexao persistente; backoff limitado e redescoberta apos desconexao."""
    delay = 1
    while not stop.is_set():
        try:
            async with Client(endpoint, timeout=4) as client:
                nodes = await discover(client)
                while not stop.is_set():
                    sample = await read_values(nodes)
                    publish(sample, None)
                    delay = 1
                    await asyncio.sleep(interval)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            publish(None, f"{type(exc).__name__}: {exc}")
            for _ in range(delay * 10):
                if stop.is_set():
                    return
                await asyncio.sleep(0.1)
            delay = min(delay * 2, 15)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default="opc.tcp://127.0.0.1:4840/tep/")
    parser.add_argument("--once", action="store_true", help="Leitura unica; falha resulta em codigo nao zero")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(read_once(args.endpoint)), ensure_ascii=False))

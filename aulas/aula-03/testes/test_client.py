"""Servidor de teste explicito; estes valores nao sao TEP."""
import asyncio
from datetime import datetime, timezone, timedelta
import socket
import sys
from pathlib import Path
import pytest
from asyncua import Server, ua
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "streamlit"))
from opc_client import discover, read_values, read_once, collect, NAMESPACE, TAGS

def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]

async def fixture_server(port):
    server = Server()
    await server.init()
    server.set_endpoint(f"opc.tcp://127.0.0.1:{port}/tep/")
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])
    await server.register_namespace("urn:extra:namespace-for-test")
    ns = await server.register_namespace(NAMESPACE)
    reactor = await server.nodes.objects.add_object(ns, "Reator")
    nodes = {}
    for name, value, unit in zip(TAGS, [2705., 74.7, 120.3], ["kPa(g)", "%", "C"]):
        node = await reactor.add_variable(ns, name, value)
        await node.add_property(ns, "Unidade", unit)
        dv = ua.DataValue(ua.Variant(value, ua.VariantType.Double))
        dv.SourceTimestamp = datetime.now(timezone.utc)
        await node.write_value(dv)
        nodes[name] = (node, unit)
    return server, nodes

@pytest.mark.asyncio
async def test_real_protocol_discovery_shifted_namespace():
    port = free_port()
    server, _ = await fixture_server(port)
    async with server:
        sample = await read_once(f"opc.tcp://127.0.0.1:{port}/tep/")
        assert tuple(sample["values"]) == TAGS
        assert sample["values"]["Pressao"]["unit"] == "kPa(g)"
        assert all(v["quality"] == "Good" for v in sample["values"].values())

@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["stale", "nan", "bad"])
async def test_reject_invalid_data(case):
    server, nodes = await fixture_server(free_port())
    node, _ = nodes["Pressao"]
    dv = ua.DataValue(ua.Variant(float('nan') if case == 'nan' else 1., ua.VariantType.Double))
    dv.SourceTimestamp = datetime.now(timezone.utc) - timedelta(seconds=60 if case == 'stale' else 0)
    if case == 'bad':
        dv.StatusCode = ua.StatusCode(ua.StatusCodes.BadSensorFailure)
    await node.write_value(dv)
    with pytest.raises(Exception):
        await read_values(nodes)

@pytest.mark.asyncio
async def test_recovery_after_initial_unavailable_server():
    port = free_port()
    stop = asyncio.Event()
    records = []
    def publish(sample, error):
        records.append((sample, error))
        if sample:
            stop.set()
    task = asyncio.create_task(collect(f"opc.tcp://127.0.0.1:{port}/tep/", publish, stop, .05))
    await asyncio.sleep(.2)
    server, _ = await fixture_server(port)
    try:
        async with server:
            await asyncio.wait_for(task, 12)
    finally:
        stop.set()
        if not task.done():
            task.cancel()
    assert any(error for _, error in records)
    assert any(sample for sample, _ in records)

@pytest.mark.asyncio
async def test_reconnect_after_server_restart():
    port = free_port()
    endpoint = f"opc.tcp://127.0.0.1:{port}/tep/"
    stop = asyncio.Event()
    connected = asyncio.Event()
    disconnected = asyncio.Event()
    recovered = asyncio.Event()
    def publish(sample, error):
        if error:
            disconnected.set()
        elif sample:
            if disconnected.is_set():
                recovered.set()
                stop.set()
            connected.set()
    server, _ = await fixture_server(port)
    await server.start()
    task = asyncio.create_task(collect(endpoint, publish, stop, .1))
    try:
        await asyncio.wait_for(connected.wait(), 10)
        await server.stop()
        await asyncio.wait_for(disconnected.wait(), 10)
        server, _ = await fixture_server(port)
        await server.start()
        await asyncio.wait_for(recovered.wait(), 15)
        await asyncio.wait_for(task, 5)
    finally:
        stop.set()
        if not task.done():
            task.cancel()
        await server.stop()

@pytest.mark.asyncio
async def test_client_keeps_internal_address_with_external_advertisement():
    port = free_port()
    server, _ = await fixture_server(port)
    server.set_endpoint('opc.tcp://10.77.0.10:4840/tep/')
    server.socket_address = ('127.0.0.1', port)
    async with server:
        sample = await read_once(f'opc.tcp://127.0.0.1:{port}/tep/')
        assert sample['values']['Pressao']['quality'] == 'Good'

import asyncio
import os
from datetime import datetime, timezone
from asyncua import Server, ua
from tep import TEPSimulator

ENDPOINT = os.getenv("OPC_ADVERTISED_ENDPOINT", "opc.tcp://127.0.0.1:4840/tep/")

async def main():
    sim = TEPSimulator(backend="python", random_seed=1234)
    sim.initialize()

    server = Server()
    await server.init()
    server.set_endpoint(ENDPOINT)
    server.socket_address = (os.getenv("OPC_BIND_HOST", "0.0.0.0"), 4840)
    server.set_server_name("Laboratorio Industrial - TEP")
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    ns = await server.register_namespace("urn:laboratorio-industrial:tep")
    reator = await server.nodes.objects.add_object(ns, "Reator")
    especificacoes = [
        ("Pressao", 6, "kPa(g)"),
        ("Nivel", 7, "%"),
        ("Temperatura", 8, "C"),
    ]
    medidas = sim.get_measurements()
    sinais = []
    for nome, indice, unidade in especificacoes:
        no = await reator.add_variable(ns, nome, float(medidas[indice]))
        await no.add_property(ns, "Unidade", unidade)
        sinais.append((no, indice))

    async with server:
        print(f"Servidor iniciado: {ENDPOINT}", flush=True)
        while True:
            inicio = asyncio.get_running_loop().time()
            if not sim.step():
                raise RuntimeError("O modelo interrompeu a simulacao.")
            medidas = sim.get_measurements()
            horario = datetime.now(timezone.utc)
            for no, indice in sinais:
                dado = ua.DataValue(ua.Variant(float(medidas[indice]), ua.VariantType.Double))
                dado.SourceTimestamp = horario
                await no.write_value(dado)
            print(f"{horario.isoformat()} | t_modelo={sim.time * 3600:.1f}s", flush=True)
            decorrido = asyncio.get_running_loop().time() - inicio
            await asyncio.sleep(max(0.0, 1.0 - decorrido))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServidor encerrado.")

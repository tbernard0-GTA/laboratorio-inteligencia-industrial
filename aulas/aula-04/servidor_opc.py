import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import ipaddress
import os
import re
from typing import Mapping


@dataclass(frozen=True)
class ConfiguracaoEndpoint:
    bind_host: str
    port: int
    endpoint: str


def _validar_host(valor: str, nome: str, *, anunciado: bool = False) -> str:
    # IPv4 e nomes DNS sem porta; IPv6 não é suportado nesta etapa.
    if not valor or len(valor) > 253 or valor != valor.strip():
        raise ValueError(f"{nome} deve ser um endereço IPv4 ou nome DNS válido")
    try:
        ip = ipaddress.IPv4Address(valor)
    except ipaddress.AddressValueError:
        labels = valor.split(".")
        if (all(c in "0123456789." for c in valor) or any(
            not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
            for label in labels
        )):
            raise ValueError(f"{nome} deve ser um endereço IPv4 ou nome DNS válido")
    else:
        if anunciado and ip.is_unspecified:
            raise ValueError(f"{nome} não pode ser 0.0.0.0")
    return valor


def configurar_endpoint(environ: Mapping[str, str] | None = None) -> ConfiguracaoEndpoint:
    env = os.environ if environ is None else environ
    bind_host = _validar_host(env.get("OPC_UA_BIND_HOST", "192.168.1.19"), "OPC_UA_BIND_HOST")
    advertise_host = _validar_host(
        env.get("OPC_UA_ADVERTISE_HOST", "192.168.1.19"), "OPC_UA_ADVERTISE_HOST", anunciado=True
    )
    port_text = env.get("OPC_UA_PORT", "4840")
    if not re.fullmatch(r"[0-9]+", port_text):
        raise ValueError("OPC_UA_PORT deve ser um inteiro entre 1 e 65535")
    port = int(port_text)
    if not 1 <= port <= 65535:
        raise ValueError("OPC_UA_PORT deve ser um inteiro entre 1 e 65535")
    return ConfiguracaoEndpoint(bind_host, port, f"opc.tcp://{advertise_host}:{port}/tep/")


async def main():
    # Importações aqui permitem testar a configuração sem instalar as dependências da aula.
    from asyncua import Server, ua
    from tep import TEPSimulator

    config = configurar_endpoint()
    sim = TEPSimulator(backend="python", random_seed=1234)
    sim.initialize()

    server = Server()
    await server.init()
    server.set_endpoint(config.endpoint)
    server.socket_address = (config.bind_host, config.port)
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
        print(f"Servidor iniciado. Endpoint base: {config.endpoint} (escuta: {config.bind_host}:{config.port})", flush=True)
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

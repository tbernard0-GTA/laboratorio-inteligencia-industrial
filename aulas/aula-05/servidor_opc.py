import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import ipaddress
import os
import re
from typing import Mapping

from catalogo_tags import CATALOGO, ler_tags

NAMESPACE = "urn:laboratorio-industrial:tep"
LEGADAS = (("Pressao", "XMEAS(7)", "kPa(g)"),
           ("Nivel", "XMEAS(8)", "%"),
           ("Temperatura", "XMEAS(9)", "C"))

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


async def criar_nos(server, simulador):
    """Cria as três variáveis legadas antes dos nós novos, como na Aula 4."""
    from asyncua import ua

    valores = ler_tags(simulador)
    ns = await server.register_namespace(NAMESPACE)
    reator = await server.nodes.objects.add_object(ns, "Reator")
    legados = {}
    for nome, tag, unidade in LEGADAS:
        no = await reator.add_variable(ns, nome, valores[tag], ua.VariantType.Double)
        await no.add_property(ns, "Unidade", unidade)
        legados[tag] = no

    tep = await server.nodes.objects.add_object(ua.NodeId("TEP", ns), ua.QualifiedName("TEP", ns))
    grupos = {}
    for grupo in ("XMEAS", "XMV"):
        grupos[grupo] = await tep.add_object(
            ua.NodeId(f"TEP.{grupo}", ns), ua.QualifiedName(grupo, ns)
        )
    nos = {}
    for tag in CATALOGO:
        grupo = "XMEAS" if tag.categoria == "medicao" else "XMV"
        nodeid = ua.NodeId(f"TEP.{tag.identificador}", ns)
        no = await grupos[grupo].add_variable(
            nodeid, ua.QualifiedName(tag.identificador, ns), valores[tag.identificador], ua.VariantType.Double
        )
        await no.add_property(ns, "Unidade", tag.unidade)
        await no.add_property(ns, "Descricao", tag.descricao)
        await no.add_property(ns, "Categoria", tag.categoria)
        await no.add_property(ns, "IndicePython", tag.indice)
        nos[tag.identificador] = no
    await publicar_valores(nos, legados, valores, datetime.now(timezone.utc))
    return ns, nos, legados


async def publicar_valores(nos, legados, valores, horario):
    """Publica um mesmo retrato e timestamp; escritas OPC UA são sequenciais."""
    from asyncua import ua

    for identificador, no in nos.items():
        dado = ua.DataValue(ua.Variant(valores[identificador], ua.VariantType.Double))
        dado.StatusCode = ua.StatusCode(ua.StatusCodes.Good)
        dado.SourceTimestamp = horario
        await no.write_value(dado)
        if identificador in legados:
            await legados[identificador].write_value(dado)


async def executar_ciclo(simulador, nos, legados):
    if not simulador.step():
        raise RuntimeError("O modelo interrompeu a simulacao.")
    valores = ler_tags(simulador)
    horario = datetime.now(timezone.utc)
    await publicar_valores(nos, legados, valores, horario)
    return valores, horario


async def main():
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
    _, nos, legados = await criar_nos(server, sim)

    async with server:
        print(f"Servidor iniciado. Endpoint base: {config.endpoint} (escuta: {config.bind_host}:{config.port})", flush=True)
        while True:
            inicio = asyncio.get_running_loop().time()
            _, horario = await executar_ciclo(sim, nos, legados)
            print(f"{horario.isoformat()} | t_modelo={sim.time * 3600:.1f}s", flush=True)
            await asyncio.sleep(max(0.0, 1.0 - (asyncio.get_running_loop().time() - inicio)))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServidor encerrado.")



import asyncio
import socket
import unittest
from unittest.mock import patch

from catalogo_tags import CATALOGO
from servidor_opc import LEGADAS, NAMESPACE, configurar_endpoint, criar_nos, executar_ciclo

try:
    from asyncua import Client, Server, ua
    from tep import TEPSimulator
except ImportError:
    Client = Server = ua = TEPSimulator = None


class ConfiguracaoTest(unittest.TestCase):
    def test_endpoint_compativel_e_validacao(self):
        config = configurar_endpoint({"OPC_UA_BIND_HOST": "127.0.0.1", "OPC_UA_ADVERTISE_HOST": "localhost", "OPC_UA_PORT": "14840"})
        self.assertEqual(config.endpoint, "opc.tcp://localhost:14840/tep/")
        self.assertEqual(config.bind_host, "127.0.0.1")
        for env in ({"OPC_UA_PORT": "0"}, {"OPC_UA_ADVERTISE_HOST": "0.0.0.0"}):
            with self.subTest(env=env), self.assertRaises(ValueError):
                configurar_endpoint(env)


@unittest.skipIf(Client is None, "asyncua e tep são necessários para a integração")
class ServidorIntegracaoTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.sim = TEPSimulator(backend="python", random_seed=1234)
        self.sim.initialize()
        self.server = Server()
        await self.server.init()
        # A porta é local e efêmera; uma eventual colisão faz o teste falhar.
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        self.url = f"opc.tcp://127.0.0.1:{port}/tep/"
        self.server.set_endpoint(self.url)
        self.server.socket_address = ("127.0.0.1", port)
        self.server.set_security_policy([ua.SecurityPolicyType.NoSecurity])
        self.ns, self.nos, self.legados = await criar_nos(self.server, self.sim)
        await self.server.start()
        self.addAsyncCleanup(self.server.stop)
        self.client = Client(self.url, timeout=10)
        await self.client.connect()
        self.addAsyncCleanup(self.client.disconnect)

    async def test_hierarquia_leituras_acesso_e_ciclos(self):
        ns = await self.client.get_namespace_index(NAMESPACE)
        objects = self.client.nodes.objects
        reator = await objects.get_child([f"{ns}:Reator"])
        tep = await objects.get_child([f"{ns}:TEP"])
        xmeas = await tep.get_child([f"{ns}:XMEAS"])
        xmv = await tep.get_child([f"{ns}:XMV"])
        self.assertEqual(len(await xmeas.get_children()), 41)
        self.assertEqual(len(await xmv.get_children()), 12)
        self.assertEqual(len(await reator.get_children()), 3)
        self.assertEqual(len({n.nodeid for n in self.nos.values()}), 53)

        ids_antes = {}
        for tag in CATALOGO:
            grupo = xmeas if tag.categoria == "medicao" else xmv
            no = await grupo.get_child([f"{ns}:{tag.identificador}"])
            self.assertEqual(no.nodeid, ua.NodeId(f"TEP.{tag.identificador}", ns))
            ids_antes[tag.identificador] = no.nodeid.Identifier
            self.assertNotIn(ua.AccessLevel.CurrentWrite, await no.get_access_level())
            self.assertNotIn(ua.AccessLevel.CurrentWrite, await no.get_user_access_level())
            for nome, esperado in (("Unidade", tag.unidade), ("Descricao", tag.descricao),
                                   ("Categoria", tag.categoria), ("IndicePython", tag.indice)):
                propriedade = await no.get_child([f"{ns}:{nome}"])
                self.assertEqual(await propriedade.read_value(), esperado)
                self.assertNotIn(ua.AccessLevel.CurrentWrite, await propriedade.get_user_access_level())

        # Confere rejeição real de escrita, inclusive em XMV e nas tags legadas.
        for no in (self.nos["XMEAS(1)"], self.nos["XMV(1)"], self.legados["XMEAS(7)"]):
            remoto = self.client.get_node(no.nodeid)
            with self.assertRaises(ua.UaStatusCodeError):
                await remoto.write_value(ua.Variant(123.0, ua.VariantType.Double))

        antes = await self.client.get_node(self.nos["XMEAS(7)"].nodeid).read_data_value()
        with patch.object(self.sim, "step", wraps=self.sim.step) as step:
            valores, horario = await executar_ciclo(self.sim, self.nos, self.legados)
            self.assertEqual(step.call_count, 1)
        self.assertGreater(horario, antes.SourceTimestamp)
        for tag in CATALOGO:
            vetor = self.sim.get_measurements() if tag.categoria == "medicao" else self.sim.get_manipulated_vars()
            dado = await self.client.get_node(self.nos[tag.identificador].nodeid).read_data_value()
            self.assertEqual(dado.Value.Value, float(vetor[tag.indice]))
            self.assertEqual(dado.Value.Value, valores[tag.identificador])
            self.assertTrue(dado.StatusCode.is_good())
            self.assertEqual(dado.SourceTimestamp, horario)

        for nome, identificador, unidade in LEGADAS:
            legado = await reator.get_child([f"{ns}:{nome}"])
            self.assertNotIn(ua.AccessLevel.CurrentWrite, await legado.get_user_access_level())
            self.assertEqual(await (await legado.get_child([f"{ns}:Unidade"])).read_value(), unidade)
            dado_legado = await legado.read_data_value()
            dado_novo = await self.client.get_node(self.nos[identificador].nodeid).read_data_value()
            self.assertEqual(dado_legado.Value, dado_novo.Value)
            self.assertEqual(dado_legado.StatusCode, dado_novo.StatusCode)
            self.assertEqual(dado_legado.SourceTimestamp, dado_novo.SourceTimestamp)

        await asyncio.sleep(0.01)
        _, segundo_horario = await executar_ciclo(self.sim, self.nos, self.legados)
        self.assertGreater(segundo_horario, horario)
        self.assertEqual((await self.client.get_node(self.nos["XMV(12)"].nodeid).read_data_value()).SourceTimestamp, segundo_horario)

        # Recriar o espaço de endereços não altera os identificadores textuais.
        outro = Server()
        await outro.init()
        outro_ns, outros_nos, outros_legados = await criar_nos(outro, self.sim)
        self.assertEqual(ns, outro_ns)
        self.assertEqual(ids_antes, {key: no.nodeid.Identifier for key, no in outros_nos.items()})
        self.assertEqual({key: no.nodeid for key, no in self.legados.items()},
                         {key: no.nodeid for key, no in outros_legados.items()})

    async def test_ids_legados_iguais_a_construcao_da_aula_4(self):
        # Reproduz a sequência de criação da Aula 4 para conferir seus NodeIds numéricos.
        antigo = Server()
        await antigo.init()
        ns = await antigo.register_namespace(NAMESPACE)
        reator = await antigo.nodes.objects.add_object(ns, "Reator")
        for nome, identificador, unidade in LEGADAS:
            no = await reator.add_variable(ns, nome, 0.0)
            await no.add_property(ns, "Unidade", unidade)
            self.assertEqual(no.nodeid, self.legados[identificador].nodeid)


if __name__ == "__main__":
    unittest.main()

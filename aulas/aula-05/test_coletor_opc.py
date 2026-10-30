import asyncio
from datetime import datetime, timezone
import importlib.util
import socket
import statistics
import unittest
from unittest.mock import AsyncMock, patch

if importlib.util.find_spec("asyncua"):
    from asyncua import Client, Server, ua
    import coletor_opc
    from catalogo_tags import CATALOGO
    from servidor_opc import criar_nos, executar_ciclo
else:
    Client = Server = ua = None

try:
    from tep import TEPSimulator
except ImportError:
    TEPSimulator = None


@unittest.skipIf(Client is None, "asyncua não instalado")
class TratamentoTest(unittest.IsolatedAsyncioTestCase):
    async def test_preserva_qualidade_status_valor_e_timestamp_ausente(self):
        agora = datetime.now(timezone.utc)
        bons = [ua.DataValue(ua.Variant(float(i)), StatusCode=ua.StatusCode(ua.StatusCodes.Good),
                             SourceTimestamp=agora) for i in range(53)]
        bons[1] = ua.DataValue(ua.Variant(12.5), StatusCode=ua.StatusCode(ua.StatusCodes.Uncertain),
                               SourceTimestamp=agora)
        bons[2] = ua.DataValue(Value=None, StatusCode=ua.StatusCode(ua.StatusCodes.BadNoCommunication),
                               SourceTimestamp=None)
        cliente = AsyncMock()
        cliente.read_attributes.return_value = bons
        nos = {tag.identificador: object() for tag in CATALOGO}
        ciclo = await coletor_opc.ler_ciclo(cliente, nos)
        cliente.read_attributes.assert_awaited_once()
        self.assertEqual(ciclo.leituras[1].qualidade, "Uncertain")
        self.assertEqual(ciclo.leituras[1].valor, 12.5)
        self.assertEqual(ciclo.leituras[1].status_code, ua.StatusCodes.Uncertain)
        self.assertEqual(ciclo.leituras[2].qualidade, "Bad")
        self.assertIsNone(ciclo.leituras[2].valor)
        self.assertIsNone(ciclo.leituras[2].source_timestamp)
        self.assertEqual(ciclo.leituras[2].status_code, ua.StatusCodes.BadNoCommunication)
        self.assertIs(ciclo.leituras[2].data_value, bons[2])
        cliente.read_attributes.return_value = bons[:-1]
        with self.assertRaises(ValueError):
            await coletor_opc.ler_ciclo(cliente, nos)

    async def test_reconecta_com_pausa_e_redescobre(self):
        cliente1, cliente2 = AsyncMock(), AsyncMock()
        cliente1.__aenter__.return_value = cliente1
        cliente2.__aenter__.return_value = cliente2
        amostra = coletor_opc.Ciclo((), 0.01)
        with patch.object(coletor_opc, "Client", side_effect=[cliente1, cliente2]), \
             patch.object(coletor_opc, "descobrir_tags", new_callable=AsyncMock, return_value={}) as descobrir, \
             patch.object(coletor_opc, "ler_ciclo", new_callable=AsyncMock,
                          side_effect=[amostra, OSError("conexão interrompida"), amostra]), \
             patch.object(coletor_opc.asyncio, "sleep", new_callable=AsyncMock) as sleep:
            gerador = coletor_opc.ciclos("opc.tcp://127.0.0.1:1/tep/", espera_reconexao=5)
            try:
                self.assertIs(await anext(gerador), amostra)
                self.assertIs(await anext(gerador), amostra)
                self.assertIn(5, [chamada.args[0] for chamada in sleep.await_args_list])
                self.assertEqual(descobrir.await_count, 2)
                descobrir.assert_any_await(cliente1)
                descobrir.assert_any_await(cliente2)
            finally:
                await gerador.aclose()


@unittest.skipIf(Client is None or TEPSimulator is None, "asyncua e tep são necessários")
class ColetorIntegracaoTest(unittest.IsolatedAsyncioTestCase):
    async def test_servidor_real_e_tempo_de_aquisicao(self):
        sim = TEPSimulator(backend="python", random_seed=1234)
        sim.initialize()
        server = Server()
        await server.init()
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            porta = sock.getsockname()[1]
        url = f"opc.tcp://127.0.0.1:{porta}/tep/"
        server.set_endpoint(url)
        server.socket_address = ("127.0.0.1", porta)
        server.set_security_policy([ua.SecurityPolicyType.NoSecurity])
        await server.register_namespace("urn:teste:namespace-extra")
        ns, nos_servidor, legadas = await criar_nos(server, sim)
        self.assertGreater(ns, 2)
        valores, horario = await executar_ciclo(sim, nos_servidor, legadas)
        async with server:
            async with Client(url, timeout=10) as client:
                nos = await coletor_opc.descobrir_tags(client)
                self.assertEqual(len(nos), 53)
                self.assertEqual(set(nos), {tag.identificador for tag in CATALOGO})
                self.assertFalse({"Pressao", "Nivel", "Temperatura"} & set(nos))
                tempos = []
                for _ in range(10):
                    ciclo = await coletor_opc.ler_ciclo(client, nos)
                    tempos.append(ciclo.duracao_segundos)
                    self.assertEqual(len(ciclo.leituras), 53)
                    self.assertEqual(len({item.identificador for item in ciclo.leituras}), 53)
                    for item in ciclo.leituras:
                        self.assertEqual(item.valor, valores[item.identificador])
                        self.assertEqual(item.source_timestamp, horario)
                        self.assertEqual(item.status_code, 0)
                        self.assertEqual(item.qualidade, "Good")
                        self.assertEqual(item.coleta_utc.utcoffset().total_seconds(), 0)
                print(f"\nAquisição local de 53 tags (10 ciclos): média={statistics.mean(tempos)*1000:.2f} ms, "
                      f"mín={min(tempos)*1000:.2f} ms, máx={max(tempos)*1000:.2f} ms", flush=True)

                gerador = coletor_opc.ciclos(url)
                try:
                    produzido = await asyncio.wait_for(anext(gerador), timeout=30)
                    self.assertEqual({item.identificador for item in produzido.leituras}, set(valores))
                    self.assertEqual({item.identificador: item.valor for item in produzido.leituras}, valores)
                finally:
                    await gerador.aclose()

                # Um nó extra deve interromper a descoberta em vez de ser ignorado.
                grupo = await server.nodes.objects.get_child([f"{ns}:TEP", f"{ns}:XMV"])
                extra = await grupo.add_variable(ns, "inesperado", 1.0)
                with self.assertRaises(ValueError):
                    await coletor_opc.descobrir_tags(client)
                await extra.delete()
                await nos_servidor["XMV(12)"].delete()
                with self.assertRaises(ValueError):
                    await coletor_opc.descobrir_tags(client)


if __name__ == "__main__":
    unittest.main()

import asyncio
from contextlib import closing, redirect_stdout
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from consultar_historico import CONSULTAS, abrir_leitura, executar
from historico_sqlite import abrir_banco, gravar_ciclo, registrar
from test_historico_sqlite import CicloTeste, ciclo_exemplo

INICIO = "2026-10-30T12:00:00Z"
FIM = "2026-10-30T12:03:00Z"


class ConsultasTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "temporario.sqlite3"
        self.db = abrir_banco(self.path)
        self.addCleanup(self.db.close)

    def consultar(self, nome, **params):
        with closing(abrir_leitura(self.path)) as db:
            return executar(db, nome, inicio=INICIO, fim=FIM, **params)

    def preencher(self):
        base = datetime(2026, 10, 30, 12, tzinfo=timezone.utc)
        for indice in range(3):
            instante = base + timedelta(seconds=indice * 30)
            leituras = []
            for item in ciclo_exemplo().leituras:
                valor = {"XMEAS(7)": 100.0 + indice, "XMEAS(9)": 20.0 + indice,
                         "XMV(10)": 40.0 + indice}.get(item.identificador, 3.0)
                dado = replace(item, valor=valor, coleta_utc=instante,
                               source_timestamp=instante + timedelta(seconds=indice))
                if item.identificador == "XMV(10)":
                    dado = replace(dado, source_timestamp=instante + timedelta(seconds=10))
                if indice == 1 and item.identificador == "XMEAS(9)":
                    dado = replace(dado, valor=None, source_timestamp=None,
                                   qualidade="Bad", status_code=0x80000000)
                if indice == 2 and item.identificador == "XMEAS(9)":
                    dado = replace(dado, qualidade="Uncertain", status_code=0x40000000)
                if indice == 0 and item.identificador == "XMEAS(8)":
                    dado = replace(dado, source_timestamp=None)
                if indice == 1 and item.identificador == "XMEAS(8)":
                    dado = replace(dado, valor=None)
                leituras.append(dado)
            gravar_ciclo(self.db, f"ciclo-{indice}", CicloTeste(tuple(leituras)))

    def test_banco_vazio_ou_sem_leituras(self):
        self.assertEqual(len(self.consultar("tags")), 53)
        self.assertEqual(self.consultar("contagem"), [{"ciclos": 0, "leituras": 0}])
        for nome in CONSULTAS - {"tags", "contagem"}:
            with self.subTest(nome=nome):
                self.assertEqual(self.consultar(nome), [])

    def test_consultas_com_janela_agregacao_e_qualidade(self):
        self.preencher()
        self.assertEqual(self.consultar("contagem"), [{"ciclos": 3, "leituras": 159}])
        tags = self.consultar("tags")
        self.assertEqual((tags[6]["identificador"], tags[8]["identificador"]), ("XMEAS(7)", "XMEAS(9)"))
        amostras = self.consultar("amostras", tag="XMEAS(7)", limite=2)
        self.assertEqual([linha["valor"] for linha in amostras], [102.0, 101.0])
        self.assertEqual(len(self.consultar("temperatura_30min")), 3)
        with closing(abrir_leitura(self.path)) as db:
            self.assertEqual(len(executar(db, "temperatura_30min", fim=FIM)), 3)
        resumo = self.consultar("resumo_minuto")
        self.assertEqual(len(resumo), 1)
        self.assertEqual((resumo[0]["amostras"], resumo[0]["media"], resumo[0]["minimo"], resumo[0]["maximo"]),
                         (1, 20.0, 20.0, 20.0))
        resumo_pressao = self.consultar("resumo_minuto", tag="XMEAS(7)")
        self.assertEqual([(r["amostras"], r["media"], r["minimo"], r["maximo"]) for r in resumo_pressao],
                         [(1, 102.0, 102.0, 102.0), (2, 100.5, 100.0, 101.0)])
        anomalias = self.consultar("anomalias")
        self.assertEqual({linha["qualidade"] for linha in anomalias}, {"Bad", "Uncertain"})
        self.assertIsNone(next(linha for linha in anomalias if linha["qualidade"] == "Bad")["source_timestamp"])
        self.assertEqual({r["validade"] for r in self.consultar("anomalias", tag="XMEAS(8)")},
                         {"valor_invalido", "source_timestamp_ausente"})

    def test_join_por_ciclo_preserva_correspondencia_e_valores_invalidos(self):
        self.preencher()
        linhas = self.consultar("comparacao")
        self.assertEqual(len(linhas), 3)
        por_ciclo = {linha["ciclo_id"]: linha for linha in linhas}
        self.assertEqual((por_ciclo["ciclo-2"]["pressao_kpa_g"], por_ciclo["ciclo-2"]["temperatura_c"],
                          por_ciclo["ciclo-2"]["agua_reator_percentual"]), (102.0, 22.0, 42.0))
        self.assertIsNone(por_ciclo["ciclo-1"]["temperatura_c"])
        self.assertEqual(por_ciclo["ciclo-1"]["temperatura_validade"], "valor_invalido")

    def test_janelas_limites_e_somente_leitura(self):
        self.preencher()
        with closing(abrir_leitura(self.path)) as db:
            linhas = executar(db, "amostras", tag="XMEAS(7)", inicio=INICIO,
                              fim="2026-10-30T12:00:30Z")
            self.assertEqual(len(linhas), 1)  # fim exclusivo
            with self.assertRaises(sqlite3.OperationalError):
                db.execute("DELETE FROM leituras")
            for args in ({"tag": "XMEAS(99)"}, {"limite": 0}, {"inicio": FIM, "fim": INICIO}):
                with self.subTest(args=args), self.assertRaises(ValueError):
                    executar(db, "amostras", **args)
        ausente = Path(self.temp.name) / "nao-existe.sqlite3"
        with self.assertRaises(sqlite3.OperationalError):
            abrir_leitura(ausente)
        self.assertFalse(ausente.exists())

    def test_planos_de_execucao_indices(self):
        self.preencher()
        for nome in ("amostras", "temperatura_30min", "resumo_minuto", "comparacao", "anomalias"):
            detalhes = " | ".join(linha["detail"] for linha in self.consultar(nome, plano=True))
            self.assertIn("leituras_tag_coleta", detalhes, nome)
            if nome == "comparacao":
                self.assertIn("sqlite_autoindex_leituras_1", detalhes)
            print(f"\nPLANO {nome}: {detalhes}")

    def test_executor_pela_linha_de_comando(self):
        self.preencher()
        programa = str(Path(__file__).with_name("consultar_historico.py"))
        resultado = subprocess.run([sys.executable, programa, str(self.path), "contagem"],
                                   capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(resultado.stdout), [{"ciclos": 3, "leituras": 159}])
        plano = subprocess.run([sys.executable, programa, str(self.path), "comparacao", "--plano"],
                               capture_output=True, text=True, check=True)
        self.assertTrue(any("leituras_tag_coleta" in item["detail"] for item in json.loads(plano.stdout)))


@unittest.skipUnless(importlib.util.find_spec("asyncua") and importlib.util.find_spec("tep"),
                     "asyncua e tep são necessários")
class IntegracaoDinamicaTest(unittest.IsolatedAsyncioTestCase):
    async def test_simulador_avanca_e_consultas_leem_historico(self):
        from asyncua import Server, ua
        from tep import TEPSimulator
        from servidor_opc import criar_nos, executar_ciclo

        sim = TEPSimulator(backend="python", random_seed=1234)
        sim.initialize()
        server = Server()
        await server.init()
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        url = f"opc.tcp://127.0.0.1:{port}/tep/"
        server.set_endpoint(url)
        server.socket_address = ("127.0.0.1", port)
        server.set_security_policy([ua.SecurityPolicyType.NoSecurity])
        _, nos, legados = await criar_nos(server, sim)
        passos = []

        async def atualizar():
            while True:
                _, timestamp = await executar_ciclo(sim, nos, legados)
                passos.append(timestamp)
                await asyncio.sleep(0.1)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "simulacao.sqlite3"
            db = abrir_banco(path)
            try:
                async with server:
                    tarefa = asyncio.create_task(atualizar())
                    try:
                        with redirect_stdout(io.StringIO()):
                            await asyncio.wait_for(registrar(url, db, intervalo=0.3, limite_ciclos=6), timeout=90)
                    finally:
                        tarefa.cancel()
                        try:
                            await tarefa
                        except asyncio.CancelledError:
                            pass
                self.assertGreaterEqual(len(passos), 2)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM leituras").fetchone()[0], 318)
                with closing(abrir_leitura(path)) as leitor:
                    linhas = executar(leitor, "comparacao", limite=10)
                    self.assertEqual(len(linhas), 6)
                    valores = [linha["pressao_kpa_g"] for linha in linhas]
                    temperaturas = [linha["temperatura_c"] for linha in linhas]
                    self.assertGreater(len(set(valores)), 1)
                    self.assertGreater(len(set(temperaturas)), 1)
                    fontes = db.execute("SELECT COUNT(DISTINCT source_timestamp) FROM leituras WHERE tag_id='XMEAS(7)'").fetchone()[0]
                    coletas = db.execute("SELECT COUNT(DISTINCT coleta_utc) FROM leituras WHERE tag_id='XMEAS(7)'").fetchone()[0]
                    self.assertGreater(fontes, 1)
                    self.assertEqual(coletas, 6)
                    print(f"\nSimulação local: {len(passos)} passos, 6 ciclos, 318 leituras; "
                          f"pressão/temperatura variaram em {len(set(valores))}/{len(set(temperaturas))} valores; "
                          f"pressão teve {fontes} timestamps de publicação.")
                    print("Exemplo de comparação simulada:", linhas[0])
                    agregados = executar(leitor, "resumo_minuto", tag="XMEAS(7)")
                    self.assertGreaterEqual(sum(linha["amostras"] for linha in agregados), 1)
                    print("Exemplo de resumo de pressão simulado:", agregados[0])
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()

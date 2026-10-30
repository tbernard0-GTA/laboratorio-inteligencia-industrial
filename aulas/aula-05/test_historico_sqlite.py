import asyncio
from contextlib import closing, redirect_stdout
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import importlib.util
import io
import json
from pathlib import Path
import socket
import sqlite3
import statistics
import tempfile
import unittest

from catalogo_tags import CATALOGO
from historico_sqlite import abrir_banco, gravar_ciclo, registrar


@dataclass(frozen=True)
class LeituraTeste:
    identificador: str
    valor: object
    source_timestamp: object
    coleta_utc: object
    status_code: object
    qualidade: str


@dataclass(frozen=True)
class CicloTeste:
    leituras: tuple
    duracao_segundos: float = 0.0


def ciclo_exemplo():
    agora = datetime(2026, 1, 2, tzinfo=timezone.utc)
    return CicloTeste(tuple(LeituraTeste(tag.identificador, 42.0, agora, agora, 0, "Good") for tag in CATALOGO))


class HistoricoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "teste.sqlite3"
        self.db = abrir_banco(self.path)
        self.addCleanup(self.db.close)

    def test_esquema_catalogo_wal_foreign_keys_e_reabertura(self):
        self.assertEqual(self.db.execute("SELECT count(*) FROM tags").fetchone()[0], 53)
        self.assertEqual(set(self.db.execute("SELECT identificador, categoria, indice, descricao, unidade FROM tags")),
                         {(t.identificador, t.categoria, t.indice, t.descricao, t.unidade) for t in CATALOGO})
        self.assertEqual(self.db.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        self.assertEqual(self.db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertEqual(self.db.execute("PRAGMA busy_timeout").fetchone()[0], 5000)
        gravar_ciclo(self.db, "ciclo-1", ciclo_exemplo())
        self.db.close()
        self.db = abrir_banco(self.path)
        self.addCleanup(self.db.close)
        self.assertEqual(self.db.execute("SELECT count(*) FROM leituras").fetchone()[0], 53)
        self.assertEqual(self.db.execute("SELECT count(*) FROM tags").fetchone()[0], 53)

    def test_ciclo_completo_idempotencia_e_amostras_iguais(self):
        ciclo = ciclo_exemplo()
        self.assertTrue(gravar_ciclo(self.db, "primeiro", ciclo)[0])
        self.assertFalse(gravar_ciclo(self.db, "primeiro", ciclo)[0])
        self.assertTrue(gravar_ciclo(self.db, "segundo", ciclo)[0])
        self.assertEqual(self.db.execute("SELECT count(*) FROM leituras").fetchone()[0], 106)
        linhas = self.db.execute("SELECT valor, source_timestamp FROM leituras WHERE tag_id='XMEAS(1)' ORDER BY ciclo_id").fetchall()
        self.assertEqual(linhas[0], linhas[1])
        modificado = CicloTeste((replace(ciclo.leituras[0], valor=7.0), *ciclo.leituras[1:]))
        with self.assertRaises(ValueError):
            gravar_ciclo(self.db, "primeiro", modificado)
        self.assertEqual(self.db.execute("SELECT count(*) FROM leituras").fetchone()[0], 106)

    def test_rollback_falha_durante_insercao(self):
        self.db.execute("CREATE TRIGGER falha BEFORE INSERT ON leituras WHEN NEW.tag_id='XMEAS(10)' BEGIN SELECT RAISE(ABORT, 'falha de teste'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            gravar_ciclo(self.db, "falha", ciclo_exemplo())
        self.assertEqual(self.db.execute("SELECT count(*) FROM ciclos").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT count(*) FROM leituras").fetchone()[0], 0)

    def test_null_nan_e_qualidades(self):
        ciclo = ciclo_exemplo()
        items = list(ciclo.leituras)
        items[0] = replace(items[0], valor=None, source_timestamp=None)
        items[1] = replace(items[1], valor=float("nan"))
        items[2] = replace(items[2], valor=7.5, status_code=0x80000000, qualidade="Bad")
        items[3] = replace(items[3], valor=8.5, status_code=0x40000000, qualidade="Uncertain")
        items[4] = replace(items[4], status_code=None, qualidade="Desconhecida")
        items[5] = replace(items[5], valor=True)
        items[6] = replace(items[6], source_timestamp=None)
        gravar_ciclo(self.db, "qualidade", CicloTeste(tuple(items)))
        rows = {row[0]: row[1:] for row in self.db.execute("SELECT tag_id, valor, source_timestamp, status_code, qualidade, validade FROM leituras")}
        self.assertEqual(rows["XMEAS(1)"], (None, None, 0, "Good", "valor_invalido"))
        self.assertIsNone(rows["XMEAS(2)"][0])
        self.assertEqual(rows["XMEAS(3)"][0], 7.5)
        self.assertEqual(rows["XMEAS(3)"][-2:], ("Bad", "qualidade_nao_good"))
        self.assertEqual(rows["XMEAS(4)"][-2:], ("Uncertain", "qualidade_nao_good"))
        self.assertEqual(rows["XMEAS(5)"][-2:], ("Desconhecida", "qualidade_nao_good"))
        self.assertIsNone(rows["XMEAS(6)"][0])
        self.assertEqual(rows["XMEAS(7)"][-1], "source_timestamp_ausente")

    def test_leitor_concorrente_enquanto_ciclo_esta_em_transacao(self):
        gravar_ciclo(self.db, "antigo", ciclo_exemplo())
        with closing(sqlite3.connect(self.path, timeout=1)) as leitor:
            vistos = []
            def consultar():
                vistos.append(leitor.execute("SELECT count(*) FROM leituras").fetchone()[0])
                return 0
            self.db.create_function("observar_leitor", 0, consultar)
            self.db.execute("CREATE TRIGGER concorrencia AFTER INSERT ON leituras WHEN NEW.tag_id='XMEAS(10)' BEGIN SELECT observar_leitor(); END")
            gravar_ciclo(self.db, "novo", ciclo_exemplo())
            self.assertEqual(vistos, [53])
            self.assertEqual(leitor.execute("SELECT count(*) FROM leituras").fetchone()[0], 106)

    def test_rejeita_ciclo_incompleto_e_banco_alheio(self):
        with self.assertRaises(ValueError):
            gravar_ciclo(self.db, "incompleto", CicloTeste(ciclo_exemplo().leituras[:-1]))
        outra = Path(self.tmp.name) / "outro.sqlite3"
        with closing(sqlite3.connect(outra)) as db:
            db.execute("CREATE TABLE dados (valor INTEGER)")
            db.commit()
        with self.assertRaises(ValueError):
            abrir_banco(outra)
        with closing(sqlite3.connect(outra)) as db:
            self.assertEqual(db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(), [("dados",)])


@unittest.skipUnless(importlib.util.find_spec("asyncua") and importlib.util.find_spec("tep"), "asyncua e tep são necessários")
class HistoricoIntegracaoTest(unittest.IsolatedAsyncioTestCase):
    async def test_tep_opc_coletor_sqlite_e_reinicio(self):
        from asyncua import Server, ua
        from tep import TEPSimulator
        from servidor_opc import criar_nos, executar_ciclo

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
        _, nos, legadas = await criar_nos(server, sim)
        valores, _ = await executar_ciclo(sim, nos, legadas)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "historico_teste.sqlite3"
            saida = io.StringIO()
            async with server:
                db = abrir_banco(path)
                try:
                    with redirect_stdout(saida):
                        await asyncio.wait_for(registrar(url, db, intervalo=0.1, limite_ciclos=3), timeout=60)
                finally:
                    db.close()
                db = abrir_banco(path)
                try:
                    with redirect_stdout(saida):
                        await asyncio.wait_for(registrar(url, db, intervalo=0.1, limite_ciclos=2), timeout=60)
                    self.assertEqual(db.execute("SELECT count(*) FROM ciclos").fetchone()[0], 5)
                    self.assertEqual(db.execute("SELECT count(*) FROM leituras").fetchone()[0], 265)
                    rows = db.execute("SELECT tag_id, valor, qualidade, validade, source_timestamp FROM leituras").fetchall()
                    for tag, valor, qualidade, validade, source in rows:
                        self.assertEqual(valor, valores[tag])
                        self.assertEqual((qualidade, validade), ("Good", "valido"))
                        self.assertIsNotNone(source)
                finally:
                    db.close()
            medicoes = [json.loads(linha) for linha in saida.getvalue().splitlines()]
            self.assertEqual(len(medicoes), 5)
            tamanho = path.stat().st_size
            print("\nExperimento: 5 ciclos, 265 registros, SQLite final=" + str(tamanho) + " bytes; " +
                  ", ".join(f"{nome}_médio={statistics.mean(m[nome + '_segundos'] for m in medicoes)*1000:.2f} ms"
                            for nome in ("leitura", "gravacao", "total")), flush=True)
            print("Duração dos ciclos (ms): " + ", ".join(f"{m['total_segundos']*1000:.2f}" for m in medicoes), flush=True)


if __name__ == "__main__":
    unittest.main()

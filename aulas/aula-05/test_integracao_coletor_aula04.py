"""Integração local: servidor da Aula 5 e coletor original da Aula 4."""

from datetime import datetime
from contextlib import closing
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

RAIZ = Path(__file__).resolve().parents[2]
AULA04 = RAIZ / "aulas" / "aula-04"
AULA05 = RAIZ / "aulas" / "aula-05"
REVISAO_TEP = "9a6c8e5fcef4a2850778704e7793c87b0a187005"
SINAIS = {"Pressao": "kPa(g)", "Nivel": "%", "Temperatura": "C"}


def parar(processo):
    if processo.poll() is None:
        processo.terminate()
        try:
            processo.wait(timeout=10)
        except subprocess.TimeoutExpired:
            processo.kill()
            processo.wait(timeout=10)


@unittest.skipUnless(importlib.util.find_spec("asyncua") and importlib.util.find_spec("tep"),
                     "asyncua e tep são necessários para a integração")
@unittest.skipUnless(os.name == "posix" and Path("/data").is_dir(),
                     "a integração precisa de /data temporário em ambiente POSIX isolado")
class ColetorAula04Test(unittest.TestCase):
    def test_servidor_aula05_e_coletor_original(self):
        from asyncua import ua

        # Falha de forma explícita se o ambiente não comprovar a revisão exigida.
        direct_url = importlib.metadata.distribution("tep").read_text("direct_url.json")
        self.assertIsNotNone(direct_url, "instalação do TEP sem identificação da revisão")
        self.assertEqual(json.loads(direct_url)["vcs_info"]["commit_id"], REVISAO_TEP)
        self.assertEqual(importlib.metadata.version("asyncua"), "2.1.0")

        with tempfile.TemporaryDirectory(prefix="teste-aula05-", dir="/data") as tmp:
            diretorio = Path(tmp)
            banco = diretorio / "coleta-temporaria.sqlite3"
            # O sistema escolhe uma porta livre para o servidor de teste.
            with socket.socket() as reserva:
                reserva.bind(("127.0.0.1", 0))
                porta = reserva.getsockname()[1]
            url = f"opc.tcp://127.0.0.1:{porta}/tep/"
            ambiente = os.environ.copy()
            ambiente.update(OPC_UA_BIND_HOST="127.0.0.1", OPC_UA_ADVERTISE_HOST="127.0.0.1",
                            OPC_UA_PORT=str(porta), OPC_UA_URL=url, SQLITE_PATH=str(banco),
                            PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1")
            with (diretorio / "servidor.log").open("w+", encoding="utf-8") as log_servidor, \
                 (diretorio / "coletor.log").open("w+", encoding="utf-8") as log_coletor:
                servidor = subprocess.Popen([sys.executable, str(AULA05 / "servidor_opc.py")],
                                             cwd=AULA05, env=ambiente, stdout=log_servidor,
                                             stderr=subprocess.STDOUT)
                self.addCleanup(parar, servidor)
                coletor = None
                try:
                    limite = time.monotonic() + 90
                    while True:
                        if servidor.poll() is not None:
                            self.fail("Servidor encerrou antes de aceitar conexões")
                        try:
                            with socket.create_connection(("127.0.0.1", porta), timeout=0.5):
                                break
                        except OSError:
                            if time.monotonic() >= limite:
                                self.fail("Servidor não iniciou dentro de 90 segundos")
                            time.sleep(0.2)

                    coletor = subprocess.Popen([sys.executable, str(AULA04 / "coletor.py")],
                                               cwd=AULA04, env=ambiente, stdout=log_coletor,
                                               stderr=subprocess.STDOUT)
                    self.addCleanup(parar, coletor)
                    limite = time.monotonic() + 90
                    while True:
                        if servidor.poll() is not None or coletor.poll() is not None:
                            self.fail("Servidor ou coletor encerrou durante a coleta")
                        if banco.exists():
                            try:
                                with closing(sqlite3.connect(f"{banco.as_uri()}?mode=ro", uri=True)) as db:
                                    contagens = dict(db.execute("SELECT sinal, count(*) FROM leituras GROUP BY sinal"))
                                if all(contagens.get(sinal, 0) >= 2 for sinal in SINAIS):
                                    break
                            except sqlite3.OperationalError:
                                pass  # Banco ou tabela ainda em inicialização.
                        if time.monotonic() >= limite:
                            self.fail("Não houve duas amostras persistidas para cada sinal em 90 segundos")
                        time.sleep(0.2)
                except Exception:
                    log_servidor.flush()
                    log_coletor.flush()
                    log_servidor.seek(0)
                    log_coletor.seek(0)
                    print("\nServidor:\n", log_servidor.read(), "\nColetor:\n", log_coletor.read(), file=sys.stderr)
                    raise
                finally:
                    if coletor is not None:
                        parar(coletor)
                    parar(servidor)

            # Reabre o banco produzido pelo processo real, sem usar banco de campo.
            with closing(sqlite3.connect(banco)) as db:
                colunas = [linha[1] for linha in db.execute("PRAGMA table_info(leituras)")]
                self.assertEqual(colunas, ["id", "sinal", "valor", "unidade", "source_timestamp",
                                           "coleta_utc", "status_code", "qualidade", "validade"])
                self.assertEqual(db.execute("PRAGMA journal_mode").fetchone()[0], "wal")
                self.assertIn("amostra_origem", [linha[1] for linha in db.execute("PRAGMA index_list(leituras)")])
                linhas = db.execute("SELECT sinal, valor, unidade, source_timestamp, coleta_utc, "
                                    "status_code, qualidade, validade FROM leituras ORDER BY id").fetchall()
                self.assertEqual({linha[0] for linha in linhas}, set(SINAIS))
                for sinal, valor, unidade, source, coleta, status, qualidade, validade in linhas:
                    self.assertTrue(isinstance(valor, (int, float)) and math.isfinite(valor))
                    self.assertEqual(unidade, SINAIS[sinal])
                    self.assertEqual((status, qualidade, validade), (0, "Good", "valido"))
                    self.assertIsNotNone(datetime.fromisoformat(source).utcoffset())
                    self.assertIsNotNone(datetime.fromisoformat(coleta).utcoffset())
                for sinal in SINAIS:
                    fontes = [linha[3] for linha in linhas if linha[0] == sinal]
                    self.assertGreaterEqual(len(fontes), 2)
                    self.assertEqual(len(fontes), len(set(fontes)))

                # Reapresenta uma amostra real pelo gravar original: não deve duplicar.
                spec = importlib.util.spec_from_file_location("coletor_aula04_original", AULA04 / "coletor.py")
                modulo = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(modulo)
                sinal, valor, unidade, source, coleta, status, _, _ = linhas[0]
                dado = ua.DataValue(Value=ua.Variant(valor, ua.VariantType.Double),
                                    SourceTimestamp=datetime.fromisoformat(source),
                                    StatusCode=ua.StatusCode(status))
                modulo.gravar(db, sinal, unidade, dado, datetime.fromisoformat(coleta))
                self.assertEqual(db.execute("SELECT count(*) FROM leituras").fetchone()[0], len(linhas))


if __name__ == "__main__":
    unittest.main()

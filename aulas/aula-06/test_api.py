"""Valida API e integração local, sem acesso ao banco do laboratório."""
from contextlib import closing
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import time
import unittest
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from consultar_historico import abrir_leitura, executar
from catalogo_tags import CATALOGO
from historico_sqlite import abrir_banco, gravar_ciclo


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.temp.name) / "historico.sqlite3"
        cls.writer = abrir_banco(cls.db_path)
        agora = datetime.now(timezone.utc) - timedelta(minutes=1)
        for i in range(12):
            instante = agora + timedelta(seconds=i) if i else agora - timedelta(days=3)
            leituras = tuple(SimpleNamespace(identificador=t.identificador,
                valor=None if i == 11 and t.identificador == "XMEAS(9)" else float(i),
                source_timestamp=instante, coleta_utc=instante, status_code=0,
                qualidade="Good") for t in CATALOGO)
            gravar_ciclo(cls.writer, f"ciclo-{i}", SimpleNamespace(leituras=leituras))
        env = dict(os.environ, BANCO_HISTORICO=str(cls.db_path))
        cls.proc = subprocess.Popen(["python", "-m", "uvicorn", "main:app", "--app-dir", "/opt/api", "--host", "127.0.0.1", "--port", "18765"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
        for _ in range(300):
            try:
                with urlopen("http://127.0.0.1:18765/health", timeout=1):
                    return
            except (URLError, TimeoutError):
                if cls.proc.poll() is not None:
                    raise RuntimeError("Uvicorn terminou antes de iniciar")
                time.sleep(.2)
        cls.proc.terminate()
        cls.proc.wait(timeout=10)
        raise RuntimeError("Uvicorn não iniciou")

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(timeout=10)
        cls.writer.close()
        cls.temp.cleanup()

    def test_health_docs_e_openapi(self):
        with urlopen("http://127.0.0.1:18765/health") as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(json.load(r), {"status": "ok", "service": "iilab-api", "version": "0.1.0"})
        with urlopen("http://127.0.0.1:18765/docs") as r:
            self.assertEqual(r.status, 200)
        with urlopen("http://127.0.0.1:18765/openapi.json") as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(set(json.load(r)["paths"]), {"/health", "/api/v1/tags", "/api/v1/historico"})


    def test_tags_retorna_catalogo_serializado(self):
        with closing(abrir_leitura(self.db_path)) as db:
            esperado = executar(db, "tags")
        with urlopen("http://127.0.0.1:18765/api/v1/tags") as r:
            self.assertEqual(r.status, 200)
            tags = json.load(r)
        self.assertEqual(len(tags), 53)
        self.assertEqual(tags, esperado)
        self.assertEqual(set(tags[0]), {"identificador", "categoria", "indice", "descricao", "unidade"})
        self.assertEqual(tags[0]["identificador"], "XMEAS(1)")

    def test_banco_indisponivel_nao_expoe_caminho(self):
        caminho = Path(self.temp.name) / "ausente.sqlite3"
        env = dict(os.environ, BANCO_HISTORICO=str(caminho))
        proc = subprocess.Popen(["python", "-m", "uvicorn", "main:app", "--app-dir", "/opt/api", "--host", "127.0.0.1", "--port", "18766"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
        try:
            for _ in range(300):
                try:
                    with urlopen("http://127.0.0.1:18766/health", timeout=1):
                        break
                except (URLError, TimeoutError):
                    if proc.poll() is not None:
                        self.fail("Uvicorn terminou antes de iniciar")
                    time.sleep(.2)
            else:
                self.fail("Uvicorn não iniciou")
            with self.assertRaises(HTTPError) as erro:
                urlopen("http://127.0.0.1:18766/api/v1/tags")
            self.assertEqual(erro.exception.code, 503)
            self.assertEqual(json.load(erro.exception), {"detail": "Histórico indisponível"})
            with self.assertRaises(HTTPError) as erro:
                urlopen("http://127.0.0.1:18766/api/v1/historico?" + urlencode({"tag": "XMEAS(9)"}))
            self.assertEqual(erro.exception.code, 503)
            self.assertEqual(json.load(erro.exception), {"detail": "Histórico indisponível"})
            self.assertFalse(caminho.exists())
            with sqlite3.connect(caminho) as db:
                db.execute("CREATE TABLE outra (id INTEGER)")
            with self.assertRaises(HTTPError) as erro:
                urlopen("http://127.0.0.1:18766/api/v1/historico?" + urlencode({"tag": "XMEAS(9)"}))
            self.assertEqual(erro.exception.code, 503)
            self.assertEqual(json.load(erro.exception), {"detail": "Histórico indisponível"})
        finally:
            proc.terminate()
            proc.wait(timeout=10)

    def test_historico_ordenacao_limites_e_null(self):
        base = "http://127.0.0.1:18765/api/v1/historico?"
        def consultar(**params):
            with urlopen(base + urlencode(params)) as resposta:
                self.assertEqual(resposta.status, 200)
                return json.load(resposta)
        padrao = consultar(tag="XMEAS(9)")
        self.assertEqual(len(padrao), 10)
        self.assertEqual(len(consultar(tag="XMEAS(9)", limite=1)), 1)
        todos = consultar(tag="XMEAS(9)", limite=200)
        self.assertEqual(len(todos), 12)
        self.assertEqual(todos[0]["ciclo_id"], "ciclo-11")
        self.assertEqual(todos[-1]["ciclo_id"], "ciclo-0")
        self.assertIsNone(todos[0]["valor"])
        self.assertEqual(todos[0]["validade"], "valor_invalido")
        self.assertEqual(set(todos[0]), {"ciclo_id", "tag_id", "valor", "source_timestamp", "coleta_utc", "status_code", "qualidade", "validade"})
        self.assertEqual([row["coleta_utc"] for row in todos], sorted((row["coleta_utc"] for row in todos), reverse=True))
        self.assertEqual(todos[1]["qualidade"], "Good")
        self.assertEqual(todos[1]["valor"], 10.0)
        for params, status in [({"tag": "NAO_EXISTE"}, 404), ({}, 422),
                               ({"tag": "XMEAS(9)", "limite": 0}, 422),
                               ({"tag": "XMEAS(9)", "limite": 201}, 422),
                               ({"tag": "XMEAS(9)", "limite": "texto"}, 422)]:
            with self.subTest(params=params), self.assertRaises(HTTPError) as erro:
                urlopen(base + urlencode(params))
            self.assertEqual(erro.exception.code, status)


class HistoricoTest(unittest.TestCase):
    def test_leitura_wal_schema_e_ausencia(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "historico.sqlite3"
            with closing(abrir_banco(path)) as writer:
                self.assertEqual(writer.execute("PRAGMA journal_mode").fetchone()[0], "wal")
                with closing(abrir_leitura(path)) as reader:
                    self.assertEqual(len(executar(reader, "tags")), 53)
                    self.assertEqual(executar(reader, "contagem"), [{"ciclos": 0, "leituras": 0}])
                    with self.assertRaises(sqlite3.OperationalError):
                        reader.execute("DELETE FROM tags")
                with self.assertRaises(sqlite3.ProgrammingError):
                    reader.execute("SELECT 1")
            missing = Path(d) / "inexistente.sqlite3"
            with self.assertRaises(sqlite3.OperationalError):
                abrir_leitura(missing)
            self.assertFalse(missing.exists())
            other = Path(d) / "outro.sqlite3"
            with sqlite3.connect(other) as db:
                db.execute("CREATE TABLE x (id INTEGER)")
            with self.assertRaises(ValueError):
                abrir_leitura(other)


if __name__ == "__main__":
    unittest.main(verbosity=2)

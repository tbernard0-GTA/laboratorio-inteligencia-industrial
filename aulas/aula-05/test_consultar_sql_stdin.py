from pathlib import Path
import sqlite3
import tempfile
import unittest

from consultar_sql_stdin import consultar
from historico_sqlite import abrir_banco


class ConsultaStdinTest(unittest.TestCase):
    def test_select_e_escrita_recusada(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / "teste.sqlite3"
            db = abrir_banco(caminho)
            db.close()
            self.assertEqual(consultar(caminho, "SELECT count(*) AS total FROM tags"), [{"total": 53}])
            for sql in ("DELETE FROM tags", "ATTACH DATABASE ':memory:' AS outro", "PRAGMA query_only=OFF"):
                with self.subTest(sql=sql), self.assertRaises(sqlite3.DatabaseError):
                    consultar(caminho, sql)


if __name__ == "__main__":
    unittest.main()

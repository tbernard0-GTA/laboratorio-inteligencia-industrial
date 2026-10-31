from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import healthcheck_aula05
from historico_sqlite import abrir_banco, gravar_ciclo
from test_historico_sqlite import CicloTeste, ciclo_exemplo


class HealthHistoricoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "historico.sqlite3"
        self.db = abrir_banco(self.path)
        self.addCleanup(self.db.close)

    def verificar(self):
        with patch.object(healthcheck_aula05, "Path", return_value=self.path):
            healthcheck_aula05.verificar_historico()

    def ciclo(self, horario, *, bad=False):
        itens = [replace(x, coleta_utc=horario, source_timestamp=horario) for x in ciclo_exemplo().leituras]
        if bad:
            itens[0] = replace(itens[0], qualidade="Bad", status_code=0x80000000)
        return CicloTeste(tuple(itens))

    def test_vazio_completo_e_incompleto(self):
        with self.assertRaises(RuntimeError):
            self.verificar()
        gravar_ciclo(self.db, "atual", self.ciclo(datetime.now(timezone.utc)))
        self.verificar()
        self.db.execute("DELETE FROM leituras WHERE ciclo_id='atual' AND tag_id='XMV(12)'")
        with self.assertRaises(RuntimeError):
            self.verificar()

    def test_ciclo_bad_e_antigo(self):
        agora = datetime.now(timezone.utc)
        gravar_ciclo(self.db, "antigo", self.ciclo(agora - timedelta(seconds=65)))
        with self.assertRaises(RuntimeError):
            self.verificar()
        gravar_ciclo(self.db, "ruim", self.ciclo(agora, bad=True))
        with self.assertRaises(RuntimeError):
            self.verificar()


if __name__ == "__main__":
    unittest.main()

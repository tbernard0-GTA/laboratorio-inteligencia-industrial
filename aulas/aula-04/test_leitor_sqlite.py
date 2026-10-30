"""Testes com banco sintético; não são amostras do processo."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import tempfile
import unittest

from leitor_sqlite import abrir, estado, ler


class LeitorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'teste.sqlite3'
        self.writer = sqlite3.connect(self.path)
        self.writer.execute('PRAGMA journal_mode=WAL')
        self.writer.execute('CREATE TABLE leituras (id INTEGER PRIMARY KEY, sinal TEXT, valor REAL, unidade TEXT, source_timestamp TEXT, coleta_utc TEXT, status_code INTEGER, qualidade TEXT, validade TEXT)')
        self.writer.execute('CREATE UNIQUE INDEX amostra_origem ON leituras(sinal,source_timestamp) WHERE source_timestamp IS NOT NULL')
        self.writer.commit()
        self.agora = datetime.now(timezone.utc)

    def tearDown(self):
        self.writer.close()
        self.tmp.cleanup()

    def inserir(self, sinal='Pressao', valor=42.0, quality='Good', valid='valido', source=None, coleta=None, status=0):
        t = self.agora.isoformat(timespec='microseconds')
        self.writer.execute('INSERT INTO leituras(sinal,valor,unidade,source_timestamp,coleta_utc,status_code,qualidade,validade) VALUES (?,?,?,?,?,?,?,?)', (sinal, valor, 'kPa(g)', source if source is not None else t, coleta if coleta is not None else t, status, quality, valid))
        self.writer.commit()

    def test_vazio_e_ausente(self):
        atuais, historico, _ = ler(self.path, 5, self.agora)
        self.assertEqual(estado(atuais['Pressao'], self.agora), 'Sem dados')
        self.assertEqual(historico['Pressao'], [])
        with self.assertRaises(FileNotFoundError):
            abrir(self.path.parent / 'nao-existe.sqlite3')

    def test_concorrencia_qualidade_e_ultimo_conhecido(self):
        self.inserir()
        self.inserir(valor=None, quality='Bad', valid='valor_invalido', status=0x80000000, source=(self.agora + timedelta(seconds=1)).isoformat())
        atuais, historico, conhecidos = ler(self.path, 5, self.agora)
        self.assertEqual(estado(atuais['Pressao'], self.agora), 'Qualidade ruim ou valor inválido')
        self.assertEqual(conhecidos['Pressao']['valor'], 42.0)
        self.assertEqual(len(historico['Pressao']), 2)
        db = abrir(self.path)
        with self.assertRaises(sqlite3.OperationalError):
            db.execute('DELETE FROM leituras')
        db.close()

    def test_desatualizado_e_timestamp_ausente(self):
        self.inserir(source=(self.agora-timedelta(seconds=11)).isoformat())
        atuais, _, _ = ler(self.path, 5, self.agora)
        self.assertEqual(estado(atuais['Pressao'], self.agora), 'Desatualizado')
        row = dict(atuais['Pressao'])
        row['source_timestamp'] = None
        self.assertEqual(estado(row, self.agora), 'Horário de origem indisponível')

    def test_esquema_incorreto(self):
        self.writer.execute('DROP TABLE leituras')
        self.writer.commit()
        with self.assertRaises(sqlite3.OperationalError):
            ler(self.path, 5, self.agora)


if __name__ == '__main__':
    unittest.main()

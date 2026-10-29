"""Testes locais com dados sintéticos; não representam coleta do Pi."""
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from asyncua import Server, ua
import coletor


class BancoTest(unittest.TestCase):
    def test_qualidade_duplicados_e_persistencia(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(Path, 'is_relative_to', return_value=True):
            path = Path(tmp) / 'sintetico.sqlite3'
            db = coletor.abrir_banco(path)
            self.assertEqual(db.execute('PRAGMA journal_mode').fetchone()[0], 'wal')
            agora = datetime.now(timezone.utc)
            def dado(valor, source, status):
                return ua.DataValue(Value=ua.Variant(valor), SourceTimestamp=source,
                                    StatusCode=ua.StatusCode(status))
            good = dado(42.0, agora, ua.StatusCodes.Good)
            coletor.gravar(db, 'Pressao', 'kPa(g)', good, agora)
            coletor.gravar(db, 'Pressao', 'kPa(g)', good, agora)
            coletor.gravar(db, 'Pressao', 'kPa(g)', dado(42.0, agora + timedelta(seconds=1), ua.StatusCodes.Good), agora)
            coletor.gravar(db, 'Nivel', '%', dado(float('nan'), None, ua.StatusCodes.BadNoCommunication), agora)
            coletor.gravar(db, 'Nivel', '%', dado(3.0, None, ua.StatusCodes.Uncertain), agora)
            db.close()
            db = coletor.abrir_banco(path)
            rows = db.execute('SELECT sinal, valor, source_timestamp, status_code, qualidade FROM leituras ORDER BY id').fetchall()
            self.assertEqual(len(rows), 4)
            self.assertEqual(rows[2][1], None)
            self.assertIsNone(rows[2][2])
            self.assertEqual(rows[2][4], 'Bad')
            self.assertEqual(rows[3][4], 'Uncertain')
            db.close()


class ReconexaoTest(unittest.IsolatedAsyncioTestCase):
    async def test_pausa_antes_da_reconexao(self):
        with patch.object(coletor, 'coletar', new_callable=AsyncMock, side_effect=[ConnectionError('sintético'), asyncio.CancelledError]), patch.object(coletor.asyncio, 'sleep', new_callable=AsyncMock) as sleep:
            with self.assertRaises(asyncio.CancelledError):
                await coletor.executar(None, 'teste')
            sleep.assert_awaited_once_with(5)

    async def test_servidor_sintetico(self):
        import socket
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        server = Server()
        await server.init()
        url = f'opc.tcp://127.0.0.1:{port}/tep/'
        server.set_endpoint(url)
        ns = await server.register_namespace(coletor.NAMESPACE)
        reator = await server.nodes.objects.add_object(ns, 'Reator')
        for nome in coletor.SINAIS:
            await reator.add_variable(ns, nome, 42.0)
        with tempfile.TemporaryDirectory() as tmp, patch.object(Path, 'is_relative_to', return_value=True):
            db = coletor.abrir_banco(Path(tmp) / 'sintetico.sqlite3')
            async with server:
                task = asyncio.create_task(coletor.coletar(db, url))
                try:
                    for _ in range(50):
                        if db.execute('SELECT count(*) FROM leituras').fetchone()[0] >= 3:
                            break
                        await asyncio.sleep(.1)
                    self.assertEqual(db.execute('SELECT count(DISTINCT sinal) FROM leituras').fetchone()[0], 3)
                finally:
                    task.cancel()
                    with self.assertRaises(asyncio.CancelledError):
                        await task
            db.close()


if __name__ == '__main__':
    unittest.main()

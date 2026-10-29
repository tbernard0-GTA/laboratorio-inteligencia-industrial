"""Executa TEP REAL localmente (nao mock, nao Raspberry, nao Docker)."""
import asyncio
import os
from pathlib import Path
import subprocess
import socket
import sys
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'streamlit'))
from opc_client import read_once

async def main():
    # Nao aceite servidor preexistente como prova deste subprocesso.
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 4840))
    env = dict(os.environ, OPC_ADVERTISED_ENDPOINT='opc.tcp://127.0.0.1:4840/tep/', OPC_BIND_HOST='127.0.0.1')
    with subprocess.Popen([sys.executable, str(ROOT / 'servidor_opc.py')], env=env, stdout=subprocess.DEVNULL) as process:
        try:
            for _ in range(30):
                try:
                    if process.poll() is not None:
                        raise RuntimeError('Subprocesso TEP encerrou')
                    first = await read_once('opc.tcp://127.0.0.1:4840/tep/')
                    break
                except Exception:
                    if process.poll() is not None:
                        raise RuntimeError('Servidor encerrou')
                    await asyncio.sleep(1)
            else:
                raise RuntimeError('Servidor nao ficou pronto')
            await asyncio.sleep(2)
            second = await read_once('opc.tcp://127.0.0.1:4840/tep/')
            if process.poll() is not None:
                raise RuntimeError('Subprocesso TEP encerrou durante teste')
            for name in first['values']:
                assert second['values'][name]['timestamp'] > first['values'][name]['timestamp']
                assert second['values'][name]['quality'] == 'Good'
            assert any(first['values'][n]['value'] != second['values'][n]['value'] for n in first['values'])
            print('PASS: TEP real, 3 tags, unidades, Good, timestamps e valores avancando')
            print(second)
        finally:
            process.terminate()
            process.wait(timeout=10)

asyncio.run(main())

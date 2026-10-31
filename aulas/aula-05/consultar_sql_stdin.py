"""Executa uma consulta SQL enviada por stdin no banco ativo, somente leitura."""
from contextlib import closing
import json
import sqlite3
import sys

from consultar_historico import abrir_leitura


def consultar(caminho, sql):
    with closing(abrir_leitura(caminho)) as db:
        permitidos = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION,
                      sqlite3.SQLITE_RECURSIVE}
        db.set_authorizer(lambda acao, *_: sqlite3.SQLITE_OK if acao in permitidos else sqlite3.SQLITE_DENY)
        return [dict(linha) for linha in db.execute(sql)]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python consultar_sql_stdin.py BANCO < consulta.sql")
    print(json.dumps(consultar(sys.argv[1], sys.stdin.read()), ensure_ascii=False, indent=2))

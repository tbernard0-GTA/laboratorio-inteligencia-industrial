"""Executa consultas predefinidas do historiador da Aula 5 em modo somente leitura."""

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import sqlite3
from contextlib import closing

from catalogo_tags import CATALOGO
from historico_sqlite import APPLICATION_ID, SCHEMA_VERSION

ARQUIVO_SQL = Path(__file__).parent / "sql" / "consultas.sql"
CONSULTAS = {"tags", "contagem", "amostras", "temperatura_30min", "resumo_minuto", "comparacao", "anomalias"}


def carregar_consultas():
    texto = ARQUIVO_SQL.read_text(encoding="utf-8")
    partes = re.split(r"(?m)^-- consulta: ([a-z_0-9]+)\s*$", texto)
    resultado = dict(zip(partes[1::2], (parte.strip() for parte in partes[2::2])))
    if len(partes[1::2]) != len(CONSULTAS) or set(resultado) != CONSULTAS:
        raise ValueError("Arquivo de consultas inconsistente")
    return resultado


def abrir_leitura(caminho):
    """Não cria arquivo, não usa immutable e não modifica esquema nem dados."""
    uri = Path(caminho).resolve().as_uri() + "?mode=ro"
    db = sqlite3.connect(uri, uri=True, timeout=5)
    try:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        if (db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID or
                db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION):
            raise ValueError("Banco não é um historiador da Aula 5 na versão esperada")
        return db
    except BaseException:
        db.close()
        raise


def _horario(texto):
    try:
        data = datetime.fromisoformat(texto.replace("Z", "+00:00"))
        if data.tzinfo is None or data.utcoffset() is None:
            raise ValueError("fuso horário ausente")
        return data.astimezone(timezone.utc)
    except (ValueError, AttributeError) as exc:
        raise ValueError("Horário deve ser ISO 8601 com fuso, por exemplo 2026-10-30T12:00:00Z") from exc


def executar(db, nome, *, tag="XMEAS(9)", inicio=None, fim=None, limite=100, plano=False):
    if nome not in CONSULTAS:
        raise ValueError("Consulta não reconhecida")
    if tag not in {t.identificador for t in CATALOGO}:
        raise ValueError("Tag não consta no catálogo")
    if isinstance(limite, bool) or not isinstance(limite, int) or not 1 <= limite <= 10000:
        raise ValueError("Limite deve ser inteiro entre 1 e 10000")
    final = _horario(fim) if fim is not None else datetime.now(timezone.utc)
    inicial = _horario(inicio) if inicio is not None else final - timedelta(minutes=30 if nome == "temperatura_30min" else 1440)
    if inicial >= final:
        raise ValueError("Início deve anteceder fim")
    params = {"tag": tag, "inicio": inicial.isoformat(timespec="microseconds"),
              "fim": final.isoformat(timespec="microseconds"), "limite": limite}
    sql = carregar_consultas()[nome]
    if plano:
        sql = "EXPLAIN QUERY PLAN " + sql
    return [dict(linha) for linha in db.execute(sql, params)]


def main():
    parser = argparse.ArgumentParser(description="Consultas predefinidas do historiador da Aula 5")
    parser.add_argument("banco", help="caminho do banco SQLite da Aula 5")
    parser.add_argument("consulta", choices=sorted(CONSULTAS))
    parser.add_argument("--tag", default="XMEAS(9)")
    parser.add_argument("--inicio", help="data ISO 8601 com fuso, limite inclusivo")
    parser.add_argument("--fim", help="data ISO 8601 com fuso, limite exclusivo")
    parser.add_argument("--limite", type=int, default=100)
    parser.add_argument("--plano", action="store_true", help="exibe EXPLAIN QUERY PLAN")
    args = parser.parse_args()
    with closing(abrir_leitura(args.banco)) as db:
        resultado = executar(db, args.consulta, tag=args.tag, inicio=args.inicio,
                             fim=args.fim, limite=args.limite, plano=args.plano)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

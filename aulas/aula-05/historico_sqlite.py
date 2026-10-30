"""Historiador independente para os ciclos OPC UA da Aula 5."""

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import math
from numbers import Real
from pathlib import Path
import sqlite3
import time
from uuid import uuid4

from catalogo_tags import CATALOGO

APPLICATION_ID = 0x49494C35  # IIL5
SCHEMA_VERSION = 1


def _utc(valor):
    if valor is None:
        return None
    if not isinstance(valor, datetime) or valor.tzinfo is None or valor.utcoffset() is None:
        raise ValueError("timestamp deve conter fuso horário")
    return valor.astimezone(timezone.utc).isoformat(timespec="microseconds")


def abrir_banco(caminho):
    """Abre apenas banco novo ou identificado como historiador da Aula 5."""
    caminho = Path(caminho)
    if str(caminho) == ":memory:":
        raise ValueError("Use um arquivo SQLite independente, não :memory:")
    db = sqlite3.connect(caminho, timeout=5, isolation_level=None)
    try:
        db.execute("PRAGMA busy_timeout=5000")
        db.execute("PRAGMA foreign_keys=ON")
        app_id = db.execute("PRAGMA application_id").fetchone()[0]
        versao = db.execute("PRAGMA user_version").fetchone()[0]
        tabelas = db.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()[0]
        if (app_id == 0 and (tabelas or versao)) or app_id not in (0, APPLICATION_ID):
            raise ValueError("Banco não pertence ao historiador da Aula 5")
        if app_id == APPLICATION_ID and versao != SCHEMA_VERSION:
            raise ValueError("Versão do esquema incompatível")
        if db.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() != "wal":
            raise RuntimeError("SQLite não ativou WAL")
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute("CREATE TABLE IF NOT EXISTS tags (identificador TEXT PRIMARY KEY, categoria TEXT NOT NULL, indice INTEGER NOT NULL, descricao TEXT NOT NULL, unidade TEXT NOT NULL, UNIQUE(categoria, indice))")
            db.execute("CREATE TABLE IF NOT EXISTS ciclos (id TEXT PRIMARY KEY, coleta_utc TEXT NOT NULL, conteudo_sha256 TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS leituras (ciclo_id TEXT NOT NULL REFERENCES ciclos(id), tag_id TEXT NOT NULL REFERENCES tags(identificador), valor REAL, source_timestamp TEXT, coleta_utc TEXT NOT NULL, status_code INTEGER, qualidade TEXT NOT NULL CHECK(qualidade IN ('Good','Uncertain','Bad','Desconhecida')), validade TEXT NOT NULL CHECK(validade IN ('valido','valor_invalido','qualidade_nao_good','source_timestamp_ausente')), PRIMARY KEY(ciclo_id, tag_id))")
            db.execute("CREATE INDEX IF NOT EXISTS leituras_tag_coleta ON leituras(tag_id, coleta_utc)")
            db.execute("CREATE INDEX IF NOT EXISTS leituras_tag_origem ON leituras(tag_id, source_timestamp)")
            for tag in CATALOGO:
                db.execute("INSERT OR IGNORE INTO tags VALUES (?, ?, ?, ?, ?)",
                           (tag.identificador, tag.categoria, tag.indice, tag.descricao, tag.unidade))
            registrado = set(db.execute("SELECT identificador, categoria, indice, descricao, unidade FROM tags"))
            esperado = {(t.identificador, t.categoria, t.indice, t.descricao, t.unidade) for t in CATALOGO}
            if registrado != esperado:
                raise ValueError("Catálogo do banco incompatível; migração necessária")
            db.execute(f"PRAGMA application_id={APPLICATION_ID}")
            db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
            db.execute("COMMIT")
        except BaseException:
            db.execute("ROLLBACK")
            raise
        return db
    except BaseException:
        db.close()
        raise


def _linha(leitura):
    raw = leitura.valor
    valor = None
    if isinstance(raw, Real) and not isinstance(raw, bool):
        try:
            numero = float(raw)
            if math.isfinite(numero):
                valor = numero
        except (OverflowError, ValueError):
            pass
    qualidade = leitura.qualidade
    if qualidade not in ("Good", "Uncertain", "Bad", "Desconhecida"):
        raise ValueError("Qualidade desconhecida")
    if (leitura.status_code is None) != (qualidade == "Desconhecida"):
        raise ValueError("StatusCode e qualidade ausente inconsistentes")
    if leitura.status_code is not None:
        if not isinstance(leitura.status_code, int) or not 0 <= leitura.status_code <= 0xFFFFFFFF:
            raise ValueError("StatusCode inválido")
        bits = leitura.status_code & 0xC0000000
        esperada = "Good" if bits == 0 else "Uncertain" if bits == 0x40000000 else "Bad"
        if qualidade != esperada:
            raise ValueError("Qualidade não corresponde ao StatusCode")
    origem = _utc(leitura.source_timestamp)
    validade = ("valor_invalido" if valor is None else
                "qualidade_nao_good" if qualidade != "Good" else
                "source_timestamp_ausente" if origem is None else "valido")
    coleta = _utc(leitura.coleta_utc)
    if coleta is None:
        raise ValueError("Horário de coleta ausente")
    return (leitura.identificador, valor, origem, coleta,
            leitura.status_code, qualidade, validade)


def gravar_ciclo(db, ciclo_id, ciclo):
    """Grava 53 leituras atomicamente; repetir o mesmo ID e conteúdo é idempotente."""
    if not isinstance(ciclo_id, str) or not ciclo_id.strip():
        raise ValueError("Identificador de ciclo vazio")
    linhas = [_linha(leitura) for leitura in ciclo.leituras]
    ids = [linha[0] for linha in linhas]
    if len(ids) != 53 or set(ids) != {tag.identificador for tag in CATALOGO}:
        raise ValueError("Ciclo deve conter cada uma das 53 tags exatamente uma vez")
    linhas.sort(key=lambda linha: linha[0])
    conteudo = json.dumps(linhas, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    digest = hashlib.sha256(conteudo.encode("utf-8")).hexdigest()
    inicio = time.monotonic()
    db.execute("BEGIN IMMEDIATE")
    try:
        existente = db.execute("SELECT conteudo_sha256 FROM ciclos WHERE id=?", (ciclo_id,)).fetchone()
        if existente:
            if existente[0] != digest:
                raise ValueError("Identificador de ciclo já usado com conteúdo diferente")
            db.execute("COMMIT")
            return False, time.monotonic() - inicio
        db.execute("INSERT INTO ciclos VALUES (?, ?, ?)", (ciclo_id, linhas[0][3], digest))
        db.executemany("INSERT INTO leituras VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ((ciclo_id, *linha) for linha in linhas))
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise
    return True, time.monotonic() - inicio


async def registrar(url, db, intervalo=5.0, limite_ciclos=None):
    """Conecta pelo coletor existente; falhas SQLite interrompem a operação."""
    from coletor_opc import ciclos

    if not math.isfinite(intervalo) or intervalo <= 0:
        raise ValueError("intervalo deve ser finito e positivo")
    gerador = ciclos(url, intervalo=intervalo)
    total = 0
    try:
        async for ciclo in gerador:
            inicio_tratamento = time.monotonic()
            ciclo_id = str(uuid4())
            _, gravacao = gravar_ciclo(db, ciclo_id, ciclo)
            total_ciclo = ciclo.duracao_segundos + time.monotonic() - inicio_tratamento
            total += 1
            print(json.dumps({"ciclo_id": ciclo_id, "registros": len(ciclo.leituras),
                              "leitura_segundos": ciclo.duracao_segundos,
                              "gravacao_segundos": gravacao,
                              "total_segundos": total_ciclo}), flush=True)
            if limite_ciclos is not None and total >= limite_ciclos:
                return
    finally:
        await gerador.aclose()


def main():
    parser = argparse.ArgumentParser(description="Historiador SQLite independente da Aula 5")
    parser.add_argument("url", help="endpoint OPC UA")
    parser.add_argument("--banco", required=True, help="arquivo SQLite dedicado à Aula 5")
    parser.add_argument("--intervalo", type=float, default=5.0, help="intervalo alvo em segundos (padrão 5)")
    args = parser.parse_args()
    db = abrir_banco(args.banco)
    try:
        asyncio.run(registrar(args.url, db, args.intervalo))
    finally:
        db.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

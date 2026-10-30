"""Consultas limitadas e somente leitura do histórico do coletor."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3

SINAIS = {"Pressao": ("Pressão", "kPa(g)"), "Nivel": ("Nível", "%"), "Temperatura": ("Temperatura", "°C")}
COLUNAS = "id,sinal,valor,unidade,source_timestamp,coleta_utc,status_code,qualidade,validade"
LIMITE = 1200
ATRASO = 10


def abrir(path):
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Banco não encontrado: {path}")
    db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=5000")
    db.execute("PRAGMA query_only=ON")
    return db


def ler(path, minutos, agora=None):
    agora = agora or datetime.now(timezone.utc)
    inicio = (agora - timedelta(minutes=minutos)).isoformat(timespec="microseconds")
    db = abrir(path)
    try:
        atual, historico, conhecidos = {}, {}, {}
        for sinal in SINAIS:
            atual[sinal] = db.execute(f"SELECT {COLUNAS} FROM leituras WHERE sinal=? ORDER BY id DESC LIMIT 1", (sinal,)).fetchone()
            conhecidos[sinal] = db.execute(f"SELECT {COLUNAS} FROM leituras WHERE sinal=? AND valor IS NOT NULL AND validade=? AND qualidade=? ORDER BY id DESC LIMIT 1", (sinal, 'valido', 'Good')).fetchone()
            historico[sinal] = list(reversed(db.execute(f"SELECT {COLUNAS} FROM leituras WHERE sinal=? AND source_timestamp>=? ORDER BY source_timestamp DESC LIMIT ?", (sinal, inicio, LIMITE)).fetchall()))
        return atual, historico, conhecidos
    finally:
        db.close()


def estado(row, agora=None):
    if row is None:
        return "Sem dados"
    if row["qualidade"] != "Good" or row["status_code"] >> 30 != 0 or row["validade"] != "valido" or row["valor"] is None:
        return "Qualidade ruim ou valor inválido"
    agora = agora or datetime.now(timezone.utc)
    try:
        for campo in ("coleta_utc", "source_timestamp"):
            texto = row[campo]
            if not texto:
                return "Horário de origem indisponível"
            instante = datetime.fromisoformat(texto.replace("Z", "+00:00"))
            if instante.tzinfo is None:
                return "Horário inválido"
            idade = (agora - instante.astimezone(timezone.utc)).total_seconds()
            if idade < -ATRASO:
                return "Horário no futuro"
            if idade > ATRASO:
                return "Desatualizado"
    except (ValueError, TypeError, OverflowError):
        return "Horário inválido"
    return "Atual"

from contextlib import closing
import os
import sqlite3

from fastapi import FastAPI, HTTPException, Query
from catalogo_tags import CATALOGO
from consultar_historico import abrir_leitura, executar

app = FastAPI(title="Industrial Intelligence Lab API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "iilab-api", "version": "0.1.0"}


@app.get("/api/v1/tags")
def tags():
    """Lista o catálogo registrado no histórico, sem indicar atualidade das leituras."""
    try:
        with closing(abrir_leitura(os.environ.get("BANCO_HISTORICO", "/data/historico_aula05.sqlite3"))) as db:
            return executar(db, "tags")
    except (sqlite3.Error, OSError, ValueError):
        raise HTTPException(status_code=503, detail="Histórico indisponível") from None


@app.get("/api/v1/historico")
def historico(tag: str, limite: int = Query(default=10, ge=1, le=200)):
    """Retorna as últimas amostras armazenadas para uma tag do catálogo."""
    if tag not in {item.identificador for item in CATALOGO}:
        raise HTTPException(status_code=404, detail="Tag não encontrada")
    try:
        with closing(abrir_leitura(os.environ.get("BANCO_HISTORICO", "/data/historico_aula05.sqlite3"))) as db:
            return executar(db, "amostras", tag=tag, limite=limite,
                            inicio="0001-01-01T00:00:00+00:00",
                            fim="9999-12-31T23:59:59.999999+00:00")
    except (sqlite3.Error, OSError, ValueError):
        raise HTTPException(status_code=503, detail="Histórico indisponível") from None

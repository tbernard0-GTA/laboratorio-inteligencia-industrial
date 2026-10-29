"""Interface do histórico real; não se conecta ao servidor OPC UA."""
import os
import sqlite3
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from leitor_sqlite import SINAIS, estado, ler

st.set_page_config(page_title="Industrial Intelligence Lab", layout="wide")
st.title("Industrial Intelligence Lab")
st.caption("Reator · histórico OPC UA · horários em UTC")
janelas = {"5 minutos": 5, "15 minutos": 15, "1 hora": 60, "6 horas": 360}
janela = janelas[st.selectbox("Janela histórica", list(janelas), index=1)]


@st.fragment(run_every=3)
def painel():
    try:
        atuais, historicos, conhecidos = ler(os.environ.get("SQLITE_PATH", "/data/leituras.sqlite3"), janela)
    except (OSError, sqlite3.Error, ValueError) as exc:
        st.error(f"Não foi possível consultar o histórico. Confira o banco, permissões e coletor. Detalhe: {exc}")
        return

    agora = datetime.now(timezone.utc)
    colunas = st.columns(3)
    for coluna, (sinal, (rotulo, unidade)) in zip(colunas, SINAIS.items()):
        row = atuais[sinal]
        situacao = estado(row, agora)
        with coluna:
            valor = "—" if row is None or row["valor"] is None else f'{row["valor"]:.2f} {unidade}'
            st.metric(rotulo, valor, border=True)
            if situacao == "Atual":
                st.success("Atual · qualidade Good")
            else:
                st.warning(situacao + (f' · qualidade {row["qualidade"]}' if row else ""))
            if row:
                st.caption(f'Origem UTC: {row["source_timestamp"] or "indisponível"}')
                st.caption(f'Última coleta UTC: {row["coleta_utc"]}')
            conhecido = conhecidos[sinal]
            if situacao != "Atual" and conhecido:
                st.caption(f'Último valor conhecido com qualidade Good: {conhecido["valor"]:.2f} {unidade} · coleta {conhecido["coleta_utc"]}')
    st.divider()
    st.subheader("Tendências")
    st.caption("Até 1.200 amostras mais recentes por sinal. Apenas valores válidos e qualidade Good; horário de origem UTC.")
    for sinal, (rotulo, unidade) in SINAIS.items():
        boas = [r for r in historicos[sinal] if r["qualidade"] == "Good" and r["status_code"] >> 30 == 0 and r["validade"] == "valido" and r["valor"] is not None]
        st.markdown(f"**{rotulo} · {unidade}**")
        if boas:
            df = pd.DataFrame({"Horário UTC": pd.to_datetime([r["source_timestamp"] for r in boas], utc=True), rotulo: [r["valor"] for r in boas]}).set_index("Horário UTC")
            st.line_chart(df, height=180)
        else:
            st.info("Sem amostras válidas na janela selecionada.")


painel()

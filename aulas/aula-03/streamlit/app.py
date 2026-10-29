import os
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
from collector import Collector
from opc_client import TAGS

st.set_page_config(page_title="Laboratorio industrial | Aula 3", page_icon="🏭", layout="wide")
st.title("Laboratorio de inteligencia industrial")
st.caption("Aula 3 · TEP simulado → OPC UA real → Python → Streamlit · somente leitura")
endpoint = os.getenv("OPC_ENDPOINT", "opc.tcp://127.0.0.1:4840/tep/")

@st.cache_resource
def get_collector(url):
    return Collector(url)

@st.fragment(run_every="2s")
def dashboard():
    samples, error = get_collector(endpoint).snapshot()
    st.caption(f"Servidor: {endpoint}")
    if not samples:
        st.warning(error or "Aguardando dados")
        return
    last = samples[-1]
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(last["received_at"])).total_seconds()
    if error or age > 10:
        st.error(f"SEM DADOS ATUAIS · {error or 'Leitura desatualizada'}")
        st.caption(f"Ultima leitura preservada para diagnostico: {last['received_at']}; nao representa valor atual.")
    else:
        st.success("Conectado · qualidade Good · leituras atuais")
        for column, name in zip(st.columns(3), TAGS):
            value = last["values"][name]
            column.metric(f"{name} ({value['unit']})", f"{value['value']:.2f}")
            column.caption(f"Fonte UTC: {value['timestamp']}")
    st.subheader("Tendencias recentes — memoria limitada a 600 amostras")
    for name, column in zip(TAGS, st.columns(3)):
        frame = pd.DataFrame({"UTC": [datetime.fromisoformat(s["received_at"]) for s in samples], name: [s["values"][name]["value"] for s in samples]}).set_index("UTC")
        column.caption(f"{name} ({last['values'][name]['unit']})")
        column.line_chart(frame, height=190)
    st.caption("Sem persistencia: reiniciar o dashboard limpa as tendencias. Reiniciar TEP reinicia o modelo. Nenhum mock e usado por esta aplicacao.")

dashboard()

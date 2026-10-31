# Base local ARM64 verificada por ID antes do build; não baixa dependências.
FROM iilab-tep-opc:local

USER root
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python -m pip check && python -c "import importlib.metadata as m,json; assert m.version('numpy')=='2.2.6'; assert m.version('asyncua')=='2.1.0'; assert m.version('tep')=='2.5.0'; assert json.loads(m.distribution('tep').read_text('direct_url.json'))['vcs_info']['commit_id']=='9a6c8e5fcef4a2850778704e7793c87b0a187005'" \
    && mkdir -p /data && chown 10001:10001 /data
COPY catalogo_tags.py servidor_opc.py coletor_opc.py historico_sqlite.py consultar_historico.py consultar_sql_stdin.py healthcheck_aula05.py /app/
COPY sql/consultas.sql /app/sql/consultas.sql
USER 10001
CMD ["python", "/app/servidor_opc.py"]

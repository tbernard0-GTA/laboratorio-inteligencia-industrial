FROM python:3.12-slim-bookworm AS server-build
RUN apt-get update && apt-get install -y --no-install-recommends git build-essential pkg-config && rm -rf /var/lib/apt/lists/*
COPY docker/requirements-server.txt /tmp/requirements.txt
RUN python -m pip wheel --wheel-dir /wheels -r /tmp/requirements.txt

FROM python:3.12-slim-bookworm AS server
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY --from=server-build /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels tep numpy asyncua && rm -rf /wheels && useradd --uid 10001 --create-home app
COPY servidor_opc.py /app/
COPY streamlit/opc_client.py /app/
USER 10001
CMD ["python", "servidor_opc.py"]

FROM python:3.12-slim-bookworm AS dashboard
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY streamlit/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && useradd --uid 10001 --create-home app
COPY streamlit/ /app/
USER 10001
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]

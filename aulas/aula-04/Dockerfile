FROM python:3.13-slim-trixie AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential git pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements-servidor.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir --only-binary=:all: numpy==2.2.6 \
    && python -m pip install --no-cache-dir -r /tmp/requirements.txt \
    && python -m pip check

FROM python:3.13-slim-trixie AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin iilab
COPY --from=build /opt/venv /opt/venv
WORKDIR /app
COPY servidor_opc.py /app/servidor_opc.py
USER 10001
EXPOSE 4840/tcp
STOPSIGNAL SIGINT
CMD ["python", "servidor_opc.py"]

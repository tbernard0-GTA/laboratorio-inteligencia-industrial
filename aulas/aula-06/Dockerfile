FROM iilab-aula05:1
USER root
COPY requirements.txt /tmp/aula06-requirements.txt
RUN python -m pip install --no-cache-dir --only-binary=:all: -r /tmp/aula06-requirements.txt && python -m pip check
COPY api/ /opt/aula06-default/
COPY api/ /opt/api/
ENV PYTHONPATH=/app PYTHONDONTWRITEBYTECODE=1
WORKDIR /opt/aula06-default
USER 10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--app-dir", "/opt/api", "--host", "0.0.0.0", "--port", "8000"]

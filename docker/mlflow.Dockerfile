FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir mlflow

COPY mlflow/mlflow_config.yaml mlflow_config.yaml
COPY mlflow/tracking_server.py tracking_server.py

ENV MLFLOW_BACKEND_STORE_URI=sqlite:///mlflow/mlflow.db
ENV MLFLOW_ARTIFACT_ROOT=/mlflow_artifacts
ENV MLFLOW_PORT=5000

EXPOSE 5000

CMD [\"python\", \"tracking_server.py\"]

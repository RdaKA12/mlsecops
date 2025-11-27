# MLSecOps Modernization Plan

This plan outlines the steps to replace manual MLSecOps implementations with industry-standard tools selected from your list.

## Goal Description
The objective is to transition from manual, hard-coded security checks to a robust, tool-driven MLSecOps pipeline.
**Selected Tools:**
- **Red Teaming**: **Garak** (Vulnerability Scanning), **Promptfoo** (Behavioral Testing).
- **Guardrails**: **LLM Guard** (Input/Output Scanning).
- **Observability**: **OpenTelemetry** (Tracing/Metrics), **Prometheus** (Metrics Collection).
- **API Layer**: **FastAPI**.

## User Review Required
> [!IMPORTANT]
> **API Keys**: To use real models (OpenAI, Hugging Face), you will need valid API keys.
> **Docker**: Observability (Prometheus/Grafana) is best run via Docker. I will provide a `docker-compose.override.yml`.

## Proposed Changes

### 1. Dependencies & Environment
Add necessary tools to `requirements.txt`.

#### [MODIFY] [requirements.txt](file:///d:/Projects/mlsecops-project/requirements.txt)
- Add `langchain`, `langchain-openai`, `llm-guard`, `garak`, `promptfoo` (via npm/pip).
- Add `fastapi`, `uvicorn`.
- Add `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`, `prometheus-client`, `opentelemetry-exporter-prometheus`.

### 2. Model & Service Implementation (API + Observability)
Implement the FastAPI service with LangChain, Guardrails, and OpenTelemetry.

#### [NEW] [src/llm_service.py](file:///d:/Projects/mlsecops-project/src/llm_service.py)
- **FastAPI** app structure.
- **OpenTelemetry** instrumentation to trace requests.
- **Prometheus** exporter to expose metrics at `/metrics`.
- **LangChain** integration for the LLM logic.

### 3. Guardrails Integration (Korkuluklar)
Integrate **LLM Guard** directly into the API pipeline.

#### [MODIFY] [src/llm_service.py](file:///d:/Projects/mlsecops-project/src/llm_service.py)
- Apply `InputScanner` (e.g., Anonymize, PromptInjection) before LLM call.
- Apply `OutputScanner` (e.g., Deanonymize, NoRefusal) after LLM call.

### 4. Red Teaming (Kırmızı Takım)
Automate security testing.

#### [NEW] [security/garak_config.yaml](file:///d:/Projects/mlsecops-project/security/garak_config.yaml)
- Config to scan the local FastAPI endpoint.

#### [NEW] [promptfoo.yaml](file:///d:/Projects/mlsecops-project/promptfoo.yaml)
- Test cases for regression and specific failure modes.

### 5. Infrastructure (Docker)
Add observability stack.

#### [NEW] [docker-compose.override.yml](file:///d:/Projects/mlsecops-project/docker-compose.override.yml)
- Add services: `prometheus`, `grafana`.
- Configure Prometheus to scrape `host.docker.internal:8000` (or the service container).

## Verification Plan

### Automated Tests
- **Red Teaming**: Run `garak` and `promptfoo` against the running API.
- **Observability**: Verify metrics appear in Prometheus (http://localhost:9090) after making requests.

### Manual Verification
- Send requests to `http://localhost:8000/chat`.
- Check logs and traces.

import os
import time
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from prometheus_client import start_http_server, Counter, Histogram
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter

# LLM Guard
# Setup OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
# In a real app, you'd export to Jaeger/Zipkin/OTLP. Here we just print to console for demo or no-op if not configured.
# trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

app = FastAPI(title="MLSecOps LLM Service")

# Prometheus Metrics
REQUEST_COUNT = Counter("llm_request_total", "Total LLM requests", ["status"])
REQUEST_LATENCY = Histogram("llm_request_latency_seconds", "LLM request latency")

class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    response: str
    is_sanitized: bool

@app.on_event("startup")
async def startup_event():
    # Start Prometheus metrics server on a separate port or expose via /metrics
    # For simplicity in FastAPI, we can just let Prometheus scrape this app if we add the middleware,
    # but standard python client starts a separate server.
    # Let's use the standard client to expose on 9090 or similar if needed, 
    # but usually we just mount a route. 
    # For this demo, we'll assume the sidecar/prometheus scrapes the app.
    # We will skip manual start_http_server and rely on OTEL or manual route if needed.
    pass

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start_time = time.time()
    prompt_text = request.prompt
    
    with tracer.start_as_current_span("llm_request"):
        # 1. (Optional) Input handling – no external guardrails to keep deps minimal
        sanitized_prompt = prompt_text

        # 2. LLM Call
        with tracer.start_as_current_span("llm_generation"):
            try:
                # Dummy generation: keep everything local, no external calls
                if "ignore previous" in sanitized_prompt.lower():
                    response_text = "I cannot ignore previous instructions due to policy."
                else:
                    response_text = f"Echo: {sanitized_prompt}"
            except Exception as e:
                REQUEST_COUNT.labels(status="error").inc()
                raise HTTPException(status_code=500, detail=str(e))

        sanitized_response = response_text

        REQUEST_COUNT.labels(status="success").inc()
        REQUEST_LATENCY.observe(time.time() - start_time)

        return ChatResponse(response=sanitized_response, is_sanitized=(sanitized_prompt != request.prompt))

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

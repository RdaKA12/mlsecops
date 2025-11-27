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

# LangChain
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

# LLM Guard
from llm_guard.input_scanners import PromptInjection, Anonymize, Secrets
from llm_guard.output_scanners import Deanonymize, NoRefusal, BanTopics
from llm_guard.vault import Vault

# Setup OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
# In a real app, you'd export to Jaeger/Zipkin/OTLP. Here we just print to console for demo or no-op if not configured.
# trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

app = FastAPI(title="MLSecOps LLM Service")

# Prometheus Metrics
REQUEST_COUNT = Counter("llm_request_total", "Total LLM requests", ["status"])
REQUEST_LATENCY = Histogram("llm_request_latency_seconds", "LLM request latency")
GUARDRAIL_TRIGGERED = Counter("llm_guardrail_triggered_total", "Guardrails triggered", ["type", "scanner"])

# Initialize Guardrails
vault = Vault()
input_scanners = [
    PromptInjection(),
    Anonymize(vault=vault),
    Secrets(redact_mode="replace"),
]
output_scanners = [
    Deanonymize(vault=vault),
    NoRefusal(),
]

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
        # 1. Input Guardrails
        with tracer.start_as_current_span("input_guardrails"):
            sanitized_prompt = prompt_text
            all_valid = True
            for scanner in input_scanners:
                sanitized_prompt, valid, score = scanner.scan(sanitized_prompt)
                if not valid:
                    GUARDRAIL_TRIGGERED.labels(type="input", scanner=scanner.__class__.__name__).inc()
                    all_valid = False
                    # We can choose to block or continue with sanitized
                    # For strict security, we might block:
                    # raise HTTPException(status_code=400, detail=f"Input rejected by {scanner.__class__.__name__}")
            
            # If Anonymize ran, sanitized_prompt might be different
        
        if not all_valid:
             # Option: Reject request
             # return ChatResponse(response="I cannot answer that due to security policies.", is_sanitized=True)
             pass # For demo, we proceed with sanitized prompt

        # 2. LLM Call
        with tracer.start_as_current_span("llm_generation"):
            try:
                # Check for API Key
                if os.getenv("OPENAI_API_KEY"):
                    llm = ChatOpenAI(temperature=0.7)
                    messages = [HumanMessage(content=sanitized_prompt)]
                    ai_msg = llm.invoke(messages)
                    response_text = ai_msg.content
                else:
                    # Dummy Fallback for demo without keys
                    response_text = f"Echo (No API Key): {sanitized_prompt}"
                    if "ignore previous" in sanitized_prompt.lower():
                        response_text = "I cannot ignore instructions."
            except Exception as e:
                REQUEST_COUNT.labels(status="error").inc()
                raise HTTPException(status_code=500, detail=str(e))

        # 3. Output Guardrails
        with tracer.start_as_current_span("output_guardrails"):
            sanitized_response = response_text
            for scanner in output_scanners:
                sanitized_response, valid, score = scanner.scan(sanitized_prompt, sanitized_response)
                if not valid:
                    GUARDRAIL_TRIGGERED.labels(type="output", scanner=scanner.__class__.__name__).inc()
                    sanitized_response = "Response withheld due to security policy."

        REQUEST_COUNT.labels(status="success").inc()
        REQUEST_LATENCY.observe(time.time() - start_time)

        return ChatResponse(response=sanitized_response, is_sanitized=(sanitized_prompt != request.prompt))

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app, Counter, Histogram
import time
from redis.asyncio import Redis
from app.core.settings import get_settings
from app.core.logging import configure_logging
from app.core.auth import Authenticator
from app.infra.database import Database
from app.infra.limiter import UserLimiter
from app.services.catalog import ProductRetriever
from app.services.ai_graph import AIWorkflow
from app.api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_settings()
    configure_logging(cfg.log_level)
    app.state.cfg = cfg
    app.state.db = Database(cfg.database_url)
    app.state.redis = Redis.from_url(cfg.redis_url, decode_responses=True)
    app.state.auth = Authenticator(cfg)
    app.state.limiter = UserLimiter(app.state.redis, cfg.per_user_rate_limit)
    app.state.workflow = AIWorkflow(cfg, ProductRetriever(cfg))
    try:
        yield
    finally:
        await app.state.auth.close()
        await app.state.redis.aclose()
        await app.state.db.close()

app = FastAPI(title="Enterprise E-Commerce AI Assistant", version="2.0.0", lifespan=lifespan)
settings = get_settings()
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
                   allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type", "X-Request-ID"])
HTTP_REQUESTS = Counter("ecomm_http_requests_total", "HTTP request count", ["method", "route", "status"])
HTTP_DURATION = Histogram("ecomm_http_request_seconds", "HTTP request duration", ["method", "route"])

@app.middleware("http")
async def record_metrics(request, call_next):
    started = time.monotonic()
    response = await call_next(request)
    route = request.scope.get("route")
    route_name = getattr(route, "path", "unmatched")
    HTTP_REQUESTS.labels(request.method, route_name, str(response.status_code)).inc()
    HTTP_DURATION.labels(request.method, route_name).observe(time.monotonic() - started)
    return response

app.mount("/metrics", make_asgi_app())
app.include_router(router, prefix=settings.api_prefix)
try:
    if settings.otlp_endpoint:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        provider = TracerProvider()
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otlp_endpoint)))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
except ImportError:
    pass

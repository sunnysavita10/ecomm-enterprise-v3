# Enterprise upgrade sequence

## P0 before external production
- Add database migrations (Alembic); shorten chat DB transactions; lock conversations to avoid parallel writes.
- Integrate AWS Secrets Manager and managed Postgres/Redis, approved OIDC tenant identity, encrypted traffic, network policy.
- Fix JWKS rotation/cache refresh, add threat modeling and auth integration tests.
- Migrate the ORIGINAL product reviews dataset with a new embeddings collection.
- Add integration tests against real OpenAI/AstraDB/MCP, stable retry budgets, failure-injection tests.

## P1 performance
- Hybrid BM25 + vector, reranker, source citations and SKU-level metadata filtering.
- Decouple ingestion using SQS/Celery, DLQ and idempotent upserts.
- Prometheus/OpenTelemetry/Langfuse telemetry, privacy-aware logging, token/cost monitoring.
- Load tests with k6/Locust, concurrency limits, graceful overload and capacity plans.
- SSE token streaming and cancellation-aware background execution.

## P2 platform
- Terraform EKS/RDS/ElastiCache and AWS WAF; short-lived GitHub Actions OIDC deployment identity.
- Progressive delivery, canary, automatic rollback, SLO alerts.
- RAGAS/DeepEval datasets, human review, regression gates.
- Multi-model gateway (LiteLLM), routing, caching and bounded fallback.

## Webinar demo
1. Run Compose locally and query synthetic catalog.
2. Demonstrate request schemas, owner-bound conversations, Redis rate limit.
3. Explain async graph and evidence-only responses.
4. Show K8 Deployment + HPA and discuss why HPA alone does not guarantee throughput.
5. Present production gap list rather than claiming untested scalability.

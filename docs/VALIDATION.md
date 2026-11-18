# Validation matrix
| Feature | Code included | Verified in artifact build | Remaining work |
|---|---|---|---|
| Syntax / packaging | Yes | compileall | Full dependencies runtime |
| FastAPI and LangGraph | Yes | Static | Integration with DB/Redis/LLM |
| OpenAI/Groq fallback | Yes | Unit logic where dependencies installed | Real provider timeouts/quotas |
| AstraDB | Yes | Static | Auth, embeddings, sample ingestion in real DB |
| Real hybrid BM25 | No | N/A | Configure vector+lexical index and RRF integration |
| Terraform EKS/RDS/Redis/ECR/S3 | Yes | Syntax only if terraform available | terraform validate/plan/apply, IAM review |
| Celery Redis | Yes | Static | Broker end-to-end test |
| RAGAS/DeepEval | Optional adapters | Import-only | Real judge calls and dataset gates |
| Grafana/Prometheus | Yes | Config only | Runtime collector wiring |
| Langfuse | Optional callbacks | Config only | Provision and test tracing service |
| Load tests | Locust scenario | Not executed | Load generator and environment |
| Original scraper/data | Import script | Not imported | Local clone and data reconciliation |

Do not present this as audited enterprise production deployment until checked against these criteria.

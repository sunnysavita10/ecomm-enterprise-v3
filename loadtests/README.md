# Performance testing
Run only against infrastructure you own and have permission to load test.
Install `pip install locust` then `locust -f loadtests/locustfile.py --host http://localhost:8000`.
Development AUTH_MODE=dev needs no JWT. Production requires `LOADTEST_JWT` obtained from your identity provider.
Ramp gradually at 10, 50, 100, 500 virtual users. Capture p50/p95/p99 latency, errors, model-provider 429s, RDS connections, Redis CPU, HPA events and per-request cost. Virtual users are NOT equal to sustained concurrent inflight requests.
No load-test result is claimed for this ZIP.

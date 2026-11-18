# Langfuse integration
Set LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY for your Langfuse deployment.
Instrument model calls through the Langfuse LangChain CallbackHandler. Avoid exporting conversation PII unless the data policy permits it. This file documents the deployment configuration; the callback is opt-in in app/services/observability.py.

"""Optional Langfuse LangChain callback integration."""
import os
def langfuse_callbacks():
    if not all(os.getenv(k) for k in ('LANGFUSE_PUBLIC_KEY','LANGFUSE_SECRET_KEY')):return []
    from langfuse.langchain import CallbackHandler
    return [CallbackHandler()]

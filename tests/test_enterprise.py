import pytest
from types import SimpleNamespace
from app.services.hybrid_search import tokenize,rrf_fuse,lexical_score
from app.services.guardrails import validate_message,redact_secrets
from app.services.llm_gateway import LLMGateway,ProviderUnavailable
from app.domain.schemas import Source
from app.services.catalog import RetrievalResult
from fastapi import HTTPException

def test_lexical_search_and_rrf():
    a=RetrievalResult('Long battery',Source(product_id='a',product_title='Phone A',price='100',rating='4'))
    b=RetrievalResult('Camera',Source(product_id='b',product_title='Phone B',price='200',rating='5'))
    assert lexical_score('battery',a)>lexical_score('battery',b)
    assert rrf_fuse([[a,b],[b,a]],2)[0].source.product_id in ('a','b')

def test_guardrail():
    with pytest.raises(HTTPException):validate_message(' ',100)
    assert '[REDACTED]' in redact_secrets('sk-'+'x'*25)

class Bad:
    async def ainvoke(self,m):raise TimeoutError('down')
class Good:
    async def ainvoke(self,m):return SimpleNamespace(content='answer')

@pytest.mark.asyncio
async def test_fallback():
    cfg=SimpleNamespace(llm_provider_order='openai,groq',llm_timeout_seconds=0.5,provider_retries=0,circuit_breaker_threshold=1,circuit_breaker_cooldown_seconds=30)
    gw=LLMGateway(cfg,{'openai':Bad(),'groq':Good()})
    assert (await gw.ainvoke([])).content=='answer'
    assert gw.last_provider=='groq'

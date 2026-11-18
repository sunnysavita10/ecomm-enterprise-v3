"""Provider abstraction with per-provider retries, circuit breaker and cost estimate."""
import asyncio
import time
from dataclasses import dataclass
from typing import Protocol
from app.core.settings import Settings

class ModelClient(Protocol):
    async def ainvoke(self, messages): ...

@dataclass
class ModelUsage:
    provider: str
    estimated_cost_usd: float = 0.0

class ProviderUnavailable(Exception): pass

class LLMGateway:
    def __init__(self, cfg: Settings, clients: dict[str, ModelClient] | None = None):
        self.cfg = cfg
        self._clients=clients or self._make_clients(cfg)
        self._failures:dict[str,int]={}
        self._blocked_until:dict[str,float]={}
        self.last_provider=None

    @staticmethod
    def _make_clients(cfg):
        clients={}
        if cfg.openai_api_key:
            from langchain_openai import ChatOpenAI
            clients['openai']=ChatOpenAI(model=cfg.openai_model,api_key=cfg.openai_api_key,temperature=0,max_retries=0,timeout=cfg.llm_timeout_seconds)
        if cfg.groq_api_key:
            from langchain_groq import ChatGroq
            clients['groq']=ChatGroq(model=cfg.groq_model,api_key=cfg.groq_api_key,temperature=0,max_retries=0,timeout=cfg.llm_timeout_seconds)
        return clients

    async def ainvoke(self, messages):
        if not self._clients: raise ProviderUnavailable('No LLM providers configured')
        errors=[]
        order=[p.strip() for p in self.cfg.llm_provider_order.split(',') if p.strip()]
        for provider in order:
            client=self._clients.get(provider)
            if client is None or time.monotonic()<self._blocked_until.get(provider,0): continue
            for attempt in range(self.cfg.provider_retries+1):
                try:
                    from app.services.observability import langfuse_callbacks
                    callbacks=langfuse_callbacks()
                    result=await asyncio.wait_for(client.ainvoke(messages,config={"callbacks":callbacks}) if callbacks else client.ainvoke(messages),timeout=self.cfg.llm_timeout_seconds)
                    self._failures[provider]=0;self.last_provider=provider
                    return result
                except (Exception) as exc:
                    errors.append(type(exc).__name__)
                    self._failures[provider]=self._failures.get(provider,0)+1
                    if self._failures[provider]>=self.cfg.circuit_breaker_threshold:
                        self._blocked_until[provider]=time.monotonic()+self.cfg.circuit_breaker_cooldown_seconds
                        break
                    if attempt<self.cfg.provider_retries:
                        await asyncio.sleep(min(0.25*(2**attempt),2))
        raise ProviderUnavailable('All configured model providers failed: '+', '.join(errors[-4:]))

import asyncio
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError
from app.domain.schemas import ChatRequest,ChatResponse,HealthResponse
from app.infra.database import ChatMessage,ensure_conversation,load_history
from app.services.guardrails import validate_message
from app.services.llm_gateway import ProviderUnavailable

router=APIRouter()
@router.get('/health/live',response_model=HealthResponse)
async def liveness():return HealthResponse(status='ok')
@router.get('/health/ready',response_model=HealthResponse)
async def readiness(request:Request):
    try:
        await request.app.state.db.is_ready();await request.app.state.redis.ping()
    except Exception:raise HTTPException(503,'Dependencies unavailable') from None
    return HealthResponse(status='ready')

@router.post('/chat',response_model=ChatResponse)
async def chat(payload:ChatRequest,request:Request):
    s=request.app.state
    principal=await s.auth.authenticate(request)
    await s.limiter.check(principal.user_id)
    message=validate_message(payload.message,s.cfg.max_input_chars)
    request_id=str(uuid4())
    # Distributed per-conversation mutual exclusion prevents interleaved turns across pods.
    cid_key=str(payload.conversation_id) if payload.conversation_id else str(uuid4())
    lock=s.redis.lock('chat-lock:'+principal.user_id+':'+cid_key,timeout=int(s.cfg.request_timeout_seconds)+15,blocking_timeout=2)
    if not await lock.acquire():raise HTTPException(409,'Conversation is busy, retry shortly')
    try:
        try:
            async with s.db.sessions() as session:
                async with session.begin():
                    cid=await ensure_conversation(session,payload.conversation_id,principal.user_id)
                    rows=await load_history(session,cid,s.cfg.max_history_messages)
                    history=[{'role':m.role,'content':m.content} for m in rows]
        except LookupError:raise HTTPException(404,'Conversation not found') from None
        except SQLAlchemyError:raise HTTPException(503,'Conversation database unavailable') from None
        try:
            answer,sources=await asyncio.wait_for(s.workflow.run(message,history),timeout=s.cfg.request_timeout_seconds)
        except asyncio.TimeoutError:raise HTTPException(504,'AI request timed out') from None
        except ProviderUnavailable:raise HTTPException(502,'All model providers unavailable') from None
        except Exception:raise HTTPException(502,'AI service temporarily unavailable') from None
        try:
            async with s.db.sessions() as session:
                async with session.begin():
                    # Re-check ownership on write even after the earlier read transaction.
                    await ensure_conversation(session,cid,principal.user_id)
                    session.add_all([ChatMessage(conversation_id=cid,role='user',content=message),ChatMessage(conversation_id=cid,role='assistant',content=answer)])
        except SQLAlchemyError:raise HTTPException(503,'Conversation database unavailable') from None
        return ChatResponse(conversation_id=cid,answer=answer,sources=sources,request_id=request_id)
    finally:
        try:
            if await lock.owned():await lock.release()
        except Exception:pass

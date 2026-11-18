"""Input validation and output grounding hygiene; not a complete prompt injection defense."""
import re
from fastapi import HTTPException
BLOCKED = (re.compile(r'(?i)\b(?:sk-[a-z0-9]{20,}|AKIA[0-9A-Z]{16})\b'),)
def validate_message(message:str,max_chars:int)->str:
    message=message.strip()
    if not message or len(message)>max_chars: raise HTTPException(422,'Question is empty or too long')
    if any(p.search(message) for p in BLOCKED): raise HTTPException(422,'Remove secrets from your request')
    return message
def evidence_is_sufficient(evidence)->bool:
    return bool(evidence) and any(x.source.product_id and x.source.product_title for x in evidence)
def redact_secrets(value:str)->str:
    value=re.sub(r'(?i)sk-[a-z0-9]{20,}','[REDACTED]',value)
    return re.sub(r'AKIA[0-9A-Z]{16}','[REDACTED]',value)

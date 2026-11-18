import pytest
from pydantic import ValidationError
from app.core.settings import Settings
from app.domain.schemas import ChatRequest

def test_dev_settings():
    s = Settings(_env_file=None, environment="development", auth_mode="dev")
    assert s.retrieval_mode in {"demo", "astra"}

def test_prod_rejects_demo_auth():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="production", auth_mode="dev")

def test_chat_input_validation():
    with pytest.raises(ValidationError):
        ChatRequest(message="")
    with pytest.raises(ValidationError):
        ChatRequest(message="x" * 3001)

import pytest
from app.core.settings import Settings
from app.services.catalog import ProductRetriever
from app.services.ai_graph import AIWorkflow

@pytest.mark.asyncio
async def test_local_demo_answer():
    cfg = Settings(_env_file=None, retrieval_mode="demo", demo_catalog_path="data/products.csv", openai_api_key="")
    answer, sources = await AIWorkflow(cfg, ProductRetriever(cfg)).run("phone battery", [])
    assert "Example Phone A" in answer
    assert sources[0].product_id == "P1001"

@pytest.mark.asyncio
async def test_no_data_is_explicit():
    cfg = Settings(_env_file=None, retrieval_mode="demo", demo_catalog_path="data/products.csv", openai_api_key="")
    answer, sources = await AIWorkflow(cfg, ProductRetriever(cfg)).run("zyxwvu", [])
    assert not sources
    assert "couldn't find" in answer

"""Optional independent MCP retrieval service; run as a separate process."""
import asyncio
from mcp.server.fastmcp import FastMCP
from app.core.settings import get_settings
from app.services.catalog import ProductRetriever

cfg = get_settings()
retriever = ProductRetriever(cfg)
mcp = FastMCP("ecommerce-catalog")

@mcp.tool()
async def get_product_info(query: str) -> list[dict]:
    """Read-only product catalog search."""
    if not query or len(query) > cfg.max_input_chars:
        raise ValueError("Invalid query")
    docs = await retriever.retrieve(query)
    return [{"product_id": d.source.product_id, "title": d.source.product_title,
             "price": d.source.price, "rating": d.source.rating, "review": d.text[:1500]} for d in docs]

if __name__ == "__main__":
    mcp.run(transport="stdio")  # For remote use, put behind authenticated gateway.

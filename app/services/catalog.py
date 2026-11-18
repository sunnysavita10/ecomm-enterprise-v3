import asyncio
import csv
from pathlib import Path
from dataclasses import dataclass
from app.core.settings import Settings
from app.domain.schemas import Source

@dataclass
class RetrievalResult:
    text: str
    source: Source

class ProductRetriever:
    def __init__(self, cfg: Settings):
        self.cfg = cfg
        self.vectorstore = None
        self._rows = []
        if cfg.retrieval_mode == "demo":
            path = Path(cfg.demo_catalog_path)
            if path.exists():
                with path.open(encoding="utf-8-sig", newline="") as f:
                    self._rows = list(csv.DictReader(f))

    async def retrieve(self, query: str) -> list[RetrievalResult]:
        if self.cfg.retrieval_mode == "demo":
            words = set(query.casefold().split())
            ranked = sorted(self._rows, key=lambda r: sum(w in (r.get("product_title", "") + " " + r.get("top_reviews", "")).casefold() for w in words), reverse=True)
            return [self._convert(r) for r in ranked[:self.cfg.retrieval_k] if words and any(w in (r.get("product_title", "") + " " + r.get("top_reviews", "")).casefold() for w in words)]
        if self.vectorstore is None:
            from langchain_astradb import AstraDBVectorStore
            from langchain_openai import OpenAIEmbeddings
            self.vectorstore = AstraDBVectorStore(
                embedding=OpenAIEmbeddings(model=self.cfg.openai_embedding_model, api_key=self.cfg.openai_api_key),
                collection_name=self.cfg.astra_collection,
                api_endpoint=self.cfg.astra_db_api_endpoint,
                token=self.cfg.astra_db_application_token,
                namespace=self.cfg.astra_db_keyspace or None,
            )
        docs = await self.vectorstore.asimilarity_search(query, k=max(self.cfg.retrieval_k * 3, 10))
        items = [RetrievalResult(text=d.page_content, source=Source(
            product_id=str(d.metadata.get("product_id", "unknown")),
            product_title=str(d.metadata.get("product_title", "Unknown product")),
            price=str(d.metadata["price"]) if d.metadata.get("price") is not None else None,
            rating=str(d.metadata["rating"]) if d.metadata.get("rating") is not None else None,
        )) for d in docs]
        if self.cfg.hybrid_enabled:
            from app.services.hybrid_search import hybrid_rank
            # Candidate-level lexical reranking only; real corpus-wide hybrid requires Astra lexical/BM25 retrieval.
            return hybrid_rank(query, items, items, self.cfg.retrieval_k)
        return items[:self.cfg.retrieval_k]

    def _convert(self, row):
        return RetrievalResult(text=row.get("top_reviews", ""), source=Source(
            product_id=str(row.get("product_id", "")), product_title=row.get("product_title", ""),
            price=row.get("price") or None, rating=row.get("rating") or None))

"""Idempotent AstraDB ingestion. Run explicitly, never on API startup."""
import csv
import os
import uuid
from pathlib import Path
from langchain_astradb import AstraDBVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from app.core.settings import get_settings

def main():
    c = get_settings()
    if not (c.openai_api_key and c.astra_db_api_endpoint and c.astra_db_application_token):
        raise SystemExit("Set OPENAI_API_KEY and ASTRA_DB credentials")
    path = Path(os.environ.get("CATALOG_CSV", "data/products.csv"))
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    store = AstraDBVectorStore(
        embedding=OpenAIEmbeddings(model=c.openai_embedding_model, api_key=c.openai_api_key),
        collection_name=c.astra_collection, api_endpoint=c.astra_db_api_endpoint,
        token=c.astra_db_application_token, namespace=c.astra_db_keyspace or None)
    docs = []
    ids = []
    for r in rows:
        product_id = str(r["product_id"])
        docs.append(Document(page_content=str(r.get("top_reviews", "")), metadata={
            "product_id": product_id, "product_title": str(r.get("product_title", "")),
            "price": str(r.get("price", "")), "rating": str(r.get("rating", ""))}))
        ids.append(str(uuid.uuid5(uuid.NAMESPACE_URL, "ecomm-product:" + product_id)))
    for start in range(0, len(docs), 50):
        store.add_documents(docs[start:start+50], ids=ids[start:start+50])
    print(f"Upserted {len(docs)} products")

if __name__ == "__main__":
    main()

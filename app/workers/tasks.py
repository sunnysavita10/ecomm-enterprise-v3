"""Durable, retryable ingestion jobs. Never call external provider per request startup."""
import csv
import os
import uuid
from pathlib import Path
from celery import Celery
from app.core.settings import get_settings

config=get_settings()
celery_app=Celery('ecomm',broker=config.redis_url,backend=config.redis_url)
celery_app.conf.update(task_serializer='json',accept_content=['json'],result_serializer='json',task_acks_late=True,worker_prefetch_multiplier=1,task_reject_on_worker_lost=True)

@celery_app.task(bind=True,autoretry_for=(ConnectionError,TimeoutError),retry_backoff=True,retry_jitter=True,max_retries=4)
def ingest_catalog(self,csv_path='data/products.csv'):
    from langchain_astradb import AstraDBVectorStore
    from langchain_openai import OpenAIEmbeddings
    from langchain_core.documents import Document
    cfg=get_settings()
    path=Path(csv_path).resolve()
    allowed=Path(os.environ.get('INGEST_ROOT','data')).resolve()
    if not path.is_relative_to(allowed) or path.suffix.lower()!='.csv':
        raise ValueError('Catalog path must be a CSV under INGEST_ROOT')
    with path.open(newline='',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    if not rows:return {'upserted':0}
    required={'product_id','product_title','top_reviews'}
    if not required.issubset(rows[0]):raise ValueError('Invalid catalog schema')
    store=AstraDBVectorStore(embedding=OpenAIEmbeddings(model=cfg.openai_embedding_model,api_key=cfg.openai_api_key),collection_name=cfg.astra_collection,api_endpoint=cfg.astra_db_api_endpoint,token=cfg.astra_db_application_token,namespace=cfg.astra_db_keyspace or None)
    count=0
    for n in range(0,len(rows),cfg.ingestion_batch_size):
        batch=rows[n:n+cfg.ingestion_batch_size]
        docs=[Document(page_content=r.get('top_reviews',''),metadata={k:str(r.get(k,'')) for k in ('product_id','product_title','price','rating')}) for r in batch]
        ids=[str(uuid.uuid5(uuid.NAMESPACE_URL,'ecomm-product:'+str(r['product_id']))) for r in batch]
        store.add_documents(docs,ids=ids);count+=len(batch)
    return {'upserted':count,'collection':cfg.astra_collection}

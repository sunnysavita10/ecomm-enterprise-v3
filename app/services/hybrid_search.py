"""Reciprocal-rank fusion and deterministic lexical reranking; supports Astra semantic results."""
import re
from dataclasses import dataclass
from app.services.catalog import RetrievalResult

def tokenize(value: str)->set[str]:
    return set(re.findall(r'[a-z0-9]+',value.lower()))

def lexical_score(query: str, result: RetrievalResult)->float:
    tokens=tokenize(query)
    if not tokens: return 0
    title=tokenize(result.source.product_title)
    text=tokenize(result.text)
    return (2*len(tokens & title)+len(tokens & text))/max(len(tokens),1)

def rrf_fuse(rankings:list[list[RetrievalResult]],limit:int=4,k:int=60)->list[RetrievalResult]:
    scores:dict[str,float]={};items={}
    for ranking in rankings:
        for rank,item in enumerate(ranking,1):
            key=item.source.product_id
            scores[key]=scores.get(key,0)+1/(k+rank)
            items[key]=item
    return [items[key] for key in sorted(scores,key=lambda key:(-scores[key],key))[:limit]]

def hybrid_rank(query:str, semantic:list[RetrievalResult], lexical:list[RetrievalResult], limit:int=4):
    # BM25 is recommended for large production corpora; this local lexical scorer is deterministic.
    ranked_lexical=sorted(lexical,key=lambda row:lexical_score(query,row),reverse=True)
    return rrf_fuse([semantic,ranked_lexical],limit=limit)

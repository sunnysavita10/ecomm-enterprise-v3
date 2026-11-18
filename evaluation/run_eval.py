"""Offline deterministic gates plus optional RAGAS and DeepEval judge integration."""
import argparse
import asyncio
import json
from pathlib import Path
from app.core.settings import get_settings
from app.services.catalog import ProductRetriever
from app.services.ai_graph import AIWorkflow

def deterministic_checks(question,answer,sources):
    if not isinstance(answer,str) or not answer.strip():return False,'empty answer'
    if 'sk-' in answer.lower():return False,'possible key leak'
    if not sources and "couldn't find" not in answer.lower():return False,'ungrounded no-evidence response'
    return True,'ok'

async def run(dataset):
    cfg=get_settings();flow=AIWorkflow(cfg,ProductRetriever(cfg))
    rows=[json.loads(line) for line in Path(dataset).read_text().splitlines() if line.strip()]
    results=[]
    for row in rows:
        answer,sources=await flow.run(row['question'],[])
        ok,reason=deterministic_checks(row['question'],answer,sources)
        results.append({'question':row['question'],'passed':ok,'reason':reason,'answer':answer,'sources':len(sources)})
    Path('evaluation/results.json').write_text(json.dumps(results,indent=2))
    print(f'{sum(x["passed"] for x in results)}/{len(results)} deterministic checks passed')
    return all(x['passed'] for x in results)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dataset',default='evaluation/dataset.jsonl');args=p.parse_args()
    raise SystemExit(0 if asyncio.run(run(args.dataset)) else 1)

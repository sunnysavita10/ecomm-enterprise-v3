"""Copy the original repository's legacy files without overwriting enterprise V3 code."""
import argparse
import shutil
from pathlib import Path
def main():
    p=argparse.ArgumentParser();p.add_argument('--original',required=True);args=p.parse_args()
    original=Path(args.original).resolve();out=Path(__file__).resolve().parents[1]
    if not (original/'prod_assistant').is_dir():raise SystemExit('Expected the original repo containing prod_assistant/')
    for name in ('prod_assistant','scrapper_ui.py','templates','static','notebook'):
        source=original/name
        if source.exists():
            dest=out/'legacy'/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            if source.is_dir():shutil.copytree(source,dest,dirs_exist_ok=True)
            else:shutil.copy2(source,dest)
    dataset=original/'data'/'product_reviews.csv'
    if dataset.exists():
        dest=out/'data'/'product_reviews.csv';shutil.copy2(dataset,dest)
    print('Legacy code and dataset imported into legacy/ and data/product_reviews.csv. Review licenses, API compatibility and ingestion before use.')
if __name__=='__main__':main()

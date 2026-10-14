"""Run non-causal descriptive diagnostics on the existing HWO evidence matrix."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd
from hwoevidence.coverage_diagnostics import (
    wilson_coverage_intervals,disjoint_distance_coverage,pairwise_missingness_fisher
)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,default=Path('results/evidence_matrix.csv'))
    parser.add_argument('--out',type=Path,default=Path('results/coverage_diagnostics'))
    args=parser.parse_args()
    df=pd.read_csv(args.input)
    if df['target_id'].duplicated().any():
        raise ValueError('duplicate target_id: row-fanout would bias coverage')
    args.out.mkdir(parents=True,exist_ok=True)
    ci=wilson_coverage_intervals(df)
    strata=disjoint_distance_coverage(df)
    associations=pairwise_missingness_fisher(df)
    ci.to_csv(args.out/'wilson_coverage.csv',index=False)
    strata.to_csv(args.out/'disjoint_distance_coverage.csv',index=False)
    associations.to_csv(args.out/'missingness_fisher.csv',index=False)
    summary=dict(n_targets=int(len(df)),n_categories=4,n_pairwise_tests=int(len(associations)),
                 n_distance_missing=int(pd.to_numeric(df['sy_dist'],errors='coerce').isna().sum()),
                 caveat='Curated HWO target list; intervals are descriptive, not population selection corrections.')
    (args.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))

if __name__=='__main__':main()

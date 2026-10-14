"""Descriptive uncertainty and missingness diagnostics for the curated HWO target list.

No inference to an unbiased population of nearby stars is justified: this is a
selected list. Confidence intervals summarize finite-list/binomial variability,
not errors in the underlying catalog cross-matches or survey completeness.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, norm

CATEGORIES=("stellar_parameters","activity","multiplicity","astrometric_acceleration")


def _flags(data:pd.DataFrame)->pd.DataFrame:
    missing=set(CATEGORIES)-set(data.columns)
    if missing:raise ValueError(f"missing coverage columns: {sorted(missing)}")
    if len(data)==0:raise ValueError('evidence table must not be empty')
    flags=data.loc[:,CATEGORIES].copy()
    # NaN is absence of a verified measurement, not positive evidence.
    for col in CATEGORIES:
        flags[col]=flags[col].map(lambda x: str(x).strip().lower() in ('true','1') if pd.notna(x) else False)
    return flags.astype(bool)


def wilson_coverage_intervals(data:pd.DataFrame,confidence:float=0.95)->pd.DataFrame:
    """Wilson intervals for each category; denominators are always explicit."""
    if not (0<confidence<1):raise ValueError('confidence must lie in (0,1)')
    flags=_flags(data);n=len(flags);z=float(norm.ppf((1+confidence)/2))
    rows=[]
    for category in CATEGORIES:
        k=int(flags[category].sum());p=k/n;denom=1+z*z/n
        center=(p+z*z/(2*n))/denom
        half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
        rows.append(dict(category=category,n_present=k,n_targets=n,fraction=p,
                         wilson_lower=max(0,center-half),wilson_upper=min(1,center+half)))
    return pd.DataFrame(rows)


def disjoint_distance_coverage(data:pd.DataFrame,bins=(0.,10.,20.,30.,np.inf))->pd.DataFrame:
    """Disjoint bins avoid misleading comparison of overlapping cumulative cuts."""
    flags=_flags(data)
    if 'sy_dist' not in data:raise ValueError('sy_dist column is required')
    edges=np.asarray(bins,dtype=float)
    if len(edges)<2 or not np.all(np.diff(edges)>0):raise ValueError('bins must increase')
    distances=pd.to_numeric(data['sy_dist'],errors='coerce')
    labels=pd.cut(distances,bins=edges,include_lowest=True,right=True)
    rows=[]
    for interval in labels.cat.categories:
        mask=(labels==interval).to_numpy()
        n=int(mask.sum())
        for category in CATEGORIES:
            k=int(flags[category].to_numpy()[mask].sum())
            rows.append(dict(distance_bin=str(interval),category=category,n_present=k,
                             n_targets=n,fraction=k/n if n else float('nan')))
    rows.append(dict(distance_bin='unassigned (missing/outside bins)',category='all',
                     n_present=0,n_targets=int(labels.isna().sum()),fraction=float('nan')))
    return pd.DataFrame(rows)


def pairwise_missingness_fisher(data:pd.DataFrame)->pd.DataFrame:
    """Exploratory two-sided Fisher tests and BH-adjusted q values for 6 pairs."""
    flags=_flags(data)
    rows=[]
    for i,left in enumerate(CATEGORIES):
        for right in CATEGORIES[i+1:]:
            a=~flags[left].to_numpy();b=~flags[right].to_numpy()
            table=np.array([[np.sum(~a & ~b),np.sum(~a & b)],
                            [np.sum(a & ~b),np.sum(a & b)]],dtype=int)
            odds,p=fisher_exact(table,alternative='two-sided')
            rows.append(dict(left=left,right=right,n_targets=len(flags),
                             both_missing=int(table[1,1]),left_only_missing=int(table[1,0]),
                             right_only_missing=int(table[0,1]),neither_missing=int(table[0,0]),
                             odds_ratio=float(odds),pvalue=float(p)))
    result=pd.DataFrame(rows)
    p=result['pvalue'].to_numpy();order=np.argsort(p,kind='stable');m=len(p)
    adjusted=np.minimum.accumulate((p[order]*m/np.arange(1,m+1))[::-1])[::-1]
    q=np.empty(m);q[order]=np.clip(adjusted,0,1)
    result['bh_qvalue']=q
    return result

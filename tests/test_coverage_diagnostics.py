import numpy as np
import pandas as pd
import pytest
from hwoevidence.coverage_diagnostics import (
    CATEGORIES,wilson_coverage_intervals,disjoint_distance_coverage,pairwise_missingness_fisher
)


def sample():
    return pd.DataFrame(dict(sy_dist=[5.,15.,25.,np.nan],stellar_parameters=[1,1,1,1],
                             activity=[1,0,1,1],multiplicity=[0,0,1,0],
                             astrometric_acceleration=[1,1,0,1]))


def test_wilson_counts_and_bounds():
    out=wilson_coverage_intervals(sample()).set_index('category')
    assert out.loc['multiplicity','n_present']==1
    assert out.loc['stellar_parameters','n_present']==4
    assert out.loc['stellar_parameters','wilson_lower']<1
    assert out['wilson_lower'].between(0,1).all()
    assert out['wilson_upper'].between(0,1).all()


def test_wilson_known_half_successes():
    df=sample();df['activity']=[True,True,False,False]
    out=wilson_coverage_intervals(df).set_index('category')
    assert out.loc['activity','fraction']==0.5
    assert np.isclose(out.loc['activity','wilson_lower'],0.150038989,atol=1e-6)


def test_wilson_rejects_bad_confidence():
    with pytest.raises(ValueError):wilson_coverage_intervals(sample(),1)


def test_distance_bins_disjoint_and_unassigned():
    out=disjoint_distance_coverage(sample())
    selected=out[out.category=='activity']
    assert selected['n_targets'].sum()==3
    assert out.iloc[-1]['n_targets']==1


def test_distance_boundary_in_first_bin():
    df=sample();df.loc[0,'sy_dist']=10.
    out=disjoint_distance_coverage(df)
    assert out[(out.category=='activity') & (out.distance_bin.str.contains('10.0'))]['n_targets'].sum()>=1


def test_distance_bins_reject_unsorted():
    with pytest.raises(ValueError):disjoint_distance_coverage(sample(),bins=(0,20,10))


def test_fisher_table_preserves_denominators():
    out=pairwise_missingness_fisher(sample())
    assert len(out)==6
    assert (out[['both_missing','left_only_missing','right_only_missing','neither_missing']].sum(axis=1)==4).all()
    assert out['bh_qvalue'].between(0,1).all()


def test_fisher_identical_missingness_has_positive_association():
    df=sample();df['activity']=[True,True,False,False];df['multiplicity']=df['activity']
    out=pairwise_missingness_fisher(df)
    row=out[(out.left=='activity') & (out.right=='multiplicity')].iloc[0]
    assert np.isinf(row.odds_ratio)
    assert row.both_missing==2


def test_missing_categories_rejected():
    with pytest.raises(ValueError):wilson_coverage_intervals(sample().drop(columns=['activity']))


def test_csv_boolean_round_trip():
    df=sample();df['multiplicity']=['False','False','True','False']
    out=wilson_coverage_intervals(df).set_index('category')
    assert out.loc['multiplicity','n_present']==1

"""Reproduce the independent-HIP HWO sensitivity analysis from pinned CSV."""
import json
from pathlib import Path

import pandas as pd

from hwoevidence.hip_dependence import (
    hip_fdr_audit,
    wds_acceleration_contrast,
    wds_distance_contrast,
)


def main():
    root = Path(__file__).resolve().parents[1]
    frame = pd.read_csv(root / "results" / "evidence_matrix.csv")
    report = {
        "source": "results/evidence_matrix.csv (pinned HWO evidence matrix)",
        "hip_fdr": hip_fdr_audit(frame),
        "wds_near_vs_far": wds_distance_contrast(frame),
        "wds_by_hgca_significance": wds_acceleration_contrast(frame),
    }
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()

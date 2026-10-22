#!/usr/bin/env python3
"""Reconstruct frozen probabilities and all point estimates from real study data."""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import sys
import time
START = time.perf_counter()
import numpy as np
import pandas as pd

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE/"src"))
from ssi_repro.frozen import FEATURES, FrozenModel, features_from_counts, ranking_metrics, significant_digits


def run(root):
    root = Path(root).resolve()
    checks = []

    def record(name, passed, **evidence):
        checks.append({"name": name, "passed": bool(passed), **evidence})

    def close(name, observed, expected, tolerance):
        a, b = np.asarray(observed, dtype=float), np.asarray(expected, dtype=float)
        delta = float(np.max(np.abs(a-b))) if a.size else 0.0
        record(name, bool(np.all(np.isfinite(a)) and np.all(np.isfinite(b)) and delta <= tolerance),
               maximum_absolute_difference=delta, absolute_tolerance=tolerance)

    model = FrozenModel.load(root/"model")
    cohort = pd.read_csv(root/"data/derived/prediction/lagged_prediction_cohort.csv.gz")
    heldout = pd.read_csv(root/"data/derived/prediction/heldout_predictions.csv")
    record("cohort_key_unique", not cohort.duplicated(["set", "unit", "year"]).any())
    record("heldout_key_unique", not heldout.duplicated(["set", "unit", "year"]).any())
    record("cohort_rows", len(cohort) == 57694, observed=len(cohort), expected=57694)
    recomputed = features_from_counts(cohort)
    for f in FEATURES:
        close("feature_from_actual_lag_counts_"+f, recomputed[f], cohort[f], 1e-12)
    record("signal_matches_target_count_comparison", np.array_equal(
        cohort.outcome.to_numpy(), (cohort.y > cohort.e).to_numpy().astype(int)))
    available_years = cohort[["n_lag1", "n_lag2", "n_lag3"]].notna().sum(axis=1)
    record("history_depth_matches_available_reports", np.array_equal(available_years, cohort.history_years))
    train = cohort[cohort["set"] == "Training"]
    train_features = recomputed.loc[train.index]
    for f in FEATURES:
        close("training_only_center_"+f, [train_features[f].mean()], [model.centers[f]], 1e-12)
        close("training_only_sample_scale_"+f, [train_features[f].std(ddof=1)], [model.scales[f]], 1e-12)
    populations = {}
    expected_populations = {
        "Training": dict(reports=39353, signals=6634, sites=392, services=9052, operations=3751313, SSI_cases=20306, years=[2017, 2018, 2019, 2020, 2021, 2022]),
        "Test": dict(reports=18132, signals=3540, sites=337, services=7117, operations=1959747, SSI_cases=11897, years=[2023, 2024, 2025]),
        "Oregon external": dict(reports=209, signals=55, sites=46, operations=34916, SSI_cases=219, years=[2017]),
    }
    for name, expected in expected_populations.items():
        d = cohort[cohort["set"] == name]
        observed = dict(reports=len(d), signals=int(d.outcome.sum()), sites=d.site.nunique(),
                        services=d.unit.nunique(), operations=int(d.n.sum()), SSI_cases=int(d.y.sum()),
                        years=sorted(d.year.unique().astype(int).tolist()))
        populations[name] = observed
        for k, v in expected.items():
            record("population_"+name.replace(" ", "_")+"_"+k, observed[k] == v, observed=observed[k], expected=v)
    record("development_and_evaluation_target_years_disjoint", not set(train.year).intersection(
        cohort.loc[cohort["set"] == "Test", "year"]))
    record("heldout_excludes_training", set(heldout["set"]) == {"Test", "Oregon external"})
    joined = heldout.merge(cohort, on=["set", "unit", "year"], suffixes=("_heldout", "_cohort"), validate="one_to_one", how="outer", indicator=True)
    record("all_heldout_match_cohort", (joined.loc[joined["set"] != "Training", "_merge"] == "both").all())
    matches = joined[joined["_merge"] == "both"]
    for f in ["n", "y", "e", "n_lag1", "y_lag1", "e_lag1", "outcome"]:
        close("heldout_matches_cohort_"+f, matches[f+"_heldout"], matches[f+"_cohort"], 1e-12)
    probabilities = model.predict(heldout)
    raw_probabilities = model.predict(heldout, rounded=False)
    close("all_heldout_frozen_probabilities_12_significant_digits", probabilities, heldout.combined, 2e-12)
    close("raw_probabilities_within_archived_rounding", raw_probabilities, heldout.combined, 6e-13)
    standardized = model.standardized(heldout)
    for f in FEATURES:
        close("heldout_standardized_feature_"+f, standardized[f+"_z"], heldout[f+"_z"], 1e-12)
    frozen = heldout.copy()
    frozen["combined"] = probabilities
    rebuilt_comparators = {
        "prior_volume": significant_digits(heldout.n_lag1.to_numpy()),
        "prior_cases": significant_digits(heldout.y_lag1.to_numpy()),
        "prior_sir": significant_digits((heldout.y_lag1.to_numpy()+0.5)/(heldout.e_lag1.to_numpy()+0.5)),
    }
    for name, values in rebuilt_comparators.items():
        close("comparator_from_actual_counts_"+name, values, heldout[name], 1e-10)
        frozen[name] = values
    metrics = {}
    reference = pd.read_csv(root/"reference_results/prediction_metrics_1999_cluster_bootstrap.csv")
    case_reference = pd.read_csv(root/"reference_results/future_SSI_case_capture_comparisons.csv")
    for dataset in ("Test", "Oregon external"):
        d = frozen[frozen["set"] == dataset]
        metrics[dataset] = {}
        for method in ("combined", "prior_cases", "prior_volume", "prior_sir"):
            m = ranking_metrics(d.outcome, d[method], d.y)
            metrics[dataset][method] = m
            ref = reference[(reference.dataset == dataset) &
                            (reference.group == "All ages and procedures") & (reference.method == method)]
            for metric in ("AUC", "AP", "capture_10", "capture_20", "capture_30"):
                value = m[metric] if metric in ("AUC", "AP") else m["capacity"][str(int(metric.split("_")[-1])/100)]["signal_capture"]
                row = ref[ref.metric == metric]
                record("reference_row_unique_"+dataset+"_"+method+"_"+metric, len(row) == 1)
                if len(row) == 1:
                    close("point_metric_"+dataset+"_"+method+"_"+metric, [value], [row.estimate.iloc[0]], 1e-11)
            for capacity, values in m["capacity"].items():
                close("exact_review_budget_"+dataset+"_"+method+"_"+capacity,
                      [values["selected_report_equivalents"]], [float(capacity)*len(d)], 1e-8)
    for _, row in case_reference.iterrows():
        key = str(float(row.capacity))
        combined = metrics["Test"]["combined"]["capacity"][key]["case_capture"]
        comparator = metrics["Test"][row.comparator]["capacity"][key]["case_capture"]
        for name, value, expected in (("combined", combined, row.combined_capture),
                                      ("comparator", comparator, row.comparator_capture),
                                      ("difference", combined-comparator, row.difference)):
            close("case_capture_"+row.comparator+"_"+key+"_"+name, [value], [expected], 1e-11)
    test, tr = cohort[cohort["set"] == "Test"], train
    overlap = {"sites": len(set(test.site).intersection(tr.site)), "services": len(set(test.unit).intersection(tr.unit))}
    record("development_evaluation_hospital_overlap", overlap["sites"] == 298, observed=overlap["sites"], expected=298)
    record("development_evaluation_service_overlap", overlap["services"] == 6088, observed=overlap["services"], expected=6088)
    elapsed = time.perf_counter()-START
    result = {"status": "pass" if all(c["passed"] for c in checks) else "fail",
              "scope": "Actual retained study inputs, all18,341 heldout probabilities, training-only scaling, target cohorts, AUC/AP, exact tie-aware signal/case capture. No model refit and no bootstrap rerun.",
              "checks": checks, "populations": populations, "training_test_overlap": overlap,
              "metrics": metrics, "elapsed_seconds": elapsed,
              "runtime": {"Python": platform.python_version(), "NumPy": np.__version__, "pandas": pd.__version__, "system": platform.system(), "machine": platform.machine()},
              "input_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in [root/"model/model_coefficients.csv", root/"model/training_feature_scaling.csv", root/"model/model_metadata.json", root/"data/derived/prediction/heldout_predictions.csv", root/"data/derived/prediction/lagged_prediction_cohort.csv.gz"]},
              "limitations": ["Checks reproduce archived frozen point estimates, not all inferential intervals or P values.", "Training uncertainty is not estimated; no model retraining or recalibration.", "The prediction target is an aggregate annual SSI signal; captured SSIs are not prevented infections."]}
    target = root/"validation/frozen_model_check.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"status": result["status"], "checks": len(checks), "failed": [c["name"] for c in checks if not c["passed"]], "elapsed_seconds": round(elapsed, 3), "report": str(target.relative_to(root))}))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PACKAGE, help="Extracted release directory")
    args = parser.parse_args()
    raise SystemExit(run(args.root))

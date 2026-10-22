"""Portable evaluation of the archived, frozen service-level SSI signal model.

The probability target is an annual report with observed SSIs above the source
prediction. Captured SSI counts describe burden reached by a service review
queue; they do not estimate prevented infections. No fitting or resampling is
performed here.
"""
from dataclasses import dataclass
from pathlib import Path
import json
import numpy as np
import pandas as pd

FEATURES = ("log_volume", "log_expected_rate", "log_prior_sir", "log_history_sir")


def features_from_counts(frame):
    """Rebuild all four features from actual lagged counts, leaving gaps unfilled.

    t-1 must be observed. Older missing lag years are excluded from their sums,
    rather than interpreted as annual zero counts or imputed reports.
    """
    required = [f"{x}_lag{j}" for x in ("n", "y", "e") for j in (1, 2, 3)]
    missing = set(required).difference(frame.columns)
    if missing:
        raise ValueError(f"Missing lagged count columns: {sorted(missing)}")
    a = {x: frame[[f"{x}_lag{j}" for j in (1, 2, 3)]].to_numpy(dtype=float)
         for x in ("n", "y", "e")}
    for x, v in a.items():
        if np.any(np.isinf(v)) or np.any(v[np.isfinite(v)] < 0):
            raise ValueError(f"Invalid nonnegative lagged {x} counts")
        if np.any(~np.isfinite(v[:, 0])):
            raise ValueError("Immediately preceding report counts must be observed")
    missing_masks = [np.isnan(a[x]) for x in ("n", "y", "e")]
    if not all(np.array_equal(missing_masks[0], m) for m in missing_masks[1:]):
        raise ValueError("A missing earlier report must have consistent missing counts")
    if np.any(a["n"][~np.isnan(a["n"])] <= 0):
        raise ValueError("Every observed earlier report needs positive operations")
    values = {
        "log_volume": np.log1p(a["n"][:, 0]),
        "log_expected_rate": np.log((a["e"][:, 0] + 0.5)/(a["n"][:, 0] + 1)),
        "log_prior_sir": np.log((a["y"][:, 0] + 0.5)/(a["e"][:, 0] + 0.5)),
        "log_history_sir": np.log((np.nansum(a["y"], axis=1) + 0.5)/
                                  (np.nansum(a["e"], axis=1) + 0.5)),
    }
    return pd.DataFrame(values, index=frame.index)


def significant_digits(values, digits=12):
    """Apply decimal significant-digit score rounding before defining ties."""
    a = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(a)):
        raise ValueError("Scores must be finite")
    return np.fromiter((float(format(x, f".{digits}g")) for x in a), float, len(a))


@dataclass(frozen=True)
class FrozenModel:
    coefficients: dict
    centers: dict
    scales: dict
    metadata: dict

    @classmethod
    def load(cls, model_directory):
        folder = Path(model_directory)
        metadata = json.loads((folder/"model_metadata.json").read_text())
        coefficients = pd.read_csv(folder/metadata["coefficient_file"])
        scaling = pd.read_csv(folder/metadata["scaling_file"])
        if coefficients.term.duplicated().any() or scaling.feature.duplicated().any():
            raise ValueError("Duplicate coefficient or scaling key")
        c = dict(zip(coefficients.term, coefficients.estimate.astype(float)))
        s = scaling.set_index("feature")
        if set(s.index) != set(FEATURES) or np.any(s.scale <= 0):
            raise ValueError("Model requires all four positive scaling constants")
        expected = {"(Intercept)", "agePediatric"}
        expected.update(f"{f}_z" for f in FEATURES)
        expected.update("procedure"+p for p in metadata["known_procedures"]
                        if p != metadata["reference_procedure"])
        if set(c) != expected or not np.all(np.isfinite(list(c.values()))):
            raise ValueError("Coefficient terms do not match declared frozen model")
        return cls(c, s.center.to_dict(), s.scale.to_dict(), metadata)

    def standardized(self, frame):
        features = features_from_counts(frame)
        return pd.DataFrame({f+"_z": (features[f]-self.centers[f])/self.scales[f]
                             for f in FEATURES}, index=frame.index)

    def predict(self, frame, rounded=True):
        """Compute frozen probabilities from lagged counts and exact category names.

        Unknown ages and procedures raise an error. They are never mapped to the
        reference category, because that would silently change the model.
        """
        for column, allowed in (("age", self.metadata["known_ages"]),
                                ("procedure", self.metadata["known_procedures"])):
            if column not in frame or frame[column].isna().any():
                raise ValueError(f"Missing {column} category")
            unknown = set(frame[column]).difference(allowed)
            if unknown:
                raise ValueError(f"Unknown {column}: {sorted(unknown)}")
        z = self.standardized(frame)
        eta = np.full(len(frame), self.coefficients["(Intercept)"], dtype=float)
        eta += (frame.age.to_numpy() == "Pediatric")*self.coefficients["agePediatric"]
        for procedure in self.metadata["known_procedures"]:
            if procedure != self.metadata["reference_procedure"]:
                eta += (frame.procedure.to_numpy() == procedure)*self.coefficients["procedure"+procedure]
        for f in FEATURES:
            eta += z[f+"_z"].to_numpy()*self.coefficients[f+"_z"]
        # Stable logistic transformation, including extreme valid predictor values.
        p = np.empty_like(eta)
        positive = eta >= 0
        p[positive] = 1/(1+np.exp(-eta[positive]))
        e = np.exp(eta[~positive])
        p[~positive] = e/(1+e)
        return significant_digits(p, self.metadata["score_significant_digits"]) if rounded else p


def _arrays(scores, weights=None):
    s = np.asarray(scores, dtype=float)
    w = np.ones(len(s)) if weights is None else np.asarray(weights, dtype=float)
    if s.ndim != 1 or w.shape != s.shape or not np.all(np.isfinite(s)):
        raise ValueError("Scores must be a finite one-dimensional array")
    if np.any(~np.isfinite(w)) or np.any(w < 0) or w.sum() <= 0:
        raise ValueError("Weights must be finite, nonnegative and have positive total")
    return s, w


def selection_fractions(scores, capacity, weights=None):
    """Return expected within-tie selection fractions at an exact review budget.

    Hospital multiplicity weights are separate from these fractions. All rows
    in a boundary tie share the same fraction, independent of row order.
    """
    s, w = _arrays(scores, weights)
    if not np.isfinite(capacity) or not 0 <= capacity <= 1:
        raise ValueError("Review capacity must be between zero and one")
    selected = np.zeros(len(s), dtype=float)
    if capacity == 0:
        return selected
    if capacity == 1:
        return np.ones(len(s), dtype=float)
    order = np.argsort(-s, kind="stable")
    ends = np.r_[np.flatnonzero(np.diff(s[order]) != 0)+1, len(s)]
    starts = np.r_[0, ends[:-1]]
    remaining = float(capacity*w.sum())
    for start, end in zip(starts, ends):
        idx = order[start:end]
        weight = float(w[idx].sum())
        if weight == 0:
            continue
        fraction = min(1.0, max(0.0, remaining/weight))
        selected[idx] = fraction
        remaining -= fraction*weight
        if remaining <= np.finfo(float).eps*w.sum()*4:
            break
    return selected


def ranking_metrics(outcome, scores, cases=None, capacities=(0.1, 0.2, 0.3), weights=None):
    """Weighted AUC, AP and signal/case capture with proportional boundary ties."""
    s, w = _arrays(scores, weights)
    y = np.asarray(outcome, dtype=float)
    if y.shape != s.shape or not np.all(np.isin(y, (0, 1))):
        raise ValueError("Outcome must be binary and match scores")
    if cases is not None:
        cases = np.asarray(cases, dtype=float)
        if cases.shape != s.shape or np.any(~np.isfinite(cases)) or np.any(cases < 0):
            raise ValueError("SSI counts must be finite, nonnegative and match scores")
    order = np.argsort(-s, kind="stable")
    starts = np.r_[0, np.flatnonzero(np.diff(s[order]) != 0)+1]
    positive = np.add.reduceat(w[order]*y[order], starts)
    negative = np.add.reduceat(w[order]*(1-y[order]), starts)
    tp, tn = positive.sum(), negative.sum()
    cp, cn = np.cumsum(positive), np.cumsum(negative)
    auc = float(np.sum(positive*(tn-cn+0.5*negative))/(tp*tn)) if tp > 0 and tn > 0 else float("nan")
    precision = np.divide(cp, cp+cn, out=np.zeros_like(cp), where=(cp+cn) > 0)
    ap = float(np.sum(positive/tp*precision)) if tp > 0 else float("nan")
    result = {"AUC": auc, "AP": ap, "signals": float(tp), "report_equivalents": float(w.sum()), "capacity": {}}
    for c in capacities:
        f = selection_fractions(s, float(c), w)
        selected = f*w
        signal_count = float(np.sum(selected*y))
        m = {"selected_report_equivalents": float(selected.sum()),
             "signal_capture": signal_count/tp if tp > 0 else float("nan"),
             "precision": signal_count/selected.sum() if selected.sum() else float("nan")}
        if cases is not None:
            total_cases = float(np.sum(w*cases))
            m["case_capture"] = float(np.sum(selected*cases)/total_cases) if total_cases > 0 else float("nan")
        result["capacity"][str(c)] = m
    return result

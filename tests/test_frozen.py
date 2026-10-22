"""Boundary tests complement, rather than replace, validation on real study data."""
from pathlib import Path
import sys
import unittest
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
from ssi_repro.frozen import FrozenModel, features_from_counts, ranking_metrics, selection_fractions, significant_digits


class SelectionTests(unittest.TestCase):
    def test_boundary_tie_shares_exact_budget_and_ignores_row_order(self):
        scores = np.array([3., 2., 2., 1.])
        f = selection_fractions(scores, 0.5)
        np.testing.assert_allclose(f, [1., 0.5, 0.5, 0.])
        permutation = np.array([2, 0, 3, 1])
        shuffled = selection_fractions(scores[permutation], 0.5)
        np.testing.assert_allclose(shuffled, f[permutation])
        self.assertAlmostEqual(f.sum(), 2.)

    def test_hospital_multiplicity_tie_uses_report_equivalents(self):
        scores, weights = np.array([4., 4., 1.]), np.array([2., 1., 1.])
        f = selection_fractions(scores, 0.5, weights)
        np.testing.assert_allclose(f, [2/3, 2/3, 0])
        self.assertAlmostEqual(float(f@weights), 0.5*weights.sum())

    def test_zero_weight_hospital_and_endpoint_budgets(self):
        scores, weights = np.array([5., 4., 1.]), np.array([0., 2., 2.])
        f = selection_fractions(scores, 0.25, weights)
        self.assertAlmostEqual(float(f@weights), 1.)
        np.testing.assert_array_equal(selection_fractions(scores, 0, weights), [0, 0, 0])
        np.testing.assert_array_equal(selection_fractions(scores, 1, weights), [1, 1, 1])

    def test_tied_auc_half_credit_and_capture_denominators(self):
        m = ranking_metrics([1, 0, 1, 0], [1, 1, 0, 0], [4, 8, 2, 0], capacities=[0.25])
        self.assertAlmostEqual(m["AUC"], 0.5)
        self.assertAlmostEqual(m["AP"], 0.5)
        c = m["capacity"]["0.25"]
        self.assertAlmostEqual(c["signal_capture"], 0.25)
        self.assertAlmostEqual(c["case_capture"], 6/14)
        self.assertAlmostEqual(c["precision"], 0.5)

    def test_rounding_defines_ties(self):
        scores = significant_digits([0.12345678901231, 0.12345678901234])
        self.assertEqual(scores[0], scores[1])
        np.testing.assert_array_equal(selection_fractions(scores, 0.5), [0.5, 0.5])

    def test_reject_invalid_capacity_or_weights(self):
        with self.assertRaises(ValueError): selection_fractions([1, 0], 1.1)
        with self.assertRaises(ValueError): selection_fractions([1, 0], 0.5, [1, -1])
        with self.assertRaises(ValueError): selection_fractions([1, np.nan], 0.5)
        with self.assertRaises(ValueError): ranking_metrics([1, 2], [1, 0])


class RealFrozenModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = FrozenModel.load(ROOT/"model")
        cls.heldout = pd.read_csv(ROOT/"data/derived/prediction/heldout_predictions.csv")

    def test_real_heldout_probabilities_from_counts(self):
        p = self.model.predict(self.heldout)
        np.testing.assert_allclose(p, self.heldout.combined, rtol=0, atol=1e-11)
        self.assertEqual(len(p), 18341)

    def test_unknown_procedure_is_not_silently_reference(self):
        row = self.heldout.iloc[:1].copy()
        row["procedure"] = "Unknown procedure"
        with self.assertRaisesRegex(ValueError, "Unknown procedure"):
            self.model.predict(row)

    def test_unknown_or_missing_age_is_rejected(self):
        row = self.heldout.iloc[:1].copy()
        row["age"] = "Unknown age"
        with self.assertRaisesRegex(ValueError, "Unknown age"):
            self.model.predict(row)
        row["age"] = None
        with self.assertRaisesRegex(ValueError, "Missing age"):
            self.model.predict(row)

    def test_actual_zero_expected_predictor_remains_finite(self):
        rows = self.heldout[self.heldout.e_lag1 == 0]
        self.assertGreater(len(rows), 0)
        self.assertTrue(np.isfinite(features_from_counts(rows).to_numpy()).all())
        self.assertTrue(np.isfinite(self.model.predict(rows)).all())

    def test_missing_older_history_uses_only_observed_reports(self):
        rows = self.heldout[self.heldout.history_years == 1]
        self.assertGreater(len(rows), 0)
        features = features_from_counts(rows)
        np.testing.assert_allclose(features.log_prior_sir, features.log_history_sir, atol=1e-14)

    def test_missing_immediate_report_or_inconsistent_missingness_rejected(self):
        row = self.heldout.iloc[:1].copy()
        row["y_lag1"] = np.nan
        with self.assertRaisesRegex(ValueError, "Immediately preceding"):
            self.model.predict(row)
        row = self.heldout.iloc[:1].copy()
        row["e_lag2"] = np.nan
        with self.assertRaisesRegex(ValueError, "consistent missing counts"):
            self.model.predict(row)


if __name__ == "__main__":
    unittest.main()

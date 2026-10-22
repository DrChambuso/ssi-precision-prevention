# Frozen model and exact review-capacity evaluation

This component reconstructs predictions from the study's actual retained lagged counts, frozen coefficients and training scaling. It independently recalculates point estimates. It does not refit the model or rewrite the original bootstrap procedures.

## Run

From the extracted release directory, using the environment specified in `environment/`:

```sh
python scripts/check_frozen_model.py --root .
python -m unittest discover -s tests -p test_frozen.py -v
```

The check writes `validation/frozen_model_check.json` and exits with a nonzero code if any comparison fails. All paths are relative to the extracted release; no author-computer path is required. The executed validation used Python 3.12.14, NumPy 2.3.5 and pandas 2.2.3.

## Inputs and provenance

- `model/model_coefficients.csv`: 33 frozen coefficient estimates, with the archived standard errors and P values retained for provenance. The portable evaluator uses the estimates only.
- `model/training_feature_scaling.csv`: four development means and sample standard deviations.
- `model/model_metadata.json`: reference categories, exact allowed categories, score-rounding rule and target definition.
- `model/report_alert_model.rds`: the original fitted R model object, preserved without refitting. Its coefficients are also supplied as readable CSV; Python evaluation does not deserialize R objects.
- `model/model_fit_audit.txt`: original convergence audit, six iterations and model rank.
- `data/derived/prediction/lagged_prediction_cohort.csv.gz`: all 57,694 actual development and evaluation rows, including the 39,353-row development population.
- `data/derived/prediction/heldout_predictions.csv`: 18,132 California test rows and 209 Oregon evaluation rows, with their archived predictions.
- `reference_results/prediction_metrics_1999_cluster_bootstrap.csv`, `prediction_paired_comparisons_1999_cluster_bootstrap.csv` and `future_SSI_case_capture_comparisons.csv`: original final inference records. These include historical bootstrap estimates; the portable check compares their point estimates without claiming to rerun their uncertainty calculations.

The authoritative readable coefficient and scaling CSVs retain their UTF-8 byte-order mark (BOM). Python/pandas reads these correctly. In R, import them explicitly and check column names before indexing:

```r
coefficients <- read.csv("model/model_coefficients.csv", fileEncoding="UTF-8-BOM", check.names=FALSE)
scaling <- read.csv("model/training_feature_scaling.csv", fileEncoding="UTF-8-BOM", check.names=FALSE)
stopifnot(all(c("term", "estimate") %in% names(coefficients)), nrow(coefficients) == 33)
```

The BOM and line-ending provenance mean byte hashes differ from some original archive CSVs, while all 33 coefficient values and their term order are numerically identical. Numerical equivalence is documented separately from byte identity.

Coefficient, scaling and cohort inputs were copied from the final manuscript project dataset after parsed numerical comparison with the original integrated analysis archive. The original heldout predictions, fitted R object and fit audit were retained from that analysis archive. `provenance/frozen_model_sources.json` records copied-file hashes and comparison details. File hashes are also recorded in the executed validation report.

## Model specification

The unit is an annual hospital-age-procedure service report. The fitted binary target is whether observed SSI counts exceed the source-predicted SSI count in the target year. Adult and abdominal aortic aneurysm repair are the reference categories. The model includes age, 27 procedure indicators and four standardized numerical predictors, plus the intercept, for 33 coefficients.

For previous-year operations N, observed SSIs O and source-predicted SSIs E, the numerical features are:

```text
log_volume        = log(1 + N[t-1])
log_expected_rate = log((E[t-1] + 0.5)/(N[t-1] + 1))
log_prior_sir     = log((O[t-1] + 0.5)/(E[t-1] + 0.5))
log_history_sir   = log((sum available O[t-1:t-3] + 0.5)/
                        (sum available E[t-1:t-3] + 0.5))
```

The immediately preceding report is required. Missing older years are excluded from their sums. They are not imputed and are not reclassified as quiet annual reports. Zero predicted counts remain eligible. Natural logarithms are used. Each feature is centered and divided by its sample standard deviation from the 2017-2022 development rows only. No evaluation mean or scale is estimated.

The frozen probability is the logistic transformation of the intercept, applicable categorical coefficients and four coefficient-weighted standardized features. Scores are rounded to 12 significant decimal digits before ties are defined, reproducing the original ranking specification. Unknown age or procedure labels raise an explicit error; they are never silently assigned to a reference category.

The model was unpenalized, with no variable selection, hyperparameter tuning or calendar-year predictor. The California target years 2023-2025 and the Oregon target year 2017 are evaluated without model refitting or recalibration. California development and later evaluation share 298 hospitals and 6,088 services. The evaluation therefore is temporal and partly overlapping, rather than hospital-disjoint.

## Ranking and capture arithmetic

The portable `ranking_metrics` function gives a positive/negative pair half credit when scores tie in the AUC calculation. Average precision uses distinct score thresholds and stepwise recall increments.

At a review capacity c, the budget is exactly c times the number of eligible report equivalents. Scores above the boundary are fully selected. Every row in a boundary tie receives the same fractional selection weight. Hospital multiplicities, if supplied as weights, are kept separate from selection fractions. The result represents uniform random selection within the tied boundary and is invariant to input row order.

Signal capture divides selected annual signals by all annual signals. SSI-case capture divides SSI counts in selected target reports by all target SSI counts. These are separate denominators and objectives. Precision divides selected signals by selected report equivalents. Capacities of 10%, 20% and 30% are checked against retained final numerical results for the frozen model and prior-count/volume comparators. The prior smoothed O/E comparator is checked for signal metrics as well.

The nominal budget counts report slots. It does not imply equal staff time or equal operation coverage. The primary capacity comparison pools the three California evaluation years; an annual implementation should evaluate its chosen annual budget separately.

## Executed verification

The validation checks all 18,341 heldout probabilities from actual lagged counts. It also reconstructs the four features across the entire 57,694-row cohort, checks development-only scaling, verifies cohort sizes and target-year separation, checks archived standardized features, rebuilds comparator scores, recalculates AUC/AP, and verifies exact-budget signal and case capture.

The first completed run passed all 180 checks in approximately 1 second on an Apple arm64 machine. The JSON report records the actual runtime, input hashes, numerical tolerances, all check results and recalculated metrics. Differences at about 1e-12 in rounded probabilities reflect finite decimal storage of archived coefficients and cross-language arithmetic. Raw probabilities agree within 6e-13. These differences do not alter any validated point metric.

The 12 unit tests cover proportional boundary ties, row-order invariance, hospital multiplicity weights, empty-weight groups, zero/full budgets, tied AUC half credit, distinct capture denominators, score rounding, malformed inputs, actual zero-prediction reports, missing older history, and rejection of unknown categories. These small arithmetic fixtures supplement the complete real-data check; no simulated dataset replaces study data.

## Scope and limitations

No bootstrap interval or P value is newly calculated by this component. The original final signal-performance resampling used 1,999 draws with seed 20261016 and its retained dataset/subgroup loop order. SSI-case-capture resampling used 1,999 draws with seed 20261017 and multinomial hospital multiplicities. These different original procedures are preserved separately in archival analysis code and must not be treated as identical from the draw count alone.

The clinical purpose is to identify surgical services at increased potential SSI risk and focus precision-prevention review. The model predicts an aggregate annual surveillance signal. Its probabilities are not individual patient risks. Captured SSIs describe observed burden reached by a review queue; they do not measure prevented infections or establish clinical effectiveness. National microbiology summaries are separate contextual evidence and are not linked to these California or Oregon records at patient, event or isolate level.

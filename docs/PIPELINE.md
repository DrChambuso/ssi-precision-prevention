# Statistical pipeline and archived implementation

This release preserves the executed study implementations and runs them inside an isolated directory under `results/`. The adapters change filesystem locations and normalize dash characters in visible text. They do not replace model equations, smoothing constants, resampling units, seeds, replicate counts, significance tests or confidence interval definitions. Numerical blocks extracted from earlier mixed delivery or metadata scripts are explicitly identified in `provenance/pipeline_manifest.json`.

The historical source files have absolute author workstation paths. Distributed copies in `pipeline_sources/` replace those prefixes with `__LEGACY_ROOT__` and `__SOURCE_ROOT__`. The runner resolves the tokens only in generated `results/legacy_workspace/runtime_sources/` copies. The manifest records the SHA-256 of the original file and the distributed copy separately. Original study files are not modified.

## Requirements

Use the Python environment described in `environment/` with NumPy and pandas, plus R and the survival package. The final core logistic fit uses R `stats::glm`; it does not use scikit-learn. The independent numerical verification uses NumPy and pandas. The core original R environment was R 4.5.0 with survival 3.8-3. The release distinguishes recorded or reconstructed historical software information from the current verification environment.

The documented runner targets Linux and macOS. It uses an advisory file lock for the execution ledger. `RSCRIPT` can point to a specific Rscript executable. Runtime numerical and figure outputs can be large. Use the frozen scoring and compact verification workflow in the main README for a quicker entry point.

## Inspect and initialize

From the release root:

```text
python scripts/legacy_pipeline.py list
python scripts/legacy_pipeline.py initialize
```

Initialization copies selected factual study inputs and archived reference outputs from `reference_results/pipeline/seed_tree/` to `results/legacy_workspace/`. Large plain-text CSVs are compressed for distribution and restored by the runner. The original source panel and legacy inputs have their own preserved role; a reference table in this tree is not evidence that a stage was recomputed. Only a successful entry in `execution_ledger.json` records actual execution of the named script. Each script also has a complete log.

The workspace must be inside this release's `results/` directory. A different release-local workspace can be supplied using `--workspace results/my_run`. A stage can be executed independently against the archived inputs. To reproduce newly generated dependencies, use the complete sequence below or add `--with-dependencies` for its explicitly recorded prerequisites. Some study analyses share common input archives without a direct procedural dependency.

## Core prediction and hospital-cluster inference

```text
python scripts/legacy_pipeline.py run --stage prediction_prepare --stage prediction_fit --stage prediction_evaluate --stage prediction_diagnostics --stage prediction_verify --stage inferential --stage earlier_context --stage within_unit --stage severity_survival --stage inferential_verify --stage signal_bootstrap --stage case_bootstrap
```

The stage order constructs predictors, estimates a training-only logistic model, evaluates frozen later predictions, fits hospital-cluster models and sensitivity analyses, independently reconstructs score/sandwich calculations, and performs the final paired bootstrap comparisons.

- Training targets are California 2017-2022. Test targets are California 2023-2025. Oregon 2017 is evaluated separately as a compatibility-limited external source.
- Four numeric predictors use training-only centers and sample standard deviations. The model also contains age and procedure factors. Exported coefficients and scaling enable independent scoring.
- A target-year annual signal is `observed SSIs > source-predicted SSIs`. It is a surveillance review outcome and does not identify the onset time of an individual patient's infection.
- Exact report review budgets use fractional inclusion at tied score boundaries. Comparators and the history-informed model use the same hospital draws.
- The final signal bootstrap uses 1,999 draws and seed 20261016. The final future SSI case-capture bootstrap uses 1,999 draws and seed 20261017. These supersede earlier single-method exploratory confidence intervals for the paired comparison.
- `survival_absolute`, available separately, uses 999 draws and seed 20261018 for absolute five-year signal probability differences.

## Frozen exploratory service profiles

```text
python scripts/legacy_pipeline.py run --stage service_profiles_fit --stage service_profiles_panels --stage service_profiles_verify
```

This is a separate descriptive profile analysis. K-means centers and PCA scaling/loadings are learned in training data and then frozen for projection onto the later reports. The fit uses seed 20261019; the optional display sample uses seed 20261020; the later profile prevalence bootstrap uses seed 20261021. All 18,132 later reports are retained in the final full projection. These profile labels are distinct from the national compositional microbiology profiles and the logistic model's predicted signal probability.

## National microbiology analyses

```text
python scripts/legacy_pipeline.py run --stage microbiology_tables --stage microbiology_exact --stage microbiology_context_tables --stage microbiology_profiles_prepare --stage microbiology_profiles_fit --stage microbiology_profiles_evaluate
```

The downstream reconstruction starts from preserved factual table extracts: span-expanded 2015-2017 HTML table content and checked 2018-2021 PDF page text. Count partitions, phenotype rounding bounds, exact R tests and family-specific BH calculations can be regenerated. These are published aggregate pathogen-report marginals. They do not provide patient, event, isolate or hospital linkage to California. Resistance and nonsusceptibility remain distinct, suppressed values remain missing, and reconstructed rounding-compatible bounds remain derived quantities.

The `microbiology_context_tables` adapter retains all original numerical context calculations, including completeness fields and cross-period replication, while retaining archived source metadata. It omits only the original-file checksum refresh block and does not claim to re-verify raw bytes.

The separate stages `microbiology_extract` and `microbiology_context` require original source files supplied using `--source-root`. That directory must contain the two historical source subdirectories listed in the provenance documentation: `Conference Bloodstreem Dataset/Sources/CDC_AR/` and `Survaillance dataset/Sources/CDC_AR/full-hai-pathogens-ar-report/`. `microbiology_extract` parses the 2015-2017 HTML files. The retained historical code does not itself perform the 2018-2021 PDF-to-page-text conversion. For a new extraction, preserve PDF hashes, extract the identified pages with layout retained, and compare every parsed row with the archived factual extract before running downstream tests. The `microbiology_context` stage verifies original source-file hashes as part of producing context metadata; it deliberately does not fabricate source bytes or hashes when originals are absent.

## Vector figure generators

```text
python scripts/legacy_pipeline.py run --stage figures_base --stage figures_microbiology
```

These scripts generate the archived scientific vector panels from numerical tables. Run `microbiology_context_tables` after rebuilding microbiology tables so the completeness fields required by the national figure generator are present. Updated runtime statistics are synchronized into their historical read locations. The resulting files are under `results/legacy_workspace/outputs/SSI_Prevention_Intelligence/SSI_Inferential_Microbiology_Figures/individual_vector_pdfs/`.

Final main-text and supplementary figures additionally underwent vector panel assembly, panel lettering, font resizing, annotation removal and page-layout edits. The figure provenance crosswalk identifies the final assets and the distinction from the base analytical panels. A successful base generator is not a claim of pixel-identical reproduction of later editorial layout.

## Compare regenerated numerical outputs

```text
python scripts/legacy_pipeline.py compare --table work/ssi_new_prediction/model_coefficients.csv
python scripts/legacy_pipeline.py compare --table work/ssi_inferential_stats/two_year_memory_contrasts.csv
python scripts/legacy_pipeline.py compare --table work/ssi_inferential_stats/prediction_paired_comparisons_1999_cluster_bootstrap.csv
python scripts/legacy_pipeline.py compare --table work/ssi_inferential_stats/future_SSI_case_capture_comparisons.csv
```

Comparison requires identical rows, columns, text and missing-value locations, plus numeric agreement within the declared tolerance. The default absolute and relative tolerance is 1e-7 and can be tightened using `--atol`. No test outcome is inferred from filenames. Machine-readable comparison results, actual execution logs and a release verification summary are retained under `validation/` or the corresponding generated workspace. Bootstrap uncertainty is conditional on the frozen training fit. No clinical prevention benefit follows from a successful numerical reproduction.

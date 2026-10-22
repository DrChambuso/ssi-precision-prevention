# SSI precision-prevention study: reproducibility release

Version 1.0.0-rc2, prepared 22 October 2026.

Source reconstruction, statistical inference, frozen prediction, national microbiology analysis and vector-figure materials for *Early surgical site infection signals across 6.7 million operations and procedure specific pathogen guide for prevention*.

**License status: pending institutional approval. No open-source license has been granted.**

This is the paper-associated release candidate. Numerical verification and execution records are in `validation/`. Public hosting, the permanent identifier and the authors' software-license decision are recorded in `RELEASE_STATUS.json`; the repository is at https://github.com/DrChambuso/ssi-precision-prevention . A DOI has not been assigned. See `docs/RELEASE_CHECKLIST.md` before submission. Public sharing is authorized while the institutional license decision remains pending.

## Paper-associated version

The complete reproducibility package is supplied with the versioned GitHub release. It contains the data, serialized model, all code and vector figures. The repository source tree and the downloadable package have matching scientific contents.

Public repository: https://github.com/DrChambuso/ssi-precision-prevention

The exact published version and commit link will be confirmed in the release record. The software license remains pending institutional approval.

## Start here

Use Python 3.12.14 with the core requirements and R 4.5.0 for the inferential workflow. No GPU is needed. Paths are relative to the extracted repository.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r environment/requirements-core.txt
python scripts/reconstruct_surveillance.py
python scripts/check_frozen_model.py --root .
python -m unittest discover -s tests -v
python scripts/legacy_pipeline.py --help
```

The first two commands after installation use the actual supplied study aggregates and frozen model. They require no network access and do not refit the prediction model. See `validation/` for the measured verification times and `environment/` for the environment actually tested. A fresh isolated environment installed all six pinned core dependencies in 22.06 seconds; all 180 frozen-model checks and 15 unit tests then passed. Installation time depends on the machine and network. See `docs/INDEPENDENT_REVIEW.md` for measured demo times and the tested scope.

To verify the original source files as well:

```sh
python scripts/fetch_california_sources.py --destination data/raw/california
python scripts/reconstruct_surveillance.py --source-dir data/raw/california
```

The acquisition script checks the original SHA-256 values. It stops if a live source has changed. The retained source-row crosswalk identifies each original file and data-row position, the canonical hospital/service identity and procedure. Offline reconstruction begins with that supplied extraction; the optional raw-source check validates all underlying counts. Historical acquisition dates that were not retained are identified as unknown.

## What the model predicts

The clinical purpose is to prioritize surgical services for precision-prevention review. The fitted statistical target is whether an annual hospital-age-procedure report has observed SSIs above the source-predicted count. The source's risk-adjusted predicted infection count and this model's signal probability are different variables. Capture quantifies subsequent reported SSI burden reached by review; it does not estimate infections prevented or individual-patient onset.

California hospital surveillance and national NHSN pathogen/resistance summaries are separate aggregate populations. They are not linked by patient, hospital, infection event or isolate. Do not combine their denominators.

## Repository guide

| Location | Contents |
| --- | --- |
| `data/derived/` | Canonical California annual data, original-row crosswalk and frozen prediction cohorts |
| `data/Data_dictionary.csv` | Master variable definitions, units and missing-value meanings |
| `model/` | All 33 coefficients, four training centers/scales, serialized R fit and explicit factor coding |
| `src/ssi_repro/` | Portable frozen probability, ranking and capture implementation |
| `scripts/` | Reconstruction, frozen checks, historical-stage runner and vector audit |
| `pipeline_sources/` | Path-adapted original analytical implementations with provenance hashes |
| `reference_results/` | Retained numerical targets and required historical inputs |
| `figures/` | Final vector masters with final-number crosswalk and integrity report |
| `figure_sources/` | Retained editorial/vector finishing code, with regeneration scope documented |
| `docs/analysis_specification.json` | Machine-readable study specification, seeds, formulas and inference families |
| `docs/PIPELINE.md` | Stage commands, dependencies, executed stages and limitations |
| `docs/FROZEN_MODEL.md` | Predictor definitions, factor references, exact scoring and verification |
| `docs/FIGURES.md` | Final figure mapping, vector scope and regeneration instructions |
| `provenance/` | File lineage, source URLs/hashes and clearly marked archived audits |
| `validation/` | New executed checks, tolerances, execution logs and numerical comparisons |
| `manifest.sha256` | Release-file integrity values, excluding runtime outputs |

## Analysis conventions that must remain fixed

- One California record is a hospital-age group-procedure-calendar year, not one patient. Only exact calendar-year predecessors supply lags. Missing reports are never converted to quiet years.
- The 2020 nonoverlapping half-year counts are summed within the annual key. Overlapping annual versions must not be added again.
- Earlier feature transformations use the specified 0.5 smoothing and training-only means and sample standard deviations. The 2023-2025 test cohort does not enter model fitting or scaling.
- All ranking scores are rounded to 12 significant digits. Ties at a fixed review boundary are selected proportionally, with the exact report budget shared by all tied reports.
- Signal bootstrap inference uses 1,999 whole-hospital draws, seed 20261016. Case-capture inference uses 1,999 multinomial hospital draws, seed 20261017. Sampling order and implementations are preserved separately.
- Inference, multiplicity families, nonestimable-model rules and national composition/resistance denominators are specified in `docs/analysis_specification.json`. Do not infer individual-level risks from report shares.

## Reproducing figures and analyses

Start with `docs/PIPELINE.md`; full stages write into a separate release-local results workspace. Frozen coefficients and reference results are inputs and are not overwritten. Do not confuse historical figure numbers with the final manuscript: the former Figure 14 is current Figure 12. Final-number mappings and unresolved manuscript caption gaps are explicit in `docs/FIGURES.md`.

Standalone PDF masters are retained as vector artifacts. A Word preview is not evidence of vector content. The vector audit counts image XObjects and checks extractable text/fonts; see its scope and exceptions before describing an entire artwork as purely vector.

## Validation and reuse

A test pass applies only to the inputs, commands and environment recorded in its report. Archived audits are provenance, not evidence of a new rerun. Full source-to-final-layout reconstruction is only claimed for stages actually executed and compared. The release checklist identifies any remaining gaps.

Use `CITATION.cff` to cite the software after the public version identifier is assigned. Keep the data-source notices in `THIRD_PARTY_NOTICES.md`. Direct correspondence to Ramadhani Chambuso, r.chambuso@ajman.ac.ae.

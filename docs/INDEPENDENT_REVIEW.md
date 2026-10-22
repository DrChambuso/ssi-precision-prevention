# Independent release review

Reviewed on 22 October 2026. The executed record is `validation/independent_release_review.json`.

## Portability checks actually executed

The release was copied to a temporary directory under `/tmp`, with a space in its directory name. Previous generated analysis results and Python caches were excluded from the copy. Commands ran from that relocated directory with a minimal environment, without `PYTHONPATH`, `CODEX_HOME` or `RSCRIPT` path overrides. No original author-computer data directory was configured.

The following commands completed successfully using the existing tested Python dependency runtime:

```sh
python scripts/reconstruct_surveillance.py
python scripts/check_frozen_model.py --root .
python -m unittest discover -s tests -v
python scripts/legacy_pipeline.py list
```

The surveillance reconstruction passed with the actual supplied 78,583 source-row records, 72,854 annual reports, 6,737,972 operations and 37,525 SSIs. The relocated frozen-model check passed all 180 checks. All 15 current unit tests passed, including the three source-reconstruction tests and 12 frozen-evaluation tests. Listing legacy stages verifies that the manifest and runner resolve relative to the relocated release; it does not mean every listed stage was executed by this review.

## Independent R artifact check

The original `model/report_alert_model.rds` was loaded in R 4.5.0 from the relocated release. Its actual model factor levels confirm the prediction reference categories:

- Adult age group.
- Abdominal aortic aneurysm repair procedure.

The model contains 33 coefficients. Their maximum absolute difference from the readable coefficient CSV was 4.67e-15, consistent with finite decimal serialization. Predictions from the original R object agreed with archived heldout probabilities within 1.01e-12 after the specified 12-significant-digit score rounding.

The prediction model's procedure reference is distinct from the association-model reference. The retained inferential script explicitly releveled procedure to colon surgery. The prediction script uses the first alphabetical procedure factor level, abdominal aortic aneurysm repair. The public model metadata correctly records the prediction reference. No reference category was substituted across these different models.

## CSV lineage and import safety

The authoritative model CSV retains a UTF-8 BOM and differs in bytes from the original archive CSV. Both archive variants in the reference seed tree contain the same 33 coefficient values and term order after correct parsing, with maximum parsed estimate difference 0. Byte equality and numerical equivalence are distinct provenance checks.

For R import, `docs/FROZEN_MODEL.md` now shows `fileEncoding="UTF-8-BOM"` and an explicit column-name/row-count assertion. This avoids accidental header mismatch under a different locale. The independent R check validates column presence and matching model term names before calculating coefficient differences.

## Fresh dependency installation and clean-environment checks

A separate fresh isolated Python 3.12.14 virtual environment was created under `/tmp`, without inheriting installed system packages. All six exact pinned core dependencies were downloaded and installed with pip using the supplied requirements, with no package cache and no global installation. Environment creation took 1.42 seconds; the timed network dependency installation took 22.06 seconds on the tested macOS arm64 machine.

The actual relocated release then ran successfully using that new environment:

| Command | Measured elapsed time | Result |
| --- | --- | --- |
| Surveillance reconstruction | 15.88 seconds | Passed actual source-row and annual-panel checks |
| Frozen-model verification | 0.87 seconds | All 180 checks passed |
| Unit test suite | 0.40 seconds | All 15 tests passed |

These are whole-process elapsed times. The first surveillance process includes initial imports and startup in the new environment. Installation duration depends on the machine, network and package source and is not a universal estimate.

The earlier offline install attempt failed because no cached NumPy wheel was available, and the default sandbox network attempt encountered a DNS restriction. Those environment-availability outcomes did not establish a package defect. Downloading the same pinned dependencies with approved network access succeeded. The executed report preserves both the earlier relocation checks and the successful clean-install commands, measured durations and installed versions.

This clean installation validates the core Python environment and its documented checks. It does not claim a fresh installation or full end-to-end rerun of all historical R, microbiology and figure-production environments.

## Remaining release boundaries

This review did not independently rerun every inferential model, bootstrap interval or figure layout. Their actual execution and comparison records must be assessed separately. Runtime output folders can contain environment-specific paths and should not be confused with portable source inputs. Public hosting, a persistent archive identifier and an approved software license remain publication-release decisions.

# Release readiness and author handover

The release is version 1.0.0-rc2. It is a technically verified local release candidate, not an announced public deposit. The main manuscript was not reproduced or edited.

## Completed and supported by executed evidence

- Validated all 78,583 retained California source rows against the counts and file hashes of all 22 original CSV files; annual reconstruction reproduces 72,854 reports, 6,737,972 operations and 37,525 SSIs.
- Reconstructed all 18,341 retained held-out probabilities, including the separately identified Oregon compatibility cohort; the California test subset remains 18,132 reports. All 180 frozen-model checks pass.
- Reran 23 analytical/plotting stages, including the training-only fit, clustered models, earlier-context and within-unit sensitivity, service profiles, national microbiology analyses and distinct 1,999-draw signal and case bootstraps.
- Compared 28 regenerated numerical tables with their archived targets. All comparisons pass; the maximum absolute numeric difference is 8.27e-25. The frozen coefficient, scaling and prediction tables and both final paired-comparison tables reproduce exactly in the recorded environment.
- Preserved 32 final PDFs (11 actual main figures plus S01-S21), 56 pages, with zero displayed raster images. Preserved original manuscript SVGs for the five relevant exports. Main figure 12 was regenerated from derived tables with identical extracted text and pixel-identical rendering at 144 dpi.
- Ran the relocated package with actual study inputs from a temporary folder containing a space, without author-specific environment paths. All 15 unit tests pass. See the independent review for the fresh-install result and measured timing.
- Recorded historical versus current software environments separately, source and script hashes, scientific definitions, figure mappings, software citation metadata and third-party notices.

## Outstanding publication checks and license status

1. Keep the license pending institutional approval until an authorized decision is received. Public repository creation is authorized; no open-source reuse license is being granted. Add the approved LICENSE text and SPDX identifier to CITATION.cff. Data and dependencies retain their separate terms.
2. Select the public repository and archive the paper-associated version. Use the actual version-specific DOI or permanent URL in the Code availability statement and software citation. Test access without an authenticated session.
3. Reconcile the existing main-manuscript figure-number gap (6 and 7) and the figure 11 caption. These editorial issues are recorded without altering the final manuscript during code preparation.
4. Keep the documented computational boundaries explicit. Original national PDF page extraction and every historical editorial finishing operation have not been certified as one automatic source-to-final-layout run.

## Seal the approved release

After changing license or identifier metadata, rerun the checks, update the version/status as appropriate and regenerate the integrity manifest. The supplied archive SHA-256 refers to this release candidate only. Do not attach that digest to a modified archive.

```sh
python scripts/reconstruct_surveillance.py
python scripts/check_frozen_model.py --root .
python -m unittest discover -s tests -v
python scripts/audit_release.py --write-manifest
python scripts/audit_release.py
```

The user authorized public GitHub hosting and explicitly kept the license pending institutional approval. The DOI, GitHub account, author permissions and independent human statistical review are not fabricated. The peer review here was a separate computational review within this preparation workflow.

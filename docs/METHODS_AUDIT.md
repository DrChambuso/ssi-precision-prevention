# Methods and reproducibility release audit

Read-only audit dated 2026-10-22. Originals were preserved. No model was refitted and no full analytical pipeline was rerun in this audit.

## Verified directly in retained files

- The latest working manuscript is outputs/Manuscript_with_hypothesis_references.docx. The final supplement is outputs/submission_supplementary_material/Submission_files/Supplementary_Material.docx.
- Frozen coefficient CSV contains all 33 model coefficients. All coefficient values match Supplementary Table S2 exactly at the stored decimal precision (maximum absolute difference 0). All four centers and scales match Supplementary Table S1 exactly (maximum difference 0).
- Archived R session confirms R 4.5.0, survival 3.8-3 and Matrix 1.7-3, aarch64-apple-darwin20, with R BLAS and LAPACK 3.12.1.
- Original frozen-fit code standardizes numeric features using training means and sample standard deviations; fits binomial logistic GLM; freezes predictions; rounds all method scores to 12 significant digits; and writes coefficient, scaling, fit audit, predictions and fitted R model files.
- Final signal inference code specifies 1,999 hospital bootstrap samples, NumPy default_rng seed 20261016, paired methods, proportional boundary ties, percentile confidence limits and the centered-null two-sided bootstrap P value. Its hospital-draw sequence depends on the exact dataset and subgroup loop ordering, which must be preserved for exact replication.
- Original SSI-case-capture implementation specifies 1,999 paired hospital multinomial draws with seed 20261017, the same boundary-tie budget rule, and six-comparison BH correction. It must not be replaced with the signal script merely because both draw counts equal 1,999.
- Retained master reconstruction audit reports 78,583 original source rows from 22 CSV files, reconciled to 72,854 annual rows. A separate final audit contains 181 checks and an empty issues list. These retained audit reports were inspected, not rerun here.

## Exact specification recovered

analysis_spec.json contains cohort populations, outcome definitions, four predictor transformations, all frozen coefficients/scaling, follow-up rules, sparse-model rules, inference details, multiplicity families, operational and national profiles, rounding-compatible AMR count rules, and all final main figure legend bindings.

Bootstrap procedures remain distinct: 400 full-panel descriptive draws; 250 original calibration/loss draws; 1,999 final prediction and case-capture draws with different seeds and RNG sampling procedures; 999 absolute five-year differences; 1,999 later operational-profile draws; source-profile bootstrap or exhaustive enumeration for national depth summaries.

## Issues to address in a public package

1. Public code location, versioned archive identifier and author-selected license are not confirmed in the manuscript. Do not claim public availability or fabricate a DOI, GitHub URL or authors' license choice.
2. The current main Methods states Python 3.12.14, pandas 2.2.3 and NumPy 2.3.5, plus NumPy 2.5.4/Matplotlib 3.11.2 for figures. The supplement explicitly distinguishes Python 3.12.14/pandas 2.2.3/NumPy 2.3.5 as the reanalysis audit environment, not all original runs. Capture current tested dependencies independently and distinguish archival records from a new release environment.
3. Retained scripts contain absolute author-computer paths and historical output locations. A public release must use package-relative configuration. Keep original scripts as provenance and document adapters, so changes do not silently alter analyses.
4. Multiple legacy figure variants exist. The final manuscript contains main Figures 1-13 and the supplement contains Figures S1-S21. Former Figure 14 is current main Figure 12. Match results and cleaned figure output to the actual final manuscript rather than relying on original numbers. The supplied figure allocation crosswalk also identifies caption inconsistencies in main Figure 1 and Figure 11 that should not be silently treated as verified corrections during code packaging.
5. Some main figures are embedded as raster previews even though standalone vector masters exist. A release should preserve standalone source vector masters and identify exactly which output file is authoritative; do not call every embedded Word image vector.
6. The clinical aim is potential SSI occurrence and precision-prevention review at the surgical-service level. The fitted target is an annual observed-count-above-source-predicted signal. Capture measures burden reached by review, not prevented infections. The release must preserve that unit and distinction.
7. California hospital annual panels and national NHSN microbiology summaries are separate aggregate populations. No isolate, patient, SSI event or hospital linkage should be inferred. National count-test CIs do not reconstruct hospital clustering.
8. National source-profile alternative report-weighted bootstrap seed was not verified in this limited read-only audit. Retain the exact corresponding original implementation and output record rather than infer the seed from adjacent methods.

## Source locations useful to packaging

- Desktop manuscript project: author_archive/Desktop/AJ_Unv_Microbiology/AU_Proposals/15-SURGICAL_INFECTIONS/1_FOR AU GRANT SUBMISSION/1_For sumission/1_TRANSLATIONAL MEDICINE
- Frozen model and figure-level datasets: Final Dataset/figure_data/prediction and Final Dataset/figure_data/final_analyses/statistics beneath that project.
- Original source and analysis scripts: archive:legacy_integrated_release
- Original final integrity checks: archive:analysis_root/work/ssi_final_dataset
- Current figure layout scripts: current_work/work, including redesign_fig14_advanced.py and supplement reconstruction/cleanup scripts.

All new visible text uses ASCII hyphen-minus. JSON serializes non-ASCII source characters safely and has no prohibited Unicode dash/minus characters.

## Subsequent release validation

This document records the initial read-only methods audit. It preceded the release-local analysis reruns. Consult the new execution, numerical comparison, frozen-model and relocation reports in `validation/` for what was subsequently executed. The initial audit's statement that no model was refitted describes that audit only.

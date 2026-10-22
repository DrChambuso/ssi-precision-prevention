# Figure provenance, regeneration and structural audit

## What is supplied

The release preserves 32 final figure PDFs: 11 numbered main-text figures and all 21 supplementary figures. Main-text numbers are 1-5 and 8-13. The reviewed manuscript contains no figure numbered 6 or 7. This numbering gap is recorded rather than filled with invented or duplicated figures. Confirm numbering in the submission manuscript before publication.

`provenance/figure_crosswalk.csv` identifies every archived figure, its historical source label, its source SHA-256, its release SHA-256 and any conversion. Historical analytical figure IDs, older main-text IDs and final manuscript IDs are different namespaces. For example, final main figure 12 derives from the historical main figure 14 layout; the original statistical atlas figure 12 is an Oregon transport analysis. Use the crosswalk instead of matching numbers alone.

The figure PDFs are publication artifacts, not proof that all scientific analyses have been rerun. The archived numerical results, full pipeline and validation reports elsewhere in this release establish the scope of computational reproduction.

## Main-text mapping

| Final manuscript figure | Source represented | Release operation |
| --- | --- | --- |
| 1 | Historical main1, main2 and lower annual-composition component main3 | Exact combined PDF copy |
| 2 | Historical main4 and main5 | Exact combined PDF copy |
| 3 | Maximum-population all-age, adult and pediatric follow-up with summary | Exact manuscript SVG retained; vector PDF exported |
| 4 | Adult maximum-population procedure timing | Exact manuscript SVG retained; vector PDF exported |
| 5 | Common-2018 adult procedure sensitivity | Exact manuscript SVG retained; vector PDF exported |
| 8 | Historical main10, analytical figure 27, frozen earlier service profiles | Exact combined PDF copy |
| 9 | Historical main11, held-out procedure ROC curves | Exact manuscript SVG retained; vector PDF exported |
| 10 | Historical main12, analytical figure 28, national microbiology profiles | Exact compact PDF copy |
| 11 | Historical main13, analytical figure 24, age-period resistance panels | Exact compact PDF copy |
| 12 | Historical main14, complete procedure table with capture gains and selected pathogen enrichment | Exact final PDF copy; executable derived-table renderer also provided |
| 13 | Historical main15, analytical figure 19, conceptual layered review | Exact manuscript SVG retained; vector PDF exported |

The source manuscript itself and its personal metadata are not redistributed. The five embedded SVGs needed to preserve final artwork are in `figure_sources/manuscript_svg/`. Their text is largely glyph outlines, which remain scalable vectors but are not searchable text. The original SVGs remain the authoritative artwork for those exports.

## Supplementary figures

All S01-S21 are retained with their assigned numbers. S08 uses the later one-page combined a/b revision rather than the earlier two-page version. S21 preserves the unique conceptual material previously numbered main16. It is not a measured set-overlap analysis. The other supplementary PDFs are byte-identical copies of the final submission figure assets. See the crosswalk for titles and source hashes.

## Executable figure 12 rendering

Run from the repository root after installing the optional figure dependencies:

```sh
python scripts/regenerate_main_12.py --font-dir /path/to/lawfully-installed/Arial
```

The supplied directory must contain `Arial.ttf`, `Arial Bold.ttf` and `Arial Italic.ttf`. Fonts are not redistributed. On a Mac with these fonts lawfully installed, their directory is usually `/System/Library/Fonts/Supplemental`. On other systems, supply an equivalent licensed installation using the same filenames. Do not rename an unrelated font and represent the output as typographically identical.

The renderer uses `pypdf`, `reportlab` and `lxml`. It writes to `generated_figures/main12/` so that archived final artwork is preserved. Internal output names retain the historical figure 14 identifier for traceability. The displayed table and all plotted estimates are unchanged by the path adaptation.

This is genuine figure rendering from the archived numerical tables in `data/derived/main12/`. Panel a reads a verified 28-procedure display cache. Panels b and c read paired capture and pathogen-enrichment results, including confidence limits, from their supplied derived tables. It does not reconstruct raw surveillance sources, fit models, recompute bootstrap confidence intervals or independently validate the source tables. Those steps belong to the statistical workflow.

No automatic font substitution is enabled, because font changes can alter alignment and text width. A user who elects to use an open-source metric-compatible alternative must update the three font registrations explicitly, document the substitute and inspect the resulting figure. Such an export can preserve scientific values and vector geometry while differing typographically from the archived master.

The release validation report records the comparison actually achieved for the renderer. A successful run is not a claim of exact file-byte equality: PDF creation dates and metadata can differ even when rendered artwork and extracted text agree.

## Archived editorial scripts

`figure_sources/editorial_archive/` contains 17 historical finishing scripts. They document lower-case bold panel labels, font consistency, legends, panel spacing, compact headers, supplementary cleanup and selected numerical annotation restorations. These are provenance records, not a portable one-command recreation of every final figure.

Private absolute path constants have been replaced by a logical path adapter. `provenance/editorial_code_adaptation.json` records hashes of the historical and adapted files. The changes normalize source formatting and adapt paths, without changing the scientific formulas or constants. The archives require historical intermediate assets not all contained in this release. The explicit environment variables are `SSI_EDITORIAL_WORKSPACE`, `SSI_EDITORIAL_PROJECT`, `SSI_FONT_DIR` and, for unresolved legacy basenames, `SSI_EDITORIAL_UNRESOLVED`. Missing configuration fails with an explanatory error.

Do not execute archived scripts to overwrite the final masters. Their operations can be sequential, state-dependent edits of older PDFs. The final masters and source hash crosswalk are the authoritative released artifacts. The upstream numerical figure builders and statistical scripts, where supplied elsewhere in the release, are distinct from these finishing operations.

## Structural audit

Install the optional `PyMuPDF==1.28.2` dependency, then run:

```sh
python scripts/audit_vectors.py
```

This recreates `validation/vector_audit.json`. The audit counts displayed raster image occurrences, image resources, vector paths, extractable text, font resources, embedding status and prohibited dash characters in extractable text. It handles multiple-page supplementary figures.

The initial audit found no displayed raster images across the 32 archived PDFs. This means that the audited artwork contains no displayed bitmap image objects; it does not certify scientific accuracy or make outlined text editable. Font resources and embedding findings are listed explicitly in the JSON. Main figures 1 and 10 contain unused standard Helvetica resources that are not embedded. No unembedded fonts were found among extractable text. Glyph outlines do not require embedded font files.

Five SVG-to-PDF conversions are separately documented in `validation/svg_conversion_audit.json`. PDF export can change rendering antialiasing or coordinate precision. The source SVGs are retained to avoid claiming that conversion creates a more authoritative source. Inspect the supplied conversion comparisons and the figure at its intended display size before production.

The ASCII dash requirement can be checked automatically for extractable PDF text. Outlined SVG glyphs require source or visual review; a zero extracted-text count does not establish that visible text is missing or that its original character encoding was ASCII.

## Remaining release limitations

- Reconcile absent main figure numbers 6 and 7 in the manuscript before final submission.
- Preserve the original SVGs for the five outlined-text figures and review any downstream PDF conversion.
- Final figure legends must be checked against the current manuscript, particularly the four-panel resistance figure 11, whose older caption described two age-block panels.
- Historical finishing scripts are preserved, but complete automated recreation of every final editorial layout has not been claimed or tested.
- Final public repository identity, archival identifier and applicable licenses must be confirmed by the author group. These files do not themselves constitute a public deposit.

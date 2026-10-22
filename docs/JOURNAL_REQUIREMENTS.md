# Code release policy evidence and practical checklist

Policy access date: 2026-10-22. Prepared for the SSI surveillance and microbiology study. This is a preparation and review document, not evidence that a public release, DOI registration, permission review, or author approval has occurred.

## Scope and interpretation

The study uses custom source reconstruction, statistical analysis, frozen-model evaluation, and figure-generation code central to its claims. The central-code provisions therefore apply. The journal's policy does not prescribe Python rather than R, a particular workflow engine, a container, a particular open-source license, or the exact repository structure below.

The original statement that materials are retained with study records does not identify an accessible software version. It should not be presented as a completed public code release. A reserved DOI is not an active public deposit. A repository URL without a tag or commit does not unambiguously identify the version used for the paper.

## Journal requirements and recommendations

| Item | Status | Evidence and study implication |
| --- | --- | --- |
| Provide central custom code to editors and reviewers on request | Journal requirement | Nature Medicine requires access to previously unreported central code/algorithms. Prepare reviewer-accessible code rather than relying only on an author statement. [S1] |
| Include a Code availability statement | Journal requirement | State access method and restrictions. Place after Data availability and before references under the journal's section guidance. Identify the actual maintained version and license. [S1, S2] |
| Supply versioned code and documentation for software review | Submission guideline requirement when central new software/code is assessed | Provide code, version information, README, installation details, dependencies, hardware requirements, example-data demo, and installation/run-time information. A ZIP or accessible link is accepted. [S2] |
| Maintain the paper-associated version | Publication condition in software guidance | Preserve code, test inputs, parameters and documentation for the reported version. Repository delivery is an alternative to supplementary software if the version is maintained and uniquely identified. [S2] |
| Deposit code in a DOI-minting repository and cite it | Journal recommendation / best practice | Archive the release in Zenodo, Code Ocean or a suitable persistent repository; formally cite the code in the references. Do not call GitHub-plus-Zenodo a uniquely mandated route. [S1] |
| Use an OSI-approved license | Journal recommendation | The authors must approve an applicable license; record any restrictions. The policy does not mandate MIT, BSD, GPL or Apache. [S1, S2] |
| Ask an unfamiliar colleague to install and run the code | Strong recommendation in software guidance | Record the independent reviewer's environment, commands, expected outputs and discrepancies rather than asserting independent validation without evidence. [S2] |
| Provide a reporting summary | Journal requirement where relevant | The life-sciences reporting summary should describe actual collection and analysis software, versions, statistical design and code access consistently with the repository. [S1] |

These classifications preserve the difference between the policy's mandatory language and its recommendations. Editors determine the acceptable final form, particularly if restrictions exist. [S2]

## Repository and persistent identifier practice

- Develop in a version-controlled repository. Archive a paper-specific release and keep its commit hash and release tag in the software manifest. GitHub documents a Zenodo integration that archives each GitHub release with a DOI; organizational access can require the repository owner's approval. [S3]
- Cite the DOI for the exact archived version used to produce the paper. Zenodo distinguishes a version DOI from a concept DOI covering all versions. Keep both when supplied by the archive, but use the version DOI to identify the reproducibility target. [S4]
- Include accurate citation metadata. GitHub displays preferred software citations from a root `CITATION.cff`. If `.zenodo.json` is also present, Zenodo uses that metadata instead of `CITATION.cff`, so the records must agree. [S5, S6]
- Include the authors' approved software license as an actual license file. A public GitHub repository alone does not grant the broad reuse permissions of an open-source license. Keep third-party license notices and distinguish software licensing from source-data rights. [S7]
- If a DOI is reserved in a draft, mark it as reserved and unpublished in working records. Registration occurs when the Zenodo record is published. Do not announce that readers can access a release until the landing page and files have been checked without an authenticated session. [S8]

## Practical release gates for this study

The items below are study-specific recommendations, not a verbatim journal checklist. The release should show each item's status and evidence rather than marking all items complete by default.

### 1. Provenance and release boundaries

- Inventory every analysis and figure-producing script; map it to main-text and supplementary outputs.
- Record the source identity, URL, retrieval date if known, original filename, file hash, table/sheet/page, and any manual extraction or correction.
- Mark missing retrieval dates as unknown. Do not substitute this policy access date for an earlier data acquisition date.
- Identify third-party source-data terms, redistribution permissions, identifiers and access instructions. Provide lawful download/reconstruction instructions where redistribution is not allowed.
- Exclude unrelated personal records, credentials, local absolute paths, protected health information, account details and unpublished third-party material from the release archive.
- Keep raw sources unchanged. Put transformations and adjudicated corrections in auditable code or a correction table.

### 2. Data definitions and analysis reconstruction

- Document the hospital-age-procedure-year unit, denominator, reported SSI count, predicted count, eligibility rules and missing/suppressed-cell handling.
- Define signals as observed SSI counts above the source-predicted count and preserve the model's actual statistical target separately from the clinical prevention aim.
- Verify source-to-analysis row counts, exclusions, duplicates, join cardinalities and year/age/procedure crosswalks.
- Keep California surveillance and national microbiology sources explicitly separate; do not imply patient, event, hospital or isolate linkage.
- Map all analyses to prespecified or exploratory status where the study records establish it. Do not retrospectively label an analysis prespecified without evidence.

### 3. Statistical specification

- Export actual formulas, family/link functions, offsets, covariates, interactions, contrasts, reference levels, clustering unit and small-sample corrections where used.
- Store the actual adjustment baseline construction and nonoverlap rules, time ordering and target-year windows.
- Record confidence-interval construction, two-sided testing conventions and multiple-testing families, including the actual BH correction scope.
- Specify whole-hospital bootstrap sampling, number of resamples, random seeds, stratification if any, repeated-hospital handling, failed fits and interval method.
- Preserve the actual handling of unavailable estimates, zero counts, nonestimable effects and missing covariates.
- For pathogen shares, report denominator definitions, pooling rules, taxon harmonization, period replication rules and ratio/CI methods.

### 4. Frozen prediction artifact

- Export every actual predictor in order, its definition, transformation, reference coding and training-only centering/scaling values.
- Export fitted coefficients, intercept, class/target encoding and the exact probability formula or serialized estimator with its software version.
- Identify the training, tuning and final test partitions, the freeze point if documented, and any calibration or threshold-selection procedure.
- Specify missing-value treatment, clipping, category handling, report ranking and tie-breaking rules at 10%, 20% and 30% capacity.
- Recompute several predictions independently from the coefficient/scaling export and compare against the saved model output.
- Include actual evaluation code for discrimination, calibration if performed, signal capture, case capture and paired differences, with correct denominators.
- Never use synthetic demo estimates or a newly fitted replacement model as evidence for the manuscript's frozen model.

### 5. Environment and operation

- Provide the tested operating system, language versions, pinned direct and transitive dependencies where feasible, and system libraries/font requirements.
- Document installation, example input, commands, expected outputs, measured install time, measured runtime and tested hardware.
- Offer a clear workflow order from acquisition/reconstruction through analysis, model evaluation, tables and final vector figures.
- Keep demo and full-data runs visibly distinct. Demo data should exercise data schemas and failure cases without being mistaken for study observations.
- Prevent silent replacement of frozen artifacts or overwriting source data; report failures clearly.

### 6. Verification and release record

- Run the workflow in a clean environment and preserve the run log and environment manifest.
- Compare cohort totals and every main claim against source-derived values, including 72,854 annual reports, 6,737,972 operations, 37,525 SSIs and the final test-set denominators, only when supported by the audited data.
- Verify main and supplementary figure/table values, point estimates, CIs, statistical tests and displayed rounding from machine-readable outputs.
- Audit vector PDFs/SVGs for embedded raster content, missing glyphs, font embedding and panel/legend consistency; do not claim true vector if the graphics contain source raster plots.
- Apply the user's ASCII hyphen-minus requirement to visible and extracted text in code documentation, figures and deliverables.
- Create a SHA-256 manifest of the release files and record the software version, tag, commit, archive DOI, manuscript version and test report.
- Resolve unexplained differences before declaring full reproduction. A partial pipeline should identify which outputs it verifies and which remain unverified.
- Before publication, obtain the authors' selected license and confirmed repository metadata, validate the release anonymously, and insert the real code citation/URL/DOI in the manuscript and reporting summary.

## Suggested minimal public release structure

```text
README.md
CITATION.cff
LICENSE
CHANGELOG.md
environment/
config/
src/
scripts/
data/README.md
data_dictionary/
demo/
model/
results/tables/
results/figures/
validation/
provenance/
manifest.sha256
```

This is a suggested structure. Every populated directory should contain real study material or be omitted; do not ship empty scaffolding and describe it as a completed reproducibility resource.

## Verified official sources

All links accessed 2026-10-22. Only publisher, repository-provider and platform-provider sources are listed.

- **S1.** Nature Medicine. Reporting standards and availability of data, materials, code and protocols. https://www.nature.com/nm/editorial-policies/reporting-standards . The live-page fetch was blocked by the publisher's identity redirect; the indexed official page supplied the policy text, including central-code availability, section placement, DOI repository, citation and licensing guidance.
- **S2.** Nature Portfolio. Guidelines for authors submitting code & software. https://www.nature.com/documents/GuidelinesCodePublication.pdf . Official two-page software submission and acceptance guidance. The separate dynamic checklist is at https://www.nature.com/documents/nr-software-policy.pdf and requires a compatible PDF reader; its fields were not treated as readable evidence here.
- **S3.** GitHub Docs. Referencing and citing content. https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content .
- **S4.** Zenodo. What is DOI versioning? https://support.zenodo.org/help/en-gb/1-upload-deposit/97-what-is-doi-versioning .
- **S5.** GitHub Docs. About CITATION files. https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files .
- **S6.** Zenodo. Describe software. https://help.zenodo.org/docs/github/describe-software/ .
- **S7.** GitHub Docs. Licensing a repository. https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository .
- **S8.** Zenodo. Create new upload. https://help.zenodo.org/docs/deposit/create-new-upload/ . DOI reservation instructions: https://help.zenodo.org/docs/deposit/describe-records/reserve-doi/ .

## Boundaries of this review

No repository was created, no archive was published, no DOI was reserved, no license was selected or legally approved, and no manuscript was edited as part of this policy review. The journal requirements should be checked again at actual submission if the journal updates its guidance or provides manuscript-specific instructions.

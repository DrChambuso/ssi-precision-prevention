# Source data, software and fonts

The original code license, once authorized, applies to original study code only. It does not replace source-data, Python/R dependency or font licenses.

## California surveillance

Provider: California Department of Public Health, Healthcare-Associated Infections Program, via the California Health and Human Services Open Data Portal. Source: https://data.chhs.ca.gov/dataset/surgical-site-infections-ssis-for-operative-procedures-in-california-hospitals . The retained metadata identifies "Terms of Use" as the data license. The exact 22 source resources and SHA-256 values are in `provenance/california_source_manifest.csv`. Public hospital names are source identifiers, not patient records. Published suppression is respected; missing/suppressed cells are not reconstructed as individual counts.

The supplied annual/source-row tables are derived public aggregates. Raw third-party source PDFs, proprietary fonts and unrelated author files are not part of the core release. Check provider terms before redistributing new source snapshots. An original source hash identifies bytes; it does not confer a data license.

## National microbiology

Provider: US Centers for Disease Control and Prevention, National Healthcare Safety Network. Original national pathogen and antimicrobial-resistance reports for 2015-2017 and 2018-2021 supply separate procedure, age and infection-depth context. Exact source locators, retained extraction tables and original parsing code are identified in the pipeline provenance. Checked PDF page-text extracts, when required by the retained parser, are documented as an intermediate extraction step; raw-PDF regeneration must not be represented as automated unless executed.

## Dependencies and fonts

Python and R packages retain their respective licenses. Dependencies are installed from their normal distributions, not relicensed or bundled as original study code. No Apple or Microsoft font file is redistributed. Historical finishing scripts that require Arial identify that local dependency; a metrically different substitute may change line wrapping and is not guaranteed to reproduce the exact final layout. The supplied final PDFs retain their own embedded font subsets.

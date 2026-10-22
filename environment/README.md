# Environment provenance

Core release checks were run with Python 3.12.14, NumPy 2.3.5 and pandas 2.2.3 on macOS arm64. `requirements-core.txt` pins the direct and transitive packages used by those checks. `tested_core_environment.json` records the actual runtime. R inference uses the packages in `tested_R_session.txt`; the central model scripts use base R and survival 3.8-3.

Historical analytical and plotting environments differ. `provenance/archived_audits/software_provenance_audit.json` distinguishes direct historical session output from reconstructed package versions. Do not describe the current core requirements as the exact environment of every original analysis or figure.

Figure regeneration may require the additional packages identified in `docs/FIGURES.md` and `docs/PIPELINE.md`. These are separate from the offline numerical demo. Original proprietary fonts are not redistributed.

Initial analysis reruns used the existing documented runtime. A separate fresh isolated Python environment then downloaded and installed all six pinned core requirements in 22.06 seconds (environment creation: 1.42 seconds). The relocated core demo and all 15 tests passed in that new environment. Fresh-demo whole-process times were 15.88 seconds for surveillance reconstruction including first imports, 0.87 seconds for all 180 frozen-model checks and 0.40 seconds for unit tests. See `validation/independent_release_review.json`. These measured times are specific to this host and network. This does not establish a fresh installation of every historical R/figure environment. A typical computer with at least 8 GB RAM is a practical starting point; full sensitivity-model memory requirements should be measured for the chosen environment.

# Manuscript version links

A GitHub repository landing page identifies the project. A full commit SHA permalink identifies a fixed version of its files. A tagged, immutable release can preserve the complete downloadable package associated with the manuscript. A GitHub URL is not a DOI.

The license remains pending institutional approval. Do not describe the code as open source. Do not enable automatic Zenodo archiving while no recognized software license is specified: Zenodo can apply its default license in that situation. A DOI deposit requires review of its actual rights metadata or institutional clarification.

Official guidance:

- GitHub licensing: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
- Commit permalinks: https://docs.github.com/en/repositories/working-with-files/using-files/getting-permanent-links-to-files
- Immutable releases: https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases
- Zenodo license fallback: https://support.zenodo.org/help/en-gb/24-github-integration/149-how-to-specify-a-license-for-a-software-record-on-github

The actual repository, commit and release URLs will be inserted only after creation and verification. No permanent public identifier is claimed by this preparation document.

## Verified repository and controlled import

The repository exists at https://github.com/DrChambuso/ssi-precision-prevention . The paper-associated version tag is v1.0.0-rc2. The final commit and release links are recorded after successful publication; this file does not mint a DOI.

The repository import workflow reads only its own draft release asset, authenticates the complete ZIP with an explicitly supplied SHA256, verifies every internal file checksum and rejects unsafe paths or workflow changes. It copies verified data and source files without running code from the archive, then commits them with the repository-scoped GitHub Actions token. The workflow is a publication transfer mechanism; it is not an independent statistical reanalysis.

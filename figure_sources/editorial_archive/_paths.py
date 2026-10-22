"""Resolve author-approved historical inputs without private absolute paths."""
from pathlib import Path
import os
def historical_path(logical):
    key, _, relative = logical.partition("/")
    env = {"workspace": "SSI_EDITORIAL_WORKSPACE", "project": "SSI_EDITORIAL_PROJECT", "fonts": "SSI_FONT_DIR", "unresolved": "SSI_EDITORIAL_UNRESOLVED"}[key]
    value = os.environ.get(env)
    if not value:
        raise RuntimeError(f"Archived source requires {env}; see docs/FIGURES.md. Final archived PDFs do not require these inputs.")
    return str(Path(value) / relative)

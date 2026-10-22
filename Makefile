PYTHON ?= python3

.PHONY: demo test check pipeline figures

demo:
	$(PYTHON) scripts/reconstruct_surveillance.py
	$(PYTHON) scripts/check_frozen_model.py --root .

test:
	$(PYTHON) -m unittest discover -s tests -v

check:
	$(PYTHON) scripts/audit_release.py

pipeline:
	$(PYTHON) scripts/legacy_pipeline.py run --stage prediction_prepare --stage prediction_fit --stage prediction_evaluate --stage prediction_diagnostics --stage prediction_verify --stage inferential --stage earlier_context --stage within_unit --stage severity_survival --stage inferential_verify --stage signal_bootstrap --stage case_bootstrap

figures:
	$(PYTHON) scripts/audit_vectors.py

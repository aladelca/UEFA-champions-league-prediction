.PHONY: setup clean-raw build-matches build-features leakage split-time experiments evaluate train simulate api test pipeline

PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)

setup:
	$(PYTHON) -m pip install -r requirements.txt

clean-raw:
	$(PYTHON) -m src.data.clean_raw

build-matches:
	$(PYTHON) -m src.data.build_matches_unique

build-features:
	$(PYTHON) -m src.features.build_pre_match_features

leakage:
	$(PYTHON) -m src.features.validators

split-time:
	$(PYTHON) -m src.modeling.split_time

experiments:
	$(PYTHON) -m src.modeling.run_experiments

evaluate:
	$(PYTHON) -m src.modeling.evaluate

train:
	$(PYTHON) -m src.modeling.train_match_model

simulate:
	$(PYTHON) -m src.simulation.aggregate_probs

api:
	uvicorn src.api.main:app --reload

test:
	$(PYTHON) -m pytest -q

pipeline:
	bash scripts/run_pipeline.sh

PYTHON ?= python
SEED ?= 42
CONFIG ?= config/params.yaml
OUTDIR ?=
RUN_ARGS = --seed $(SEED) --config $(CONFIG) $(if $(OUTDIR),--outdir $(OUTDIR),)

.PHONY: verify storage-check t0 t1 t2 t3 t4 all

verify:
	$(PYTHON) -m pytest -q
	$(PYTHON) -m src.common.schema

storage-check:
	$(PYTHON) -m src.data_prep.storage_check --seed $(SEED) --config $(CONFIG) $(if $(OUTDIR),--outdir $(OUTDIR),)

t0:
	$(PYTHON) -m src.pipeline t0 $(RUN_ARGS)

t1:
	$(PYTHON) -m src.pipeline t1 $(RUN_ARGS)

t2:
	$(PYTHON) -m src.pipeline t2 $(RUN_ARGS)

t3:
	$(PYTHON) -m src.pipeline t3 $(RUN_ARGS)

t4:
	$(PYTHON) -m src.pipeline t4 $(RUN_ARGS)

all: t0 t1 t2 t3 t4

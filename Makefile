PY ?= python3

.PHONY: help fetch solvers run site clean

help:
	@echo "make fetch    - download benchmark instances into instances/"
	@echo "make solvers  - compile the vendored Tanaka solvers into solvers/bin/"
	@echo "make run      - run solvers (ARGS='--dataset zhu --limit-per-class 10 --jobs 4')"
	@echo "make site     - build the static site into site/"

fetch:
	$(PY) scripts/fetch_instances.py

solvers:
	bash scripts/build_solvers.sh

run:
	$(PY) -m brpbench.run $(ARGS)

site:
	$(PY) -m brpbench.site $(ARGS)

clean:
	rm -rf site/data build
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	$(MAKE) -C solvers/tanaka_restricted_distinct_1.3 clean || true
	$(MAKE) -C solvers/tanaka_restricted_distinct_1.11 clean || true
	$(MAKE) -C solvers/tanaka_unrestricted_distinct_1.01 clean || true
	$(MAKE) -C solvers/tanaka_restricted_duplicate_1.02 clean || true
	$(MAKE) -C solvers/ucrp_idbb_jt23 clean || true
	$(MAKE) -C solvers/rcrp_idbb_jt23 clean || true

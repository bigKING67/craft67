PYTHON ?= python3

.PHONY: doctor lint test schema benchmark validate host-smoke package-check validate-all example upstream-check

doctor:
	$(PYTHON) skills/creative-craft/scripts/creative_craft.py doctor

lint:
	ruff check skills/creative-craft/scripts scripts tests

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"

schema:
	$(PYTHON) scripts/validate_schemas.py

benchmark:
	$(PYTHON) scripts/benchmark_unique_items.py

validate:
	$(PYTHON) scripts/validate.py

host-smoke:
	$(PYTHON) scripts/host_smoke.py

package-check:
	$(PYTHON) scripts/check_package.py

validate-all: lint schema validate host-smoke package-check
	$(PYTHON) skills/creative-craft/scripts/creative_craft.py self-test

example:
	$(PYTHON) skills/creative-craft/scripts/creative_craft.py compile-image \
		--file examples/premium-haircare-launch/image-job.json
	$(PYTHON) skills/creative-craft/scripts/creative_craft.py compile-video \
		--file examples/premium-haircare-launch/video-job.json
	$(PYTHON) skills/creative-craft/scripts/creative_craft.py validate-project \
		--root examples/premium-haircare-launch

# Read-only upstream drift report for docs/upstream-watch.json (needs gh + network; not part of validate-all).
upstream-check:
	$(PYTHON) scripts/upstream_drift.py

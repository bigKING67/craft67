export PYTHONDONTWRITEBYTECODE := 1

.PHONY: test lint schema validate package-check release-gate doctor

test:
	uv run --locked python -m unittest discover -s tests -p 'test_*.py'

lint:
	uv run --locked ruff check .

schema:
	uv run --locked python scripts/validate.py --schemas-only

validate:
	uv run --locked python scripts/validate.py

package-check:
	python3 scripts/package_check.py

release-gate:
	python3 scripts/release_gate.py

doctor:
	python3 skills/review-craft/scripts/review_craft.py doctor --json

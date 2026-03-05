.PHONY: setup demo test lint clean

PY := python3
EXAMPLES_BASELINE := examples/baseline
EXAMPLES_DEMO := examples/drifted
ARTIFACTS := artifacts
NOW := 2026-03-01T00:00:00Z

setup:
	@$(PY) -V
	@mkdir -p $(ARTIFACTS)

demo: setup
	@PYTHONPATH=src $(PY) -m portfolio_proof report --examples $(EXAMPLES_DEMO) --artifacts $(ARTIFACTS) --now $(NOW)
	@echo "Report generated at $(ARTIFACTS)/report.md"

test:
	@PYTHONPATH=src $(PY) -m unittest discover -s tests -p "test_*.py" -v

lint:
	@$(PY) -m compileall -q src
	@PYTHONPATH=src $(PY) -m portfolio_proof validate --examples $(EXAMPLES_BASELINE) --now $(NOW) >/dev/null

clean:
	@rm -rf $(ARTIFACTS) .pytest_cache .mypy_cache __pycache__

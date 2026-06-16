.PHONY: clean format lint requirements test

PYTHON_INTERPRETER ?= python3

requirements:
	$(PYTHON_INTERPRETER) -m pip install -U pip setuptools wheel
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt

format:
	ruff format src tests

lint:
	ruff check src tests

test:
	PYTHONPATH=src pytest tests
